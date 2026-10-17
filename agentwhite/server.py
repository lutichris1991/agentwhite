from __future__ import annotations

import json
import os
import threading
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .adapters import scan
from .aiui import AI_HTML
from .analysis import analyze_wifi, fetch_http_resource, local_ai_status, verify_services, REMEDIATION
from .inspection import inspect_ble
from .local_ai import analyze_findings
from .storage import StateStore
from .webui import HTML

HOST = "127.0.0.1"
PORT = 8765
STORE = StateStore()

AGENTS = [
    {"name": "Supervisor", "role": "Scope + orchestration"},
    {"name": "Recon", "role": "Wi-Fi / Bluetooth / LAN discovery"},
    {"name": "Verification", "role": "Independent proof of observable exposure"},
    {"name": "AccessScope", "role": "Reachable services + post-access resource mapping"},
    {"name": "Evidence", "role": "Local reproducible evidence"},
    {"name": "Remediation", "role": "Patch guidance"},
    {"name": "Retest", "role": "Repeat validation after fixes"},
    {"name": "AI Analyst", "role": "Evidence-grounded local Ollama analysis"},
]


class AgentWhiteHandler(BaseHTTPRequestHandler):
    server_version = "AgentWhite/0.2"

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
            home = HTML.replace(
                '<a class="btn" href="/api/export"',
                '<a class="btn" href="/ai">AI Analyst</a>\n    <a class="btn" href="/api/export"',
                1,
            )
            self._html(home)
            return
        if parsed.path == "/ai":
            self._html(AI_HTML)
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
            if self.path == "/api/inspect":
                self._inspect(body)
                return
            if self.path == "/api/resource":
                self._resource(body)
                return
            if self.path == "/api/ai-analysis":
                self._ai_analysis(body)
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

    def _require_enrolled(self, device_id: str) -> dict:
        if not device_id:
            raise ValueError("device_id is required")
        device = STORE.get_device(device_id)
        if not device:
            raise ValueError("Unknown device. Run discovery first.")
        if not device.get("enrolled"):
            raise PermissionError("Active validation requires explicit target enrollment.")
        return device

    def _verify(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        try:
            device = self._require_enrolled(device_id)
        except PermissionError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.FORBIDDEN)
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
                    "message": "Use Inspect Access on this enrolled Bluetooth target to establish a BLE session and enumerate readable GATT resources.",
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

    def _inspect(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        try:
            device = self._require_enrolled(device_id)
        except PermissionError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.FORBIDDEN)
            return

        if device.get("kind") != "bluetooth":
            raise ValueError("Post-access inspection currently supports enrolled Bluetooth/BLE targets. LAN HTTP proof is available through the Resource Viewer.")

        address = str(device.get("address") or "")
        inspection = inspect_ble(address)
        readable = int(inspection.get("readable_count") or 0)
        connected = bool(inspection.get("connected"))
        STORE.add_finding(
            device_id=device_id,
            category="bluetooth-access-verification",
            severity="medium" if readable else "info",
            title=(
                f"BLE access verified: {readable} readable characteristic(s)"
                if connected
                else "BLE access session could not be established"
            ),
            proof={
                "address": address,
                "connected": connected,
                "service_count": inspection.get("service_count", 0),
                "characteristic_count": inspection.get("characteristic_count", 0),
                "readable_count": readable,
            },
            remediation=(
                "Review the exposed GATT characteristics and require pairing, bonding, encryption, or application-layer authorization for data that should not be readable by an ordinary nearby client. Remove unnecessary services and keep device firmware current."
            ),
            status="verified" if connected else "blocked",
        )
        self._json({"inspection": inspection})

    def _resource(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        try:
            device = self._require_enrolled(device_id)
        except PermissionError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.FORBIDDEN)
            return

        if device.get("kind") != "lan":
            raise ValueError("Resource viewing currently applies to enrolled LAN devices.")

        try:
            port = int(body.get("port"))
        except (TypeError, ValueError):
            raise ValueError("port must be an integer")
        path = str(body.get("path", "/") or "/")
        address = str(device.get("address") or "")
        result = fetch_http_resource(address, port, path)

        status = int(result.get("status") or 0)
        verified = 200 <= status < 400
        finding_status = "verified" if verified else "blocked"
        title = (
            f"HTTP resource access verified on TCP/{port}"
            if verified
            else f"HTTP resource access blocked or challenged on TCP/{port}"
        )
        proof = {
            key: value
            for key, value in result.items()
            if key not in {"image_data_url", "text_preview", "hex_preview"}
        }
        STORE.add_finding(
            device_id=device_id,
            category="resource-verification",
            severity="info",
            title=title,
            proof=proof,
            remediation=REMEDIATION.get(
                port,
                "Confirm this resource is intentionally reachable and protected by the expected authentication and network controls.",
            ),
            status=finding_status,
        )
        self._json({"verified": verified, "resource": result})

    def _ai_analysis(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        model = str(body.get("model", "")).strip() or None
        if device_id and not STORE.get_device(device_id):
            raise ValueError("Unknown device.")
        findings = STORE.list_findings(device_id=device_id or None)
        self._json(analyze_findings(findings, model=model))


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), AgentWhiteHandler)
    url = f"http://{HOST}:{PORT}"
    print(f"AgentWhite {__version__} running locally at {url}")
    print("Press Ctrl+C to stop.")
    if os.environ.get("AGENTWHITE_NO_BROWSER") != "1":
        threading.Timer(0.7, lambda: webbrowser.open(url)).start()
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping AgentWhite...")
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
