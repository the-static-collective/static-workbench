"""HOUSE-owned notes and resumable work sessions; no project writes or authority."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from pydantic import BaseModel, Field


class ReturnConflict(ValueError):
    """An explicitly selected local record is missing, stale, or invalid."""


class NoteInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    raw_text: str = Field(min_length=1, max_length=20000)
    margin: str = Field(default="", max_length=4000)
    carry: str = Field(default="", max_length=4000)


class SessionInput(BaseModel):
    note_id: int = Field(ge=1)
    expected_note_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    project: str = Field(default="", max_length=160)
    intention: str = Field(min_length=1, max_length=4000)
    next_step: str = Field(min_length=1, max_length=4000)
    unresolved: str = Field(default="", max_length=4000)


class CheckpointInput(BaseModel):
    expected_revision: int = Field(ge=1)
    changed: str = Field(default="", max_length=4000)
    next_step: str = Field(min_length=1, max_length=4000)
    unresolved: str = Field(default="", max_length=4000)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _digest(value: dict) -> str:
    carrier = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    return hashlib.sha256(carrier.encode("utf-8")).hexdigest()


class ReturnDesk:
    """Separate SQLite store: RAW notes immutable, checkpoint chain append-only."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS return_notes (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    raw_text TEXT NOT NULL,
                    margin TEXT NOT NULL,
                    carry TEXT NOT NULL,
                    sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS return_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    note_id INTEGER NOT NULL REFERENCES return_notes(id),
                    note_sha256 TEXT NOT NULL,
                    project TEXT NOT NULL,
                    intention TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS return_checkpoints (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES return_sessions(id),
                    revision INTEGER NOT NULL,
                    created_at TEXT NOT NULL,
                    changed TEXT NOT NULL,
                    next_step TEXT NOT NULL,
                    unresolved TEXT NOT NULL,
                    previous_sha256 TEXT,
                    sha256 TEXT NOT NULL,
                    UNIQUE(session_id, revision)
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @staticmethod
    def _nonblank(value: str, field: str) -> None:
        if not value.strip():
            raise ReturnConflict(field + " must not be blank")

    def save_note(self, note: NoteInput) -> dict:
        self._nonblank(note.title, "title")
        self._nonblank(note.raw_text, "raw_text")
        carrier = note.model_dump()
        digest = _digest(carrier)
        created_at = _now()
        with self._connect() as db:
            cursor = db.execute(
                """INSERT INTO return_notes
                (created_at, title, raw_text, margin, carry, sha256)
                VALUES (?, ?, ?, ?, ?, ?)""",
                (created_at, note.title, note.raw_text, note.margin, note.carry, digest),
            )
            note_id = cursor.lastrowid
        return {"id": note_id, "created_at": created_at, **carrier, "sha256": digest}

    def get_note(self, note_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM return_notes WHERE id = ?", (note_id,)).fetchone()
            return dict(row) if row else None

    def list_notes(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                "SELECT id, created_at, title, sha256 FROM return_notes ORDER BY id DESC LIMIT 100"
            ).fetchall()
            return [dict(row) for row in rows]

    @staticmethod
    def _checkpoint(db: sqlite3.Connection, session_id: int, revision: int,
                    changed: str, next_step: str, unresolved: str,
                    previous_sha256: str | None) -> dict:
        created_at = _now()
        content = {
            "session_id": session_id,
            "revision": revision,
            "changed": changed,
            "next_step": next_step,
            "unresolved": unresolved,
            "previous_sha256": previous_sha256,
        }
        digest = _digest(content)
        cursor = db.execute(
            """INSERT INTO return_checkpoints
            (session_id, revision, created_at, changed, next_step, unresolved, previous_sha256, sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
            (session_id, revision, created_at, changed, next_step, unresolved, previous_sha256, digest),
        )
        return {"id": cursor.lastrowid, "created_at": created_at, **content, "sha256": digest}

    def create_session(self, payload: SessionInput) -> dict:
        self._nonblank(payload.intention, "intention")
        self._nonblank(payload.next_step, "next_step")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            note = db.execute(
                "SELECT sha256 FROM return_notes WHERE id = ?", (payload.note_id,)
            ).fetchone()
            if note is None:
                raise ReturnConflict("note not found")
            if note["sha256"] != payload.expected_note_sha256:
                raise ReturnConflict("note digest differs from selected note")
            created_at = _now()
            cursor = db.execute(
                """INSERT INTO return_sessions
                (created_at, note_id, note_sha256, project, intention)
                VALUES (?, ?, ?, ?, ?)""",
                (created_at, payload.note_id, note["sha256"], payload.project, payload.intention),
            )
            session_id = int(cursor.lastrowid)
            checkpoint = self._checkpoint(
                db, session_id, 1, "", payload.next_step, payload.unresolved, None
            )
        return {"id": session_id, "created_at": created_at, "note_id": payload.note_id,
                "note_sha256": note["sha256"], "project": payload.project,
                "intention": payload.intention, "checkpoint": checkpoint}

    def save_checkpoint(self, session_id: int, payload: CheckpointInput) -> dict:
        self._nonblank(payload.next_step, "next_step")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if not db.execute("SELECT 1 FROM return_sessions WHERE id = ?", (session_id,)).fetchone():
                raise ReturnConflict("session not found")
            previous = db.execute(
                """SELECT revision, sha256 FROM return_checkpoints
                WHERE session_id = ? ORDER BY revision DESC LIMIT 1""", (session_id,)
            ).fetchone()
            if previous is None or previous["revision"] != payload.expected_revision:
                raise ReturnConflict("session changed since it was opened; reopen before saving")
            return self._checkpoint(
                db, session_id, previous["revision"] + 1, payload.changed,
                payload.next_step, payload.unresolved, previous["sha256"]
            )

    def get_session(self, session_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT * FROM return_sessions WHERE id = ?", (session_id,)
            ).fetchone()
            if row is None:
                return None
            note = db.execute(
                "SELECT * FROM return_notes WHERE id = ?", (row["note_id"],)
            ).fetchone()
            checkpoints = db.execute(
                """SELECT * FROM return_checkpoints WHERE session_id = ?
                ORDER BY revision ASC""", (session_id,)
            ).fetchall()
        return {**dict(row), "note": dict(note),
                "checkpoints": [dict(item) for item in checkpoints],
                "latest": dict(checkpoints[-1]) if checkpoints else None}

    def list_sessions(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT s.*, n.title AS note_title,
                c.revision, c.next_step, c.sha256 AS checkpoint_sha256
                FROM return_sessions AS s
                JOIN return_notes AS n ON n.id = s.note_id
                JOIN return_checkpoints AS c ON c.session_id = s.id
                AND c.revision = (
                    SELECT MAX(revision) FROM return_checkpoints WHERE session_id = s.id
                )
                ORDER BY s.id DESC LIMIT 100"""
            ).fetchall()
            return [dict(row) for row in rows]
