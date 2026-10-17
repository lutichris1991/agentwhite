from __future__ import annotations

import json
import os
import sqlite3
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
        with self._connect() as conn:
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

                CREATE INDEX IF NOT EXISTS idx_findings_device_id
                    ON findings(device_id);
                """
            )

    def upsert_devices(self, devices: list[dict[str, Any]]) -> None:
        now = _utc_now()
        with self._connect() as conn:
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

    def list_devices(self, kind: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM devices"
        params: tuple[Any, ...] = ()
        if kind:
            sql += " WHERE kind = ?"
            params = (kind,)
        sql += " ORDER BY last_seen DESC, name ASC"
        with self._connect() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._device_row(row) for row in rows]

    def get_device(self, device_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
        return self._device_row(row) if row else None

    def set_enrolled(self, device_id: str, enrolled: bool) -> dict[str, Any] | None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE devices SET enrolled = ? WHERE id = ?",
                (1 if enrolled else 0, device_id),
            )
        return self.get_device(device_id)

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
        with self._connect() as conn:
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
            return int(cursor.lastrowid)

    def list_findings(self, device_id: str | None = None) -> list[dict[str, Any]]:
        sql = "SELECT * FROM findings"
        params: tuple[Any, ...] = ()
        if device_id:
            sql += " WHERE device_id = ?"
            params = (device_id,)
        sql += " ORDER BY created_at DESC, id DESC"
        with self._connect() as conn:
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
