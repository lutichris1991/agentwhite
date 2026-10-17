from __future__ import annotations

import asyncio
from typing import Any


def _format_value(raw: bytes, max_bytes: int = 256) -> dict[str, Any]:
    clipped = bytes(raw[:max_bytes])
    text = clipped.decode("utf-8", "replace")
    printable = sum(1 for ch in text if ch.isprintable() or ch in "\r\n\t")
    ratio = printable / max(1, len(text))
    return {
        "bytes": len(raw),
        "truncated": len(raw) > max_bytes,
        "hex": clipped.hex(" "),
        "text": text if ratio >= 0.75 else None,
    }


async def _inspect_ble_async(address: str) -> dict[str, Any]:
    try:
        from bleak import BleakClient
    except Exception as exc:
        raise ValueError(
            "BLE inspection requires the optional 'bleak' package. Install AgentWhite with the bluetooth extra or use the Windows standalone build."
        ) from exc

    result: dict[str, Any] = {
        "address": address,
        "connected": False,
        "services": [],
    }

    try:
        async with BleakClient(address, timeout=10.0) as client:
            result["connected"] = bool(client.is_connected)
            services = client.services
            for service in services:
                service_row: dict[str, Any] = {
                    "uuid": str(service.uuid),
                    "description": getattr(service, "description", None),
                    "characteristics": [],
                }
                for characteristic in service.characteristics:
                    props = [str(p).lower() for p in (characteristic.properties or [])]
                    row: dict[str, Any] = {
                        "uuid": str(characteristic.uuid),
                        "description": getattr(characteristic, "description", None),
                        "handle": getattr(characteristic, "handle", None),
                        "properties": props,
                        "readable": "read" in props,
                    }
                    if "read" in props:
                        try:
                            raw = await client.read_gatt_char(characteristic)
                            row["read_result"] = _format_value(bytes(raw))
                            row["read_status"] = "success"
                        except Exception as exc:
                            row["read_status"] = "blocked"
                            row["read_error"] = str(exc)
                    service_row["characteristics"].append(row)
                result["services"].append(service_row)
    except Exception as exc:
        raise ValueError(f"Could not establish an enrolled BLE inspection session: {exc}") from exc

    result["service_count"] = len(result["services"])
    result["characteristic_count"] = sum(len(s["characteristics"]) for s in result["services"])
    result["readable_count"] = sum(
        1
        for service in result["services"]
        for char in service["characteristics"]
        if char.get("read_status") == "success"
    )
    return result


def inspect_ble(address: str) -> dict[str, Any]:
    if not address:
        raise ValueError("Bluetooth address is required.")
    try:
        return asyncio.run(_inspect_ble_async(address))
    except RuntimeError as exc:
        raise ValueError(f"BLE inspection could not start: {exc}") from exc
