from __future__ import annotations

import json
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .adapters import scan
from .analysis import analyze_wifi, local_ai_status, verify_services
from .storage import StateStore
from .webui import HTML

HOST = "127.0.0.1"
PORT = 8765
STORE = StateStore()

AGENTS = [
    {"name": "Supervisor", "role": "Scope + orchestration"},
    {"name": "Recon", "role": "Wi-Fi / Bluetooth / LAN discovery"},
    {"name": "Verification", "role": "Independent proof of observable exposure"},
    {"name": "AccessScope", "role": "Reachable services + resources"},
    {"name": "Evidence", "role": "Local reproducible evidence"},
    {"name": "Remediation", "role": "Patch guidance"},
    {"name": "Retest", "role": "Repeat validation after fixes"},
]


class AgentWhiteHandler(BaseHTTPRequestHandler):
    server_version = "AgentWhite/0.1"

    def log_message(self, fmt: str, *args: object) -> None:
        print(f"[AgentWhite] {self.address_string()} - {fmt % args}")

    def _json(self, payload: object, status: int = 200) -> None:
        data = json.dumps(payload, indent=2, default=str).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _html(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(data)

    def _body(self) -> dict:
        length = int(self.headers.get("Content-Length", "0") or 0)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            parsed = json.loads(raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            raise ValueError("Request body must be valid JSON.")
        if not isinstance(parsed, dict):
            raise ValueError("Request body must be a JSON object.")
        return parsed

    def do_GET(self) -> None:
        parsed = urlparse(self.path)
        if parsed.path == "/":
            self._html(HTML)
            return
        if parsed.path == "/api/state":
            self._json(
                {
                    "version": __version__,
                    "devices": STORE.list_devices(),
                    "findings": STORE.list_findings(),
                    "agents": AGENTS,
                    "ai": local_ai_status(),
                }
            )
            return
        if parsed.path == "/api/findings":
            query = parse_qs(parsed.query)
            device_id = query.get("device_id", [None])[0]
            self._json({"findings": STORE.list_findings(device_id=device_id)})
            return
        if parsed.path == "/api/export":
            self._json(
                {
                    "product": "AgentWhite",
                    "version": __version__,
                    "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "devices": STORE.list_devices(),
                    "findings": STORE.list_findings(),
                }
            )
            return
        self._json({"error": "Not found"}, status=404)

    def do_POST(self) -> None:
        try:
            body = self._body()
            if self.path == "/api/discover":
                self._discover(body)
                return
            if self.path == "/api/enroll":
                self._enroll(body)
                return
            if self.path in {"/api/verify", "/api/retest"}:
                self._verify(body)
                return
            self._json({"error": "Not found"}, status=404)
        except ValueError as exc:
            self._json({"error": str(exc)}, status=400)
        except Exception as exc:
            self._json({"error": f"AgentWhite error: {exc}"}, status=500)

    def _discover(self, body: dict) -> None:
        kind = str(body.get("kind", "all")).lower()
        devices = scan(kind)
        STORE.upsert_devices(devices)
        observations = []
        for device in devices:
            if device.get("kind") == "wifi":
                observations.extend(analyze_wifi(device))
        self._json(
            {
                "discovered": len(devices),
                "devices": devices,
                "passive_observations": observations,
            }
        )

    def _enroll(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        if not device_id:
            raise ValueError("device_id is required")
        enrolled = bool(body.get("enrolled", True))
        device = STORE.set_enrolled(device_id, enrolled)
        if not device:
            raise ValueError("Unknown device. Run discovery first.")
        self._json({"device": device})

    def _verify(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        if not device_id:
            raise ValueError("device_id is required")
        device = STORE.get_device(device_id)
        if not device:
            raise ValueError("Unknown device. Run discovery first.")
        if not device.get("enrolled"):
            self._json(
                {"error": "Active validation requires explicit target enrollment."},
                status=HTTPStatus.FORBIDDEN,
            )
            return

        findings: list[dict] = []
        if device["kind"] == "lan":
            address = str(device.get("address") or "")
            findings = verify_services(address)
        elif device["kind"] == "wifi":
            findings = analyze_wifi(device)
        elif device["kind"] == "bluetooth":
            self._json(
                {
                    "verified": 0,
                    "findings": [],
                    "message": "Bluetooth inventory is working; active BLE service/characteristic validators are the next hardware milestone.",
                }
            )
            return

        for finding in findings:
            STORE.add_finding(
                device_id=device_id,
                category=finding["category"],
                severity=finding["severity"],
                title=finding["title"],
                proof=finding["proof"],
                remediation=finding["remediation"],
            )
        self._json({"verified": len(findings), "findings": findings})


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AgentWhiteHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"AgentWhite {__version__} running locally at {url}")
    print("Press Ctrl+C to stop.")
    threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AgentWhite...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
