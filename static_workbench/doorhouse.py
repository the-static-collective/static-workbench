"""HOUSE-REMEMBERS-DOORS-001: a local playable crossing loop.

This module deliberately implements only the Workbench-local truth floor.
External organs are named as adapter doors, never impersonated.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


class DoorHouseConflict(ValueError):
    pass


class DoorHouseMissing(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _encoded(value) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value) -> str:
    return hashlib.sha256(_encoded(value).encode("utf-8")).hexdigest()


class DoorHouse:
    """Single-user local world: sealed letter -> selection -> crossing -> receipt."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS dh_world (
                    singleton INTEGER PRIMARY KEY CHECK(singleton=1),
                    entered_at TEXT NOT NULL,
                    version INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS dh_letters (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    body TEXT NOT NULL,
                    parent_crossing_id TEXT,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    opened_at TEXT
                );
                CREATE TABLE IF NOT EXISTS dh_doors (
                    id TEXT PRIMARY KEY,
                    letter_id TEXT NOT NULL,
                    label TEXT NOT NULL,
                    perturbation TEXT NOT NULL,
                    adapter_hint TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    selected_at TEXT,
                    crossed_at TEXT
                );
                CREATE TABLE IF NOT EXISTS dh_receipts (
                    id TEXT PRIMARY KEY,
                    door_id TEXT NOT NULL,
                    world_before INTEGER NOT NULL,
                    world_after INTEGER NOT NULL,
                    snapshot TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
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
    def _world(db):
        return db.execute("SELECT * FROM dh_world WHERE singleton=1").fetchone()

    @classmethod
    def _require_world(cls, db):
        row = cls._world(db)
        if row is None:
            raise DoorHouseConflict("Enter the House before touching its letters.")
        return row

    @staticmethod
    def _letter(db, letter_id):
        row = db.execute("SELECT * FROM dh_letters WHERE id=?", (letter_id,)).fetchone()
        if row is None:
            raise DoorHouseMissing("letter not found")
        return row

    @staticmethod
    def _door(db, door_id):
        row = db.execute("SELECT * FROM dh_doors WHERE id=?", (door_id,)).fetchone()
        if row is None:
            raise DoorHouseMissing("door not found")
        return row

    @staticmethod
    def _create_letter(db, title, body, doors, parent_crossing_id=None):
        letter_id = uuid4().hex
        created_at = _now()
        letter_snapshot = {
            "title": title, "body": body, "parent_crossing_id": parent_crossing_id,
        }
        letter_sha = _digest({"kind": "sealed_letter", **letter_snapshot})
        db.execute(
            "INSERT INTO dh_letters VALUES (?,?,?,?,?,?,NULL)",
            (letter_id, title, body, parent_crossing_id, letter_sha, created_at),
        )
        for label, perturbation, adapter_hint in doors:
            door_id = uuid4().hex
            door_snapshot = {
                "letter_id": letter_id,
                "label": label,
                "perturbation": perturbation,
                "adapter_hint": adapter_hint,
            }
            db.execute(
                "INSERT INTO dh_doors VALUES (?,?,?,?,?,?,?,NULL,NULL)",
                (door_id, letter_id, label, perturbation, adapter_hint,
                 _digest({"kind": "proposed_door", **door_snapshot}), created_at),
            )
        return letter_id

    def enter(self):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            if self._world(db) is None:
                db.execute("INSERT INTO dh_world VALUES (1,?,0)", (_now(),))
                self._create_letter(
                    db,
                    "A letter is waiting on the table.",
                    "The House remembers what happened, but it does not decide what happens next. "
                    "Open this letter, inspect the doors, and choose one crossing.",
                    [
                        ("Make one thing",
                         "Transform this letter into one bounded local artifact.",
                         "Haunted Toaster / local renderer"),
                        ("Measure one change",
                         "Keep the carrier fixed and vary one declared condition.",
                         "Dogram"),
                        ("Carry it forward",
                         "Package the chosen intent so another organ could receive it without inheriting authority.",
                         "reLATTE"),
                    ],
                )
        return self.state()

    def state(self):
        with self._db() as db:
            world = self._world(db)
            if world is None:
                return {
                    "entered": False,
                    "world_version": None,
                    "letters": [], "doors": [], "receipts": [],
                    "laws": self.laws(),
                }
            letters = [dict(r) for r in db.execute(
                "SELECT * FROM dh_letters ORDER BY rowid DESC LIMIT 30"
            ).fetchall()]
            doors = [dict(r) for r in db.execute(
                "SELECT * FROM dh_doors ORDER BY rowid DESC LIMIT 100"
            ).fetchall()]
            receipts = []
            for row in db.execute(
                "SELECT * FROM dh_receipts ORDER BY rowid DESC LIMIT 30"
            ).fetchall():
                item = dict(row)
                item["snapshot"] = json.loads(item["snapshot"])
                receipts.append(item)
            return {
                "entered": True,
                "entered_at": world["entered_at"],
                "world_version": world["version"],
                "letters": letters,
                "doors": doors,
                "receipts": receipts,
                "laws": self.laws(),
            }

    @staticmethod
    def laws():
        return [
            "PROPOSAL != SELECTION",
            "SELECTION != CROSSING",
            "DOOR != OCCURRENCE",
            "LOCAL RECEIPT != DONOR RECEIPT",
            "ADAPTER STUB != INTEGRATION",
            "MEMORY != AUTHORITY",
        ]

    def open_letter(self, letter_id):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            self._require_world(db)
            letter = self._letter(db, letter_id)
            if letter["opened_at"] is None:
                db.execute("UPDATE dh_letters SET opened_at=? WHERE id=?", (_now(), letter_id))
        return self.state()

    def select(self, door_id, expected_world_version):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            world = self._require_world(db)
            if world["version"] != expected_world_version:
                raise DoorHouseConflict("world changed since this view; inspect it again")
            door = self._door(db, door_id)
            letter = self._letter(db, door["letter_id"])
            if letter["opened_at"] is None:
                raise DoorHouseConflict("a sealed letter cannot select a door")
            if door["crossed_at"] is not None:
                raise DoorHouseConflict("that historical door has already been crossed")
            db.execute("UPDATE dh_doors SET selected_at=NULL WHERE crossed_at IS NULL")
            db.execute("UPDATE dh_doors SET selected_at=? WHERE id=?", (_now(), door_id))
        return self.state()

    def cross(self, door_id, expected_world_version):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            world = self._require_world(db)
            if world["version"] != expected_world_version:
                raise DoorHouseConflict("world changed since selection; inspect it again")
            door = self._door(db, door_id)
            letter = self._letter(db, door["letter_id"])
            if letter["opened_at"] is None:
                raise DoorHouseConflict("the source letter is still sealed")
            if door["selected_at"] is None:
                raise DoorHouseConflict("selection is required before crossing")
            if door["crossed_at"] is not None:
                raise DoorHouseConflict("that door has already become history")

            before = int(world["version"])
            after = before + 1
            envelope = {
                "kind": "workbench.crossing-envelope/v0",
                "source": {"letter_id": letter["id"], "sha256": letter["sha256"]},
                "proposal": {"door_id": door["id"], "sha256": door["sha256"]},
                "perturbation": door["perturbation"],
                "authority": "local-human-selection",
            }
            envelope_sha = _digest(envelope)
            artifact = {
                "kind": "workbench.local-artifact/v0",
                "title": f"World {after}: {door['label']}",
                "body": (
                    f"The House performed one bounded local transformation: {door['perturbation']} "
                    "No external organ was invoked."
                ),
                "source_envelope_sha256": envelope_sha,
            }
            artifact_sha = _digest(artifact)
            receipt_id = uuid4().hex
            snapshot = {
                "envelope": envelope,
                "artifact": artifact,
                "execution": {
                    "body": "static-workbench/local",
                    "mode": "REAL_LOCAL_TRANSFORM",
                },
                "adapters": {
                    "dogram": "STRUCTURED_PERTURBATION_RECORDED",
                    "relatte": "STUB_NOT_CONNECTED",
                    "ghot": "LOCAL_BODY_ONLY_NOT_GHOT_ASSIGNMENT",
                    "tranchnode": "LOCAL_WITNESS_ONLY",
                    "autodisco": "STUB_NOT_CONNECTED",
                    "haunted_toaster": "STUB_NOT_CONNECTED",
                    "love": "LETTER_AND_DOOR_GRAMMAR_ONLY",
                },
                "world": {"before": before, "after": after},
            }
            receipt_sha = _digest({"kind": "agency_receipt", "snapshot": snapshot})
            db.execute(
                "INSERT INTO dh_receipts VALUES (?,?,?,?,?,?,?)",
                (receipt_id, door_id, before, after, _encoded(snapshot), receipt_sha, _now()),
            )
            db.execute("UPDATE dh_doors SET crossed_at=? WHERE id=?", (_now(), door_id))
            db.execute("UPDATE dh_world SET version=? WHERE singleton=1", (after,))
            self._create_letter(
                db,
                f"The room changed. World {after} is now behind you.",
                f"You crossed “{door['label']}”. The receipt remembers the path; it does not choose the next one.",
                [
                    ("Return with one thing changed",
                     "Repeat the previous pattern with exactly one declared change.",
                     "Dogram"),
                    ("Give the artifact a body",
                     "Offer the local artifact to a renderer without assuming admission.",
                     "Haunted Toaster"),
                    ("Let a stranger hear it first",
                     "Prepare a bounded first-listen packet with no hidden history.",
                     "Autodisco / First-Listen Radio"),
                ],
                parent_crossing_id=receipt_id,
            )
        return self.state()
