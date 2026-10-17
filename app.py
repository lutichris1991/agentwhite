from __future__ import annotations

import asyncio
import html
import ipaddress
import json
import os
import platform
import re
import socket
import sqlite3
import subprocess
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from flask import Flask, jsonify, request, Response

APP_NAME = "AgentWhite"
VERSION = "0.1.0"
BASE_DIR = Path(os.getenv("AGENTWHITE_HOME", Path.home() / ".agentwhite"))
BASE_DIR.mkdir(parents=True, exist_ok=True)
EVIDENCE_DIR = BASE_DIR / "evidence"
EVIDENCE_DIR.mkdir(exist_ok=True)
DB_PATH = BASE_DIR / "agentwhite.db"

COMMON_PORTS = {
    21: "FTP", 22: "SSH", 23: "Telnet", 53: "DNS", 80: "HTTP",
    139: "NetBIOS", 443: "HTTPS", 445: "SMB", 554: "RTSP",
    1883: "MQTT", 3389: "RDP", 5353: "mDNS", 8000: "HTTP-alt",
    8080: "HTTP-alt", 8443: "HTTPS-alt", 9100: "Printer"
}
HTTP_PORTS = {80: "http", 443: "https", 8000: "http", 8080: "http", 8443: "https"}

app = Flask(__name__)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with db() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS targets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            label TEXT NOT NULL,
            host TEXT NOT NULL UNIQUE,
            kind TEXT NOT NULL DEFAULT 'network',
            authorized INTEGER NOT NULL DEFAULT 1,
            created_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS findings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            target_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            severity TEXT NOT NULL,
            title TEXT NOT NULL,
            detail TEXT NOT NULL,
            evidence_json TEXT,
            remediation TEXT,
            created_at TEXT NOT NULL,
            FOREIGN KEY(target_id) REFERENCES targets(id)
        );
        """)


def run_command(args: list[str], timeout: int = 12) -> str:
    try:
        cp = subprocess.run(args, capture_output=True, text=True, timeout=timeout,
                            creationflags=(subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0))
        return (cp.stdout or "") + (cp.stderr or "")
    except Exception:
        return ""


def windows_wifi() -> dict[str, Any]:
    if os.name != "nt":
        return {"supported": False, "reason": "Windows netsh collector is only available on Windows."}
    interface_text = run_command(["netsh", "wlan", "show", "interfaces"])
    networks_text = run_command(["netsh", "wlan", "show", "networks", "mode=bssid"])
    connected = {}
    for line in interface_text.splitlines():
        if ":" not in line:
            continue
        k, v = [x.strip() for x in line.split(":", 1)]
        key = k.lower()
        if key in {"name", "description", "guid", "physical address", "state", "ssid", "bssid",
                   "network type", "radio type", "authentication", "cipher", "channel",
                   "receive rate (mbps)", "transmit rate (mbps)", "signal"}:
            connected[key] = v

    networks = []
    current = None
    for raw in networks_text.splitlines():
        line = raw.strip()
        m = re.match(r"SSID\s+\d+\s*:\s*(.*)", line)
        if m:
            if current:
                networks.append(current)
            current = {"ssid": m.group(1) or "<hidden>", "bssids": []}
            continue
        if current is None:
            continue
        m = re.match(r"Authentication\s*:\s*(.*)", line)
        if m:
            current["authentication"] = m.group(1)
        m = re.match(r"Encryption\s*:\s*(.*)", line)
        if m:
            current["encryption"] = m.group(1)
        m = re.match(r"BSSID\s+\d+\s*:\s*(.*)", line)
        if m:
            current["bssids"].append({"bssid": m.group(1)})
        elif line.startswith("Signal") and current["bssids"]:
            current["bssids"][-1]["signal"] = line.split(":", 1)[1].strip()
        elif line.startswith("Radio type") and current["bssids"]:
            current["bssids"][-1]["radio"] = line.split(":", 1)[1].strip()
        elif line.startswith("Channel") and current["bssids"]:
            current["bssids"][-1]["channel"] = line.split(":", 1)[1].strip()
    if current:
        networks.append(current)
    return {"supported": True, "connected": connected, "networks": networks}


def local_ipv4() -> str:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("8.8.8.8", 80))
        return s.getsockname()[0]
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"
    finally:
        s.close()


def arp_table() -> list[dict[str, str]]:
    text = run_command(["arp", "-a"])
    rows = []
    for line in text.splitlines():
        m = re.search(r"(\d{1,3}(?:\.\d{1,3}){3})\s+([0-9a-fA-F:-]{11,17})\s+(\w+)", line)
        if m:
            rows.append({"ip": m.group(1), "mac": m.group(2), "type": m.group(3)})
    return rows


def ping_host(host: str) -> bool:
    cmd = ["ping", "-n" if os.name == "nt" else "-c", "1",
           "-w" if os.name == "nt" else "-W", "250" if os.name == "nt" else "1", host]
    out = run_command(cmd, timeout=2)
    return "TTL=" in out.upper() or "bytes from" in out.lower()


def discover_lan() -> dict[str, Any]:
    ip = local_ipv4()
    try:
        net = ipaddress.ip_network(f"{ip}/24", strict=False)
    except Exception:
        return {"local_ip": ip, "devices": arp_table(), "note": "Could not derive local /24 network."}

    hosts = [str(h) for h in net.hosts()]
    # A light presence sweep. It does not attempt authentication or exploitation.
    with ThreadPoolExecutor(max_workers=48) as ex:
        futures = {ex.submit(ping_host, h): h for h in hosts}
        for fut in as_completed(futures):
            try:
                fut.result()
            except Exception:
                pass
    seen = {x["ip"]: x for x in arp_table()}
    seen.setdefault(ip, {"ip": ip, "mac": "local", "type": "this-device"})
    return {"local_ip": ip, "network": str(net), "devices": list(seen.values())}


async def _ble_scan() -> list[dict[str, Any]]:
    try:
        from bleak import BleakScanner
    except Exception:
        return [{"error": "Bleak is not installed in this build."}]
    devices = await BleakScanner.discover(timeout=7.0, return_adv=True)
    out = []
    for address, pair in devices.items():
        dev, adv = pair
        out.append({
            "name": dev.name or adv.local_name or "Unknown BLE device",
            "address": address,
            "rssi": getattr(adv, "rssi", None),
            "service_uuids": list(getattr(adv, "service_uuids", []) or []),
            "manufacturer_ids": list((getattr(adv, "manufacturer_data", {}) or {}).keys()),
        })
    return out


def ble_scan() -> list[dict[str, Any]]:
    try:
        return asyncio.run(_ble_scan())
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_ble_scan())
        finally:
            loop.close()
    except Exception as e:
        return [{"error": str(e)}]


def validate_host(host: str) -> str:
    host = host.strip()
    try:
        ipaddress.ip_address(host)
        return host
    except ValueError:
        if re.fullmatch(r"[a-zA-Z0-9._-]{1,253}", host):
            return host
        raise ValueError("Invalid target host.")


def get_target(target_id: int) -> sqlite3.Row:
    with db() as conn:
        row = conn.execute("SELECT * FROM targets WHERE id=?", (target_id,)).fetchone()
    if not row:
        raise KeyError("Target not found")
    if not row["authorized"]:
        raise PermissionError("Target is not authorized for active checks.")
    return row


def tcp_probe(host: str, port: int, timeout: float = 0.55) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            latency = round((time.perf_counter() - started) * 1000, 1)
            sock.settimeout(0.35)
            banner = ""
            try:
                if port in (21, 22, 23, 25, 110, 143):
                    banner = sock.recv(256).decode("utf-8", errors="replace").strip()
            except Exception:
                pass
            return {"port": port, "service": COMMON_PORTS.get(port, "unknown"), "open": True,
                    "latency_ms": latency, "banner": banner[:200]}
    except Exception:
        return {"port": port, "service": COMMON_PORTS.get(port, "unknown"), "open": False}


def remediation_for_port(port: int) -> str:
    rules = {
        21: "Disable FTP where possible or replace it with SFTP/HTTPS. Restrict access with host firewall rules.",
        22: "Restrict SSH to trusted management hosts, require strong keys, disable password login where practical, and keep the server patched.",
        23: "Disable Telnet. It transmits credentials and session data without modern transport protection.",
        80: "If this is an administration interface, prefer HTTPS and restrict it to trusted management networks.",
        443: "Review TLS configuration, authentication requirements, firmware/software version, and whether the interface needs to be reachable from this segment.",
        445: "Restrict SMB to trusted networks, disable SMBv1, require authentication, and review share/NTFS permissions.",
        554: "Require RTSP authentication, update camera/NVR firmware, segment cameras, and firewall the stream from unnecessary clients.",
        1883: "Require MQTT authentication and TLS where supported, restrict topic permissions, and isolate IoT brokers.",
        3389: "Restrict RDP by firewall/VPN, require Network Level Authentication and MFA where available, and keep Windows patched.",
        8000: "Confirm the web service requires authentication and is intended to be reachable from this network.",
        8080: "Confirm the web service requires authentication and is intended to be reachable from this network.",
        8443: "Review authentication and TLS settings; restrict management interfaces to trusted hosts.",
        9100: "Restrict raw printer access to trusted clients and isolate printers from sensitive network segments.",
    }
    return rules.get(port, "Confirm this service is required, patched, authenticated, and reachable only from intended network segments.")


def record_finding(target_id: int, category: str, severity: str, title: str, detail: str,
                   evidence: dict[str, Any] | None, remediation: str) -> int:
    with db() as conn:
        cur = conn.execute(
            """INSERT INTO findings(target_id,category,severity,title,detail,evidence_json,remediation,created_at)
               VALUES(?,?,?,?,?,?,?,?)""",
            (target_id, category, severity, title, detail,
             json.dumps(evidence or {}), remediation, now_iso())
        )
        return int(cur.lastrowid)


def scan_target(target_id: int) -> dict[str, Any]:
    target = get_target(target_id)
    host = target["host"]
    results = []
    with ThreadPoolExecutor(max_workers=min(24, len(COMMON_PORTS))) as ex:
        futures = [ex.submit(tcp_probe, host, p) for p in COMMON_PORTS]
        for fut in as_completed(futures):
            results.append(fut.result())
    results.sort(key=lambda x: x["port"])
    open_ports = [r for r in results if r["open"]]
    finding_ids = []
    for r in open_ports:
        severity = "medium" if r["port"] in {21, 23, 445, 554, 1883, 3389} else "info"
        title = f"{r['service']} service reachable on TCP/{r['port']}"
        detail = f"AgentWhite established a TCP connection to {host}:{r['port']}."
        finding_ids.append(record_finding(target_id, "service", severity, title, detail, r,
                                          remediation_for_port(r["port"])))
    return {"target": dict(target), "ports": results, "open_ports": open_ports, "finding_ids": finding_ids}


def safe_url_for_target(target: sqlite3.Row, scheme: str, port: int, path: str) -> str:
    if scheme not in {"http", "https"}:
        raise ValueError("Only HTTP/HTTPS verification is supported in v0.1.")
    if not (1 <= int(port) <= 65535):
        raise ValueError("Invalid port.")
    if not path.startswith("/"):
        path = "/" + path
    return f"{scheme}://{target['host']}:{int(port)}{path}"


def verify_http(target_id: int, scheme: str, port: int, path: str = "/") -> dict[str, Any]:
    target = get_target(target_id)
    url = safe_url_for_target(target, scheme, port, path)
    req = urllib.request.Request(url, headers={"User-Agent": f"AgentWhite/{VERSION}"})
    context = None
    if scheme == "https":
        import ssl
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
    try:
        with urllib.request.urlopen(req, timeout=5, context=context) as resp:
            content_type = resp.headers.get("Content-Type", "")
            body = resp.read(262144)
            status = resp.status
            headers = dict(resp.headers.items())
    except urllib.error.HTTPError as e:
        status = e.code
        content_type = e.headers.get("Content-Type", "")
        headers = dict(e.headers.items())
        body = e.read(262144)
    except Exception as e:
        return {"ok": False, "url": url, "error": str(e)}

    evidence: dict[str, Any] = {
        "url": url, "status": status, "content_type": content_type,
        "headers": headers, "bytes_captured": len(body)
    }
    if content_type.lower().startswith("text/") or "json" in content_type.lower() or "xml" in content_type.lower() or "javascript" in content_type.lower():
        evidence["text_preview"] = body.decode("utf-8", errors="replace")[:12000]
    elif content_type.lower().startswith("image/"):
        lower_ct = content_type.lower()
        ext = ".jpg" if "jpeg" in lower_ct else ".png" if "png" in lower_ct else ".bin"
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        evidence_file = EVIDENCE_DIR / f"target-{target_id}-{stamp}{ext}"
        evidence_file.write_bytes(body)
        evidence["evidence_file"] = str(evidence_file)

    auth_header = headers.get("WWW-Authenticate")
    severity = "high" if status < 400 and not auth_header else "info"
    title = "HTTP resource returned content" if status < 400 else f"HTTP endpoint returned status {status}"
    detail = f"Verification request to {url} returned HTTP {status} and {len(body)} bytes."
    remediation = ("If this resource is sensitive or administrative, require authentication and restrict it to intended clients. "
                   "For cameras and IoT devices, segment the device and disable unauthenticated web/stream endpoints.")
    finding_id = record_finding(target_id, "verification", severity, title, detail, evidence, remediation)
    return {"ok": True, "finding_id": finding_id, **evidence}


def ollama_status() -> dict[str, Any]:
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/tags", timeout=0.7) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        models = [m.get("name") for m in data.get("models", [])]
        return {"available": True, "models": models}
    except Exception:
        return {"available": False, "models": []}


def offline_analysis(target_id: int) -> dict[str, Any]:
    target = get_target(target_id)
    with db() as conn:
        rows = conn.execute("SELECT * FROM findings WHERE target_id=? ORDER BY id DESC LIMIT 100", (target_id,)).fetchall()
    findings = [dict(r) for r in rows]
    severity_weight = {"critical": 25, "high": 15, "medium": 8, "low": 3, "info": 1}
    deductions = sum(severity_weight.get(f["severity"], 1) for f in findings)
    score = max(0, 100 - min(100, deductions))
    priorities = []
    seen = set()
    for f in findings:
        rem = f["remediation"]
        if rem and rem not in seen:
            seen.add(rem)
            priorities.append({"severity": f["severity"], "finding": f["title"], "fix": rem})
    return {
        "target": dict(target), "score": score,
        "summary": f"{len(findings)} findings recorded. Security score {score}/100 based on currently validated observations.",
        "priorities": priorities[:10],
        "engine": "AgentWhite offline rules"
    }


def ollama_analysis(target_id: int, model: str) -> dict[str, Any]:
    base = offline_analysis(target_id)
    with db() as conn:
        rows = conn.execute("SELECT severity,title,detail,remediation FROM findings WHERE target_id=? ORDER BY id DESC LIMIT 40",
                            (target_id,)).fetchall()
    prompt = (
        "You are AgentWhite, an offline defensive security analyst. Analyze only these findings from an explicitly "
        "authorized target. Do not invent access or vulnerabilities. Explain what was actually verified, prioritize "
        "remediation, and give a concise retest checklist. Return plain text.\n\n"
        + json.dumps([dict(r) for r in rows], indent=2)
    )
    payload = json.dumps({"model": model, "prompt": prompt, "stream": False}).encode()
    req = urllib.request.Request("http://127.0.0.1:11434/api/generate", data=payload,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode())
        base["engine"] = f"Ollama/{model}"
        base["ai_text"] = data.get("response", "")
    except Exception as e:
        base["ai_error"] = str(e)
    return base


@app.get("/")
def index() -> Response:
    return Response(INDEX_HTML, mimetype="text/html")


@app.get("/api/status")
def api_status():
    return jsonify({
        "name": APP_NAME, "version": VERSION, "platform": platform.platform(),
        "data_dir": str(BASE_DIR), "local_ip": local_ipv4(), "ollama": ollama_status()
    })


@app.get("/api/wifi")
def api_wifi():
    return jsonify(windows_wifi())


@app.post("/api/discover/lan")
def api_discover_lan():
    return jsonify(discover_lan())


@app.post("/api/discover/ble")
def api_discover_ble():
    return jsonify({"devices": ble_scan()})


@app.get("/api/targets")
def api_targets():
    with db() as conn:
        rows = conn.execute("SELECT * FROM targets ORDER BY id DESC").fetchall()
    return jsonify([dict(r) for r in rows])


@app.post("/api/targets")
def api_add_target():
    data = request.get_json(force=True)
    if data.get("authorization_ack") is not True:
        return jsonify({"error": "authorization_ack must be true before an active target can be enrolled."}), 400
    try:
        host = validate_host(data.get("host", ""))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400
    label = (data.get("label") or host).strip()[:120]
    kind = (data.get("kind") or "network").strip()[:40]
    try:
        with db() as conn:
            cur = conn.execute("INSERT INTO targets(label,host,kind,authorized,created_at) VALUES(?,?,?,?,?)",
                               (label, host, kind, 1, now_iso()))
            target_id = int(cur.lastrowid)
    except sqlite3.IntegrityError:
        with db() as conn:
            row = conn.execute("SELECT id FROM targets WHERE host=?", (host,)).fetchone()
        target_id = int(row["id"])
    return jsonify({"ok": True, "id": target_id})


@app.post("/api/targets/<int:target_id>/scan")
def api_scan_target(target_id: int):
    try:
        return jsonify(scan_target(target_id))
    except (KeyError, PermissionError) as e:
        return jsonify({"error": str(e)}), 404


@app.post("/api/targets/<int:target_id>/verify-http")
def api_verify_http(target_id: int):
    data = request.get_json(force=True)
    try:
        return jsonify(verify_http(target_id, data.get("scheme", "http"), int(data.get("port", 80)),
                                   data.get("path", "/")))
    except (KeyError, PermissionError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/targets/<int:target_id>/findings")
def api_findings(target_id: int):
    try:
        get_target(target_id)
    except Exception as e:
        return jsonify({"error": str(e)}), 404
    with db() as conn:
        rows = conn.execute("SELECT * FROM findings WHERE target_id=? ORDER BY id DESC", (target_id,)).fetchall()
    out = []
    for row in rows:
        item = dict(row)
        try:
            item["evidence"] = json.loads(item.pop("evidence_json") or "{}")
        except Exception:
            item["evidence"] = {}
        out.append(item)
    return jsonify(out)


@app.post("/api/targets/<int:target_id>/analyze")
def api_analyze(target_id: int):
    data = request.get_json(silent=True) or {}
    model = (data.get("model") or "").strip()
    try:
        if model and ollama_status()["available"]:
            return jsonify(ollama_analysis(target_id, model))
        return jsonify(offline_analysis(target_id))
    except Exception as e:
        return jsonify({"error": str(e)}), 400


INDEX_HTML = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>AgentWhite</title>
<style>
:root{--bg:#050807;--panel:#0b1210;--line:#1d3b2f;--green:#66ffa8;--muted:#8aa79a;--red:#ff6b6b;--amber:#ffd166;--blue:#6bdcff}
*{box-sizing:border-box}body{margin:0;background:radial-gradient(circle at top,#0b1c15,#030504 52%);color:#e8fff1;font-family:Inter,ui-sans-serif,system-ui,Segoe UI,Arial}
header{position:sticky;top:0;z-index:5;background:rgba(3,7,5,.88);backdrop-filter:blur(10px);border-bottom:1px solid var(--line);padding:18px 24px;display:flex;justify-content:space-between;align-items:center}
.brand{font-weight:900;letter-spacing:.18em;color:var(--green)}.tag{font-size:12px;color:var(--muted)}
main{max-width:1450px;margin:0 auto;padding:22px;display:grid;grid-template-columns:330px 1fr;gap:18px}
.panel{background:linear-gradient(180deg,rgba(14,28,22,.95),rgba(7,13,10,.96));border:1px solid var(--line);border-radius:16px;padding:16px;box-shadow:0 20px 70px rgba(0,0,0,.22)}
h2,h3{margin:0 0 12px}h2{font-size:15px;letter-spacing:.08em;text-transform:uppercase;color:var(--green)}h3{font-size:14px}
button,input,select{border:1px solid #29513f;background:#08110d;color:#eafff2;border-radius:10px;padding:10px 12px}
button{cursor:pointer;font-weight:700}button:hover{border-color:var(--green);box-shadow:0 0 0 2px rgba(102,255,168,.08)}button.primary{background:#123b2a;color:var(--green)}
button.warn{border-color:#5b4822;color:var(--amber)}button.danger{border-color:#5b2a2a;color:#ff9a9a}
.row{display:flex;gap:8px;flex-wrap:wrap}.stack{display:grid;gap:10px}.muted{color:var(--muted);font-size:12px}.mono{font-family:ui-monospace,SFMono-Regular,Consolas,monospace}
.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:12px}.card{border:1px solid #1a352a;background:#08100d;border-radius:12px;padding:13px}
.card strong{display:block;margin-bottom:6px}.pill{font-size:11px;padding:3px 8px;border-radius:999px;border:1px solid #315343;color:var(--muted);display:inline-block}
.sev-high{color:#ff8585}.sev-medium{color:var(--amber)}.sev-info{color:var(--blue)}
pre{white-space:pre-wrap;word-break:break-word;background:#030806;border:1px solid #173126;border-radius:10px;padding:12px;max-height:360px;overflow:auto;color:#bfffd8}
#log{height:220px}.target.active{border-color:var(--green)}.target{cursor:pointer}.split{display:grid;grid-template-columns:1fr 1fr;gap:14px}
input{width:100%}.section{margin-bottom:18px}.status-dot{display:inline-block;width:8px;height:8px;border-radius:50%;background:var(--green);margin-right:6px}
@media(max-width:1000px){main{grid-template-columns:1fr}.grid{grid-template-columns:1fr 1fr}}
@media(max-width:650px){.grid,.split{grid-template-columns:1fr}}
</style>
</head>
<body>
<header><div><div class="brand">AGENTWHITE</div><div class="tag">Offline Authorized Wireless & Local Security Auditor</div></div><div id="status" class="tag">starting…</div></header>
<main>
<aside class="stack">
<section class="panel">
<h2>Discovery</h2>
<div class="stack">
<button class="primary" onclick="loadWifi()">Wi‑Fi Survey</button>
<button onclick="discoverLan()">LAN Discovery</button>
<button onclick="discoverBle()">Bluetooth LE Survey</button>
</div>
<div class="muted" style="margin-top:10px">Discovery does not enroll a device for active testing.</div>
</section>
<section class="panel">
<h2>Enroll Authorized Target</h2>
<div class="stack">
<input id="label" placeholder="Label e.g. Garage Camera">
<input id="host" placeholder="IP / hostname e.g. 192.168.1.20">
<select id="kind"><option>network</option><option>camera</option><option>computer</option><option>router</option><option>iot</option></select>
<label class="muted"><input id="ack" type="checkbox" style="width:auto"> I own this target or have permission to test it.</label>
<button class="primary" onclick="enroll()">Enroll Target</button>
</div>
</section>
<section class="panel"><h2>Targets</h2><div id="targets" class="stack"></div></section>
</aside>

<section class="stack">
<div class="panel">
<h2>Command Center</h2>
<div id="selected" class="muted">Select an enrolled target.</div>
<div class="row" style="margin-top:12px">
<button class="primary" onclick="scanSelected()">Scan Services</button>
<button onclick="analyzeSelected()">Analyze & Patch Guidance</button>
</div>
</div>

<div class="split">
<section class="panel"><h2>Verification</h2>
<div class="muted">Verify an HTTP/HTTPS resource on the selected enrolled target and display what it actually returns.</div>
<div class="row" style="margin-top:10px">
<select id="scheme"><option>http</option><option>https</option></select>
<input id="port" value="80" style="width:90px">
<input id="path" value="/" style="flex:1;min-width:120px">
<button class="warn" onclick="verifyHttp()">Verify / View Evidence</button>
</div>
<div id="verification" style="margin-top:10px"></div>
</section>

<section class="panel"><h2>Offline AI Analyst</h2>
<div class="muted">Uses local Ollama when available; otherwise AgentWhite's built-in rules produce remediation and a score.</div>
<div class="row" style="margin-top:10px"><select id="model"><option value="">Built-in offline rules</option></select></div>
<div id="analysis" style="margin-top:10px"></div>
</section>
</div>

<section class="panel"><h2>Findings & Evidence</h2><div id="findings" class="grid"></div></section>
<section class="panel"><h2>Activity</h2><pre id="log">AgentWhite booting…</pre></section>
</section>
</main>
<script>
let selected=null;
const $=id=>document.getElementById(id);
const esc=s=>String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function log(x){$('log').textContent=typeof x==='string'?x:JSON.stringify(x,null,2)}
async function api(url,opt={}){let r=await fetch(url,{headers:{'Content-Type':'application/json'},...opt});let j=await r.json();if(!r.ok)throw new Error(j.error||r.statusText);return j}
async function boot(){let s=await api('/api/status');$('status').innerHTML=`<span class="status-dot"></span>${esc(s.platform)} · ${esc(s.local_ip)}`; 
 if(s.ollama.available){for(const m of s.ollama.models){$('model').innerHTML+=`<option>${esc(m)}</option>`}} await targets(); log(s)}
async function loadWifi(){log('Running Wi-Fi survey…');log(await api('/api/wifi'))}
async function discoverLan(){log('Discovering LAN devices…');let d=await api('/api/discover/lan',{method:'POST'});log(d)}
async function discoverBle(){log('Scanning Bluetooth LE…');let d=await api('/api/discover/ble',{method:'POST'});log(d)}
async function enroll(){let body={label:$('label').value,host:$('host').value,kind:$('kind').value,authorization_ack:$('ack').checked};
 let d=await api('/api/targets',{method:'POST',body:JSON.stringify(body)}); await targets(); selectTarget(d.id)}
async function targets(){let d=await api('/api/targets');$('targets').innerHTML=d.map(t=>`<div class="card target ${selected===t.id?'active':''}" onclick="selectTarget(${t.id})"><strong>${esc(t.label)}</strong><span class="mono">${esc(t.host)}</span><br><span class="pill">${esc(t.kind)}</span></div>`).join('')||'<div class="muted">No enrolled targets yet.</div>'}
async function selectTarget(id){selected=id;let ts=await api('/api/targets');let t=ts.find(x=>x.id===id);$('selected').innerHTML=t?`<strong>${esc(t.label)}</strong> · <span class="mono">${esc(t.host)}</span> · authorized`:'Unknown target';await targets();await loadFindings()}
async function scanSelected(){if(!selected)return alert('Select a target first.');log('Scanning enrolled target…');let d=await api(`/api/targets/${selected}/scan`,{method:'POST'});log(d);await loadFindings()}
async function verifyHttp(){if(!selected)return alert('Select a target first.');let body={scheme:$('scheme').value,port:Number($('port').value),path:$('path').value};
 let d=await api(`/api/targets/${selected}/verify-http`,{method:'POST',body:JSON.stringify(body)});$('verification').innerHTML=d.ok?`<div class="card"><strong>Verified HTTP ${esc(d.status)}</strong><div class="mono">${esc(d.url)}</div><div>${esc(d.content_type)}</div>${d.text_preview?`<pre>${esc(d.text_preview)}</pre>`:''}${d.evidence_file?`<div class="muted">Evidence saved locally: ${esc(d.evidence_file)}</div>`:''}</div>`:`<div class="sev-high">${esc(d.error)}</div>`;log(d);await loadFindings()}
async function loadFindings(){if(!selected)return;$('findings').innerHTML='loading…';let d=await api(`/api/targets/${selected}/findings`);
 $('findings').innerHTML=d.map(f=>`<div class="card"><strong class="sev-${esc(f.severity)}">${esc(f.title)}</strong><div class="muted">${esc(f.created_at)}</div><p>${esc(f.detail)}</p><div class="pill">${esc(f.severity)}</div><h3 style="margin-top:12px">Patch guidance</h3><div>${esc(f.remediation)}</div><details style="margin-top:10px"><summary>Evidence</summary><pre>${esc(JSON.stringify(f.evidence,null,2))}</pre></details></div>`).join('')||'<div class="muted">No findings yet.</div>'}
async function analyzeSelected(){if(!selected)return alert('Select a target first.');let d=await api(`/api/targets/${selected}/analyze`,{method:'POST',body:JSON.stringify({model:$('model').value})});
 $('analysis').innerHTML=`<div class="card"><strong>Score ${esc(d.score)}/100</strong><div class="muted">${esc(d.engine)}</div><p>${esc(d.summary)}</p>${d.ai_text?`<pre>${esc(d.ai_text)}</pre>`:''}<div>${(d.priorities||[]).map(x=>`<p><b>${esc(x.finding)}</b><br>${esc(x.fix)}</p>`).join('')}</div></div>`;log(d)}
boot().catch(e=>log(e.message));
</script>
</body></html>"""


def launch_browser() -> None:
    time.sleep(1.1)
    try:
        webbrowser.open("http://127.0.0.1:8765")
    except Exception:
        pass


if __name__ == "__main__":
    init_db()
    threading.Thread(target=launch_browser, daemon=True).start()
    app.run(host="127.0.0.1", port=8765, debug=False, threaded=True)
