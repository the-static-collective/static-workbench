"""LIFESTREAM-002: explicit, root-scoped, durable HOUSE moment inbox.

No background filesystem scan, OBS control, model call, source upload, or broadcast
authority. A user supplies *both* source and STATIC LIVE manifest paths relative
to a configured root. The whole source is reverified before every admission.
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .config import WorkbenchConfig
from .lifestream_001 import make_return, verify_moment, refuse
from .paths import resolve_under_root

MAX_MANIFEST = 32 * 1024


class MomentInbox:
    def __init__(self, db_path: Path, config: WorkbenchConfig):
        self.path = db_path
        self.config = config
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS moments (
                moment_id TEXT PRIMARY KEY,
                root_id TEXT NOT NULL,
                source_path TEXT NOT NULL,
                manifest_path TEXT NOT NULL,
                manifest_json TEXT NOT NULL,
                imported_at TEXT NOT NULL)""")
            db.execute("""CREATE TABLE IF NOT EXISTS returns (
                return_id TEXT PRIMARY KEY,
                moment_id TEXT NOT NULL REFERENCES moments(moment_id),
                return_json TEXT NOT NULL,
                created_at TEXT NOT NULL)""")

    def _connect(self):
        db = sqlite3.connect(self.path, timeout=3)
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def _file(self, root_id: str, relative: str) -> Path:
        roots = {root.id: root.path for root in self.config.roots}
        refuse(root_id in roots, "unconfigured root")
        refuse(isinstance(relative, str) and 0 < len(relative) <= 512,
               "root-relative file path required")
        path = resolve_under_root(roots[root_id], relative)
        refuse(not path.is_symlink(), "symlink file refused")
        refuse(path.is_file(), "selected file not found")
        return path

    def _load_manifest(self, path: Path) -> dict:
        refuse(path.stat().st_size <= MAX_MANIFEST, "moment manifest exceeds 32 KiB")
        raw = path.read_bytes()
        refuse(len(raw) <= MAX_MANIFEST, "moment manifest exceeds 32 KiB")
        manifest = json.loads(raw.decode("utf-8"))
        refuse(isinstance(manifest, dict), "moment manifest must be an object")
        return manifest

    def import_moment(self, root_id: str, manifest_path: str, source_path: str) -> dict:
        file = self._file(root_id, manifest_path)
        source = self._file(root_id, source_path)
        moment = verify_moment(self._load_manifest(file), source)
        moment_id = moment["momentId"]
        manifest_json = json.dumps(moment, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        now = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            existing = db.execute(
                "SELECT root_id,source_path,manifest_path,manifest_json FROM moments WHERE moment_id=?",
                (moment_id,)
            ).fetchone()
            intended = (root_id, source_path, manifest_path, manifest_json)
            refuse(existing is None or existing == intended,
                   "moment id is already registered with a different source or manifest")
            if existing is None:
                db.execute("""INSERT INTO moments
                    (moment_id,root_id,source_path,manifest_path,manifest_json,imported_at)
                    VALUES (?,?,?,?,?,?)""",
                    (moment_id, root_id, source_path, manifest_path, manifest_json, now))
        return {"momentId": moment_id, "eventId": moment["eventId"],
                "sourceSha256": moment["source"]["sha256"],
                "span": moment["span"], "time": moment["time"],
                "clockWitnesses": moment["clockWitnesses"], "status": "imported_source_verified"}

    def list_moments(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""SELECT moment_id,root_id,source_path,manifest_json,imported_at
                FROM moments ORDER BY imported_at DESC LIMIT 100""").fetchall()
        return [{"momentId": mid, "rootId": root, "sourcePath": source,
                 "importedAt": stamp, "eventId": json.loads(raw)["eventId"],
                 "span": json.loads(raw)["span"],
                 "clockWitnesses": json.loads(raw)["clockWitnesses"],
                 "status": "registered_not_currently_reverified"}
                for mid, root, source, raw, stamp in rows]

    def _stored(self, moment_id: str) -> tuple[dict, Path]:
        with self._connect() as db:
            row = db.execute("SELECT root_id,source_path,manifest_json FROM moments WHERE moment_id=?",
                             (moment_id,)).fetchone()
        refuse(row is not None, "unknown moment")
        root_id, source_path, manifest_json = row
        source = self._file(root_id, source_path)
        manifest = json.loads(manifest_json)
        verify_moment(manifest, source)
        return manifest, source

    def inspect(self, moment_id: str) -> dict:
        manifest, _ = self._stored(moment_id)
        return {"momentId": manifest["momentId"], "eventId": manifest["eventId"],
                "sourceSha256": manifest["source"]["sha256"], "span": manifest["span"],
                "time": manifest["time"], "clockWitnesses": manifest["clockWitnesses"],
                "status": "source_verified_no_effect"}

    def save_return(self, moment_id: str, *, kind: str, text: str,
                    admitted_by: str, reviewed: bool) -> dict:
        refuse(reviewed is True, "explicit human review required")
        refuse(isinstance(text, str), "draft text must be a string")
        manifest, source = self._stored(moment_id)
        now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
        returned = make_return(manifest, source, text.encode("utf-8"), kind, admitted_by, now)
        raw = json.dumps(returned, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
        with self._connect() as db:
            db.execute("""INSERT INTO returns(return_id,moment_id,return_json,created_at)
                VALUES (?,?,?,?)""", (returned["returnId"], moment_id, raw, now))
        return {"returnId": returned["returnId"], "momentId": moment_id,
                "effects": returned["effects"], "status": "reviewed_local_return_saved"}

    def list_returns(self, moment_id: str) -> list[dict]:
        # Do not report a missing or tampered source as a completed, available return.
        self._stored(moment_id)
        with self._connect() as db:
            rows = db.execute("""SELECT return_id,return_json,created_at FROM returns
                WHERE moment_id=? ORDER BY created_at DESC LIMIT 100""",(moment_id,)).fetchall()
        return [{"returnId": rid, "kind": json.loads(raw)["artifact"]["kind"],
                 "createdAt": stamp, "status": "stored_candidate_not_performed"} for rid,raw,stamp in rows]

    def export_return(self, moment_id: str, return_id: str) -> dict:
        manifest, source = self._stored(moment_id)
        with self._connect() as db:
            row = db.execute("SELECT return_json FROM returns WHERE return_id=? AND moment_id=?",
                             (return_id,moment_id)).fetchone()
        refuse(row is not None, "unknown return")
        from .lifestream_001 import hash_object
        returned = json.loads(row[0])
        refuse(returned["momentId"] == manifest["momentId"], "mismatched return ancestry")
        refuse(returned["effects"] == {"broadcast": False, "stage": False, "publish": False},
               "effectful return refused")
        refuse(returned["returnId"] == hash_object({k:v for k,v in returned.items() if k!="returnId"}),
               "return was altered")
        refuse(returned["artifact"]["sha256"] == __import__("hashlib").sha256(
            returned["artifact"]["text"].encode("utf-8")).hexdigest().join(["sha256:",""]),
            "return text digest mismatch")
        return returned
