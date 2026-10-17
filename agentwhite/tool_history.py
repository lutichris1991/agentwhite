from __future__ import annotations

import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .storage import data_dir


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class ToolRunStore:
    def __init__(self, db_path: Path | None = None) -> None:
        self.db_path = db_path or (data_dir() / "agentwhite.db")
        self._init_db()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self) -> None:
        with closing(self._connect()) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS tool_runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    tool_id TEXT NOT NULL,
                    action_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    effect TEXT NOT NULL,
                    scope TEXT NOT NULL,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    completed_at TEXT NOT NULL,
                    elapsed_ms INTEGER NOT NULL,
                    result_json TEXT NOT NULL
                )
                """
            )
            conn.execute("CREATE INDEX IF NOT EXISTS idx_tool_runs_tool_id ON tool_runs(tool_id)")
            conn.commit()

    def add_run(
        self,
        *,
        tool_id: str,
        action_id: str,
        label: str,
        effect: str,
        scope: str,
        status: str,
        started_at: str,
        elapsed_ms: int,
        result: dict[str, Any],
    ) -> int:
        with closing(self._connect()) as conn:
            cursor = conn.execute(
                """
                INSERT INTO tool_runs (
                    tool_id, action_id, label, effect, scope, status,
                    started_at, completed_at, elapsed_ms, result_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    tool_id,
                    action_id,
                    label,
                    effect,
                    scope,
                    status,
                    started_at,
                    _utc_now(),
                    int(elapsed_ms),
                    json.dumps(result, sort_keys=True, default=str),
                ),
            )
            run_id = int(cursor.lastrowid)
            conn.commit()
            return run_id

    def list_runs(self, limit: int = 100) -> list[dict[str, Any]]:
        limit = max(1, min(int(limit), 500))
        with closing(self._connect()) as conn:
            rows = conn.execute(
                "SELECT * FROM tool_runs ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "id": row["id"],
                "tool_id": row["tool_id"],
                "action_id": row["action_id"],
                "label": row["label"],
                "effect": row["effect"],
                "scope": row["scope"],
                "status": row["status"],
                "started_at": row["started_at"],
                "completed_at": row["completed_at"],
                "elapsed_ms": row["elapsed_ms"],
                "result": json.loads(row["result_json"] or "{}"),
            }
            for row in rows
        ]
