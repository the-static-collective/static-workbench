"""STATIC-ARG-001: opt-in, local-only composition game; no project execution.

This is a Workbench-owned playable sketch, not a Full Measure/LOADOUT receipt,
a shared player account, or an automatic source of project authority.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class ArgConflict(ValueError):
    """A proposed composition is not supported by current local game state."""


class ArgMissing(ValueError):
    """An exact referenced local game artifact does not exist."""


def _encoded(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value):
    return hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _label(text, maximum=100):
    if not isinstance(text, str) or not 1 <= len(text.strip()) <= maximum:
        raise ArgConflict("text must contain 1 to " + str(maximum) + " characters")
    return text.strip()


class FirstDoor:
    """Single-local-user append-only artifact and encounter shelf."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS arg_entry (
                    singleton INTEGER PRIMARY KEY CHECK (singleton = 1),
                    entered_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS arg_artifacts (
                    id TEXT PRIMARY KEY,
                    kind TEXT NOT NULL,
                    snapshot TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS arg_encounters (
                    id TEXT PRIMARY KEY,
                    source_id TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL,
                    door TEXT NOT NULL,
                    destination TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
            """)

    @contextmanager
    def _db(self):
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        try:
            yield db
            db.commit()
        except BaseException:
            db.rollback()
            raise
        finally:
            db.close()

    @staticmethod
    def _entered(db):
        return db.execute("SELECT 1 FROM arg_entry WHERE singleton=1").fetchone() is not None

    @classmethod
    def _require_entry(cls, db):
        if not cls._entered(db):
            raise ArgConflict("Choose Enter the House before creating game artifacts.")

    @staticmethod
    def _artifact(db, artifact_id, kind=None):
        row = db.execute("SELECT * FROM arg_artifacts WHERE id=?", (artifact_id,)).fetchone()
        if row is None:
            raise ArgMissing("local ARG artifact not found")
        record = {**dict(row), "snapshot": json.loads(row["snapshot"])}
        if kind is not None and record["kind"] != kind:
            raise ArgConflict("expected a " + kind + " artifact")
        return record

    @staticmethod
    def _save(db, kind, snapshot):
        # A frozen snapshot carries exact input ids AND their recorded digests.
        artifact_id, created_at = uuid4().hex, _now()
        digest = _digest({"kind": kind, "snapshot": snapshot})
        db.execute(
            "INSERT INTO arg_artifacts VALUES (?,?,?,?,?)",
            (artifact_id, kind, _encoded(snapshot), digest, created_at),
        )
        return {"id": artifact_id, "kind": kind, "snapshot": snapshot,
                "sha256": digest, "created_at": created_at}

    def enter(self):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute("INSERT OR IGNORE INTO arg_entry VALUES (1,?)", (_now(),))
        return self.state()

    def state(self):
        with self._db() as db:
            enrolled = self._entered(db)
            rows = db.execute(
                "SELECT * FROM arg_artifacts ORDER BY rowid DESC LIMIT 100"
            ).fetchall() if enrolled else []
            encounters = db.execute(
                "SELECT * FROM arg_encounters ORDER BY rowid DESC LIMIT 30"
            ).fetchall() if enrolled else []
        return {
            "enrolled": enrolled,
            "artifacts": [{**dict(r), "snapshot": json.loads(r["snapshot"])} for r in rows],
            "encounters": [dict(r) for r in encounters],
            "limits": {"scope": "local_single_user", "max_visible_artifacts": 100},
            "nonclaims": [
                "Game composition is not project execution or a project-native receipt.",
                "A discovered door never grants access to another project's state.",
                "No AI generation, automatic publishing, shared identity or real-world rewards.",
            ],
        }

    def seed(self, title, text):
        snapshot = {
            "title": _label(title), "text": _label(text, 1200),
            "source": {"class": "human_entered", "scope": "static_arg_local"},
        }
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._require_entry(db)
            result = self._save(db, "seed", snapshot)
        return result

    def machine(self, title, first_id, second_id):
        if first_id == second_id:
            raise ArgConflict("a machine needs two distinct Seeds")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._require_entry(db)
            first = self._artifact(db, first_id, "seed")
            second = self._artifact(db, second_id, "seed")
            snapshot = {
                "title": _label(title),
                "inputs": [
                    {"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]}
                    for item in (first, second)
                ],
                "recipe": "paired_seed_prompt",
                "prompt": first["snapshot"]["text"] + "\n--- COMPOSE WITH ---\n" + second["snapshot"]["text"],
                "status": "human_authored_game_sketch",
            }
            result = self._save(db, "machine", snapshot)
        return result

    def world(self, title, machine_id, seed_id, rule):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._require_entry(db)
            machine = self._artifact(db, machine_id, "machine")
            seed = self._artifact(db, seed_id, "seed")
            if seed_id in [item["id"] for item in machine["snapshot"]["inputs"]]:
                raise ArgConflict("the world needs a fresh Seed beyond its Machine inputs")
            snapshot = {
                "title": _label(title),
                "inputs": [
                    {"id": item["id"], "kind": item["kind"], "sha256": item["sha256"]}
                    for item in (machine, seed)
                ],
                "play_rule": _label(rule, 1200),
                "status": "local_fictional_world_sketch",
                "doors": [
                    {"id": "house", "destination": "/"},
                    {"id": "maddloop", "destination": "/maddloop"},
                    {"id": "machines", "destination": "/machines"},
                ],
            }
            result = self._save(db, "world", snapshot)
        return result

    def cross(self, world_id, door):
        destinations = {"house": "/", "maddloop": "/maddloop", "machines": "/machines"}
        if door not in destinations:
            raise ArgConflict("unknown fixed local doorway")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._require_entry(db)
            world = self._artifact(db, world_id, "world")
            event = {
                "id": uuid4().hex, "source_id": world["id"],
                "source_sha256": world["sha256"], "door": door,
                "destination": destinations[door], "created_at": _now(),
            }
            db.execute(
                "INSERT INTO arg_encounters VALUES (?,?,?,?,?,?)",
                tuple(event.values()),
            )
        return {**event, "nonclaim": "This local navigation records intent, not project admission or execution."}
