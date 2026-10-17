from __future__ import annotations

import platform
import shutil
import subprocess
from typing import Any


# Python engines that are intended to ship inside the AgentWhite Windows build.
# These are not downloaded at runtime by the standalone EXE.
BUNDLED_PYTHON_TOOLS = {
    "bleak",
    "scapy",
    "python-can",
    "pyserial",
    "pyusb",
}


# Fixed Windows installation recipes. AgentWhite never accepts a package ID,
# command, executable, or flags from the browser. The operator can only select
# one of these explicit recipes.
WINDOWS_WINGET_RECIPES: dict[str, dict[str, Any]] = {
    "nmap": {
        "package_id": "Insecure.Nmap",
        "label": "Install Nmap",
        "note": "Installs the separately licensed Nmap package through Windows Package Manager.",
    },
    "tshark": {
        "package_id": "WiresharkFoundation.Wireshark",
        "label": "Install Wireshark / TShark",
        "note": "Installs Wireshark/TShark through Windows Package Manager. Packet capture drivers may require Windows approval.",
    },
}


def current_platform() -> str:
    value = platform.system().lower()
    if value.startswith("win"):
        return "windows"
    if value == "darwin":
        return "macos"
    if value == "linux":
        return "linux"
    return value


def classify_setup(tool: dict[str, Any]) -> dict[str, Any]:
    """Explain why a registered tool is or is not currently ready.

    The registry previously reduced every missing engine to "not detected".
    This classifier distinguishes bundled Python engines, verified one-click
    Windows installs, platform mismatches, and hardware/manual setup.
    """
    os_name = current_platform()
    tool_id = str(tool.get("id") or "")
    supported = [str(x).lower() for x in (tool.get("platforms") or [])]

    if tool.get("installed"):
        return {
            "state": "ready",
            "label": "READY",
            "detail": "AgentWhite detected this engine on the current computer.",
            "installable": False,
            "method": None,
        }

    if supported and os_name not in supported:
        return {
            "state": "unsupported-platform",
            "label": "OTHER OS",
            "detail": f"This integration is registered for {', '.join(supported)}, not {os_name}.",
            "installable": False,
            "method": None,
        }

    if tool_id in BUNDLED_PYTHON_TOOLS:
        return {
            "state": "bundled-engine-missing",
            "label": "BUILT-IN ENGINE",
            "detail": "This Python engine is intended to be bundled inside the current AgentWhite Windows package. Reinstall/update AgentWhite if it is missing.",
            "installable": False,
            "method": "bundled",
        }

    if os_name == "windows" and tool_id in WINDOWS_WINGET_RECIPES:
        recipe = WINDOWS_WINGET_RECIPES[tool_id]
        winget = shutil.which("winget")
        return {
            "state": "installable" if winget else "winget-missing",
            "label": "INSTALLABLE" if winget else "WINDOWS INSTALLER NEEDED",
            "detail": recipe["note"] if winget else "Windows Package Manager (winget) was not detected on this PC.",
            "installable": bool(winget),
            "method": "winget",
            "package_id": recipe["package_id"],
            "install_label": recipe["label"],
        }

    hardware = [str(x) for x in (tool.get("hardware") or [])]
    if hardware:
        return {
            "state": "external-setup",
            "label": "SETUP REQUIRED",
            "detail": "Requires separately installed software and/or compatible hardware: " + "; ".join(hardware),
            "installable": False,
            "method": "manual",
        }

    return {
        "state": "external-setup",
        "label": "SETUP REQUIRED",
        "detail": "This upstream engine must be installed separately before AgentWhite can control it.",
        "installable": False,
        "method": "manual",
    }


def augment_tools(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for tool in tools:
        row = dict(tool)
        row["setup"] = classify_setup(row)
        rows.append(row)
    return rows


def setup_summary(tools: list[dict[str, Any]]) -> dict[str, int]:
    summary = {
        "ready": 0,
        "installable": 0,
        "bundled_engine_missing": 0,
        "external_setup": 0,
        "unsupported_platform": 0,
    }
    for tool in tools:
        state = str((tool.get("setup") or {}).get("state") or "")
        key = state.replace("-", "_")
        if key in summary:
            summary[key] += 1
    return summary


def run_setup(tool_id: str, timeout_seconds: int = 600) -> dict[str, Any]:
    """Run one fixed setup recipe explicitly selected by the operator."""
    if current_platform() != "windows":
        raise RuntimeError("The current one-click setup pack is Windows-only.")

    recipe = WINDOWS_WINGET_RECIPES.get(tool_id)
    if not recipe:
        raise ValueError("No approved one-click setup recipe exists for this tool.")

    winget = shutil.which("winget")
    if not winget:
        raise FileNotFoundError("Windows Package Manager (winget) was not found.")

    argv = [
        winget,
        "install",
        "--id",
        str(recipe["package_id"]),
        "--exact",
        "--source",
        "winget",
        "--accept-source-agreements",
        "--accept-package-agreements",
        "--silent",
        "--disable-interactivity",
    ]
    completed = subprocess.run(
        argv,
        capture_output=True,
        text=True,
        errors="replace",
        timeout=timeout_seconds,
        shell=False,
    )
    return {
        "tool_id": tool_id,
        "method": "winget",
        "package_id": recipe["package_id"],
        "returncode": completed.returncode,
        "stdout": (completed.stdout or "")[-24000:],
        "stderr": (completed.stderr or "")[-24000:],
        "auto_chain": False,
        "restart_agentwhite_recommended": True,
    }
