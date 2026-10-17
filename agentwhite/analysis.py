from __future__ import annotations

import base64
import hashlib
import http.client
import ipaddress
import json
import os
import socket
import ssl
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import data_dir

COMMON_PORTS: dict[int, str] = {
    22: "SSH",
    53: "DNS",
    80: "HTTP",
    139: "NetBIOS",
    443: "HTTPS",
    445: "SMB",
    554: "RTSP",
    631: "IPP",
    1883: "MQTT",
    3389: "RDP",
    5900: "VNC",
    8000: "HTTP-alt",
    8080: "HTTP-alt",
    8443: "HTTPS-alt",
    9100: "JetDirect",
}

HTTP_PORTS = {80: False, 443: True, 8000: False, 8080: False, 8443: True}

REMEDIATION: dict[int, str] = {
    22: "Restrict SSH to trusted management hosts, require strong key-based authentication, and disable unused accounts.",
    53: "Limit DNS service exposure to the clients that need it and disable unnecessary recursion from untrusted segments.",
    80: "If this management or device interface is not intentionally exposed, restrict it with host firewall/VLAN rules. Prefer authenticated HTTPS for administration.",
    139: "Disable legacy NetBIOS sharing where unnecessary and restrict file-sharing services to trusted network segments.",
    443: "Confirm the HTTPS service requires authentication, is fully patched, and is reachable only from intended management/client networks.",
    445: "Restrict SMB to trusted hosts/VLANs, require authentication, disable SMBv1, and review share permissions for least privilege.",
    554: "Require authentication for RTSP/video streams, disable anonymous viewing, update device firmware, and isolate cameras on a restricted VLAN.",
    631: "Restrict printer/IPP management to trusted hosts and disable remote administration if it is not needed.",
    1883: "Require MQTT authentication and TLS where supported, disable anonymous publish/subscribe, and restrict broker access by network policy.",
    3389: "Restrict RDP to trusted management paths, require Network Level Authentication and MFA where available, and keep the host fully patched.",
    5900: "Disable VNC if unused; otherwise require strong authentication/encryption and restrict access to trusted management hosts.",
    8000: "Confirm the alternate web service is intentional, authenticated, patched, and restricted to the network segments that require it.",
    8080: "Confirm the alternate web service is intentional, authenticated, patched, and restricted to the network segments that require it.",
    8443: "Confirm the alternate HTTPS service is intentional, authenticated, patched, and restricted to trusted management/client networks.",
    9100: "Restrict raw printer access to trusted clients and block the port across guest or untrusted VLANs.",
}


def _private_or_local_ip(value: str) -> bool:
    try:
        ip = ipaddress.ip_address(value)
    except ValueError:
        return False
    return bool(ip.is_private or ip.is_loopback or ip.is_link_local)


def verify_services(address: str, timeout: float = 0.35) -> list[dict[str, Any]]:
    """Conservatively verify common TCP services on an enrolled local target."""
    if not _private_or_local_ip(address):
        raise ValueError("Active validation is limited to private, loopback, or link-local IP addresses.")

    findings: list[dict[str, Any]] = []
    for port, service in COMMON_PORTS.items():
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(timeout)
        try:
            result = sock.connect_ex((address, port))
        finally:
            sock.close()
        if result != 0:
            continue

        proof: dict[str, Any] = {
            "address": address,
            "port": port,
            "service": service,
            "tcp_connection": "succeeded",
        }
        if port in {80, 8000, 8080}:
            proof.update(_http_metadata(address, port, tls=False))
        elif port in {443, 8443}:
            proof.update(_http_metadata(address, port, tls=True))

        severity = "medium" if port in {445, 554, 1883, 3389, 5900} else "info"
        findings.append(
            {
                "category": "service-exposure",
                "severity": severity,
                "title": f"{service} service verified on TCP/{port}",
                "proof": proof,
                "remediation": REMEDIATION.get(
                    port,
                    "Confirm this service is intentional, patched, authenticated where appropriate, and restricted to the network segments that need it.",
                ),
                "open_url": _service_url(address, port),
            }
        )
    return findings


def _service_url(address: str, port: int) -> str | None:
    if port in {80, 8000, 8080}:
        return f"http://{address}:{port}/"
    if port in {443, 8443}:
        return f"https://{address}:{port}/"
    return None


def _http_metadata(address: str, port: int, tls: bool) -> dict[str, Any]:
    scheme = "https" if tls else "http"
    request = urllib.request.Request(
        f"{scheme}://{address}:{port}/",
        method="HEAD",
        headers={"User-Agent": "AgentWhite/0.1"},
    )
    try:
        with urllib.request.urlopen(request, timeout=1.2) as response:
            return {
                "http_status": response.status,
                "server_header": response.headers.get("Server"),
            }
    except urllib.error.HTTPError as exc:
        return {"http_status": exc.code, "server_header": exc.headers.get("Server")}
    except Exception:
        return {}


def _safe_evidence_suffix(content_type: str) -> str:
    ctype = content_type.lower()
    if ctype == "image/jpeg":
        return ".jpg"
    if ctype == "image/png":
        return ".png"
    if ctype == "image/gif":
        return ".gif"
    if ctype == "image/webp":
        return ".webp"
    if ctype in {"application/json", "text/json"}:
        return ".json"
    if "html" in ctype:
        return ".html"
    if ctype.startswith("text/"):
        return ".txt"
    return ".bin"


