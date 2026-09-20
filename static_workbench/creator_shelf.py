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
            db.execute("""CREATE TABLE IF NOT EXISTS house_native_maxhinal_rides(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL,
                fuel_digest TEXT NOT NULL,
                ride_digest TEXT NOT NULL,
                mode TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS house_graft_rounds(
                round_sha256 TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                ride_id INTEGER NOT NULL REFERENCES house_native_maxhinal_rides(id),
                payload_json TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS house_graft_draft_revisions(
                candidate_sha256 TEXT NOT NULL,
                revision INTEGER NOT NULL,
                created_at TEXT NOT NULL,
                digest TEXT NOT NULL,
                parent_digest TEXT,
                payload_json TEXT NOT NULL,
                PRIMARY KEY(candidate_sha256,revision)
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS house_graft_witnesses(
                witness_sha256 TEXT PRIMARY KEY,
                created_at TEXT NOT NULL,
                ride_id INTEGER NOT NULL REFERENCES house_native_maxhinal_rides(id),
                payload_json TEXT NOT NULL
            )""")
            db.execute("""CREATE TABLE IF NOT EXISTS creator_maxhinal_rides(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                pack_id INTEGER NOT NULL REFERENCES creator_packs(id),
                created_at TEXT NOT NULL,
                digest TEXT NOT NULL,
                source_ride_id TEXT NOT NULL,
                raw_json TEXT NOT NULL,
                summary_json TEXT NOT NULL
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

    def save_maxhinal_ride(self, pack_id: int, raw_json: str, summary: dict[str, Any]) -> dict[str, Any]:
        with self._connect() as db:
            if db.execute("SELECT 1 FROM creator_packs WHERE id=?", (pack_id,)).fetchone() is None:
                raise CreatorConflict("selected source pack is missing")
            saved = db.execute(
                """INSERT INTO creator_maxhinal_rides
                (pack_id,created_at,digest,source_ride_id,raw_json,summary_json)
                VALUES(?,?,?,?,?,?)""",
                (pack_id, _now(), summary["ride_sha256"], summary["ride_id"], raw_json, _json(summary)),
            )
            saved_id = int(saved.lastrowid)
        return {"id": saved_id, "pack_id": pack_id, **summary}

    def get_maxhinal_ride(self, ride_id: int, include_raw: bool = False) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT id,pack_id,created_at,raw_json,summary_json FROM creator_maxhinal_rides WHERE id=?",
                (ride_id,),
            ).fetchone()
        if row is None:
            return None
        result = {"id": row["id"], "pack_id": row["pack_id"], "created_at": row["created_at"],
                  **json.loads(row["summary_json"])}
        if include_raw:
            result["raw_json"] = row["raw_json"]
        return result

    def list_maxhinal_rides(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT id,pack_id,created_at,digest,source_ride_id FROM creator_maxhinal_rides
                ORDER BY id DESC LIMIT 50"""
            ).fetchall()
        return [
            {"id": row["id"], "pack_id": row["pack_id"], "created_at": row["created_at"],
             "ride_sha256": row["digest"], "ride_id": row["source_ride_id"]}
            for row in rows
        ]

    def save_native_ride(self, ride: dict[str, Any]) -> dict[str, Any]:
        payload = _json(ride)
        ride_digest = _digest(payload.encode("utf-8"))
        with self._connect() as db:
            new_id = int(db.execute(
                """INSERT INTO house_native_maxhinal_rides
                (created_at,fuel_digest,ride_digest,mode,payload_json)
                VALUES(?,?,?,?,?)""",
                (_now(), ride["fuel_sha256"], ride_digest, ride["mode"], payload),
            ).lastrowid)
        return {"id": new_id, "ride_sha256": ride_digest, "fuel_sha256": ride["fuel_sha256"],
                "mode": ride["mode"]}

    def list_native_rides(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT id,created_at,fuel_digest,ride_digest,mode FROM house_native_maxhinal_rides
                ORDER BY id DESC LIMIT 50"""
            ).fetchall()
        return [
            {"id": row["id"], "created_at": row["created_at"], "fuel_sha256": row["fuel_digest"],
             "ride_sha256": row["ride_digest"], "mode": row["mode"]}
            for row in rows
        ]

    def get_native_ride(self, ride_id: int) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                "SELECT id,created_at,ride_digest,payload_json FROM house_native_maxhinal_rides WHERE id=?",
                (ride_id,),
            ).fetchone()
        return None if row is None else {
            "id": row["id"], "created_at": row["created_at"], "ride_sha256": row["ride_digest"],
            **json.loads(row["payload_json"]),
        }

    def save_graft_round(self, packet: dict[str, Any]) -> dict[str, Any]:
        """Save reviewed proposal questions without selecting, harvesting or modifying a ride."""
        raw = _json(packet)
        if len(raw.encode("utf-8")) > 32768:
            raise CreatorConflict("GRAFT proposal round exceeds 32 KiB")
        round_sha256 = _digest(raw.encode("utf-8"))
        with self._connect() as db:
            ride = db.execute(
                "SELECT ride_digest,payload_json FROM house_native_maxhinal_rides WHERE id=?",
                (packet["ride_id"],),
            ).fetchone()
            if (ride is None or ride["ride_digest"] != packet["ride_sha256"]
                or _digest(ride["payload_json"].encode("utf-8")) != ride["ride_digest"]):
                raise CreatorConflict("GRAFT round parent ride is missing or corrupted")
            db.execute(
                """INSERT OR IGNORE INTO house_graft_rounds
                (round_sha256,created_at,ride_id,payload_json) VALUES(?,?,?,?)""",
                (round_sha256, _now(), packet["ride_id"], raw),
            )
            stored = db.execute(
                "SELECT payload_json FROM house_graft_rounds WHERE round_sha256=?",
                (round_sha256,),
            ).fetchone()
        if stored is None or stored["payload_json"] != raw:
            raise CreatorConflict("Stored GRAFT round differs from its content address")
        return {"round_sha256": round_sha256, "round": packet}

    def get_graft_round(self, round_sha256: str) -> dict[str, Any] | None:
        if not isinstance(round_sha256, str) or len(round_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in round_sha256
        ):
            return None
        with self._connect() as db:
            row = db.execute(
                "SELECT payload_json FROM house_graft_rounds WHERE round_sha256=?",
                (round_sha256,),
            ).fetchone()
        if row is None:
            return None
        if _digest(row["payload_json"].encode("utf-8")) != round_sha256:
            raise CreatorConflict("Stored GRAFT proposal round digest mismatch")
        return {"round_sha256": round_sha256, "round": json.loads(row["payload_json"])}

    def list_graft_rounds(self, ride_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT round_sha256,created_at,payload_json FROM house_graft_rounds
                WHERE ride_id=? ORDER BY created_at DESC LIMIT 40""",
                (ride_id,),
            ).fetchall()
        return [{"round_sha256": row["round_sha256"], "created_at": row["created_at"],
                 "candidate_count": len(json.loads(row["payload_json"])["candidates"])}
                for row in rows]

    def get_graft_candidate(self, candidate_sha256: str) -> dict[str, Any] | None:
        """Resolve a uniquely addressed candidate from a verified immutable proposal round."""
        if not isinstance(candidate_sha256, str) or len(candidate_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in candidate_sha256
        ):
            return None
        with self._connect() as db:
            rows = db.execute(
                "SELECT round_sha256,payload_json FROM house_graft_rounds ORDER BY created_at DESC LIMIT 1000"
            ).fetchall()
        for row in rows:
            if _digest(row["payload_json"].encode("utf-8")) != row["round_sha256"]:
                raise CreatorConflict("Stored GRAFT round digest mismatch")
            packet = json.loads(row["payload_json"])
            for card in packet["candidates"]:
                if card["candidate_sha256"] == candidate_sha256:
                    return {"round_sha256": row["round_sha256"],
                            "round": packet, "candidate": card}
        return None

    def _graft_draft_row(self, candidate_sha256: str, revision: int | None = None):
        with self._connect() as db:
            if revision is None:
                return db.execute(
                    """SELECT candidate_sha256,revision,created_at,digest,parent_digest,payload_json
                    FROM house_graft_draft_revisions WHERE candidate_sha256=?
                    ORDER BY revision DESC LIMIT 1""", (candidate_sha256,),
                ).fetchone()
            return db.execute(
                """SELECT candidate_sha256,revision,created_at,digest,parent_digest,payload_json
                FROM house_graft_draft_revisions WHERE candidate_sha256=? AND revision=?""",
                (candidate_sha256, revision),
            ).fetchone()

    def _graft_draft_receipt(self, row) -> dict[str, Any]:
        if _digest(row["payload_json"].encode("utf-8")) != row["digest"]:
            raise CreatorConflict("Stored GRAFT draft revision digest mismatch")
        draft = json.loads(row["payload_json"])
        if (draft.get("candidate_sha256") != row["candidate_sha256"]
            or draft.get("revision") != row["revision"]
            or draft.get("parent_draft_sha256") != row["parent_digest"]):
            raise CreatorConflict("Stored GRAFT draft revision identity mismatch")
        if row["revision"] > 1:
            previous = self._graft_draft_row(row["candidate_sha256"], row["revision"] - 1)
            if previous is None or previous["digest"] != row["parent_digest"]:
                raise CreatorConflict("Stored GRAFT draft revision parent is missing or changed")
            self._graft_draft_receipt(previous)
        elif row["parent_digest"] is not None:
            raise CreatorConflict("First GRAFT draft revision cannot have a parent digest")
        return {
            "candidate_sha256": row["candidate_sha256"], "revision": row["revision"],
            "draft_sha256": row["digest"], "draft": draft, "saved": True,
            "created_at": row["created_at"],
        }

    def latest_graft_draft(self, candidate_sha256: str) -> dict[str, Any] | None:
        row = self._graft_draft_row(candidate_sha256)
        return None if row is None else self._graft_draft_receipt(row)

    def get_graft_draft_revision(self, candidate_sha256: str, revision: int) -> dict[str, Any] | None:
        row = self._graft_draft_row(candidate_sha256, revision)
        return None if row is None else self._graft_draft_receipt(row)

    def list_graft_draft_revisions(self, candidate_sha256: str) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT revision,digest FROM house_graft_draft_revisions
                WHERE candidate_sha256=? ORDER BY revision DESC LIMIT 40""",
                (candidate_sha256,),
            ).fetchall()
        return [{"revision": row["revision"], "draft_sha256": row["digest"]}
                for row in rows]

    def save_graft_draft(self, proposal: dict[str, Any], expected_revision: int,
                         expected_draft_sha256: str | None) -> dict[str, Any]:
        """Append a local draft revision under a separately validated, immutable candidate."""
        if len(_json(proposal).encode("utf-8")) > 32768:
            raise CreatorConflict("GRAFT draft exceeds 32 KiB")
        candidate_sha256 = proposal["candidate_sha256"]
        with self._connect() as db:
            # BEGIN IMMEDIATE prevents competing writers from both seeing the same head.
            db.execute("BEGIN IMMEDIATE")
            parent = db.execute(
                """SELECT revision,digest,payload_json FROM house_graft_draft_revisions
                WHERE candidate_sha256=? ORDER BY revision DESC LIMIT 1""",
                (candidate_sha256,),
            ).fetchone()
            revision = parent["revision"] if parent is not None else 0
            digest = parent["digest"] if parent is not None else None
            if revision != expected_revision or digest != expected_draft_sha256:
                raise CreatorConflict("GRAFT draft changed since it was opened; reload before saving")
            if parent is not None:
                self._graft_draft_receipt(parent)
            # Re-check source round while write transaction is held.
            round_rows = db.execute(
                "SELECT round_sha256,payload_json FROM house_graft_rounds"
            ).fetchall()
            valid_parent = False
            for parent_round in round_rows:
                if parent_round["round_sha256"] != proposal["round_sha256"]:
                    continue
                if _digest(parent_round["payload_json"].encode("utf-8")) != parent_round["round_sha256"]:
                    raise CreatorConflict("GRAFT round was changed")
                packet = json.loads(parent_round["payload_json"])
                if (packet.get("ride_id") != proposal["ride_id"]
                    or packet.get("ride_sha256") != proposal["ride_sha256"]
                    or not any(c.get("candidate_sha256") == candidate_sha256
                               for c in packet.get("candidates", []))):
                    raise CreatorConflict("GRAFT draft candidate or ride differs from the saved round")
                ride = db.execute(
                    "SELECT ride_digest,payload_json FROM house_native_maxhinal_rides WHERE id=?",
                    (proposal["ride_id"],),
                ).fetchone()
                if (ride is None or ride["ride_digest"] != proposal["ride_sha256"]
                    or _digest(ride["payload_json"].encode("utf-8")) != ride["ride_digest"]):
                    raise CreatorConflict("GRAFT draft parent ride is missing or corrupted")
                valid_parent = True
                break
            if not valid_parent:
                raise CreatorConflict("GRAFT draft candidate round is missing")
            packet = {**proposal, "revision": revision + 1, "parent_draft_sha256": digest}
            raw = _json(packet)
            saved_digest = _digest(raw.encode("utf-8"))
            db.execute(
                """INSERT INTO house_graft_draft_revisions
                (candidate_sha256,revision,created_at,digest,parent_digest,payload_json)
                VALUES(?,?,?,?,?,?)""",
                (candidate_sha256, revision + 1, _now(), saved_digest, digest, raw),
            )
        return self.latest_graft_draft(candidate_sha256)

    def save_graft_witness(self, witness: dict[str, Any]) -> dict[str, Any]:
        """Immutable Workbench-owned attachment; native ride and Dogram receipt remain separate."""
        raw = _json(witness)
        if len(raw.encode("utf-8")) > 65536:
            raise CreatorConflict("GRAFT witness exceeds 64 KiB")
        witness_id = _digest(raw.encode("utf-8"))
        with self._connect() as db:
            ride_row = db.execute(
                "SELECT ride_digest,payload_json FROM house_native_maxhinal_rides WHERE id=?",
                (witness["ride_id"],),
            ).fetchone()
            if (ride_row is None or ride_row["ride_digest"] != witness["ride_sha256"]
                or _digest(ride_row["payload_json"].encode("utf-8")) != ride_row["ride_digest"]):
                raise CreatorConflict("Linked native ride was removed or corrupted")
            db.execute(
                """INSERT OR IGNORE INTO house_graft_witnesses
                (witness_sha256,created_at,ride_id,payload_json) VALUES(?,?,?,?)""",
                (witness_id, _now(), witness["ride_id"], raw),
            )
            existing = db.execute(
                "SELECT payload_json FROM house_graft_witnesses WHERE witness_sha256=?",
                (witness_id,),
            ).fetchone()
        if existing is None or existing["payload_json"] != raw:
            raise CreatorConflict("Stored GRAFT witness differs from its content address")
        return {"witness_sha256": witness_id, "witness": witness}

    def get_graft_witness(self, witness_sha256: str) -> dict[str, Any] | None:
        if not isinstance(witness_sha256, str) or len(witness_sha256) != 64 or any(
            ch not in "0123456789abcdef" for ch in witness_sha256
        ):
            return None
        with self._connect() as db:
            row = db.execute(
                "SELECT payload_json FROM house_graft_witnesses WHERE witness_sha256=?",
                (witness_sha256,),
            ).fetchone()
        if row is None:
            return None
        if _digest(row["payload_json"].encode("utf-8")) != witness_sha256:
            raise CreatorConflict("Stored GRAFT witness digest mismatch")
        return {"witness_sha256": witness_sha256, "witness": json.loads(row["payload_json"])}

    def list_graft_witnesses(self, ride_id: int) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """SELECT witness_sha256,created_at FROM house_graft_witnesses
                WHERE ride_id=? ORDER BY created_at DESC LIMIT 40""",
                (ride_id,),
            ).fetchall()
        return [{"witness_sha256": row["witness_sha256"], "created_at": row["created_at"]}
                for row in rows]

    def save_revision(self, draft_id: int | None, expected_revision: int, payload: dict[str, Any]) -> dict[str, Any]:
        if len(payload["body"].encode("utf-8")) > MAX_DRAFT_BYTES:
            raise ValueError("draft exceeds 32 KiB")
        linked_ride_id = payload.get("maxhinal_ride_id")
        if linked_ride_id is not None:
            with self._connect() as db:
                row = db.execute(
                    "SELECT pack_id FROM creator_maxhinal_rides WHERE id=?", (linked_ride_id,)
                ).fetchone()
            if row is None or row["pack_id"] != payload["pack_id"]:
                raise CreatorConflict("Maxhinal ride must be explicitly docked to this source pack")
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
