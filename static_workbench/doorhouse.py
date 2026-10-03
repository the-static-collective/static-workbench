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
                CREATE TABLE IF NOT EXISTS dh_external_witnesses (
                    id TEXT PRIMARY KEY,
                    receipt_id TEXT NOT NULL,
                    kind TEXT NOT NULL,
                    result_sha256 TEXT NOT NULL,
                    snapshot TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    UNIQUE(receipt_id, kind)
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
                    "external_witnesses": [],
                    "laws": self.laws(),
                }
            letters = []
            for row in db.execute(
                "SELECT * FROM dh_letters ORDER BY rowid DESC LIMIT 30"
            ).fetchall():
                item = dict(row)
                if item["opened_at"] is None:
                    item["body"] = None
                letters.append(item)
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
            external_witnesses = []
            for row in db.execute(
                "SELECT * FROM dh_external_witnesses ORDER BY rowid DESC LIMIT 30"
            ).fetchall():
                item = dict(row)
                item["snapshot"] = json.loads(item["snapshot"])
                external_witnesses.append(item)
            return {
                "entered": True,
                "entered_at": world["entered_at"],
                "world_version": world["version"],
                "letters": letters,
                "doors": doors,
                "receipts": receipts,
                "external_witnesses": external_witnesses,
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
            prior = db.execute(
                """SELECT 1 FROM dh_receipts r
                   JOIN dh_doors d ON d.id=r.door_id
                   WHERE d.letter_id=? LIMIT 1""",
                (letter["id"],),
            ).fetchone()
            if prior is not None:
                raise DoorHouseConflict(
                    "that letter already produced a crossing; its other doors are historical proposals"
                )
            if door["crossed_at"] is not None:
                raise DoorHouseConflict("that historical door has already been crossed")
            db.execute("UPDATE dh_doors SET selected_at=NULL WHERE crossed_at IS NULL")
            db.execute("UPDATE dh_doors SET selected_at=? WHERE id=?", (_now(), door_id))
        return self.state()

    def receipt(self, receipt_id):
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM dh_receipts WHERE id=?", (receipt_id,)
            ).fetchone()
        if row is None:
            raise DoorHouseMissing("local crossing receipt not found")
        item = dict(row)
        item["snapshot"] = json.loads(item["snapshot"])
        return item

    def external_witness(self, receipt_id, kind):
        self.receipt(receipt_id)
        with self._db() as db:
            row = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind=?",
                (receipt_id, kind),
            ).fetchone()
        if row is None:
            return None
        item = dict(row)
        item["snapshot"] = json.loads(item["snapshot"])
        return item

    def require_relatte_hold(self, receipt_id):
        witness = self.external_witness(receipt_id, "relatte")
        if witness is None:
            raise DoorHouseConflict("reLATTE HOLD witness is required before GHoT")
        snapshot = witness["snapshot"]
        if (
            snapshot.get("status") != "RECEIVED_THEN_HELD"
            or snapshot.get("semantic_effect") != "none"
        ):
            raise DoorHouseConflict("reLATTE witness is not an intact HOLD")
        return snapshot

    def record_ghot_offer(self, receipt_id, offer):
        self.require_relatte_hold(receipt_id)
        if not isinstance(offer, dict) or offer.get("kind") != "ghot.body-choice.offer":
            raise DoorHouseConflict("invalid GHoT body-choice offer")
        offer_id = offer.get("offer_id")
        if not isinstance(offer_id, str) or not offer_id.startswith("ghot-body-offer-v0:"):
            raise DoorHouseConflict("invalid GHoT body-choice offer id")
        if "selected" in offer:
            raise DoorHouseConflict("GHoT offer selected a body before user assignment")
        candidates = offer.get("candidates")
        if not isinstance(candidates, list):
            raise DoorHouseConflict("GHoT offer has no candidate list")

        kind = "ghot_offer:" + offer_id
        offer_sha = _digest(offer)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind=?",
                (receipt_id, kind),
            ).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (uuid4().hex, receipt_id, kind, offer_sha, _encoded(offer), _now()),
                )
            elif existing["result_sha256"] != offer_sha:
                raise DoorHouseConflict("GHoT offer id collided with different content")
        return self.state()

    def latest_ghot_offer(self, receipt_id):
        self.require_relatte_hold(receipt_id)
        with self._db() as db:
            row = db.execute(
                """SELECT * FROM dh_external_witnesses
                   WHERE receipt_id=? AND kind LIKE 'ghot_offer:%'
                   ORDER BY rowid DESC LIMIT 1""",
                (receipt_id,),
            ).fetchone()
        if row is None:
            raise DoorHouseMissing("no GHoT body offer has been recorded")
        item = dict(row)
        item["snapshot"] = json.loads(item["snapshot"])
        return item

    def record_ghot_execution(self, receipt_id, offer_id, selected_node_id, result):
        receipt = self.receipt(receipt_id)
        self.require_relatte_hold(receipt_id)
        stored_offer = self.latest_ghot_offer(receipt_id)
        offer = stored_offer["snapshot"]
        if offer.get("offer_id") != offer_id:
            raise DoorHouseConflict("GHoT assignment does not use the latest body offer")

        candidate = next(
            (
                item for item in offer.get("candidates", [])
                if item.get("node_id") == selected_node_id
            ),
            None,
        )
        if candidate is None or candidate.get("eligible") is not True:
            raise DoorHouseConflict("selected GHoT body was not eligible in the stored offer")

        if not isinstance(result, dict) or result.get("kind") != "ghot.body-choice.result":
            raise DoorHouseConflict("invalid GHoT body-choice result")
        assignment = result.get("assignment")
        execution = result.get("execution")
        if not isinstance(assignment, dict) or not isinstance(execution, dict):
            raise DoorHouseConflict("incomplete GHoT execution result")
        ghot_receipt = execution.get("receipt")
        if not isinstance(ghot_receipt, dict):
            raise DoorHouseConflict("GHoT execution receipt is missing")
        if assignment.get("offer_id") != offer_id:
            raise DoorHouseConflict("GHoT execution references a different offer")
        if assignment.get("selected_node_id") != selected_node_id:
            raise DoorHouseConflict("GHoT assignment names a different body")
        if assignment.get("selection_source") != "doorhouse-user-explicit":
            raise DoorHouseConflict("GHoT assignment lost explicit selection provenance")
        if ghot_receipt.get("executor_node_id") != selected_node_id:
            raise DoorHouseConflict("GHoT receipt names a different executor body")
        if ghot_receipt.get("status") != "ok":
            raise DoorHouseConflict("GHoT receipt is not successful")
        if assignment.get("capability") != "creative.toaster.witness-sigil":
            raise DoorHouseConflict("GHoT assignment is not the bounded Toaster capability")
        materialized = result.get("workbench_materialized")
        if not isinstance(materialized, dict):
            raise DoorHouseConflict("returned Toaster artifact was not materialized")
        if (
            materialized.get("kind") != "workbench.materialized-toaster-artifact/v0"
            or materialized.get("instrument") != "witness-sigil/v0.1"
        ):
            raise DoorHouseConflict("unexpected returned Toaster artifact")
        if materialized.get("source_digest_sha256") != receipt["snapshot"].get("artifact_sha256"):
            raise DoorHouseConflict("Toaster artifact does not descend from this local artifact")

        snapshot = {
            "schema": "workbench.ghot-execution-witness/v1",
            "local_receipt_id": receipt_id,
            "local_receipt_sha256": receipt["sha256"],
            "offer_id": offer_id,
            "assignment_id": assignment.get("assignment_id"),
            "selected_node_id": selected_node_id,
            "capability": assignment.get("capability"),
            "selection_source": assignment.get("selection_source"),
            "ghot_receipt_id": ghot_receipt.get("receipt_id"),
            "executor_node_id": ghot_receipt.get("executor_node_id"),
            "output_sha256": ghot_receipt.get("output_sha256"),
            "creative_artifact": materialized,
            "status": ghot_receipt.get("status"),
            "laws": [
                "RELATTE HOLD != GHOT ASSIGNMENT",
                "OFFER != ASSIGNMENT",
                "CAPABILITY != AUTHORITY",
                "ASSIGNMENT != EXECUTION",
                "GHOT RECEIPT != LOCAL RECEIPT",
                "TOASTER PROJECTION != KEEP",
                "RETURNED ARTIFACT != NEW AUTHORITY",
            ],
        }
        result_sha = _digest(result)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='ghot_execution'",
                (receipt_id,),
            ).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        uuid4().hex,
                        receipt_id,
                        "ghot_execution",
                        result_sha,
                        _encoded(snapshot),
                        _now(),
                    ),
                )
                self._create_letter(
                    db,
                    "Something came back wearing a new body.",
                    (
                        f"GHoT body {selected_node_id} executed the Haunted Toaster "
                        "witness-sigil instrument. The SVG is a deterministic projection "
                        "of the local artifact digest, not an interpretation or KEEP verdict."
                    ),
                    [
                        (
                            "Look twice",
                            "Prepare the returned artifact as a bounded first-encounter packet without leaking its history.",
                            "Autodisco / First-Listen Radio",
                        ),
                        (
                            "Give it another body",
                            "Offer this artifact to another bounded creative instrument.",
                            "GHoT / Haunted Toaster",
                        ),
                        (
                            "Keep it as a relic",
                            "Preserve the artifact and its receipts without granting them new authority.",
                            "TranchNode / local archive",
                        ),
                    ],
                    parent_crossing_id=ghot_receipt.get("receipt_id"),
                )
            elif existing["result_sha256"] != result_sha:
                raise DoorHouseConflict(
                    "a different GHoT execution is already attached to this receipt"
                )
        return self.state()

    def record_relatte_witness(self, receipt_id, result):
        receipt = self.receipt(receipt_id)
        if not isinstance(result, dict) or result.get("schema") != "relatte.opaque-roundtrip-result/v0":
            raise DoorHouseConflict("invalid reLATTE round-trip result")

        crossing = result.get("crossing")
        received = result.get("receive_receipt")
        disposition = result.get("disposition_receipt")
        if not all(isinstance(item, dict) for item in (crossing, received, disposition)):
            raise DoorHouseConflict("incomplete reLATTE round-trip result")
        crossing_id = crossing.get("crossing_id")
        if not isinstance(crossing_id, str) or crossing_id == "":
            raise DoorHouseConflict("reLATTE crossing id is missing")
        if received.get("crossing_id") != crossing_id or received.get("kind") != "RECEIVED":
            raise DoorHouseConflict("reLATTE RECEIVE receipt mismatch")
        if disposition.get("crossing_id") != crossing_id or disposition.get("kind") != "R3_HOLD":
            raise DoorHouseConflict("reLATTE HOLD receipt mismatch")

        donor_claims = (
            crossing.get("extensions", {})
            .get("organ_adapter", {})
            .get("donor_claims", {})
        )
        if donor_claims.get("local_receipt_id") != receipt_id:
            raise DoorHouseConflict("reLATTE result does not witness this local receipt")
        if donor_claims.get("local_receipt_sha256") != receipt["sha256"]:
            raise DoorHouseConflict("reLATTE result does not preserve local receipt digest")

        result_sha = _digest(result)
        snapshot = {
            "schema": "workbench.relatte-witness/v0",
            "local_receipt_id": receipt_id,
            "local_receipt_sha256": receipt["sha256"],
            "relatte_request_id": result.get("request_id"),
            "crossing_id": crossing_id,
            "transport_id": result.get("transport_frame", {}).get("transport_id"),
            "receive_receipt_id": received.get("receipt_id"),
            "hold_receipt_id": disposition.get("receipt_id"),
            "receiver_world": received.get("world_id"),
            "receiver_state_ref": result.get("receiver_snapshot", {}).get("state_ref"),
            "status": "RECEIVED_THEN_HELD",
            "semantic_effect": "none",
            "laws": [
                "LOCAL CROSSING != reLATTE CROSSING",
                "DELIVERY != ADMISSION",
                "RECEIVED != ADMITTED",
                "HOLD != INTERPRETATION",
                "RETURNED RECEIPT != NEW AUTHORITY",
            ],
        }
        witness_id = uuid4().hex
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='relatte'",
                (receipt_id,),
            ).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        witness_id,
                        receipt_id,
                        "relatte",
                        result_sha,
                        _encoded(snapshot),
                        _now(),
                    ),
                )
            else:
                prior = dict(existing)
                if prior["result_sha256"] != result_sha:
                    raise DoorHouseConflict(
                        "a different reLATTE witness is already attached to this receipt"
                    )
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
                "artifact_sha256": artifact_sha,
                "execution": {
                    "body": "static-workbench/local",
                    "mode": "REAL_LOCAL_TRANSFORM",
                },
                "adapters": {
                    "dogram": "STRUCTURED_PERTURBATION_RECORDED",
                    "relatte": "AVAILABLE_AFTER_LOCAL_CROSSING",
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
