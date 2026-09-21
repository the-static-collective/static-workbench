"""STATIC-ARG-002 — local fictional rooms projected from one frozen World.

A visit is an append-only Workbench-owned gameplay trace, not evidence of
project execution, real-world occurrence, or permission to cross another system.
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import uuid4

from .first_door import FirstDoor, ArgConflict, _digest, _now


ROOMS = {
    "threshold": {
        "title": "The Threshold",
        "subtitle": "The rule carved into the entry",
        "description": "The place where this World began. One inscription gives it a way to be played.",
        "neighbors": ("workshop", "garden", "archive"),
        "object_id": "rule",
        "object_title": "The Entry Inscription",
        "object_hint": "Inspect the rule you gave this World.",
        "source_type": "world",
    },
    "workshop": {
        "title": "The Workshop",
        "subtitle": "The machine behind the wall",
        "description": "Two earlier Seeds are held together here without losing their separate origins.",
        "neighbors": ("threshold",),
        "object_id": "machine",
        "object_title": "The Paired Machine",
        "object_hint": "Inspect the composition that brought the first two Seeds together.",
        "source_type": "machine",
    },
    "garden": {
        "title": "The Seed Garden",
        "subtitle": "The living source",
        "description": "A third Seed was kept apart so that another possibility could take root.",
        "neighbors": ("threshold",),
        "object_id": "seed",
        "object_title": "The Unspent Seed",
        "object_hint": "Inspect the fresh Seed that made this World possible.",
        "source_type": "seed",
    },
    "archive": {
        "title": "The Return Archive",
        "subtitle": "A record of the three things you found",
        "description": "The archive opens after you encounter the rule, machine, and fresh Seed.",
        "neighbors": ("threshold",),
        "object_id": "chronicle",
        "object_title": "The World Chronicle",
        "object_hint": "Examine what these three sources made possible together.",
        "source_type": "world",
    },
}
REQUIRED = frozenset({"rule", "machine", "seed"})


class WorldEntry(FirstDoor):
    """One local participant, persistent room location, repeatable observation."""

    def __init__(self, path: Path):
        super().__init__(path)
        with self._db() as db:
            db.execute("""
                CREATE TABLE IF NOT EXISTS arg_world_moves (
                    id TEXT PRIMARY KEY,
                    world_id TEXT NOT NULL,
                    world_sha256 TEXT NOT NULL,
                    action TEXT NOT NULL,
                    room_id TEXT NOT NULL,
                    object_id TEXT,
                    source_id TEXT,
                    source_sha256 TEXT,
                    created_at TEXT NOT NULL
                )
            """)
            db.execute(
                "CREATE INDEX IF NOT EXISTS arg_world_moves_order "
                "ON arg_world_moves (world_id, created_at)"
            )

    @staticmethod
    def _verified(db, reference, kind):
        item = WorldEntry._artifact(db, reference["id"], kind)
        actual = _digest({"kind": kind, "snapshot": item["snapshot"]})
        if item["sha256"] != reference["sha256"] or actual != item["sha256"]:
            raise ArgConflict("World source lineage changed; local exploration refused")
        return item

    @classmethod
    def _sources(cls, db, world_id):
        world = cls._artifact(db, world_id, "world")
        actual = _digest({"kind": "world", "snapshot": world["snapshot"]})
        if world["sha256"] != actual:
            raise ArgConflict("World snapshot digest mismatch")
        machine = cls._verified(db, world["snapshot"]["inputs"][0], "machine")
        seed = cls._verified(db, world["snapshot"]["inputs"][1], "seed")
        first = cls._verified(db, machine["snapshot"]["inputs"][0], "seed")
        second = cls._verified(db, machine["snapshot"]["inputs"][1], "seed")
        return world, machine, seed, first, second

    @staticmethod
    def _moves(db, world_id):
        return [dict(row) for row in db.execute(
            "SELECT * FROM arg_world_moves WHERE world_id=? ORDER BY rowid ASC",
            (world_id,),
        ).fetchall()]

    @classmethod
    def _project(cls, db, world_id):
        cls._require_entry(db)
        world, machine, seed, first, second = cls._sources(db, world_id)
        moves = cls._moves(db, world_id)
        room_id = "threshold"
        visited = {"threshold"}
        examined = set()
        for move in moves:
            if move["action"] == "travel":
                room_id = move["room_id"]
                visited.add(room_id)
            elif move["action"] == "examine":
                examined.add(move["object_id"])
        unlocked = REQUIRED.issubset(examined)
        sources = {
            "rule": (world, world["snapshot"]["play_rule"]),
            "machine": (machine, machine["snapshot"]["prompt"]),
            "seed": (seed, seed["snapshot"]["text"]),
            "chronicle": (world, "This World joins " + first["snapshot"]["title"]
                          + " and " + second["snapshot"]["title"] + " through "
                          + machine["snapshot"]["title"] + ", then makes room for "
                          + seed["snapshot"]["title"] + ". Its human-authored rule is: "
                          + world["snapshot"]["play_rule"]),
        }
        rooms = []
        for key, spec in ROOMS.items():
            source, revelation = sources[spec["object_id"]]
            rooms.append({
                "id": key,
                "title": spec["title"],
                "subtitle": spec["subtitle"],
                "description": spec["description"],
                "neighbors": [n for n in spec["neighbors"]
                              if n != "archive" or unlocked],
                "locked": key == "archive" and not unlocked,
                "visited": key in visited,
                "object": {
                    "id": spec["object_id"],
                    "title": spec["object_title"],
                    "hint": spec["object_hint"],
                    "discovered": spec["object_id"] in examined,
                    "revelation": revelation if spec["object_id"] in examined else None,
                    "source": {"id": source["id"], "sha256": source["sha256"],
                               "kind": source["kind"]},
                },
            })
        return {
            "world": {"id": world["id"], "sha256": world["sha256"],
                      "title": world["snapshot"]["title"]},
            "room_id": room_id,
            "rooms": rooms,
            "archive_unlocked": unlocked,
            "discoveries": [object_id for object_id in ("rule", "machine", "seed", "chronicle")
                            if object_id in examined],
            "history": list(reversed(moves[-30:])),
            "nonclaim": "Local fictional exploration is not a real-world witness or project execution.",
        }

    def play(self, world_id):
        with self._db() as db:
            return self._project(db, world_id)

    def act(self, world_id, action, expected_room, target):
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            state = self._project(db, world_id)
            if expected_room != state["room_id"]:
                raise ArgConflict("Room changed since preview; reload before continuing")
            current = next(room for room in state["rooms"] if room["id"] == expected_room)
            if action == "travel":
                if target not in current["neighbors"] or target not in ROOMS:
                    raise ArgConflict("No accessible doorway between those rooms")
                room_id, object_id, source = target, None, None
            elif action == "examine":
                if target != current["object"]["id"]:
                    raise ArgConflict("That object is not in the current room")
                room_id, object_id = expected_room, target
                source = current["object"]["source"]
            else:
                raise ArgConflict("Unknown local world operation")
            event = {
                "id": uuid4().hex,
                "world_id": world_id,
                "world_sha256": state["world"]["sha256"],
                "action": action,
                "room_id": room_id,
                "object_id": object_id,
                "source_id": source["id"] if source else None,
                "source_sha256": source["sha256"] if source else None,
                "created_at": _now(),
            }
            db.execute(
                "INSERT INTO arg_world_moves "
                "(id,world_id,world_sha256,action,room_id,object_id,source_id,source_sha256,created_at) "
                "VALUES (?,?,?,?,?,?,?,?,?)",
                tuple(event.values()),
            )
            return self._project(db, world_id)
