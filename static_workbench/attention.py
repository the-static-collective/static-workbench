"""Local human-selected attention crossings; no rankings or execution authority."""
from __future__ import annotations

import json
import re
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field

KINDS = r"^[a-z][a-z0-9._-]{0,31}$"
DIMENSIONS = ("joyful", "useful", "curiouser")


class AttentionDeclaration(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    kind: str = Field(pattern=KINDS)
    target_id: str = Field(min_length=1, max_length=256)
    dimensions: list[Literal["joyful", "useful", "curiouser"]] = Field(default_factory=list, max_length=3)
    explicit_none: bool = False
    expected_previous_id: int | None = Field(default=None, ge=1)


def check_target(kind: str, target_id: str) -> None:
    if not re.fullmatch(KINDS, kind) or not target_id or len(target_id) > 256:
        raise HTTPException(422, "invalid attention target")
    if target_id != target_id.strip() or any(ord(ch) < 32 or ord(ch) == 127 for ch in target_id):
        raise HTTPException(422, "target id may not contain whitespace boundaries or control characters")


class AttentionStore:
    def __init__(self, state_dir: Path):
        self.path = state_dir / "attention.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS attention (
                id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
                kind TEXT NOT NULL, target_id TEXT NOT NULL,
                dimensions_json TEXT NOT NULL, explicit_none INTEGER NOT NULL,
                previous_id INTEGER)""")
            db.execute("CREATE INDEX IF NOT EXISTS attention_by_target ON attention(kind,target_id,id DESC)")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def as_record(row):
        return dict(id=row["id"], created_at=row["created_at"], kind=row["kind"],
                    target_id=row["target_id"], dimensions=json.loads(row["dimensions_json"]),
                    explicit_none=bool(row["explicit_none"]), previous_id=row["previous_id"],
                    authority="human-declared/local-only")

    def read(self, kind: str, target_id: str, limit: int = 20):
        check_target(kind, target_id)
        with self.connect() as db:
            rows = db.execute(
                "SELECT * FROM attention WHERE kind=? AND target_id=? ORDER BY id DESC LIMIT ?",
                (kind, target_id, limit)).fetchall()
        history = [self.as_record(row) for row in rows]
        return dict(kind=kind, target_id=target_id,
                    current=history[0] if history else None, history=history,
                    semantics="declaration-not-ranking; no execution authority")

    def declare(self, request: AttentionDeclaration):
        check_target(request.kind, request.target_id)
        if len(set(request.dimensions)) != len(request.dimensions):
            raise HTTPException(422, "duplicate dimension")
        if request.explicit_none and request.dimensions:
            raise HTTPException(422, "explicit none cannot contain dimensions")
        chosen = [name for name in DIMENSIONS if name in request.dimensions]
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute(
                "SELECT * FROM attention WHERE kind=? AND target_id=? ORDER BY id DESC LIMIT 1",
                (request.kind, request.target_id)).fetchone()
            previous_id = previous["id"] if previous else None
            if previous_id != request.expected_previous_id:
                raise HTTPException(409, "attention changed; reload before revising")
            if not previous or json.loads(previous["dimensions_json"]) != chosen or (
                bool(previous["explicit_none"]) != request.explicit_none
            ):
                db.execute(
                    "INSERT INTO attention(created_at,kind,target_id,dimensions_json,explicit_none,previous_id) "
                    "VALUES(?,?,?,?,?,?)",
                    (datetime.now(timezone.utc).isoformat(), request.kind, request.target_id,
                     json.dumps(chosen, separators=(",", ":")), int(request.explicit_none), previous_id))
        return self.read(request.kind, request.target_id)


def attention_router(state_dir: Path, session_token: str) -> APIRouter:
    store = AttentionStore(state_dir)
    router = APIRouter()

    @router.get("/api/attention")
    def read(kind: str = Query(pattern=KINDS, max_length=32),
             target_id: str = Query(min_length=1, max_length=256),
             limit: int = Query(default=20, ge=1, le=100)):
        return store.read(kind, target_id, limit)

    @router.post("/api/attention")
    def write(payload: AttentionDeclaration, request: Request):
        origin = request.headers.get("origin")
        host = request.headers.get("host", "")
        if origin is not None and origin != "http://" + host:
            raise HTTPException(403, "cross-origin attention write refused")
        token = request.headers.get("x-workbench-session", "")
        if not secrets.compare_digest(token, session_token):
            raise HTTPException(403, "local attention session required")
        return store.declare(payload)

    return router
