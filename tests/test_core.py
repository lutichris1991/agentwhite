import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from agentwhite.analysis import HTTP_PORTS, analyze_wifi, fetch_http_resource
from agentwhite.inspection import _format_value
from agentwhite.storage import StateStore


class AnalysisTests(unittest.TestCase):
    def test_wep_is_critical(self):
        device = {
            "name": "Lab-WEP",
            "address": "00:11:22:33:44:55",
            "details": {"authentication": "WEP", "encryption": "WEP"},
        }
        findings = analyze_wifi(device)
        self.assertEqual(findings[0]["severity"], "critical")

    def test_wpa3_is_informational(self):
        device = {
            "name": "Lab-WPA3",
            "address": "00:11:22:33:44:56",
            "details": {"authentication": "WPA3-Personal", "encryption": "CCMP"},
        }
        findings = analyze_wifi(device)
        self.assertEqual(findings[0]["severity"], "info")

    def test_resource_viewer_captures_and_hashes_local_text(self):
        class Handler(BaseHTTPRequestHandler):
            def do_GET(self):
                body = b"agentwhite-proof"
                self.send_response(200)
                self.send_header("Content-Type", "text/plain")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def log_message(self, fmt, *args):
                return

        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            port = server.server_port
            with tempfile.TemporaryDirectory() as tmp:
                with patch.dict(HTTP_PORTS, {port: False}), patch(
                    "agentwhite.analysis.data_dir", return_value=Path(tmp)
                ):
                    result = fetch_http_resource("127.0.0.1", port, "/")
                self.assertEqual(result["status"], 200)
                self.assertEqual(result["text_preview"], "agentwhite-proof")
                self.assertEqual(len(result["sha256"]), 64)
                self.assertTrue(Path(result["evidence_path"]).exists())
        finally:
            server.shutdown()
            server.server_close()


class InspectionTests(unittest.TestCase):
    def test_printable_ble_value_has_text_preview(self):
        result = _format_value(b"AgentWhite proof")
        self.assertEqual(result["text"], "AgentWhite proof")
        self.assertFalse(result["truncated"])

    def test_binary_ble_value_keeps_hex_preview(self):
        result = _format_value(bytes([0, 1, 2, 255]))
        self.assertIsNone(result["text"])
        self.assertEqual(result["hex"], "00 01 02 ff")

    def test_ble_value_is_bounded(self):
        result = _format_value(b"A" * 300, max_bytes=32)
        self.assertTrue(result["truncated"])
        self.assertEqual(result["bytes"], 300)
        self.assertEqual(len(result["text"]), 32)


class StorageTests(unittest.TestCase):
    def test_enrollment_persists(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            store.upsert_devices([
                {
                    "id": "lan-test",
                    "kind": "lan",
                    "name": "192.168.1.20",
                    "address": "192.168.1.20",
                    "details": {"mac": "00:11:22:33:44:55"},
                }
            ])
            updated = store.set_enrolled("lan-test", True)
            self.assertTrue(updated["enrolled"])
            self.assertTrue(store.get_device("lan-test")["enrolled"])

    def test_finding_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            store.upsert_devices([
                {
                    "id": "lan-test",
                    "kind": "lan",
                    "name": "192.168.1.20",
                    "address": "192.168.1.20",
                    "details": {},
                }
            ])
            store.add_finding(
                device_id="lan-test",
                category="service-exposure",
                severity="info",
                title="HTTP verified",
                proof={"port": 80},
                remediation="Restrict access.",
            )
            finding = store.list_findings("lan-test")[0]
            self.assertEqual(finding["proof"]["port"], 80)


if __name__ == "__main__":
    unittest.main()
