from __future__ import annotations

import json
import os
import threading
import time
import webbrowser
from datetime import datetime, timezone
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

from . import __version__
from .adapters import scan
from .aiui import AI_HTML
from .analysis import REMEDIATION, analyze_wifi, fetch_http_resource, local_ai_status, verify_services
from .inspection import inspect_ble
from .local_ai import analyze_findings
from .storage import StateStore
from .webui import HTML
from .workflow import available_actions

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
    {"name": "Workflow", "role": "Save engagement state and wait for the operator before every next action"},
    {"name": "AI Analyst", "role": "Evidence-grounded local Ollama analysis"},
]

ACTION_LABELS = {
    "wifi.configuration.audit": "Audit Wi-Fi Security Configuration",
    "lan.services.verify": "Verify Exposed Services",
    "bluetooth.gatt.inspect": "Inspect BLE Access",
}


class AgentWhiteHandler(BaseHTTPRequestHandler):
    server_version = "AgentWhite/0.3"

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
        if parsed.path == "/api/workspace":
            query = parse_qs(parsed.query)
            device_id = str(query.get("device_id", [""])[0]).strip()
            if not device_id:
                self._json({"error": "device_id is required"}, status=400)
                return
            try:
                self._json(self._workspace_payload(device_id))
            except ValueError as exc:
                self._json({"error": str(exc)}, status=400)
            return
        if parsed.path == "/api/findings":
            query = parse_qs(parsed.query)
            device_id = query.get("device_id", [None])[0]
            self._json({"findings": STORE.list_findings(device_id=device_id)})
            return
        if parsed.path == "/api/export":
            devices = STORE.list_devices()
            workspaces = []
            for device in devices:
                engagement = STORE.get_engagement(device["id"])
                if engagement:
                    workspaces.append(self._workspace_payload(device["id"]))
            self._json(
                {
                    "product": "AgentWhite",
                    "version": __version__,
                    "exported_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "devices": devices,
                    "findings": STORE.list_findings(),
                    "workspaces": workspaces,
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
            if self.path == "/api/action":
                self._run_action(body)
                return
            if self.path in {"/api/verify", "/api/retest"}:
                self._compat_verify(body)
                return
            if self.path == "/api/inspect":
                body = dict(body)
                body["action_id"] = "bluetooth.gatt.inspect"
                self._run_action(body)
                return
            if self.path == "/api/resource":
                self._resource(body)
                return
            if self.path == "/api/workspace/clear":
                self._clear_workspace(body)
                return
            if self.path == "/api/ai-analysis":
                self._ai_analysis(body)
                return
            self._json({"error": "Not found"}, status=404)
        except PermissionError as exc:
            self._json({"error": str(exc)}, status=HTTPStatus.FORBIDDEN)
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
        response = {"device": device}
        if enrolled:
            response["workspace"] = self._workspace_payload(device_id)
        else:
            response["message"] = "Target removed from active scope. Its workspace and prior evidence remain saved locally."
        self._json(response)

    def _require_enrolled(self, device_id: str) -> dict:
        if not device_id:
            raise ValueError("device_id is required")
        device = STORE.get_device(device_id)
        if not device:
            raise ValueError("Unknown device. Run discovery first.")
        if not device.get("enrolled"):
            raise PermissionError("Active validation requires explicit target enrollment.")
        return device

    def _workspace_payload(self, device_id: str) -> dict:
        device = STORE.get_device(device_id)
        if not device:
            raise ValueError("Unknown device.")
        engagement = STORE.get_engagement(device_id)
        findings = STORE.list_findings(device_id=device_id)
        access_sessions = STORE.list_access_sessions(device_id)
        actions = available_actions(device, findings, access_sessions) if device.get("enrolled") else []
        return {
            "device": device,
            "engagement": engagement,
            "available_actions": actions,
            "action_runs": STORE.list_action_runs(device_id),
            "access_sessions": access_sessions,
            "findings": findings,
        }

    def _save_findings(self, device_id: str, findings: list[dict]) -> list[int]:
        ids: list[int] = []
        for finding in findings:
            ids.append(
                STORE.add_finding(
                    device_id=device_id,
                    category=finding["category"],
                    severity=finding["severity"],
                    title=finding["title"],
                    proof=finding["proof"],
                    remediation=finding["remediation"],
                    status=str(finding.get("status") or "verified"),
                )
            )
        return ids

    def _run_action(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        action_id = str(body.get("action_id", "")).strip()
        device = self._require_enrolled(device_id)
        if action_id not in ACTION_LABELS:
            raise ValueError("Unsupported action. Select one of the actions offered by this target workspace.")

        expected_kind = {
            "wifi.configuration.audit": "wifi",
            "lan.services.verify": "lan",
            "bluetooth.gatt.inspect": "bluetooth",
        }[action_id]
        if device.get("kind") != expected_kind:
            raise ValueError("That action is not valid for this target type.")

        action_run_id = STORE.record_action_start(
            device_id=device_id,
            action_id=action_id,
            label=ACTION_LABELS[action_id],
        )
        started = time.perf_counter()
        result: dict = {}
        response_extra: dict = {}
        try:
            if action_id == "wifi.configuration.audit":
                findings = analyze_wifi(device)
                finding_ids = self._save_findings(device_id, findings)
                result = {
                    "findings_added": len(findings),
                    "finding_ids": finding_ids,
                    "summary": "Wi-Fi configuration audit completed. AgentWhite stopped and is waiting for your next selection.",
                }
            elif action_id == "lan.services.verify":
                address = str(device.get("address") or "")
                findings = verify_services(address)
                finding_ids = self._save_findings(device_id, findings)
                access_created: list[dict] = []
                for finding in findings:
                    proof = finding.get("proof") or {}
                    try:
                        port = int(proof.get("port"))
                    except (TypeError, ValueError):
                        continue
                    if port in {80, 443, 8000, 8080, 8443}:
                        scheme = "https" if port in {443, 8443} else "http"
                        endpoint = {"address": address, "port": port, "path": "/", "scheme": scheme}
                        session_id = STORE.upsert_access_session(
                            device_id=device_id,
                            access_key=f"http:{address}:{port}",
                            kind="http",
                            label=f"Reachable {scheme.upper()} service on TCP/{port}",
                            status="ready",
                            endpoint=endpoint,
                            obtained_via_action_run_id=action_run_id,
                        )
                        access_created.append({"id": session_id, **endpoint})
                result = {
                    "findings_added": len(findings),
                    "finding_ids": finding_ids,
                    "access_points_saved": access_created,
                    "summary": "Service verification completed. Any newly available access points are saved in this workspace; no follow-on test was started.",
                }
            elif action_id == "bluetooth.gatt.inspect":
                address = str(device.get("address") or "")
                inspection = inspect_ble(address)
                readable = int(inspection.get("readable_count") or 0)
                connected = bool(inspection.get("connected"))
                finding_id = STORE.add_finding(
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
                        "Review exposed GATT characteristics and require pairing, bonding, encryption, or application-layer authorization for data that should not be readable by an ordinary nearby client. Remove unnecessary services and keep device firmware current."
                    ),
                    status="verified" if connected else "blocked",
                )
                access_session_id = None
                if connected:
                    access_session_id = STORE.upsert_access_session(
                        device_id=device_id,
                        access_key=f"ble:{address}",
                        kind="bluetooth",
                        label="BLE GATT access",
                        status="reconnectable",
                        endpoint={
                            "address": address,
                            "service_count": inspection.get("service_count", 0),
                            "characteristic_count": inspection.get("characteristic_count", 0),
                            "readable_count": readable,
                        },
                        obtained_via_action_run_id=action_run_id,
                    )
                result = {
                    "finding_ids": [finding_id],
                    "access_session_id": access_session_id,
                    "connected": connected,
                    "readable_count": readable,
                    "summary": "BLE inspection completed. The logical access point is saved for navigation; AgentWhite did not start another test.",
                }
                response_extra["inspection"] = inspection

            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            STORE.complete_action(action_run_id, status="success", elapsed_ms=elapsed_ms, result=result)
            self._json(
                {
                    "action_run_id": action_run_id,
                    "result": result,
                    "workspace": self._workspace_payload(device_id),
                    **response_extra,
                }
            )
        except Exception as exc:
            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            STORE.complete_action(
                action_run_id,
                status="failed",
                elapsed_ms=elapsed_ms,
                result={"error": str(exc)},
            )
            raise

    def _compat_verify(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        device = self._require_enrolled(device_id)
        action_id = {
            "wifi": "wifi.configuration.audit",
            "lan": "lan.services.verify",
            "bluetooth": "bluetooth.gatt.inspect",
        }.get(str(device.get("kind")))
        if not action_id:
            raise ValueError("No verification action is available for this target.")
        compat_body = dict(body)
        compat_body["action_id"] = action_id
        self._run_action(compat_body)

    def _resource(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        device = self._require_enrolled(device_id)
        if device.get("kind") != "lan":
            raise ValueError("Resource viewing currently applies to enrolled LAN devices.")

        try:
            port = int(body.get("port"))
        except (TypeError, ValueError):
            raise ValueError("port must be an integer")
        path = str(body.get("path", "/") or "/")
        address = str(device.get("address") or "")
        action_run_id = STORE.record_action_start(
            device_id=device_id,
            action_id=f"http.resource.fetch:{port}",
            label=f"View Returned Material on TCP/{port}",
        )
        started = time.perf_counter()
        try:
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
            finding_id = STORE.add_finding(
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
            STORE.upsert_access_session(
                device_id=device_id,
                access_key=f"http:{address}:{port}",
                kind="http",
                label=f"HTTP access on TCP/{port}",
                status="ready" if verified else "challenged",
                endpoint={
                    "address": address,
                    "port": port,
                    "path": path,
                    "status": status,
                    "content_type": result.get("content_type"),
                    "sha256": result.get("sha256"),
                },
                obtained_via_action_run_id=action_run_id,
            )
            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            STORE.complete_action(
                action_run_id,
                status="success" if verified else "blocked",
                elapsed_ms=elapsed_ms,
                result={
                    "finding_id": finding_id,
                    "port": port,
                    "path": path,
                    "http_status": status,
                    "verified": verified,
                    "sha256": result.get("sha256"),
                },
            )
            self._json(
                {
                    "verified": verified,
                    "resource": result,
                    "action_run_id": action_run_id,
                    "workspace": self._workspace_payload(device_id),
                }
            )
        except Exception as exc:
            elapsed_ms = max(0, int((time.perf_counter() - started) * 1000))
            STORE.complete_action(
                action_run_id,
                status="failed",
                elapsed_ms=elapsed_ms,
                result={"error": str(exc)},
            )
            raise

    def _clear_workspace(self, body: dict) -> None:
        device_id = str(body.get("device_id", "")).strip()
        if not STORE.get_device(device_id):
            raise ValueError("Unknown device.")
        STORE.clear_workspace(device_id)
        self._json({"workspace": self._workspace_payload(device_id)})

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
