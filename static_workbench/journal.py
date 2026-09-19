from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class SenseFieldRecord:
    id: int
    created_at: str
    raw_text: str
    parent_id: int | None
    payload: dict[str, Any]


@dataclass(frozen=True)
class EventRecord:
    id: int
    created_at: str
    kind: str
    payload: dict[str, Any]


class Journal:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS sense_fields (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    parent_id INTEGER,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def append(self, kind: str, payload: dict[str, Any]) -> EventRecord:
        created_at = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO events(created_at, kind, payload_json) VALUES (?, ?, ?)",
                (created_at, kind, payload_json),
            )
            event_id = int(cursor.lastrowid)
        return EventRecord(event_id, created_at, kind, payload)


    def append_sense_field(
        self,
        raw_text: str,
        parent_id: int | None,
        payload: dict[str, Any],
    ) -> SenseFieldRecord:
        created_at = datetime.now(timezone.utc).isoformat()
        payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO sense_fields(created_at, raw_text, parent_id, payload_json) VALUES (?, ?, ?, ?)",
                (created_at, raw_text, parent_id, payload_json),
            )
            record_id = int(cursor.lastrowid)
        return SenseFieldRecord(record_id, created_at, raw_text, parent_id, payload)

    def latest_sense_fields(self, limit: int = 100) -> list[SenseFieldRecord]:
        bounded_limit = max(1, min(int(limit), 1000))
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, created_at, raw_text, parent_id, payload_json FROM sense_fields ORDER BY id DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        return [self._sense_field_from_row(row) for row in rows]

    def get_sense_field(self, record_id: int) -> SenseFieldRecord | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT id, created_at, raw_text, parent_id, payload_json FROM sense_fields WHERE id = ?",
                (int(record_id),),
            ).fetchone()
        return None if row is None else self._sense_field_from_row(row)

    @staticmethod
    def _sense_field_from_row(row: sqlite3.Row) -> SenseFieldRecord:
        return SenseFieldRecord(
            id=int(row["id"]),
            created_at=str(row["created_at"]),
            raw_text=str(row["raw_text"]),
            parent_id=None if row["parent_id"] is None else int(row["parent_id"]),
            payload=json.loads(row["payload_json"]),
        )

    def latest(self, limit: int = 100) -> list[EventRecord]:
        bounded_limit = max(1, min(int(limit), 1000))
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, created_at, kind, payload_json FROM events ORDER BY id DESC LIMIT ?",
                (bounded_limit,),
            ).fetchall()
        return [
            EventRecord(
                id=int(row["id"]),
                created_at=str(row["created_at"]),
                kind=str(row["kind"]),
                payload=json.loads(row["payload_json"]),
            )
            for row in rows
        ]
