from __future__ import annotations

import importlib
import os
import platform
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

MAX_OUTPUT_CHARS = 24000
DEFAULT_TIMEOUT_SECONDS = 10


@dataclass(frozen=True)
class ToolAction:
    id: str
    tool_id: str
    label: str
    description: str
    effect: str = "PASSIVE"
    scope: str = "local-host"
    timeout_seconds: int = DEFAULT_TIMEOUT_SECONDS
    command: tuple[str, ...] | None = None
    handler: str | None = None


# Adapter Pack 1 is intentionally read-only / inventory oriented. Commands are
# fixed here; the UI/API does not accept arbitrary command strings or flags.
TOOL_ACTIONS: tuple[ToolAction, ...] = (
    ToolAction("kismet.version", "kismet", "Read Kismet Version", "Confirm the installed Kismet engine and version.", command=("kismet", "--version")),
    ToolAction("aircrack.help", "aircrack-ng", "Read Aircrack-ng Version", "Read the installed Aircrack-ng banner/help without starting a wireless attack.", command=("aircrack-ng", "--help")),
    ToolAction("hcxtools.help", "hcxtools", "Read hcxtools Capability", "Read hcxpcapngtool help/version information without processing a capture.", command=("hcxpcapngtool", "--help")),
    ToolAction("bettercap.version", "bettercap", "Read Bettercap Version", "Confirm the installed Bettercap engine without starting a session.", command=("bettercap", "-version")),
    ToolAction("bluez.adapters", "bluez", "List Bluetooth Adapters", "List local BlueZ Bluetooth controllers only; no remote connection is started.", command=("bluetoothctl", "list")),
    ToolAction("ubertooth.help", "ubertooth", "Inspect Ubertooth Tooling", "Read the local Ubertooth BLE tool help without capturing traffic.", command=("ubertooth-btle", "-h")),
    ToolAction("libnfc.inventory", "libnfc", "Inventory NFC Readers/Targets", "Use nfc-list to enumerate locally attached NFC readers and currently visible targets without writing to them.", command=("nfc-list",)),
    ToolAction("hackrf.inventory", "hackrf", "Inspect HackRF Hardware", "Run hackrf_info to identify attached HackRF hardware and firmware.", command=("hackrf_info",)),
    ToolAction("rtl433.version", "rtl-433", "Read rtl_433 Version", "Confirm the rtl_433 decoder version without starting an RF capture.", command=("rtl_433", "-V")),
    ToolAction("killerbee.help", "killerbee", "Inspect KillerBee Tooling", "Read the Zigbee identifier tool help without starting a radio test.", command=("zbid", "-h")),
    ToolAction("tshark.interfaces", "tshark", "List Capture Interfaces", "List packet-capture interfaces visible to TShark; no capture is started.", command=("tshark", "-D")),
    ToolAction("nmap.version", "nmap", "Read Nmap Version", "Confirm a separately installed Nmap version; no network scan is started.", command=("nmap", "--version")),
    ToolAction("sigrok.scan", "sigrok-cli", "Scan Measurement Hardware", "Ask sigrok for locally attached supported measurement devices without driving target signals.", command=("sigrok-cli", "--scan")),
    ToolAction("openocd.version", "openocd", "Read OpenOCD Version", "Confirm the installed OpenOCD build without opening a debug session.", command=("openocd", "--version")),
    ToolAction("flashrom.version", "flashrom", "Read flashrom Version", "Confirm the installed flashrom build without reading or writing flash memory.", command=("flashrom", "--version")),
    ToolAction("pyserial.ports", "pyserial", "List Serial Ports", "Enumerate local serial/UART ports through pySerial.", handler="pyserial_ports"),
    ToolAction("pyusb.devices", "pyusb", "List USB Devices", "Enumerate local USB descriptors through PyUSB without sending device-specific control requests.", handler="pyusb_devices"),
    ToolAction("pythoncan.version", "python-can", "Read python-can Version", "Confirm the installed python-can library without opening a CAN bus.", handler="pythoncan_version"),
    ToolAction("scapy.version", "scapy", "Read Scapy Version", "Confirm the installed Scapy library without sending packets.", handler="scapy_version"),
    ToolAction("canutils.interfaces", "can-utils", "List Local CAN Interfaces", "List local CAN/vCAN interfaces without reading or transmitting bus traffic.", handler="can_interfaces"),
)


def _clip(value: str) -> tuple[str, bool]:
    value = value or ""
    if len(value) <= MAX_OUTPUT_CHARS:
        return value, False
    return value[:MAX_OUTPUT_CHARS], True


