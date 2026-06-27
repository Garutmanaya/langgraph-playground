from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any


DEFAULT_DB_PATH = Path(__file__).resolve().parent / "shared_context.db"


class SharedContextStore:
    """Small SQLite-backed shared context store for learning."""

    def __init__(self, db_path: str | Path = DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.initialize()

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_kv (
                    context_id TEXT NOT NULL,
                    key TEXT NOT NULL,
                    value_json TEXT NOT NULL,
                    updated_at REAL NOT NULL,
                    PRIMARY KEY (context_id, key)
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_id TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    source TEXT NOT NULL,
                    message TEXT NOT NULL,
                    payload_json TEXT,
                    created_at REAL NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS context_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    context_id TEXT NOT NULL,
                    fact_type TEXT NOT NULL,
                    fact_key TEXT NOT NULL,
                    fact_value TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    source TEXT NOT NULL,
                    created_at REAL NOT NULL
                )
                """
            )

    def set_value(self, context_id: str, key: str, value: Any) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO context_kv (context_id, key, value_json, updated_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(context_id, key)
                DO UPDATE SET value_json=excluded.value_json, updated_at=excluded.updated_at
                """,
                (context_id, key, json.dumps(value), time.time()),
            )

    def get_value(self, context_id: str, key: str, default: Any = None) -> Any:
        with self.connect() as conn:
            row = conn.execute(
                "SELECT value_json FROM context_kv WHERE context_id = ? AND key = ?",
                (context_id, key),
            ).fetchone()

        if not row:
            return default

        return json.loads(row["value_json"])

    def get_all_values(self, context_id: str) -> dict[str, Any]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT key, value_json FROM context_kv WHERE context_id = ? ORDER BY key",
                (context_id,),
            ).fetchall()

        return {row["key"]: json.loads(row["value_json"]) for row in rows}

    def add_event(
        self,
        context_id: str,
        event_type: str,
        source: str,
        message: str,
        payload: dict[str, Any] | None = None,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO context_events
                (context_id, event_type, source, message, payload_json, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    context_id,
                    event_type,
                    source,
                    message,
                    json.dumps(payload or {}),
                    time.time(),
                ),
            )

    def list_events(self, context_id: str, limit: int = 20) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT event_type, source, message, payload_json, created_at
                FROM context_events
                WHERE context_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (context_id, limit),
            ).fetchall()

        events = []
        for row in rows:
            events.append(
                {
                    "event_type": row["event_type"],
                    "source": row["source"],
                    "message": row["message"],
                    "payload": json.loads(row["payload_json"] or "{}"),
                    "created_at": row["created_at"],
                }
            )
        return events

    def add_fact(
        self,
        context_id: str,
        fact_type: str,
        fact_key: str,
        fact_value: str,
        confidence: float,
        source: str,
    ) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                INSERT INTO context_facts
                (context_id, fact_type, fact_key, fact_value, confidence, source, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    context_id,
                    fact_type,
                    fact_key,
                    fact_value,
                    confidence,
                    source,
                    time.time(),
                ),
            )

    def list_facts(self, context_id: str, limit: int = 50) -> list[dict[str, Any]]:
        with self.connect() as conn:
            rows = conn.execute(
                """
                SELECT fact_type, fact_key, fact_value, confidence, source, created_at
                FROM context_facts
                WHERE context_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (context_id, limit),
            ).fetchall()

        return [dict(row) for row in rows]

    def reset_context(self, context_id: str) -> None:
        with self.connect() as conn:
            conn.execute("DELETE FROM context_kv WHERE context_id = ?", (context_id,))
            conn.execute("DELETE FROM context_events WHERE context_id = ?", (context_id,))
            conn.execute("DELETE FROM context_facts WHERE context_id = ?", (context_id,))
