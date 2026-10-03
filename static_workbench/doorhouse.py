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

    def record_autodisco_first_encounter(self, receipt_id, result):
        receipt = self.receipt(receipt_id)
        ghot = self.external_witness(receipt_id, "ghot_execution")
        if ghot is None:
            raise DoorHouseConflict("GHoT creative execution is required before first encounter")
        creative = ghot["snapshot"].get("creative_artifact")
        if not isinstance(creative, dict):
            raise DoorHouseConflict("GHoT witness has no creative artifact")

        if (
            not isinstance(result, dict)
            or result.get("schema") != "autodisco.first-encounter-result/v0"
            or result.get("status") not in {"packet-only", "responded"}
        ):
            raise DoorHouseConflict("invalid Autodisco first-encounter result")
        packet = result.get("packet")
        if not isinstance(packet, dict):
            raise DoorHouseConflict("Autodisco first-encounter packet is missing")
        packet_id = packet.get("packet_id")
        source = packet.get("source")
        if (
            not isinstance(packet_id, str)
            or not packet_id.startswith("autodisco-first-encounter-v0:")
            or not isinstance(source, dict)
            or source.get("sha256") != creative.get("svg_sha256")
        ):
            raise DoorHouseConflict("Autodisco packet is not bound to the returned SVG")

        packet_snapshot = {
            "schema": "workbench.autodisco-first-encounter-packet/v0",
            "local_receipt_id": receipt_id,
            "local_receipt_sha256": receipt["sha256"],
            "packet_id": packet_id,
            "source": source,
            "listener": packet.get("listener"),
            "prohibitions": packet.get("prohibitions"),
            "status": result.get("status"),
            "laws": [
                "STATION MEMORY != LISTENER MEMORY",
                "PACKET != RESPONSE",
                "SIMULATION != FIRST ENCOUNTER",
            ],
        }
        packet_sha = _digest(packet)

        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing_packet = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='autodisco_packet'",
                (receipt_id,),
            ).fetchone()
            if existing_packet is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        uuid4().hex,
                        receipt_id,
                        "autodisco_packet",
                        packet_sha,
                        _encoded(packet_snapshot),
                        _now(),
                    ),
                )
                if result.get("status") == "packet-only":
                    self._create_letter(
                        db,
                        "The packet reached the booth. The microphone stayed dark.",
                        (
                            "Autodisco prepared an isolated first-encounter packet, "
                            "but no real listener model was available. No simulated "
                            "response was substituted."
                        ),
                        [
                            (
                                "Try a real listener later",
                                "Re-run the same isolated packet when a real listener is available.",
                                "Autodisco / First Encounter",
                            ),
                            (
                                "Inspect the packet",
                                "Read only the bounded packet and its isolation laws.",
                                "Autodisco",
                            ),
                            (
                                "Leave it sealed",
                                "Preserve the unanswered packet without inventing an answer.",
                                "House memory",
                            ),
                        ],
                        parent_crossing_id=packet_id,
                    )
            elif existing_packet["result_sha256"] != packet_sha:
                raise DoorHouseConflict(
                    "a different Autodisco packet is already attached to this artifact"
                )

            if result.get("status") == "responded":
                response = result.get("response")
                response_sha = result.get("response_sha256")
                model_used = result.get("model_used")
                if (
                    not isinstance(response, dict)
                    or not isinstance(response_sha, str)
                    or not isinstance(model_used, str)
                    or not model_used
                ):
                    raise DoorHouseConflict("Autodisco first response is incomplete")
                response_snapshot = {
                    "schema": "workbench.autodisco-first-response/v0",
                    "local_receipt_id": receipt_id,
                    "packet_id": packet_id,
                    "response_sha256": response_sha,
                    "model_used": model_used,
                    "response": response,
                    "laws": [
                        "FIRST RESPONSE PRECEDES DIALOGUE",
                        "OBSERVATION != INTERPRETATION",
                        "FIRST ENCOUNTER != AUTHORITY",
                    ],
                }
                response_result_sha = _digest(response_snapshot)
                existing_response = db.execute(
                    "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='autodisco_first_response'",
                    (receipt_id,),
                ).fetchone()
                if existing_response is None:
                    db.execute(
                        "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                        (
                            uuid4().hex,
                            receipt_id,
                            "autodisco_first_response",
                            response_result_sha,
                            _encoded(response_snapshot),
                            _now(),
                        ),
                    )
                    observations = response.get("observations") or []
                    body_lines = [
                        f"{item.get('mode')} — {item.get('text')}"
                        for item in observations
                        if isinstance(item, dict)
                    ]
                    closing = response.get("closing_line")
                    if isinstance(closing, str) and closing.strip():
                        body_lines.append("CLOSING — " + closing.strip())
                    self._create_letter(
                        db,
                        "Someone looked without knowing us.",
                        "\n\n".join(body_lines),
                        [
                            (
                                "Answer back",
                                "Begin dialogue only after the sealed first response has been preserved.",
                                "Autodisco dialogue",
                            ),
                            (
                                "Follow the lingering intrigue",
                                "Use the first response as a new proposal, not as source authority.",
                                "National Treasure / composition",
                            ),
                            (
                                "Make another thing",
                                "Let what lingered seed a new bounded creative crossing.",
                                "House / GHoT / Haunted Toaster",
                            ),
                        ],
                        parent_crossing_id=response_sha,
                    )
                elif existing_response["result_sha256"] != response_result_sha:
                    raise DoorHouseConflict(
                        "a different first response is already sealed for this packet"
                    )
        return self.state()

    def record_look_twice_pair(self, receipt_id, pair):
        receipt = self.receipt(receipt_id)
        ghot = self.external_witness(receipt_id, "ghot_execution")
        if ghot is None:
            raise DoorHouseConflict("GHoT creative execution is required before LOOK TWICE")
        creative = ghot["snapshot"].get("creative_artifact")
        if not isinstance(creative, dict):
            raise DoorHouseConflict("GHoT witness has no creative artifact")
        if (
            not isinstance(pair, dict)
            or pair.get("schema") != "autodisco.look-twice-pair/v0"
        ):
            raise DoorHouseConflict("invalid LOOK TWICE pair")
        pair_id = pair.get("pair_id")
        packets = pair.get("packets")
        if (
            not isinstance(pair_id, str)
            or not pair_id.startswith("autodisco-look-twice-pair-v0:")
            or not isinstance(packets, list)
            or len(packets) != 2
            or pair.get("source", {}).get("sha256") != creative.get("svg_sha256")
        ):
            raise DoorHouseConflict("LOOK TWICE pair is not bound to the returned SVG")
        listener_ids = {
            packet.get("listener", {}).get("id")
            for packet in packets
            if isinstance(packet, dict)
        }
        if len(listener_ids) != 2 or None in listener_ids:
            raise DoorHouseConflict("LOOK TWICE pair does not contain two distinct listeners")
        snapshot = {
            "schema": "workbench.look-twice-pair/v0",
            "local_receipt_id": receipt_id,
            "local_receipt_sha256": receipt["sha256"],
            "pair_id": pair_id,
            "source_sha256": pair.get("source", {}).get("sha256"),
            "pair": pair,
            "laws": [
                "SAME ARTIFACT != SHARED CONTEXT",
                "PAIR != FIRST RESPONSE",
                "FIRST RESPONSE PRECEDES CROSS-READ",
            ],
        }
        result_sha = _digest(pair)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='look_twice_pair'",
                (receipt_id,),
            ).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        uuid4().hex,
                        receipt_id,
                        "look_twice_pair",
                        result_sha,
                        _encoded(snapshot),
                        _now(),
                    ),
                )
            elif existing["result_sha256"] != result_sha:
                raise DoorHouseConflict(
                    "a different LOOK TWICE pair is already attached to this artifact"
                )
        return self.state()

    def look_twice_pair(self, receipt_id):
        witness = self.external_witness(receipt_id, "look_twice_pair")
        if witness is None:
            raise DoorHouseMissing("LOOK TWICE pair has not been prepared")
        return witness["snapshot"]["pair"]

    def look_twice_first_responses(self, receipt_id):
        self.receipt(receipt_id)
        with self._db() as db:
            rows = db.execute(
                """SELECT * FROM dh_external_witnesses
                   WHERE receipt_id=? AND kind LIKE 'look_twice_first:%'
                   ORDER BY kind""",
                (receipt_id,),
            ).fetchall()
        responses = []
        for row in rows:
            snapshot = json.loads(row["snapshot"])
            sealed = snapshot.get("sealed_response")
            if isinstance(sealed, dict):
                responses.append(sealed)
        return responses

    def record_look_twice_encounters(self, receipt_id, result):
        pair = self.look_twice_pair(receipt_id)
        if (
            not isinstance(result, dict)
            or result.get("schema") != "autodisco.look-twice-encounter-result/v0"
            or result.get("pair_id") != pair.get("pair_id")
        ):
            raise DoorHouseConflict("invalid LOOK TWICE encounter result")
        status = result.get("status")
        responses = result.get("first_responses")
        if status == "packets-only":
            if responses != [] or result.get("model_used") is not None:
                raise DoorHouseConflict("LOOK TWICE packets-only result contains fake responses")
            return self.state()
        if status != "two-first-responses-sealed":
            raise DoorHouseConflict("unexpected LOOK TWICE encounter status")
        if not isinstance(responses, list) or len(responses) != 2:
            raise DoorHouseConflict("LOOK TWICE did not return two first responses")

        pair_packet_ids = {
            packet.get("packet_id")
            for packet in pair.get("packets", [])
            if isinstance(packet, dict)
        }
        seen_packets = set()
        seen_listeners = set()
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            inserted = 0
            for sealed in responses:
                if not isinstance(sealed, dict):
                    raise DoorHouseConflict("LOOK TWICE sealed response is malformed")
                packet_id = sealed.get("packet_id")
                listener = sealed.get("listener")
                listener_id = listener.get("id") if isinstance(listener, dict) else None
                response_id = sealed.get("first_response_id")
                if (
                    sealed.get("schema") != "autodisco.look-twice-first-response/v0"
                    or sealed.get("pair_id") != pair.get("pair_id")
                    or packet_id not in pair_packet_ids
                    or packet_id in seen_packets
                    or not isinstance(listener_id, str)
                    or listener_id in seen_listeners
                    or not isinstance(response_id, str)
                    or not response_id.startswith("autodisco-look-twice-response-v0:")
                ):
                    raise DoorHouseConflict("LOOK TWICE first response binding is invalid")
                seen_packets.add(packet_id)
                seen_listeners.add(listener_id)
                kind = "look_twice_first:" + listener_id
                response_sha = _digest(sealed)
                snapshot = {
                    "schema": "workbench.look-twice-first-response/v0",
                    "local_receipt_id": receipt_id,
                    "pair_id": pair.get("pair_id"),
                    "listener": listener,
                    "packet_id": packet_id,
                    "first_response_id": response_id,
                    "response_sha256": sealed.get("response_sha256"),
                    "model_used": sealed.get("model_used"),
                    "sealed_response": sealed,
                    "laws": [
                        "FIRST RESPONSE PRECEDES CROSS-READ",
                        "SEALED != SHARED",
                        "FIRST RESPONSE IDENTITY IS IMMUTABLE",
                    ],
                }
                existing = db.execute(
                    "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind=?",
                    (receipt_id, kind),
                ).fetchone()
                if existing is None:
                    db.execute(
                        "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                        (
                            uuid4().hex,
                            receipt_id,
                            kind,
                            response_sha,
                            _encoded(snapshot),
                            _now(),
                        ),
                    )
                    inserted += 1
                elif existing["result_sha256"] != response_sha:
                    raise DoorHouseConflict(
                        "a different sealed first response already exists for this listener"
                    )

            total = db.execute(
                """SELECT COUNT(*) AS n FROM dh_external_witnesses
                   WHERE receipt_id=? AND kind LIKE 'look_twice_first:%'""",
                (receipt_id,),
            ).fetchone()["n"]
            if total != 2:
                raise DoorHouseConflict(
                    "LOOK TWICE requires exactly two sealed first responses"
                )
            if inserted:
                existing_letter = db.execute(
                    """SELECT 1 FROM dh_letters
                       WHERE parent_crossing_id=? LIMIT 1""",
                    ("look-twice-firsts:" + pair.get("pair_id"),),
                ).fetchone()
                if existing_letter is None:
                    self._create_letter(
                        db,
                        "Two strangers looked. Neither had seen the other's notes.",
                        (
                            "Static Sam and Juniper now have independently sealed first "
                            "responses to the same artifact. Their first impressions are "
                            "immutable. Cross-reading is finally allowed."
                        ),
                        [
                            (
                                "Let them look twice",
                                "Allow the two sealed first responses to see each other for a short exchange.",
                                "Autodisco / LOOK TWICE",
                            ),
                            (
                                "Read them separately",
                                "Inspect both first responses without composing them.",
                                "House witness",
                            ),
                            (
                                "Leave them unintroduced",
                                "Preserve both first encounters without opening dialogue.",
                                "House memory",
                            ),
                        ],
                        parent_crossing_id="look-twice-firsts:" + pair.get("pair_id"),
                    )
        return self.state()

    def record_look_twice_dialogue(self, receipt_id, result):
        pair = self.look_twice_pair(receipt_id)
        first_responses = self.look_twice_first_responses(receipt_id)
        if len(first_responses) != 2:
            raise DoorHouseConflict(
                "two sealed LOOK TWICE first responses are required before dialogue"
            )
        if (
            not isinstance(result, dict)
            or result.get("schema") != "autodisco.look-twice-dialogue-result/v0"
        ):
            raise DoorHouseConflict("invalid LOOK TWICE dialogue result")
        packet = result.get("dialogue_packet")
        if (
            not isinstance(packet, dict)
            or packet.get("pair_id") != pair.get("pair_id")
            or "content" in packet
            or "artifact" in packet
        ):
            raise DoorHouseConflict("LOOK TWICE dialogue packet violated the temporal gate")
        sealed = packet.get("sealed_first_responses")
        if not isinstance(sealed, list) or len(sealed) != 2:
            raise DoorHouseConflict("LOOK TWICE dialogue packet lacks two sealed responses")

        packet_snapshot = {
            "schema": "workbench.look-twice-dialogue-packet/v0",
            "local_receipt_id": receipt_id,
            "pair_id": pair.get("pair_id"),
            "dialogue_packet_id": packet.get("dialogue_packet_id"),
            "source_sha256": packet.get("source_sha256"),
            "first_response_ids": [
                item.get("first_response_id")
                for item in sealed
                if isinstance(item, dict)
            ],
            "dialogue_packet": packet,
            "status": result.get("status"),
            "laws": [
                "TWO SEALED FIRST RESPONSES PRECEDE DIALOGUE",
                "ORIGINAL ARTIFACT IS NOT REOPENED",
                "PACKET != EXCHANGE",
            ],
        }
        packet_sha = _digest(packet)
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            existing_packet = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='look_twice_dialogue_packet'",
                (receipt_id,),
            ).fetchone()
            if existing_packet is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        uuid4().hex,
                        receipt_id,
                        "look_twice_dialogue_packet",
                        packet_sha,
                        _encoded(packet_snapshot),
                        _now(),
                    ),
                )
            elif existing_packet["result_sha256"] != packet_sha:
                raise DoorHouseConflict(
                    "a different LOOK TWICE dialogue packet is already attached"
                )

            if result.get("status") == "dialogue-packet-only":
                if result.get("dialogue") is not None or result.get("model_used") is not None:
                    raise DoorHouseConflict(
                        "LOOK TWICE dialogue-packet-only result contains fake dialogue"
                    )
                return self.state()

            if result.get("status") != "dialogue-sealed":
                raise DoorHouseConflict("unexpected LOOK TWICE dialogue status")
            dialogue = result.get("dialogue")
            dialogue_id = result.get("dialogue_id")
            if not isinstance(dialogue, dict) or not isinstance(dialogue_id, str):
                raise DoorHouseConflict("LOOK TWICE sealed dialogue is incomplete")
            if (
                dialogue.get("lingering_intrigue") is not True
                and dialogue.get("door_seed") is not None
            ):
                raise DoorHouseConflict("LOOK TWICE door seed lacks lingering intrigue")
            snapshot = {
                "schema": "workbench.look-twice-dialogue/v0",
                "local_receipt_id": receipt_id,
                "pair_id": pair.get("pair_id"),
                "dialogue_id": dialogue_id,
                "dialogue_sha256": result.get("dialogue_sha256"),
                "model_used": result.get("model_used"),
                "dialogue": dialogue,
                "laws": [
                    "DIALOGUE != RETROACTIVE FIRST IMPRESSION",
                    "LINGERING INTRIGUE != SOURCE TRUTH",
                    "DOOR SEED != CROSSING",
                ],
            }
            result_sha = _digest(result)
            existing = db.execute(
                "SELECT * FROM dh_external_witnesses WHERE receipt_id=? AND kind='look_twice_dialogue'",
                (receipt_id,),
            ).fetchone()
            if existing is None:
                db.execute(
                    "INSERT INTO dh_external_witnesses VALUES (?,?,?,?,?,?)",
                    (
                        uuid4().hex,
                        receipt_id,
                        "look_twice_dialogue",
                        result_sha,
                        _encoded(snapshot),
                        _now(),
                    ),
                )
                if dialogue.get("lingering_intrigue") is True:
                    door_seed = str(dialogue.get("door_seed") or "").strip()
                    intrigue = str(dialogue.get("intrigue_statement") or "").strip()
                    body = (
                        "The first responses remained sealed. Only afterward did "
                        "Static Sam and Juniper see each other's notes."
                    )
                    if intrigue:
                        body += "\n\nLINGERING — " + intrigue
                    if door_seed:
                        body += "\n\nDOOR SEED — " + door_seed
                    self._create_letter(
                        db,
                        "They looked twice. Something was still pulling.",
                        body,
                        [
                            (
                                door_seed or "Follow what still pulls",
                                "Treat the lingering intrigue as a proposal for a new bounded crossing.",
                                "House composition",
                            ),
                            (
                                "Carry it into sound",
                                "Translate the proven temporal-isolation protocol onto a bounded audio window.",
                                "Autodisco / First-Listen Radio",
                            ),
                            (
                                "Leave the exchange sealed",
                                "Preserve the dialogue without promoting its interpretation to source truth.",
                                "House memory",
                            ),
                        ],
                        parent_crossing_id=dialogue_id,
                    )
            elif existing["result_sha256"] != result_sha:
                raise DoorHouseConflict(
                    "a different LOOK TWICE dialogue is already sealed"
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
