"""Bounded, explicit Creator Desk source packs and Workbench-owned draft revisions.

No project checkout is written. Selected local source excerpts are re-read, checked
against file digests, and held only after a separate user save action. The SQLite
shelf is local to HOUSE, not a source-of-truth or a plugin memory interface.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .config import RootConfig
from .creator import _MAX_BYTES, _MAX_DEPTH, _SKIP_DIRS, _SKIP_NAME_PARTS, _SOURCE_EXTENSIONS
from .repos import RepoStatus

MAX_SOURCES = 8
MAX_PACK_BYTES = 8192
MAX_DRAFT_BYTES = 32768


class CreatorConflict(ValueError):
    """Source changed, draft revision moved, or a prior snapshot is unavailable."""


def _digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _checked_selection(
    roots: tuple[RootConfig, ...],
    repos: list[RepoStatus],
    selection: dict[str, Any],
) -> dict[str, Any]:
    root_id = selection["root_id"]
    repo_path = selection["repo_path"]
    source_path = selection["source_path"]
    line = selection["line"]
    expected_digest = selection["file_sha256"]
    expected_excerpt = selection["snippet"]

    root = next((item for item in roots if item.id == root_id), None)
    repo = next((item for item in repos if item.root_id == root_id and item.relative_path == repo_path), None)
    if root is None or repo is None:
        raise CreatorConflict("selected repository is no longer discoverable")
    if len(source_path) > 512:
        raise ValueError("source path is too long")
    relative = Path(source_path)
    if (relative.is_absolute() or len(relative.parts) > _MAX_DEPTH + 1
        or any(part in ("", ".", "..") or part.startswith(".") or part.casefold() in _SKIP_DIRS
               or any(word in part.casefold() for word in _SKIP_NAME_PARTS) for part in relative.parts)
        or relative.suffix.casefold() not in _SOURCE_EXTENSIONS):
        raise ValueError("source is not eligible for bounded selection")
    root_real = root.path.resolve(strict=True)
    repo_real = Path(repo.path).resolve(strict=True)
    repo_real.relative_to(root_real)
    current = repo_real
    # Refuse symlinks at each path component, including a now-replaced checkout file.
    for component in relative.parts:
        current = current / component
        if current.is_symlink():
            raise ValueError("symlinked source is not eligible")
    source = current.resolve(strict=True)
    source.relative_to(repo_real)
    stat = source.stat()
    if not source.is_file() or stat.st_size > _MAX_BYTES:
        raise ValueError("source is missing or exceeds inspection limit")
    raw = source.read_bytes()
    if len(raw) > _MAX_BYTES or _digest(raw) != expected_digest:
        raise CreatorConflict("selected source changed since search; inspect it again")
    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise ValueError("selected source is not UTF-8") from exc
    lines = text.splitlines()
    if line > len(lines):
        raise CreatorConflict("selected source line is no longer available")
    excerpt = lines[line - 1].strip()
    if len(excerpt) > 240 or excerpt != expected_excerpt:
        raise CreatorConflict("selected line differs or is too long; inspect it again")
    return {
        "root_id": root_id,
        "repo_path": repo_path,
        "source_path": source_path,
        "line_start": line, "line_end": line,
        "excerpt": excerpt,
        "file_sha256": expected_digest,
        "excerpt_sha256": _digest(excerpt.encode("utf-8")),
        "worktree_head": repo.head,
        "worktree_dirty": repo.dirty,
        "source_kind": "local_worktree",
    }


def preview_pack(
    roots: tuple[RootConfig, ...],
    repos: list[RepoStatus],
    selections: list[dict[str, Any]],
) -> dict[str, Any]:
    if not 1 <= len(selections) <= MAX_SOURCES:
        raise ValueError("select between one and eight source lines")
    items = [_checked_selection(roots, repos, item) for item in selections]
    identities = [(item["root_id"], item["repo_path"], item["source_path"], item["line_start"]) for item in items]
    if len(identities) != len(set(identities)):
        raise ValueError("duplicate source lines are not allowed")
    total = sum(len(_json(item).encode("utf-8")) for item in items)
    if total > MAX_PACK_BYTES:
        raise ValueError("selected source pack exceeds 8 KiB")
    return {
        "version": "house.creator-source-pack/v0.2",
        "sources": items,
        "source_count": len(items),
        "pack_sha256": _digest(_json(items).encode("utf-8")),
        "authority": "none",
        "notice": "selected local-worktree excerpts; not frozen Git commit contents or full sources",
    }


class CreatorShelf:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        self._initialize()
        if os.name == "posix":
            os.chmod(self.path, 0o600)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _initialize(self):
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS creator_packs(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                digest TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS creator_drafts(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pack_id INTEGER NOT NULL REFERENCES creator_packs(id),
                created_at TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS creator_revisions(
                draft_id INTEGER NOT NULL REFERENCES creator_drafts(id),
                revision INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL,
                content_sha256 TEXT NOT NULL,
                PRIMARY KEY(draft_id, revision)
            )""")

    def save_pack(self, pack: dict[str, Any]) -> dict[str, Any]:
        # The exact preview payload must have been generated by the server and
        # checked again against live sources by the HTTP handler before this call.
        with self._connect() as db:
            cursor = db.execute(
                "INSERT INTO creator_packs(created_at,digest,payload_json) VALUES(?,?,?)",
                (_now(), pack["pack_sha256"], _json(pack)),
            )
            pack_id = int(cursor.lastrowid)
        return {"id": pack_id, "pack_sha256": pack["pack_sha256"], "source_count": pack["source_count"]}

    def get_pack(self, pack_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("SELECT id,created_at,payload_json FROM creator_packs WHERE id=?", (pack_id,)).fetchone()
        return None if row is None else {"id": row["id"], "created_at": row["created_at"], **json.loads(row["payload_json"])}

    def list_packs(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("SELECT id,created_at,digest,payload_json FROM creator_packs ORDER BY id DESC LIMIT 50").fetchall()
        return [{"id": row["id"], "created_at": row["created_at"], "pack_sha256": row["digest"],
                 "source_count": json.loads(row["payload_json"])["source_count"]} for row in rows]

    def save_revision(self, draft_id: int | None, expected_revision: int, payload: dict[str, Any]) -> dict[str, Any]:
        if len(payload["body"].encode("utf-8")) > MAX_DRAFT_BYTES:
            raise ValueError("draft exceeds 32 KiB")
        packed = _json(payload)
        body_digest = _digest(payload["body"].encode("utf-8"))
        now = _now()
        with self._connect() as db:
            if draft_id is None:
                if expected_revision != 0:
                    raise CreatorConflict("new drafts require expected revision zero")
                pack = db.execute("SELECT id FROM creator_packs WHERE id=?", (payload["pack_id"],)).fetchone()
                if pack is None:
                    raise CreatorConflict("source pack no longer exists")
                draft_id = int(db.execute(
                    "INSERT INTO creator_drafts(pack_id,created_at) VALUES(?,?)",
                    (payload["pack_id"], now),
                ).lastrowid)
                revision = 1
            else:
                row = db.execute("SELECT pack_id FROM creator_drafts WHERE id=?", (draft_id,)).fetchone()
                if row is None:
                    raise CreatorConflict("draft no longer exists")
                if row["pack_id"] != payload["pack_id"]:
                    raise CreatorConflict("a draft cannot silently switch source packs")
                latest = db.execute(
                    "SELECT MAX(revision) AS n FROM creator_revisions WHERE draft_id=?", (draft_id,),
                ).fetchone()["n"]
                if latest != expected_revision:
                    raise CreatorConflict("draft was revised elsewhere; reload before saving")
                revision = latest + 1
            db.execute("""INSERT INTO creator_revisions
                (draft_id,revision,created_at,payload_json,content_sha256)
                VALUES(?,?,?,?,?)""",
                (draft_id, revision, now, packed, body_digest),
            )
        return {"id": draft_id, "revision": revision, "content_sha256": body_digest, "status": "local_draft"}

    def get_draft(self, draft_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute("""SELECT d.id,d.pack_id,d.created_at,r.revision,r.created_at AS revised_at,
                r.payload_json,r.content_sha256
                FROM creator_drafts d JOIN creator_revisions r ON r.draft_id=d.id
                WHERE d.id=? ORDER BY r.revision DESC LIMIT 1""", (draft_id,)).fetchone()
        if row is None:
            return None
        return {
            "id": row["id"], "pack_id": row["pack_id"], "created_at": row["created_at"],
            "revision": row["revision"], "revised_at": row["revised_at"],
            "content_sha256": row["content_sha256"], "status": "local_draft",
            **json.loads(row["payload_json"]),
        }

    def list_drafts(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("""SELECT d.id,d.pack_id,MAX(r.revision) AS revision
                FROM creator_drafts d JOIN creator_revisions r ON r.draft_id=d.id
                GROUP BY d.id ORDER BY d.id DESC LIMIT 50""").fetchall()
        result = []
        for row in rows:
            draft = self.get_draft(row["id"])
            result.append({
                "id": draft["id"], "pack_id": draft["pack_id"], "revision": draft["revision"],
                "title": draft["title"], "kind": draft["kind"], "revised_at": draft["revised_at"],
                "status": "local_draft",
            })
        return result

    def revisions(self, draft_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute("""SELECT revision,created_at,content_sha256
                FROM creator_revisions WHERE draft_id=? ORDER BY revision DESC LIMIT 100""",
                (draft_id,)).fetchall()
        return [dict(row) for row in rows]