def _run_command(action: ToolAction) -> dict[str, Any]:
    assert action.command
    executable = action.command[0]
    path = shutil.which(executable)
    if not path:
        raise FileNotFoundError(f"Required executable is not installed or not on PATH: {executable}")
    argv = [path, *action.command[1:]]
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        timeout=action.timeout_seconds,
        shell=False,
        errors="replace",
        env=os.environ.copy(),
    )
    stdout, stdout_truncated = _clip(completed.stdout)
    stderr, stderr_truncated = _clip(completed.stderr)
    return {
        "runner": "fixed-command",
        "executable": path,
        "argv": [executable, *action.command[1:]],
        "returncode": completed.returncode,
        "stdout": stdout,
        "stderr": stderr,
        "stdout_truncated": stdout_truncated,
        "stderr_truncated": stderr_truncated,
    }


def _pyserial_ports() -> dict[str, Any]:
    from serial.tools import list_ports

    ports = []
    for port in list_ports.comports():
        ports.append(
            {
                "device": port.device,
                "description": port.description,
                "hwid": port.hwid,
                "manufacturer": port.manufacturer,
                "product": port.product,
                "serial_number": port.serial_number,
                "vid": port.vid,
                "pid": port.pid,
            }
        )
    return {"runner": "python-library", "count": len(ports), "ports": ports}


def _pyusb_devices() -> dict[str, Any]:
    import usb.core

    rows: list[dict[str, Any]] = []
    devices = usb.core.find(find_all=True)
    for device in devices or []:
        rows.append(
            {
                "bus": getattr(device, "bus", None),
                "address": getattr(device, "address", None),
                "vendor_id": f"0x{int(device.idVendor):04x}",
                "product_id": f"0x{int(device.idProduct):04x}",
                "device_class": int(device.bDeviceClass),
                "device_subclass": int(device.bDeviceSubClass),
                "device_protocol": int(device.bDeviceProtocol),
            }
        )
    return {"runner": "python-library", "count": len(rows), "devices": rows}


def _module_version(module_name: str) -> dict[str, Any]:
    module = importlib.import_module(module_name)
    version = getattr(module, "__version__", None)
    if version is None:
        version = getattr(module, "VERSION", None)
    return {"runner": "python-library", "module": module_name, "version": str(version or "unknown")}


def _can_interfaces() -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    if platform.system().lower() == "linux":
        root = Path("/sys/class/net")
        if root.exists():
            for path in sorted(root.iterdir()):
                name = path.name
                if name.startswith(("can", "vcan", "slcan")):
                    state_path = path / "operstate"
                    try:
                        state = state_path.read_text(encoding="utf-8").strip()
                    except OSError:
                        state = "unknown"
                    rows.append({"name": name, "state": state})
    return {
        "runner": "local-os",
        "platform": platform.system(),
        "count": len(rows),
        "interfaces": rows,
        "note": "Generic CAN interface enumeration is currently implemented for Linux/SocketCAN hosts.",
    }


HANDLERS: dict[str, Callable[[], dict[str, Any]]] = {
    "pyserial_ports": _pyserial_ports,
    "pyusb_devices": _pyusb_devices,
    "pythoncan_version": lambda: _module_version("can"),
    "scapy_version": lambda: _module_version("scapy"),
    "can_interfaces": _can_interfaces,
}


def list_tool_actions(installed_tool_ids: set[str] | None = None) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for action in TOOL_ACTIONS:
        available = installed_tool_ids is None or action.tool_id in installed_tool_ids
        rows.append(
            {
                "id": action.id,
                "tool_id": action.tool_id,
                "label": action.label,
                "description": action.description,
                "effect": action.effect,
                "scope": action.scope,
                "timeout_seconds": action.timeout_seconds,
                "available": available,
                "accepts_arbitrary_args": False,
                "auto_chain": False,
            }
        )
    return rows


def run_tool_action(action_id: str) -> dict[str, Any]:
    action = next((row for row in TOOL_ACTIONS if row.id == action_id), None)
    if action is None:
        raise ValueError("Unknown tool action.")
    if action.effect != "PASSIVE" or action.scope != "local-host":
        raise PermissionError("Adapter Pack 1 only permits passive local-host inventory actions.")
    if action.command:
        result = _run_command(action)
    elif action.handler:
        handler = HANDLERS.get(action.handler)
        if handler is None:
            raise RuntimeError("Tool adapter handler is not available.")
        result = handler()
    else:
        raise RuntimeError("Tool action has no approved adapter implementation.")
    return {
        "action_id": action.id,
        "tool_id": action.tool_id,
        "label": action.label,
        "effect": action.effect,
        "scope": action.scope,
        "auto_chain": False,
        "result": result,
    }
