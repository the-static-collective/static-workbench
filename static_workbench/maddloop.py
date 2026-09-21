"""MADDLOOP-001: Workbench-owned, non-effectful abstract loop sketches.

A replay here means a local encounter with a frozen arrangement, NEVER an
execution of the displayed actions, an audio engine, or a project-native receipt.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


KINDS = frozenset({"text", "action_sketch", "historical_message", "media_reference"})
MAX_LAYERS = 32


class LoopConflict(ValueError):
    pass


class LoopMissing(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


def _id():
    return uuid4().hex


def _json(data):
    return json.dumps(data, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(data):
    return hashlib.sha256(_json(data).encode("utf-8")).hexdigest()


def _checked_layer(data):
    kind = data.get("kind", "text")
    if kind not in KINDS:
        raise ValueError("unsupported loop layer kind")
    label = data.get("label", "")
    body = data.get("body", "")
    if not isinstance(label, str) or not 1 <= len(label.strip()) <= 100:
        raise ValueError("layer label must have 1-100 characters")
    if not isinstance(body, str) or not 1 <= len(body.strip()) <= 2000:
        raise ValueError("layer body must have 1-2000 characters")
    def port(name):
        value = data.get(name, "note")
        if not isinstance(value, str) or not 1 <= len(value) <= 80 or not all(
            c.isalnum() or c in "._:-" for c in value
        ):
            raise ValueError(name + " must be a simple 1-80 character identifier")
        return value
    return {
        "source_id": _id(),
        "kind": kind,
        "label": label.strip(),
        "body": body,
        "input_class": port("input_class"),
        "input_port": port("input_port"),
        "output_class": port("output_class"),
        "output_port": port("output_port"),
        "source_created_at": _now(),
        "source_authority": "human_entered_sketch",
    }


def inspect_passage(layers):
    """A matching abstract class is necessary but not an exact concrete join."""
    obstructions = []
    for index in range(len(layers) - 1):
        left, right = layers[index], layers[index + 1]
        if left["output_class"] != right["input_class"]:
            reason = "abstract_class_gap"
        elif left["output_port"] != right["input_port"]:
            reason = "concrete_lift_gap"
        else:
            continue
        obstructions.append({
            "between_layers": [index, index + 1],
            "reason": reason,
            "available": {"class": left["output_class"], "port": left["output_port"]},
            "required": {"class": right["input_class"], "port": right["input_port"]},
        })
    return {
        "status": "concrete_route_witnessed" if not obstructions else "candidate_only",
        "obstructions": obstructions,
        "nonclaim": "Port matching is a local synthetic check; it does not confer execution authority.",
    }


class MaddloopStore:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS loops (
                    id TEXT PRIMARY KEY, title TEXT NOT NULL,
                    parent_loop_id TEXT, head_revision_id TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS revisions (
                    id TEXT PRIMARY KEY, loop_id TEXT NOT NULL,
                    parent_revision_id TEXT, snapshot TEXT NOT NULL,
                    snapshot_sha256 TEXT NOT NULL, created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS encounters (
                    id TEXT PRIMARY KEY, loop_id TEXT NOT NULL,
                    revision_id TEXT NOT NULL, snapshot_sha256 TEXT NOT NULL,
                    kind TEXT NOT NULL, status TEXT NOT NULL,
                    receipt TEXT NOT NULL, created_at TEXT NOT NULL
                );
            """)

    def _db(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    @staticmethod
    def _revision(db, revision_id):
        row = db.execute("SELECT * FROM revisions WHERE id=?", (revision_id,)).fetchone()
        if row is None:
            raise LoopMissing("loop revision not found")
        return row

    @staticmethod
    def _loop(db, loop_id):
        row = db.execute("SELECT * FROM loops WHERE id=?", (loop_id,)).fetchone()
        if row is None:
            raise LoopMissing("loop not found")
        return row

    def _append_revision(self, db, loop_id, parent_revision_id, layers):
        revision_id = _id()
        stamp = _now()
        snapshot = _json(layers)
        digest = _digest(layers)
        db.execute(
            "INSERT INTO revisions VALUES (?,?,?,?,?,?)",
            (revision_id, loop_id, parent_revision_id, snapshot, digest, stamp),
        )
        return revision_id

    def create(self, title, layer):
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
            raise ValueError("loop title must have 1-100 characters")
        first = _checked_layer(layer)
        loop_id = _id()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            revision_id = self._append_revision(db, loop_id, None, [first])
            db.execute(
                "INSERT INTO loops VALUES (?,?,?,?,?)",
                (loop_id, title.strip(), None, revision_id, _now()),
            )
        return self.get(loop_id)

    def list(self):
        with self._db() as db:
            rows = db.execute(
                "SELECT id, title, parent_loop_id, head_revision_id, created_at "
                "FROM loops ORDER BY created_at DESC, id DESC LIMIT 100"
            ).fetchall()
            return [dict(r) for r in rows]

    def get(self, loop_id):
        with self._db() as db:
            loop = dict(self._loop(db, loop_id))
            revision = self._revision(db, loop["head_revision_id"])
            layers = json.loads(revision["snapshot"])
            revisions = db.execute(
                "SELECT id, parent_revision_id, snapshot_sha256, created_at "
                "FROM revisions WHERE loop_id=? ORDER BY created_at DESC, rowid DESC",
                (loop_id,),
            ).fetchall()
            encounters = db.execute(
                "SELECT id, revision_id, snapshot_sha256, kind, status, receipt, created_at "
                "FROM encounters WHERE loop_id=? ORDER BY created_at DESC, rowid DESC LIMIT 30",
                (loop_id,),
            ).fetchall()
        return {
            **loop, "layers": layers, "snapshot_sha256": revision["snapshot_sha256"],
            "passage": inspect_passage(layers),
            "revisions": [dict(r) for r in revisions],
            "encounters": [{**dict(e), "receipt": json.loads(e["receipt"])} for e in encounters],
        }

    def overdub(self, loop_id, expected_revision_id, layer):
        item = _checked_layer(layer)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            loop = self._loop(db, loop_id)
            if loop["head_revision_id"] != expected_revision_id:
                raise LoopConflict("loop changed since review; reload before overdubbing")
            parent = self._revision(db, expected_revision_id)
            layers = json.loads(parent["snapshot"])
            if len(layers) >= MAX_LAYERS:
                raise LoopConflict("loop has reached its 32-layer limit")
            revision_id = self._append_revision(db, loop_id, expected_revision_id, layers + [item])
            db.execute("UPDATE loops SET head_revision_id=? WHERE id=?", (revision_id, loop_id))
        return self.get(loop_id)

    def branch(self, loop_id, expected_revision_id, title):
        if not isinstance(title, str) or not 1 <= len(title.strip()) <= 100:
            raise ValueError("branch title must have 1-100 characters")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            parent = self._loop(db, loop_id)
            if parent["head_revision_id"] != expected_revision_id:
                raise LoopConflict("loop changed since review; reload before branching")
            snapshot = json.loads(self._revision(db, expected_revision_id)["snapshot"])
            child_id = _id()
            revision_id = self._append_revision(db, child_id, expected_revision_id, snapshot)
            db.execute(
                "INSERT INTO loops VALUES (?,?,?,?,?)",
                (child_id, title.strip(), loop_id, revision_id, _now()),
            )
        return self.get(child_id)

    def encounter(self, loop_id, expected_revision_id):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            loop = self._loop(db, loop_id)
            if loop["head_revision_id"] != expected_revision_id:
                raise LoopConflict("loop changed since review; reload before replay")
            revision = self._revision(db, expected_revision_id)
            layers = json.loads(revision["snapshot"])
            passage = inspect_passage(layers)
            status = ("composable_preview" if not passage["obstructions"]
                      else "blocked_route_preview")
            receipt = {
                "format": "workbench.maddloop-encounter/v0.1",
                "loop_id": loop_id, "revision_id": expected_revision_id,
                "source_ids": [x["source_id"] for x in layers],
                "snapshot_sha256": revision["snapshot_sha256"],
                "passage": passage,
                "nonclaims": [
                    "This encounter is a local read-only preview, not execution.",
                    "It does not imply historical speakers are present.",
                    "It does not produce source-project receipts or permission for external effects.",
                ],
            }
            encounter_id, created_at = _id(), _now()
            db.execute(
                "INSERT INTO encounters VALUES (?,?,?,?,?,?,?,?)",
                (encounter_id, loop_id, expected_revision_id, revision["snapshot_sha256"],
                 "local_preview", status, _json(receipt), created_at),
            )
        return {
            "id": encounter_id, "created_at": created_at, "kind": "local_preview",
            "status": status, "receipt": receipt,
        }
