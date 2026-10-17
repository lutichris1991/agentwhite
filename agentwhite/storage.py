from __future__ import annotations

import json
import os
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def data_dir() -> Path:
    if os.name == "nt":
        root = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        path = root / "AgentWhite"
    else:
        path = Path.home() / ".agentwhite"
    path.mkdir(parents=True, exist_ok=True)
    return path


class StateStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (data_dir() / "agentwhite.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS devices (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    name TEXT NOT NULL,
                    address TEXT,
                    details_json TEXT NOT NULL,
                    enrolled INTEGER NOT NULL DEFAULT 0,
                    first_seen TEXT NOT NULL,
                    last_seen TEXT NOT NULL
                );

                CREATE TABLE IF NOT EXISTS findings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL,
                    category TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    title TEXT NOT NULL,
                    proof_json TEXT NOT NULL,
                    remediation TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'verified',
                    created_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                );

                CREATE TABLE IF NOT EXISTS engagements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    device_id TEXT NOT NULL UNIQUE,
                    status TEXT NOT NULL DEFAULT 'active',
                    started_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL,
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                );

                CREATE TABLE IF NOT EXISTS action_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    device_id TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'running',
                    started_at TEXT NOT NULL,
                    completed_at TEXT,
                    elapsed_ms INTEGER,
                    result_json TEXT NOT NULL DEFAULT '{}',
                    FOREIGN KEY(engagement_id) REFERENCES engagements(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id)
                );

                CREATE TABLE IF NOT EXISTS access_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    engagement_id INTEGER NOT NULL,
                    device_id TEXT NOT NULL,
                    access_key TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    label TEXT NOT NULL,
                    status TEXT NOT NULL,
                    endpoint_json TEXT NOT NULL,
                    obtained_via_action_run_id INTEGER,
                    opened_at TEXT NOT NULL,
                    last_seen_at TEXT NOT NULL,
                    closed_at TEXT,
                    UNIQUE(engagement_id, access_key),
                    FOREIGN KEY(engagement_id) REFERENCES engagements(id),
                    FOREIGN KEY(device_id) REFERENCES devices(id),
                    FOREIGN KEY(obtained_via_action_run_id) REFERENCES action_runs(id)
                );

                CREATE INDEX IF NOT EXISTS idx_findings_device_id ON findings(device_id);
                CREATE INDEX IF NOT EXISTS idx_action_runs_device_id ON action_runs(device_id);
                CREATE INDEX IF NOT EXISTS idx_access_sessions_device_id ON access_sessions(device_id);
                """
            )
            conn.commit()

    def upsert_devices(self, devices: list[dict[str, Any]]) -> None:
        now = _utc_now()
        with closing(self._connect()) as conn:
            for device in devices:
                conn.execute(
                    """
                    INSERT INTO devices (
                        id, kind, name, address, details_json,
                        enrolled, first_seen, last_seen
                    ) VALUES (?, ?, ?, ?, ?, 0, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        kind = excluded.kind,
                        name = excluded.name,
                        address = excluded.address,
                        details_json = excluded.details_json,
                        last_seen = excluded.last_seen
                    """,
                    (
                        device["id"],
                        device["kind"],
                        device.get("name") or "Unknown",
                        device.get("address"),
                        json.dumps(device.get("details", {}), sort_keys=True),
                        now,
                        now,
                    ),
                )
            conn.commit()

    def list_devices(self, kind: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM devices"
        params: tuple[Any, ...] = ()
        if kind:
            sql += " WHERE kind = ?"
            params = (kind,)
        sql += " ORDER BY last_seen DESC, name ASC"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._device_row(row) for row in rows]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        return self._device_row(row) if row else None

    def set_enrolled(self, device_id: str, enrolled: bool) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            conn.execute(
                "UPDATE devices SET enrolled = ? WHERE id = ?",
                (1 if enrolled else 0, device_id),
            )
            conn.commit()
        if enrolled:
            self.ensure_engagement(device_id)
            self.set_engagement_status(device_id, "active")
        else:
            self.set_engagement_status(device_id, "paused")
        return self.get_device(device_id)

    def ensure_engagement(self, device_id: str) -> dict[str, Any]:
        now = _utc_now()
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO engagements (device_id, status, started_at, updated_at)
                VALUES (?, 'active', ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET updated_at = excluded.updated_at
                """,
                (device_id, now, now),
            )
            conn.commit()
        engagement = self.get_engagement(device_id)
        if not engagement:
            raise RuntimeError("Could not create engagement workspace.")
        return engagement

    def get_engagement(self, device_id: str) -> dict[str, Any] | None:
        with closing(self._connect()) as conn:
            row = conn.execute("SELECT * FROM engagements WHERE device_id = ?", (device_id,)).fetchone()
        if not row:
            return None
        return {
            "id": row["id"],
            "device_id": row["device_id"],
            "status": row["status"],
            "started_at": row["started_at"],
            "updated_at": row["updated_at"],
        }

    def set_engagement_status(self, device_id: str, status: str) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                "UPDATE engagements SET status = ?, updated_at = ? WHERE device_id = ?",
                (status, _utc_now(), device_id),
            )
            conn.commit()

    def record_action_start(self, *, device_id: str, action_id: str, label: str) -> int:
        engagement = self.ensure_engagement(device_id)
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO action_runs (
                    engagement_id, device_id, action_id, label, status, started_at, result_json
                ) VALUES (?, ?, ?, ?, 'running', ?, '{}')
                """,
                (engagement["id"], device_id, action_id, label, _utc_now()),
            )
            action_run_id = int(cursor.lastrowid)
            conn.execute(
                "UPDATE engagements SET updated_at = ? WHERE id = ?",
                (_utc_now(), engagement["id"]),
            )
            conn.commit()
            return action_run_id

    def complete_action(
        self,
        action_run_id: int,
        *,
        status: str,
        elapsed_ms: int,
        result: dict[str, Any],
    ) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                UPDATE action_runs
                SET status = ?, completed_at = ?, elapsed_ms = ?, result_json = ?
                WHERE id = ?
                """,
                (status, _utc_now(), int(elapsed_ms), json.dumps(result, sort_keys=True), action_run_id),
            )
            row = conn.execute("SELECT engagement_id FROM action_runs WHERE id = ?", (action_run_id,)).fetchone()
            if row:
                conn.execute(
                    "UPDATE engagements SET updated_at = ? WHERE id = ?",
                    (_utc_now(), row["engagement_id"]),
                )
            conn.commit()

    def list_action_runs(self, device_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM action_runs WHERE device_id = ? ORDER BY id DESC",
                (device_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "engagement_id": row["engagement_id"],
                "device_id": row["device_id"],
                "action_id": row["action_id"],
                "label": row["label"],
                "status": row["status"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "elapsed_ms": row["elapsed_ms"],
                "result": json.loads(row["result_json"] or "{}"),
            }
            for row in rows
        ]

    def upsert_access_session(
        self,
        *,
        device_id: str,
        access_key: str,
        kind: str,
        label: str,
        status: str,
        endpoint: dict[str, Any],
        obtained_via_action_run_id: int | None = None,
    ) -> int:
        engagement = self.ensure_engagement(device_id)
        now = _utc_now()
        with closing(self._connect()) as conn:
            conn.execute(
                """
                INSERT INTO access_sessions (
                    engagement_id, device_id, access_key, kind, label, status,
                    endpoint_json, obtained_via_action_run_id, opened_at, last_seen_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(engagement_id, access_key) DO UPDATE SET
                    label = excluded.label,
                    status = excluded.status,
                    endpoint_json = excluded.endpoint_json,
                    obtained_via_action_run_id = COALESCE(excluded.obtained_via_action_run_id, access_sessions.obtained_via_action_run_id),
                    last_seen_at = excluded.last_seen_at,
                    closed_at = NULL
                """,
                (
                    engagement["id"], device_id, access_key, kind, label, status,
                    json.dumps(endpoint, sort_keys=True), obtained_via_action_run_id, now, now,
                ),
            )
            row = conn.execute(
                "SELECT id FROM access_sessions WHERE engagement_id = ? AND access_key = ?",
                (engagement["id"], access_key),
            ).fetchone()
            conn.execute(
                "UPDATE engagements SET updated_at = ? WHERE id = ?",
                (now, engagement["id"]),
            )
            conn.commit()
            if not row:
                raise RuntimeError("Could not save access session.")
            return int(row["id"])

    def list_access_sessions(self, device_id: str) -> list[dict[str, Any]]:
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM access_sessions WHERE device_id = ? ORDER BY last_seen_at DESC, id DESC",
                (device_id,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "engagement_id": row["engagement_id"],
                "device_id": row["device_id"],
                "access_key": row["access_key"],
                "kind": row["kind"],
                "label": row["label"],
                "status": row["status"],
                "endpoint": json.loads(row["endpoint_json"] or "{}"),
                "obtained_via_action_run_id": row["obtained_via_action_run_id"],
                "opened_at": row["opened_at"],
                "last_seen_at": row["last_seen_at"],
                "closed_at": row["closed_at"],
            }
            for row in rows
        ]

    def set_access_status(self, access_session_id: int, status: str) -> None:
        now = _utc_now()
        closed_at = now if status == "closed" else None
        with closing(self._connect()) as conn:
            conn.execute(
                "UPDATE access_sessions SET status = ?, last_seen_at = ?, closed_at = ? WHERE id = ?",
                (status, now, closed_at, access_session_id),
            )
            conn.commit()

    def clear_workspace(self, device_id: str) -> None:
        engagement = self.get_engagement(device_id)
        with closing(self._connect()) as conn:
            if engagement:
                conn.execute("DELETE FROM access_sessions WHERE engagement_id = ?", (engagement["id"],))
                conn.execute("DELETE FROM action_runs WHERE engagement_id = ?", (engagement["id"],))
                conn.execute("DELETE FROM engagements WHERE id = ?", (engagement["id"],))
            conn.execute("DELETE FROM findings WHERE device_id = ?", (device_id,))
            conn.commit()
        device = self.get_device(device_id)
        if device and device.get("enrolled"):
            self.ensure_engagement(device_id)

    def add_finding(
        self,
        *,
        device_id: str,
        category: str,
        severity: str,
        title: str,
        proof: dict[str, Any],
        remediation: str,
        status: str = "verified",
    ) -> int:
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO findings (
                    device_id, category, severity, title,
                    proof_json, remediation, status, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    device_id,
                    category,
                    severity,
                    title,
                    json.dumps(proof, sort_keys=True),
                    remediation,
                    status,
                    _utc_now(),
                ),
            )
            row_id = int(cursor.lastrowid)
            conn.commit()
            return row_id

    def list_findings(self, device_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM findings"
        params: tuple[Any, ...] = ()
        if device_id:
            sql += " WHERE device_id = ?"
            params = (device_id,)
        sql += " ORDER BY created_at DESC, id DESC"
        with closing(self._connect()) as conn:
            rows = conn.execute(sql, params).fetchall()
        result: list[dict[str, Any]] = []
        for row in rows:
            result.append(
                {
                    "id": row["id"],
                    "device_id": row["device_id"],
                    "category": row["category"],
                    "severity": row["severity"],
                    "title": row["title"],
                    "proof": json.loads(row["proof_json"]),
                    "remediation": row["remediation"],
                    "status": row["status"],
                    "created_at": row["created_at"],
                }
            )
        return result

    @staticmethod
    def _device_row(row: sqlite3.Row) -> dict[str, Any]:
        return {
            "id": row["id"],
            "kind": row["kind"],
            "name": row["name"],
            "address": row["address"],
            "details": json.loads(row["details_json"]),
            "enrolled": bool(row["enrolled"]),
            "first_seen": row["first_seen"],
            "last_seen": row["last_seen"],
        }
