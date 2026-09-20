"""PATH-ALL-HOME-001: deliberate, bounded, self-reported source handoffs."""
from __future__ import annotations

import hashlib
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class Handoff(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    schema: Literal["attention-crossing.handoff/v0.1"]
    source_app: Literal["goatnote", "static-live"]
    source_record_id: str = Field(min_length=1, max_length=160)
    source_target_id: str = Field(min_length=1, max_length=256)
    source_recorded_at: str = Field(min_length=20, max_length=40)
    source_previous_id: str | None = Field(default=None, max_length=160)
    source_locator: str = Field(min_length=1, max_length=512)
    label: str = Field(min_length=1, max_length=160)
    dimensions: list[Literal["joyful", "useful", "curiouser"]] = Field(max_length=3)
    explicit_none: bool
    evidence: Literal["source-export/self-reported"]

    @field_validator("source_record_id", "source_target_id", "source_previous_id", "source_locator", "label")
    @classmethod
    def no_controls(cls, value):
        if value is not None and (value != value.strip() or
                                  any(ord(ch) < 32 or ord(ch) == 127 for ch in value)):
            raise ValueError("source identifiers and labels may not contain control characters")
        return value

    @field_validator("source_recorded_at")
    @classmethod
    def dated(cls, value):
        try:
            instant = datetime.fromisoformat(value.replace("Z", "+00:00"))
            if instant.utcoffset() is None:
                raise ValueError("timezone required")
        except (TypeError, ValueError) as exc:
            raise ValueError("source date requires a valid explicit UTC offset") from exc
        return value

    @model_validator(mode="after")
    def independent_choices(self):
        if len(set(self.dimensions)) != len(self.dimensions):
            raise ValueError("duplicate dimensions")
        if self.explicit_none and self.dimensions:
            raise ValueError("explicit none cannot contain dimensions")
        return self


class RawHandoff(BaseModel):
    model_config = ConfigDict(strict=True, extra="forbid")
    raw_json: str = Field(min_length=2, max_length=8192)


class SaveHandoff(RawHandoff):
    expected_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")


def inspect(raw: str):
    if len(raw.encode("utf-8")) > 8192:
        raise HTTPException(422, "handoff exceeds 8 KiB")
    try:
        parsed = json.loads(raw)
        value = Handoff.model_validate(parsed)
    except (ValueError, TypeError) as exc:
        raise HTTPException(422, "invalid attention handoff: " + str(exc)[:240]) from exc
    raw_sha = hashlib.sha256(raw.encode("utf-8")).hexdigest()
    normalized = json.dumps(value.model_dump(), sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    semantic_sha = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return value, raw_sha, semantic_sha


class ReturnShelf:
    def __init__(self, state_dir: Path):
        self.path = state_dir / "attention-imports.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS imports(
                id INTEGER PRIMARY KEY AUTOINCREMENT, imported_at TEXT NOT NULL,
                source_app TEXT NOT NULL, source_record_id TEXT NOT NULL,
                source_target_id TEXT NOT NULL, semantic_sha256 TEXT NOT NULL,
                raw_sha256 TEXT NOT NULL, payload_json TEXT NOT NULL,
                UNIQUE(source_app, source_record_id))""")
            db.execute("CREATE INDEX IF NOT EXISTS imports_by_target ON imports(source_app,source_target_id,id DESC)")

    def connect(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def record(row):
        return dict(import_id=row["id"], imported_at=row["imported_at"],
                    source_app=row["source_app"], source_record_id=row["source_record_id"],
                    source_target_id=row["source_target_id"],
                    source_digest=row["semantic_sha256"],
                    handoff=json.loads(row["payload_json"]),
                    authority="imported-self-report/not-independent-witness")

    def save(self, value: Handoff, raw_sha: str, semantic_sha: str):
        payload = value.model_dump()
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            previous = db.execute("SELECT * FROM imports WHERE source_app=? AND source_record_id=?",
                                  (value.source_app, value.source_record_id)).fetchone()
            if previous:
                if previous["semantic_sha256"] != semantic_sha:
                    raise HTTPException(409, "source record identity collides with a different handoff")
                return {"import": self.record(previous), "duplicate": True}
            cursor = db.execute(
                "INSERT INTO imports(imported_at,source_app,source_record_id,source_target_id,"
                "semantic_sha256,raw_sha256,payload_json) VALUES (?,?,?,?,?,?,?)",
                (datetime.now(timezone.utc).isoformat(), value.source_app, value.source_record_id,
                 value.source_target_id, semantic_sha, raw_sha,
                 json.dumps(payload, separators=(",", ":"), ensure_ascii=False)))
            saved = db.execute("SELECT * FROM imports WHERE id=?", (cursor.lastrowid,)).fetchone()
            return {"import": self.record(saved), "duplicate": False}

    def feed(self, dimension: str, limit: int):
        with self.connect() as db:
            rows = db.execute(
                "SELECT a.* FROM imports a JOIN (SELECT source_app,source_target_id,MAX(id) latest "
                "FROM imports GROUP BY source_app,source_target_id) b ON a.id=b.latest ORDER BY a.id DESC"
            ).fetchall()
        entries = [self.record(row) for row in rows]
        if dimension != "all":
            entries = [row for row in entries if dimension in row["handoff"]["dimensions"]]
        return {"entries": entries[:limit], "dimension": dimension,
                "ordering": "latest-import-for-source-target/not-source-freshness-or-ranking",
                "scope": "local imported self-reports"}


def handoff_router(state_dir: Path, session_token: str) -> APIRouter:
    store = ReturnShelf(state_dir)
    router = APIRouter()

    def guard(request: Request):
        origin = request.headers.get("origin")
        host = request.headers.get("host", "")
        if origin is not None and origin != "http://" + host:
            raise HTTPException(403, "cross-origin attention import refused")
        if not secrets.compare_digest(request.headers.get("x-workbench-session", ""), session_token):
            raise HTTPException(403, "local session token required")

    @router.post("/api/attention/import/preview")
    def preview(payload: RawHandoff, request: Request):
        guard(request)
        value, raw_sha, semantic_sha = inspect(payload.raw_json)
        return {"handoff": value.model_dump(), "raw_sha256": raw_sha,
                "source_digest": semantic_sha,
                "notice": "source-export/self-reported; preview is not approval or independent verification"}

    @router.post("/api/attention/import/save")
    def save(payload: SaveHandoff, request: Request):
        guard(request)
        value, raw_sha, semantic_sha = inspect(payload.raw_json)
        if raw_sha != payload.expected_sha256:
            raise HTTPException(409, "handoff differs from reviewed preview")
        return store.save(value, raw_sha, semantic_sha)

    @router.get("/api/attention/imports")
    def imported(dimension: Literal["all", "joyful", "useful", "curiouser"] = "all",
                 limit: int = Query(default=80, ge=1, le=100)):
        return store.feed(dimension, limit)

    return router
