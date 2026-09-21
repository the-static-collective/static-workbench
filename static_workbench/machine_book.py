"""Book of Machines 001: frozen MADDLOOP folios and non-effectful domino boards.

A folio is a source-linked, human-authored drawing/specimen. Joining folios
tests only declared synthetic ports; neither a folio nor a board runs code.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from .maddloop import LoopConflict, LoopMissing, inspect_passage


class BookMissing(ValueError):
    pass


class BookConflict(ValueError):
    pass


def _now():
    return datetime.now(timezone.utc).isoformat()


def _canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value):
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _text(value, name, max_chars):
    if not isinstance(value, str) or not 1 <= len(value.strip()) <= max_chars:
        raise ValueError(f"{name} must have 1-{max_chars} characters")
    return value.strip()


def _folio_ports(folio):
    layers = folio["layers"]
    return {
        "input": {"class": layers[0]["input_class"], "port": layers[0]["input_port"]},
        "output": {"class": layers[-1]["output_class"], "port": layers[-1]["output_port"]},
    }


def inspect_board(folios):
    """Check the entire concrete route; matching abstract classes is insufficient."""
    gaps = []
    for i, folio in enumerate(folios):
        for obstruction in inspect_passage(folio["layers"])["obstructions"]:
            gaps.append({"kind": "within_folio", "index": i, "folio_id": folio["id"], **obstruction})
    for i in range(len(folios) - 1):
        out_port = _folio_ports(folios[i])["output"]
        in_port = _folio_ports(folios[i + 1])["input"]
        if out_port["class"] != in_port["class"]:
            reason = "abstract_class_gap"
        elif out_port["port"] != in_port["port"]:
            reason = "concrete_lift_gap"
        else:
            continue
        gaps.append({
            "kind": "between_folios", "index": i,
            "from_folio_id": folios[i]["id"], "to_folio_id": folios[i + 1]["id"],
            "reason": reason, "available": out_port, "required": in_port,
        })
    return {
        "status": "synthetic_route_matched" if not gaps else "candidate_with_gaps",
        "gaps": gaps,
        "nonclaim": "Only declared ports have been checked; no project action is authorized or executed.",
    }



GAP_STRATEGIES = frozenset({
    "invent_adapter", "find_existing", "replace_domino",
    "branch_route", "leave_open",
})

class MachineBook:
    def __init__(self, path: Path, loops_path: Path):
        self.path, self.loops_path = Path(path), Path(loops_path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._db() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS folios(
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, purpose TEXT NOT NULL,
                    loop_id TEXT NOT NULL, revision_id TEXT NOT NULL,
                    snapshot_sha256 TEXT NOT NULL, layers_json TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS gap_plans(
                    id TEXT PRIMARY KEY, board_id TEXT NOT NULL,
                    board_digest TEXT NOT NULL, gap_index INTEGER NOT NULL,
                    gap_json TEXT NOT NULL, strategy TEXT NOT NULL,
                    title TEXT NOT NULL, notes TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS boards(
                    id TEXT PRIMARY KEY, title TEXT NOT NULL, folios_json TEXT NOT NULL,
                    result_json TEXT NOT NULL, created_at TEXT NOT NULL
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

    def record_folio(self, title, purpose, loop_id, expected_revision_id):
        title = _text(title, "title", 100)
        purpose = _text(purpose, "purpose", 1200)
        with sqlite3.connect(self.loops_path, timeout=5) as sources:
            sources.row_factory = sqlite3.Row
            source = sources.execute(
                "SELECT head_revision_id FROM loops WHERE id=?", (loop_id,),
            ).fetchone()
            if source is None:
                raise LoopMissing("source loop not found")
            if source["head_revision_id"] != expected_revision_id:
                raise LoopConflict("loop changed since review; reselect the source")
            revision = sources.execute(
                "SELECT snapshot, snapshot_sha256 FROM revisions WHERE id=? AND loop_id=?",
                (expected_revision_id, loop_id),
            ).fetchone()
            if revision is None:
                raise LoopMissing("source revision not found")
            layers = json.loads(revision["snapshot"])
            if not isinstance(layers, list) or not layers:
                raise BookConflict("source revision has no layers")
            if _hash(layers) != revision["snapshot_sha256"]:
                raise BookConflict("source snapshot digest mismatch")
            source_hash = revision["snapshot_sha256"]
        folio_id, created_at = uuid4().hex, _now()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            db.execute(
                "INSERT INTO folios VALUES (?,?,?,?,?,?,?,?)",
                (folio_id, title, purpose, loop_id, expected_revision_id,
                 source_hash, _canonical(layers), created_at),
            )
        return self.folio(folio_id)

    @staticmethod
    def _from_row(row):
        data = dict(row)
        data["layers"] = json.loads(data.pop("layers_json"))
        data["ports"] = _folio_ports(data)
        data["internal_passage"] = inspect_passage(data["layers"])
        data["status"] = "documented_sketch"
        data["nonclaim"] = "Folio is a recorded drawing of a loop revision, not an executable machine."
        return data

    def folio(self, folio_id):
        with self._db() as db:
            row = db.execute("SELECT * FROM folios WHERE id=?", (folio_id,)).fetchone()
        if row is None:
            raise BookMissing("folio not found")
        return self._from_row(row)

    def folios(self):
        with self._db() as db:
            rows = db.execute("SELECT * FROM folios ORDER BY created_at DESC, rowid DESC LIMIT 100").fetchall()
        return [self._from_row(row) for row in rows]

    def compose(self, title, folio_ids):
        title = _text(title, "board title", 100)
        if not isinstance(folio_ids, list) or not 2 <= len(folio_ids) <= 8:
            raise ValueError("a domino board needs 2-8 explicitly ordered folios")
        if any(not isinstance(i, str) or len(i) != 32 for i in folio_ids):
            raise ValueError("invalid folio identifier")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            folios = []
            for folio_id in folio_ids:
                row = db.execute("SELECT * FROM folios WHERE id=?", (folio_id,)).fetchone()
                if row is None:
                    raise BookMissing("folio not found: " + folio_id)
                folios.append(self._from_row(row))
            result = inspect_board(folios)
            board_id, created_at = uuid4().hex, _now()
            db.execute(
                "INSERT INTO boards VALUES (?,?,?,?,?)",
                (board_id, title, _canonical(folios), _canonical(result), created_at),
            )
        return self.board(board_id)

    def board(self, board_id):
        with self._db() as db:
            row = db.execute("SELECT * FROM boards WHERE id=?", (board_id,)).fetchone()
        if row is None:
            raise BookMissing("board not found")
        value = dict(row)
        value["folios"] = json.loads(value.pop("folios_json"))
        value["result"] = json.loads(value.pop("result_json"))
        value["kind"] = "frozen_domino_arrangement"
        return value

    def boards(self):
        with self._db() as db:
            rows = db.execute("SELECT id, title, result_json, created_at FROM boards ORDER BY created_at DESC, rowid DESC LIMIT 50").fetchall()
        return [
            {"id": row["id"], "title": row["title"],
             "status": json.loads(row["result_json"])["status"],
             "created_at": row["created_at"]}
            for row in rows
        ]

    def plan_gap(self, board_id, gap_index, strategy, title, notes):
        """A human choice about one *recorded* gap; no adapter is synthesized."""
        title = _text(title, "plan title", 100)
        notes = _text(notes, "plan notes", 1200)
        if strategy not in GAP_STRATEGIES:
            raise ValueError("choose a supported gap strategy")
        if type(gap_index) is not int or gap_index < 0:
            raise ValueError("gap index must be a nonnegative integer")
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            row = db.execute("SELECT * FROM boards WHERE id=?", (board_id,)).fetchone()
            if row is None:
                raise BookMissing("board not found")
            result = json.loads(row["result_json"])
            gaps = result["gaps"]
            if gap_index >= len(gaps):
                raise BookConflict("this board has no gap at the selected index")
            gap = gaps[gap_index]
            # The original board and all of its gaps remain frozen.
            digest = _hash({
                "folios": json.loads(row["folios_json"]),
                "result": result,
            })
            plan_id, created_at = uuid4().hex, _now()
            db.execute(
                "INSERT INTO gap_plans VALUES (?,?,?,?,?,?,?,?,?)",
                (plan_id, board_id, digest, gap_index, _canonical(gap),
                 strategy, title, notes, created_at),
            )
        return self.gap_plan(plan_id)

    @staticmethod
    def _plan_from_row(row):
        result = dict(row)
        result["gap"] = json.loads(result.pop("gap_json"))
        result["status"] = "human_chosen_design_only"
        result["nonclaim"] = (
            "This is a proposed way through a recorded gap, not a repaired "
            "route, executable adapter, or evidence that a machine exists."
        )
        return result

    def gap_plan(self, plan_id):
        with self._db() as db:
            row = db.execute("SELECT * FROM gap_plans WHERE id=?", (plan_id,)).fetchone()
        if row is None:
            raise BookMissing("gap plan not found")
        return self._plan_from_row(row)

    def gap_plans(self, board_id):
        with self._db() as db:
            row = db.execute("SELECT id FROM boards WHERE id=?", (board_id,)).fetchone()
            if row is None:
                raise BookMissing("board not found")
            plans = db.execute(
                "SELECT * FROM gap_plans WHERE board_id=? "
                "ORDER BY created_at DESC, rowid DESC LIMIT 100",
                (board_id,),
            ).fetchall()
        return [self._plan_from_row(row) for row in plans]
