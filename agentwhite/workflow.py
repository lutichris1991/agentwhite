from __future__ import annotations

from typing import Any


BASE_ACTIONS: dict[str, list[dict[str, Any]]] = {
    "wifi": [
        {
            "id": "wifi.configuration.audit",
            "label": "Audit Wi-Fi Security Configuration",
            "description": "Review the observed authentication and encryption configuration for this enrolled access point.",
            "effect": "PASSIVE",
            "kind": "test",
            "repeatable": True,
        }
    ],
    "lan": [
        {
            "id": "lan.services.verify",
            "label": "Verify Exposed Services",
            "description": "Check a conservative set of common TCP services on this enrolled local device.",
            "effect": "ACTIVE",
            "kind": "test",
            "repeatable": True,
        }
    ],
    "bluetooth": [
        {
            "id": "bluetooth.gatt.inspect",
            "label": "Inspect BLE Access",
            "description": "Establish an ordinary BLE client session and inspect services and readable GATT characteristics.",
            "effect": "ACTIVE",
            "kind": "test",
            "repeatable": True,
        }
    ],
}


def available_actions(
    device: dict[str, Any],
    findings: list[dict[str, Any]],
    access_sessions: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Return explicit user-selectable next actions for one enrolled target.

    This function only proposes actions. It never executes them. That separation is a
    core AgentWhite rule: discovery can unlock new buttons, but only the operator can
    start the next test.
    """
    actions = [dict(item) for item in BASE_ACTIONS.get(str(device.get("kind")), [])]

    if device.get("kind") == "lan":
        seen_ports: set[int] = set()
        for finding in findings:
            if finding.get("category") != "service-exposure":
                continue
            proof = finding.get("proof") or {}
            try:
                port = int(proof.get("port"))
            except (TypeError, ValueError):
                continue
            if port in {80, 443, 8000, 8080, 8443} and port not in seen_ports:
                seen_ports.add(port)
                actions.append(
                    {
                        "id": f"http.resource.inspect:{port}",
                        "label": f"View Returned Material on TCP/{port}",
                        "description": "Open the verified-access viewer for this reachable HTTP/HTTPS service.",
                        "effect": "ACTIVE",
                        "kind": "access",
                        "repeatable": True,
                        "parameters": {"port": port},
                    }
                )

    for session in access_sessions:
        if session.get("kind") == "http":
            port = (session.get("endpoint") or {}).get("port")
            action_id = f"http.resource.inspect:{port}"
            if port and not any(a.get("id") == action_id for a in actions):
                actions.append(
                    {
                        "id": action_id,
                        "label": f"Return to HTTP Access on TCP/{port}",
                        "description": "Re-open this saved access point without deleting prior evidence or test history.",
                        "effect": "ACTIVE",
                        "kind": "access",
                        "repeatable": True,
                        "parameters": {"port": int(port)},
                    }
                )

    return actions
