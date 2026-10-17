import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from unittest.mock import patch

from agentwhite.analysis import HTTP_PORTS, analyze_wifi, fetch_http_resource
from agentwhite.inspection import _format_value
from agentwhite.storage import StateStore
from agentwhite.workflow import available_actions


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
    @staticmethod
    def _seed(store: StateStore, kind: str = "lan", device_id: str = "lan-test") -> None:
        store.upsert_devices([
            {
                "id": device_id,
                "kind": kind,
                "name": "Test Target",
                "address": "192.168.1.20" if kind == "lan" else "00:11:22:33:44:55",
                "details": {"mac": "00:11:22:33:44:55"},
            }
        ])

    def test_enrollment_persists_and_creates_engagement(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            self._seed(store)
            updated = store.set_enrolled("lan-test", True)
            self.assertTrue(updated["enrolled"])
            self.assertEqual(store.get_engagement("lan-test")["status"], "active")

    def test_pause_scope_keeps_engagement_history(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            self._seed(store)
            store.set_enrolled("lan-test", True)
            run_id = store.record_action_start(device_id="lan-test", action_id="lab.test", label="Lab Test")
            store.complete_action(run_id, status="success", elapsed_ms=42, result={"ok": True})
            store.set_enrolled("lan-test", False)
            self.assertEqual(store.get_engagement("lan-test")["status"], "paused")
            self.assertEqual(store.list_action_runs("lan-test")[0]["elapsed_ms"], 42)

    def test_action_run_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            self._seed(store)
            store.set_enrolled("lan-test", True)
            run_id = store.record_action_start(device_id="lan-test", action_id="lan.services.verify", label="Verify Services")
            store.complete_action(run_id, status="success", elapsed_ms=123, result={"ports": [80]})
            run = store.list_action_runs("lan-test")[0]
            self.assertEqual(run["status"], "success")
            self.assertEqual(run["result"]["ports"], [80])

    def test_access_session_is_saved_and_updated(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            self._seed(store)
            store.set_enrolled("lan-test", True)
            first = store.upsert_access_session(
                device_id="lan-test",
                access_key="http:192.168.1.20:80",
                kind="http",
                label="HTTP",
                status="ready",
                endpoint={"address": "192.168.1.20", "port": 80, "path": "/"},
            )
            second = store.upsert_access_session(
                device_id="lan-test",
                access_key="http:192.168.1.20:80",
                kind="http",
                label="HTTP",
                status="ready",
                endpoint={"address": "192.168.1.20", "port": 80, "path": "/status"},
            )
            self.assertEqual(first, second)
            sessions = store.list_access_sessions("lan-test")
            self.assertEqual(len(sessions), 1)
            self.assertEqual(sessions[0]["endpoint"]["path"], "/status")

    def test_finding_round_trip(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = StateStore(Path(tmp) / "test.db")
            self._seed(store)
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


class WorkflowTests(unittest.TestCase):
    def test_wifi_workspace_only_proposes_action(self):
        device = {"kind": "wifi", "id": "wifi-1"}
        actions = available_actions(device, [], [])
        self.assertEqual(actions[0]["id"], "wifi.configuration.audit")
        self.assertTrue(actions[0]["repeatable"])

    def test_http_finding_unlocks_view_button_without_running_it(self):
        device = {"kind": "lan", "id": "lan-1"}
        findings = [{"category": "service-exposure", "proof": {"port": 443}}]
        actions = available_actions(device, findings, [])
        ids = [a["id"] for a in actions]
        self.assertIn("http.resource.inspect:443", ids)


if __name__ == "__main__":
    unittest.main()