def fetch_http_resource(
    address: str,
    port: int,
    path: str = "/",
    *,
    max_bytes: int = 524_288,
) -> dict[str, Any]:
    """Fetch one explicitly requested resource from an enrolled local HTTP(S) service.

    This does not follow redirects or attempt authentication bypass. It is used to prove
    what an already-reachable enrolled service actually returns.
    """
    if not _private_or_local_ip(address):
        raise ValueError("Resource viewing is limited to private, loopback, or link-local IP addresses.")
    if port not in HTTP_PORTS:
        raise ValueError("Resource viewing is only available for verified HTTP/HTTPS service ports.")
    if not path.startswith("/") or "\r" in path or "\n" in path or "://" in path:
        raise ValueError("path must be a local HTTP path beginning with '/'.")

    tls = HTTP_PORTS[port]
    if tls:
        context = ssl._create_unverified_context()
        conn: http.client.HTTPConnection = http.client.HTTPSConnection(address, port, timeout=2.5, context=context)
    else:
        conn = http.client.HTTPConnection(address, port, timeout=2.5)

    try:
        conn.request(
            "GET",
            path,
            headers={
                "User-Agent": "AgentWhite/0.1",
                "Accept": "*/*",
                "Connection": "close",
            },
        )
        response = conn.getresponse()
        raw = response.read(max_bytes + 1)
        truncated = len(raw) > max_bytes
        raw = raw[:max_bytes]
        content_type = (response.getheader("Content-Type") or "application/octet-stream").split(";", 1)[0].strip().lower()
        digest = hashlib.sha256(raw).hexdigest()

        evidence_dir = data_dir() / "evidence"
        evidence_dir.mkdir(parents=True, exist_ok=True)
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        safe_addr = address.replace(":", "_").replace("/", "_")
        filename = f"{safe_addr}_{port}_{stamp}{_safe_evidence_suffix(content_type)}"
        evidence_path = evidence_dir / filename
        if raw:
            evidence_path.write_bytes(raw)

        result: dict[str, Any] = {
            "address": address,
            "port": port,
            "path": path,
            "status": response.status,
            "reason": response.reason,
            "content_type": content_type,
            "bytes_captured": len(raw),
            "truncated": truncated,
            "sha256": digest,
            "evidence_path": str(evidence_path) if raw else None,
            "headers": {
                "server": response.getheader("Server"),
                "content_length": response.getheader("Content-Length"),
                "www_authenticate": response.getheader("WWW-Authenticate"),
                "location": response.getheader("Location"),
            },
        }

        if content_type in {"image/jpeg", "image/png", "image/gif", "image/webp"} and raw:
            result["image_data_url"] = f"data:{content_type};base64,{base64.b64encode(raw).decode('ascii')}"
        elif (
            content_type.startswith("text/")
            or content_type in {"application/json", "application/xml", "application/javascript"}
        ):
            result["text_preview"] = raw.decode("utf-8", "replace")
        elif raw:
            result["hex_preview"] = raw[:256].hex(" ")

        return result
    except (OSError, http.client.HTTPException) as exc:
        raise ValueError(f"Could not retrieve resource: {exc}") from exc
    finally:
        conn.close()


def analyze_wifi(device: dict[str, Any]) -> list[dict[str, Any]]:
    auth = str(device.get("details", {}).get("authentication", "Unknown")).upper()
    encryption = str(device.get("details", {}).get("encryption", "Unknown")).upper()
    proof = {
        "ssid": device.get("name"),
        "bssid": device.get("address"),
        "authentication": device.get("details", {}).get("authentication"),
        "encryption": device.get("details", {}).get("encryption"),
    }

    if any(token in auth for token in ("OPEN", "NONE")) or encryption in {"NONE", "OPEN"}:
        return [{
            "category": "wifi-configuration",
            "severity": "high",
            "title": "Open Wi-Fi authentication detected",
            "proof": proof,
            "remediation": "Enable WPA2-AES or preferably WPA3, use a strong unique passphrase, and disable any intentionally unused open SSID.",
        }]
    if "WEP" in auth or "WEP" in encryption:
        return [{
            "category": "wifi-configuration",
            "severity": "critical",
            "title": "WEP detected",
            "proof": proof,
            "remediation": "Replace WEP immediately with WPA2-AES or WPA3. WEP should be treated as cryptographically broken.",
        }]
    if "WPA3" in auth:
        return [{
            "category": "wifi-configuration",
            "severity": "info",
            "title": "WPA3 detected",
            "proof": proof,
            "remediation": "Keep router/AP firmware current and review whether Protected Management Frames are required by the access point.",
        }]
    if "WPA2" in auth:
        return [{
            "category": "wifi-configuration",
            "severity": "info",
            "title": "WPA2 detected",
            "proof": proof,
            "remediation": "Use AES/CCMP with a strong unique passphrase, disable legacy compatibility when possible, and migrate to WPA3 when supported.",
        }]
    if "WPA" in auth:
        return [{
            "category": "wifi-configuration",
            "severity": "medium",
            "title": "Legacy WPA configuration detected",
            "proof": proof,
            "remediation": "Migrate the network to WPA2-AES or WPA3 and disable TKIP/legacy WPA compatibility if clients no longer require it.",
        }]
    return []


def local_ai_status() -> dict[str, Any]:
    """Check whether a local Ollama installation/model can be used offline."""
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.4) as response:
            payload = json.loads(response.read().decode("utf-8"))
        models = [m.get("name") for m in payload.get("models", []) if m.get("name")]
        preferred = os.environ.get("AGENTWHITE_MODEL")
        model = preferred if preferred in models else (models[0] if models else None)
        return {"available": bool(model), "model": model, "models": models}
    except Exception:
        return {"available": False, "model": None, "models": []}
