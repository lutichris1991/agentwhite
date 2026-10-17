from __future__ import annotations

import asyncio
import hashlib
import json
import os
import platform
import re
import subprocess
from typing import Any


def _device_id(kind: str, *parts: str) -> str:
    raw = "|".join([kind, *[p or "" for p in parts]])
    return f"{kind}-" + hashlib.sha256(raw.encode("utf-8", "ignore")).hexdigest()[:16]


def _run(cmd: list[str], timeout: int = 10) -> str:
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            errors="replace",
            timeout=timeout,
            creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
        )
        return completed.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def scan_wifi() -> list[dict[str, Any]]:
    system = platform.system().lower()
    if system == "windows":
        return _scan_wifi_windows()
    if system == "linux":
        return _scan_wifi_linux()
    return []


def _scan_wifi_windows() -> list[dict[str, Any]]:
    text = _run(["netsh", "wlan", "show", "networks", "mode=bssid"], timeout=15)
    if not text:
        return []

    devices: list[dict[str, Any]] = []
    current: dict[str, Any] = {}
    bssid_data: dict[str, Any] = {}

    def flush_bssid() -> None:
        nonlocal bssid_data
        if not current or not bssid_data.get("bssid"):
            bssid_data = {}
            return
        ssid = current.get("ssid", "Hidden network")
        bssid = bssid_data.get("bssid", "")
        details = {
            "authentication": current.get("authentication", "Unknown"),
            "encryption": current.get("encryption", "Unknown"),
            "network_type": current.get("network_type", "Unknown"),
            "signal": bssid_data.get("signal"),
            "radio_type": bssid_data.get("radio_type"),
            "channel": bssid_data.get("channel"),
        }
        devices.append(
            {
                "id": _device_id("wifi", ssid, bssid),
                "kind": "wifi",
                "name": ssid,
                "address": bssid,
                "details": details,
            }
        )
        bssid_data = {}

    for raw_line in text.splitlines():
        line = raw_line.strip()
        if re.match(r"^SSID\s+\d+\s*:", line, re.I):
            flush_bssid()
            current = {"ssid": line.split(":", 1)[1].strip() or "Hidden network"}
        elif line.lower().startswith("network type"):
            current["network_type"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("authentication"):
            current["authentication"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("encryption"):
            current["encryption"] = line.split(":", 1)[1].strip()
        elif re.match(r"^BSSID\s+\d+\s*:", line, re.I):
            flush_bssid()
            bssid_data["bssid"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("signal"):
            bssid_data["signal"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("radio type"):
            bssid_data["radio_type"] = line.split(":", 1)[1].strip()
        elif line.lower().startswith("channel"):
            bssid_data["channel"] = line.split(":", 1)[1].strip()

    flush_bssid()
    return devices


def _split_nmcli(line: str) -> list[str]:
    parts: list[str] = []
    buf: list[str] = []
    escaped = False
    for ch in line:
        if escaped:
            buf.append(ch)
            escaped = False
        elif ch == "\\":
            escaped = True
        elif ch == ":":
            parts.append("".join(buf))
            buf = []
        else:
            buf.append(ch)
    parts.append("".join(buf))
    return parts


def _scan_wifi_linux() -> list[dict[str, Any]]:
    text = _run(
        ["nmcli", "-t", "-e", "yes", "-f", "SSID,BSSID,SECURITY,SIGNAL,CHAN", "dev", "wifi", "list", "--rescan", "yes"],
        timeout=15,
    )
    devices: list[dict[str, Any]] = []
    for line in text.splitlines():
        parts = _split_nmcli(line)
        if len(parts) < 5:
            continue
        ssid, bssid, security, signal, channel = parts[:5]
        devices.append(
            {
                "id": _device_id("wifi", ssid, bssid),
                "kind": "wifi",
                "name": ssid or "Hidden network",
                "address": bssid,
                "details": {
                    "authentication": security or "Open",
                    "encryption": security or "None",
                    "signal": signal,
                    "channel": channel,
                },
            }
        )
    return devices


async def _bleak_discover() -> list[dict[str, Any]]:
    try:
        from bleak import BleakScanner
    except Exception:
        return []

    devices: list[dict[str, Any]] = []
    try:
        discovered = await BleakScanner.discover(timeout=6.0, return_adv=True)
        if isinstance(discovered, dict):
            for address, pair in discovered.items():
                dev, adv = pair
                name = getattr(dev, "name", None) or getattr(adv, "local_name", None) or "BLE device"
                details = {
                    "scanner": "bleak",
                    "rssi": getattr(adv, "rssi", None),
                    "service_uuids": list(getattr(adv, "service_uuids", []) or []),
                    "manufacturer_ids": list((getattr(adv, "manufacturer_data", {}) or {}).keys()),
                }
                devices.append(
                    {
                        "id": _device_id("bluetooth", str(address)),
                        "kind": "bluetooth",
                        "name": str(name),
                        "address": str(address),
                        "details": details,
                    }
                )
            return devices
    except TypeError:
        pass
    except Exception:
        return []

    try:
        simple = await BleakScanner.discover(timeout=6.0)
    except Exception:
        return []
    for dev in simple:
        address = str(getattr(dev, "address", "") or "")
        name = str(getattr(dev, "name", None) or "BLE device")
        if not address:
            continue
        devices.append(
            {
                "id": _device_id("bluetooth", address),
                "kind": "bluetooth",
                "name": name,
                "address": address,
                "details": {"scanner": "bleak"},
            }
        )
    return devices


def _scan_bluetooth_bleak() -> list[dict[str, Any]]:
    try:
        return asyncio.run(_bleak_discover())
    except Exception:
        return []


def scan_bluetooth() -> list[dict[str, Any]]:
    # Prefer an actual BLE advertisement scan when Bleak is installed.
    devices = _scan_bluetooth_bleak()
    if devices:
        return devices

    system = platform.system().lower()
    if system == "windows":
        return _scan_bluetooth_windows()
    if system == "linux":
        return _scan_bluetooth_linux()
    return []


def _scan_bluetooth_windows() -> list[dict[str, Any]]:
    script = (
        "Get-PnpDevice -Class Bluetooth | "
        "Select-Object Status,FriendlyName,InstanceId | ConvertTo-Json -Compress"
    )
    text = _run(["powershell", "-NoProfile", "-Command", script], timeout=15)
    if not text:
        return []
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        return []
    rows = parsed if isinstance(parsed, list) else [parsed]
    devices: list[dict[str, Any]] = []
    for row in rows:
        name = str(row.get("FriendlyName") or "Bluetooth device")
        instance = str(row.get("InstanceId") or name)
        devices.append(
            {
                "id": _device_id("bluetooth", instance),
                "kind": "bluetooth",
                "name": name,
                "address": instance,
                "details": {"status": row.get("Status") or "Unknown", "instance_id": instance, "scanner": "windows-pnp"},
            }
        )
    return devices


def _scan_bluetooth_linux() -> list[dict[str, Any]]:
    _run(["bluetoothctl", "--timeout", "5", "scan", "on"], timeout=7)
    text = _run(["bluetoothctl", "devices"], timeout=5)
    devices: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = re.match(r"Device\s+([0-9A-Fa-f:]{17})\s+(.+)", line.strip())
        if not match:
            continue
        address, name = match.groups()
        devices.append(
            {
                "id": _device_id("bluetooth", address),
                "kind": "bluetooth",
                "name": name,
                "address": address,
                "details": {"scanner": "bluetoothctl"},
            }
        )
    return devices


def scan_lan() -> list[dict[str, Any]]:
    system = platform.system().lower()
    if system == "windows":
        text = _run(["arp", "-a"], timeout=5)
        pattern = re.compile(r"^\s*(\d+\.\d+\.\d+\.\d+)\s+([0-9a-fA-F-]{17})\s+(\w+)")
    else:
        text = _run(["ip", "neigh", "show"], timeout=5)
        pattern = re.compile(r"^(\S+)\s+.*lladdr\s+([0-9a-fA-F:]{17})\s+(\S+)")

    devices: list[dict[str, Any]] = []
    for line in text.splitlines():
        match = pattern.search(line)
        if not match:
            continue
        ip, mac, state = match.groups()
        mac = mac.replace("-", ":").lower()
        devices.append(
            {
                "id": _device_id("lan", ip, mac),
                "kind": "lan",
                "name": ip,
                "address": ip,
                "details": {"mac": mac, "neighbor_state": state},
            }
        )
    return devices


def scan(kind: str) -> list[dict[str, Any]]:
    if kind == "wifi":
        return scan_wifi()
    if kind == "bluetooth":
        return scan_bluetooth()
    if kind == "lan":
        return scan_lan()
    if kind == "all":
        return scan_wifi() + scan_bluetooth() + scan_lan()
    raise ValueError(f"Unsupported discovery kind: {kind}")
