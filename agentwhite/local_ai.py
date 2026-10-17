from __future__ import annotations

import json
import urllib.error
import urllib.request
from collections import Counter
from typing import Any

OLLAMA_TAGS_URL = "http://127.0.0.1:11434/api/tags"
OLLAMA_GENERATE_URL = "http://127.0.0.1:11434/api/generate"


def available_models(timeout: float = 0.6) -> list[str]:
    """Return locally installed Ollama models without contacting any cloud service."""
    try:
        with urllib.request.urlopen(OLLAMA_TAGS_URL, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return []
    return [
        str(item.get("name"))
        for item in payload.get("models", [])
        if item.get("name")
    ]


def _fallback(findings: list[dict[str, Any]]) -> dict[str, Any]:
    severities = Counter(str(f.get("severity", "info")).lower() for f in findings)
    ordered = sorted(
        findings,
        key=lambda f: {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}.get(
            str(f.get("severity", "info")).lower(), 5
        ),
    )
    priorities: list[dict[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for finding in ordered:
        title = str(finding.get("title") or "Finding")
        remediation = str(finding.get("remediation") or "Review and restrict the exposed service.")
        key = (title, remediation)
        if key in seen:
            continue
        seen.add(key)
        priorities.append(
            {
                "severity": str(finding.get("severity") or "info"),
                "finding": title,
                "fix": remediation,
            }
        )
        if len(priorities) >= 10:
            break

    summary = (
        f"Reviewed {len(findings)} recorded findings: "
        f"{severities.get('critical', 0)} critical, {severities.get('high', 0)} high, "
        f"{severities.get('medium', 0)} medium, and {severities.get('info', 0)} informational."
    )
    return {
        "engine": "AgentWhite offline rule analyst",
        "model": None,
        "summary": summary,
        "priorities": priorities,
        "analysis": "",
    }


def analyze_findings(
    findings: list[dict[str, Any]],
    model: str | None = None,
    *,
    timeout: float = 90.0,
) -> dict[str, Any]:
    """Analyze already-recorded evidence with a local Ollama model.

    The model receives only findings AgentWhite already recorded. The prompt explicitly
    forbids inventing access, vulnerabilities, or successful exploitation. If Ollama is
    absent or fails, deterministic offline remediation remains available.
    """
    fallback = _fallback(findings)
    models = available_models()
    selected = model if model in models else (models[0] if models else None)
    if not selected:
        return fallback

    compact_findings = []
    for item in findings[:60]:
        compact_findings.append(
            {
                "device_id": item.get("device_id"),
                "category": item.get("category"),
                "severity": item.get("severity"),
                "title": item.get("title"),
                "status": item.get("status"),
                "proof": item.get("proof"),
                "remediation": item.get("remediation"),
                "created_at": item.get("created_at"),
            }
        )

    prompt = """You are AgentWhite's LOCAL defensive security analyst.
Analyze only the evidence supplied below from systems the operator has explicitly enrolled for authorized testing.
Rules:
- Never claim an exploit, access level, credential, file, camera feed, or vulnerability that is not directly supported by the supplied evidence.
- Clearly separate VERIFIED observations from possibilities.
- Prioritize remediation by likely impact and exposure.
- Explain findings in plain English.
- End with a short retest checklist that uses the same already-recorded verification paths.
- Do not provide credential theft, persistence, destructive actions, or instructions for attacking unrelated systems.
- Keep the answer concise and practical.

EVIDENCE JSON:
""" + json.dumps(compact_findings, indent=2, default=str)

    request_body = json.dumps(
        {
            "model": selected,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0.2},
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        OLLAMA_GENERATE_URL,
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
        text = str(payload.get("response") or "").strip()
        if not text:
            return fallback
        return {
            **fallback,
            "engine": "Ollama local analyst",
            "model": selected,
            "analysis": text,
        }
    except (OSError, urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError) as exc:
        return {
            **fallback,
            "ai_error": str(exc),
        }
