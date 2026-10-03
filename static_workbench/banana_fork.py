"""BANANA-ELF-FORK-001: sealed independent returns from one signed consequence.

One exact co-delight field is frozen into 2-6 named booths. Each booth can return
without seeing any other booth's content. Only after every booth has submitted are
the returns revealed together. No winner, score, vote, or consensus is computed.

TAKE descendants then form an unranked pairwise relation field. A relation door can
be returned through the ordinary Field Return machinery and therefore re-enter the
existing explicit reseed metabolism without gaining any shortcut authority.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import secrets
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .field_return import _verified_field_state, compose_field_return


_FACET_ORDER = ("delightfuler", "helpfuler", "curiouser")
_ALLOWED_DISPOSITIONS = frozenset({"take", "hold", "pass"})


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _door(body: dict[str, Any]) -> dict[str, Any]:
    return {
        **body,
        "door_id": "field-door-v0:" + _digest(body),
    }


def _field(body: dict[str, Any]) -> dict[str, Any]:
    return {
        **body,
        "field_state_id": "field-station-v0:" + _digest(body),
    }


def _validated_fork_source(field_state: dict) -> tuple[list[dict], dict, dict]:
    _verified_field_state(field_state)
    delight = [
        json.loads(_canonical(door))
        for door in field_state.get("nearby_doors", [])
        if door.get("lane") == "delight"
    ]
    by_facet = {
        str(door.get("target", {}).get("facet") or ""): door
        for door in delight
    }
    if set(by_facet) != set(_FACET_ORDER):
        raise ValueError(
            "Banana-Elf fork requires exactly delightfuler/helpfuler/curiouser"
        )

    ordered = [by_facet[facet] for facet in _FACET_ORDER]
    consequences: list[dict] = []
    for door in ordered:
        target = door.get("target") or {}
        evidence = door.get("evidence") or []
        if (
            door.get("effect") != "none"
            or target.get("orientation") != "co-delight"
            or target.get("grounded_in") != "signed-receiver-consequence"
            or target.get("novelty") != "proposal-only"
            or not evidence
            or not isinstance(evidence[0], dict)
            or not evidence[0].get("signed_receipt_id")
        ):
            raise ValueError("Banana-Elf door is not grounded in signed consequence")
        consequences.append(evidence[0])

    canonical_consequence = _canonical(consequences[0])
    if any(_canonical(item) != canonical_consequence for item in consequences[1:]):
        raise ValueError("Banana-Elf doors do not share one exact consequence")

    silence = next(
        (
            json.loads(_canonical(door))
            for door in field_state.get("nearby_doors", [])
            if door.get("lane") == "silence"
        ),
        None,
    )
    if silence is None or silence.get("effect") != "none":
        raise ValueError("Banana-Elf fork requires constitutional silence")

    return ordered, silence, consequences[0]


def _normalize_participants(values: list[str]) -> list[str]:
    labels = [str(value).strip() for value in values]
    if not 2 <= len(labels) <= 6:
        raise ValueError("Banana-Elf fork requires 2-6 returners")
    if any(not label for label in labels):
        raise ValueError("Banana-Elf returner labels cannot be blank")
    if any(len(label) > 80 for label in labels):
        raise ValueError("Banana-Elf returner label is too long")
    folded = [label.casefold() for label in labels]
    if len(set(folded)) != len(folded):
        raise ValueError("Banana-Elf returner labels must be unique")
    return labels


class BananaForkStore:
    """Durable Workbench-local sealed fork room."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._initialize()

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path)
        connection.row_factory = sqlite3.Row
        return connection

    def _initialize(self) -> None:
        with self._connect() as db:
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS banana_forks (
                    fork_id TEXT PRIMARY KEY,
                    created_at TEXT NOT NULL,
                    source_field_json TEXT NOT NULL,
                    fork_json TEXT NOT NULL
                )
                """
            )
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS banana_fork_booths (
                    fork_id TEXT NOT NULL,
                    booth_id TEXT NOT NULL,
                    ordinal INTEGER NOT NULL,
                    label TEXT NOT NULL,
                    booth_token TEXT NOT NULL,
                    submitted_at TEXT,
                    response_json TEXT,
                    PRIMARY KEY(fork_id, booth_id)
                )
                """
            )

    def create(self, field_state: dict, participants: list[str]) -> dict:
        labels = _normalize_participants(participants)
        delight, silence, consequence = _validated_fork_source(field_state)
        source_field_id = str(field_state.get("field_state_id") or "")

        identity = {
            "source_field_state_id": source_field_id,
            "signed_receipt_id": consequence.get("signed_receipt_id"),
            "dispatch_crossing_id": consequence.get("dispatch_crossing_id"),
            "participants": labels,
            "door_ids": [door["door_id"] for door in delight],
        }
        fork_id = "banana-elf-fork-v0:" + _digest(identity)

        static = {
            "schema": "workbench.banana-elf-fork/v0",
            "fork_id": fork_id,
            "source_field_state_id": source_field_id,
            "source_consequence": json.loads(_canonical(consequence)),
            "delight_doors": delight,
            "silence_door": silence,
            "participant_labels": labels,
            "laws": [
                "ONE CONSEQUENCE != ONE CORRECT RETURN",
                "SEALED RETURN != CONSENSUS",
                "REVEAL != RANKING",
                "DELIGHT != SCORE",
                "AGREEMENT != RELATION",
                "DIFFERENCE != FAILURE",
                "CO-DELIGHT REQUIRES RETURN",
            ],
        }

        with self._connect() as db:
            row = db.execute(
                "SELECT fork_id FROM banana_forks WHERE fork_id = ?",
                (fork_id,),
            ).fetchone()
            if row is None:
                db.execute(
                    """
                    INSERT INTO banana_forks(
                        fork_id, created_at, source_field_json, fork_json
                    ) VALUES (?, ?, ?, ?)
                    """,
                    (
                        fork_id,
                        _now(),
                        _canonical(field_state),
                        _canonical(static),
                    ),
                )
                for ordinal, label in enumerate(labels):
                    booth_body = {
                        "fork_id": fork_id,
                        "ordinal": ordinal,
                        "label": label,
                    }
                    booth_id = "banana-elf-booth-v0:" + _digest(booth_body)
                    db.execute(
                        """
                        INSERT INTO banana_fork_booths(
                            fork_id, booth_id, ordinal, label, booth_token
                        ) VALUES (?, ?, ?, ?, ?)
                        """,
                        (
                            fork_id,
                            booth_id,
                            ordinal,
                            label,
                            secrets.token_urlsafe(24),
                        ),
                    )
        return self.get(fork_id, include_tokens=True)

    def list(self, *, include_tokens: bool = False) -> list[dict]:
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT fork_id
                FROM banana_forks
                ORDER BY created_at DESC, fork_id DESC
                """
            ).fetchall()
        return [
            self.get(str(row["fork_id"]), include_tokens=include_tokens)
            for row in rows
        ]

    def _rows(self, fork_id: str) -> tuple[sqlite3.Row, list[sqlite3.Row]]:
        with self._connect() as db:
            fork = db.execute(
                """
                SELECT created_at, source_field_json, fork_json
                FROM banana_forks
                WHERE fork_id = ?
                """,
                (fork_id,),
            ).fetchone()
            booths = db.execute(
                """
                SELECT booth_id, ordinal, label, booth_token,
                       submitted_at, response_json
                FROM banana_fork_booths
                WHERE fork_id = ?
                ORDER BY ordinal ASC
                """,
                (fork_id,),
            ).fetchall()
        if fork is None:
            raise ValueError("Banana-Elf fork not found")
        return fork, booths

    def get(self, fork_id: str, *, include_tokens: bool = False) -> dict:
        fork, booths = self._rows(str(fork_id))
        static = json.loads(str(fork["fork_json"]))
        submitted = [row for row in booths if row["response_json"] is not None]
        revealed = len(submitted) == len(booths) and bool(booths)

        booth_state = []
        for row in booths:
            item = {
                "booth_id": str(row["booth_id"]),
                "label": str(row["label"]),
                "ordinal": int(row["ordinal"]),
                "submitted": row["response_json"] is not None,
                "submitted_at": (
                    str(row["submitted_at"])
                    if row["submitted_at"] is not None
                    else None
                ),
            }
            if include_tokens:
                item["booth_token"] = str(row["booth_token"])
                item["packet"] = self._booth_packet(static, row)
            booth_state.append(item)

        result = {
            **static,
            "created_at": str(fork["created_at"]),
            "status": "revealed" if revealed else "collecting",
            "submitted_count": len(submitted),
            "booth_count": len(booths),
            "booths": booth_state,
            "returns": [],
            "take_descendants": [],
            "relation_field": None,
        }
        if revealed:
            returns = [
                json.loads(str(row["response_json"]))
                for row in booths
                if row["response_json"] is not None
            ]
            result["returns"] = returns
            result["take_descendants"] = [
                item
                for item in returns
                if (
                    item.get("field_return", {}).get("disposition") == "take"
                    and isinstance(
                        item.get("field_return", {}).get("reseed"),
                        dict,
                    )
                )
            ]
            result["relation_field"] = self._relation_field(result)
        return result

    def _booth_packet(self, static: dict, row: sqlite3.Row) -> dict:
        return {
            "schema": "workbench.banana-elf-booth-packet/v0",
            "fork_id": static["fork_id"],
            "booth_id": str(row["booth_id"]),
            "booth_token": str(row["booth_token"]),
            "label": str(row["label"]),
            "source_field_state_id": static["source_field_state_id"],
            "source_consequence": static["source_consequence"],
            "doors": static["delight_doors"] + [static["silence_door"]],
            "instructions": (
                "Choose one frozen door and TAKE/HOLD/PASS it without consulting "
                "other booth returns. Submit the exact booth_id and booth_token."
            ),
            "laws": [
                "BOOTH != VOTE",
                "SEALED != SECRET FOREVER",
                "RETURN != CONSENSUS",
                "OTHER RETURNS REMAIN UNSEEN UNTIL REVEAL",
            ],
        }

    def submit(
        self,
        fork_id: str,
        booth_id: str,
        booth_token: str,
        door_id: str,
        disposition: str,
        note: str = "",
    ) -> dict:
        fork, booths = self._rows(str(fork_id))
        static = json.loads(str(fork["fork_json"]))
        booth = next(
            (row for row in booths if str(row["booth_id"]) == str(booth_id)),
            None,
        )
        if booth is None:
            raise ValueError("Banana-Elf booth not found")
        if not secrets.compare_digest(
            str(booth["booth_token"]),
            str(booth_token),
        ):
            raise ValueError("Banana-Elf booth token mismatch")
        if booth["response_json"] is not None:
            existing = json.loads(str(booth["response_json"]))
            return {
                "schema": "workbench.banana-elf-sealed-return-ack/v0",
                "fork_id": fork_id,
                "booth_id": booth_id,
                "submission_id": existing["submission_id"],
                "sealed": self.get(fork_id)["status"] != "revealed",
                "status": self.get(fork_id)["status"],
            }

        normalized = str(disposition).strip().lower()
        if normalized not in _ALLOWED_DISPOSITIONS:
            raise ValueError("fork disposition must be TAKE, HOLD, or PASS")

        frozen_field = json.loads(str(fork["source_field_json"]))
        allowed_door_ids = {
            door["door_id"] for door in static["delight_doors"]
        } | {static["silence_door"]["door_id"]}
        if str(door_id) not in allowed_door_ids:
            raise ValueError("door is not part of this frozen Banana-Elf fork")

        field_return = compose_field_return(
            frozen_field,
            str(door_id),
            normalized,
            str(note),
        )
        body = {
            "schema": "workbench.banana-elf-fork-return/v0",
            "fork_id": fork_id,
            "booth_id": booth_id,
            "returner_label": str(booth["label"]),
            "field_return": field_return,
            "laws": [
                "SEALED RETURN != CONSENSUS",
                "RETURNER != REPRESENTATIVE",
                "TAKE != CROSSING",
                "REVEAL != RANKING",
            ],
        }
        response = {
            **body,
            "submission_id": "banana-elf-fork-return-v0:" + _digest(body),
        }

        with self._connect() as db:
            changed = db.execute(
                """
                UPDATE banana_fork_booths
                SET submitted_at = ?, response_json = ?
                WHERE fork_id = ? AND booth_id = ? AND response_json IS NULL
                """,
                (
                    _now(),
                    _canonical(response),
                    fork_id,
                    booth_id,
                ),
            ).rowcount
        if changed != 1:
            raise RuntimeError("Banana-Elf sealed return did not persist")

        state = self.get(fork_id)
        return {
            "schema": "workbench.banana-elf-sealed-return-ack/v0",
            "fork_id": fork_id,
            "booth_id": booth_id,
            "submission_id": response["submission_id"],
            "sealed": state["status"] != "revealed",
            "status": state["status"],
        }

    def relation_field(self, fork_id: str) -> dict:
        state = self.get(fork_id)
        if state["status"] != "revealed":
            raise ValueError("Banana-Elf fork remains sealed")
        relation = state.get("relation_field")
        if not isinstance(relation, dict):
            raise RuntimeError("Banana-Elf relation field unavailable")
        return relation

    def _relation_field(self, revealed: dict) -> dict:
        takes = list(revealed.get("take_descendants") or [])
        doors: list[dict] = []
        for left, right in itertools.combinations(takes, 2):
            left_return = left["field_return"]
            right_return = right["field_return"]
            left_door = left_return["selected_door"]
            right_door = right_return["selected_door"]
            body = {
                "schema": "workbench.field-station-door/v0",
                "kind": "banana-elf-relation-pair",
                "label": (
                    "Let "
                    + left["returner_label"]
                    + "'s "
                    + str(left_door.get("target", {}).get("facet") or left_door["kind"])
                    + " meet "
                    + right["returner_label"]
                    + "'s "
                    + str(right_door.get("target", {}).get("facet") or right_door["kind"])
                ),
                "why": (
                    "Two independently sealed returns now coexist. This door invites "
                    "a composition between them without claiming agreement, consensus, "
                    "preference, or a winner."
                ),
                "lane": "relation",
                "adapter": "BANANA ELF / FORK 001",
                "evidence": [
                    {
                        "kind": "banana-elf-sealed-return",
                        "submission_id": left["submission_id"],
                        "returner_label": left["returner_label"],
                        "reseed_id": left_return["reseed"]["reseed_id"],
                        "facet": left_door.get("target", {}).get("facet"),
                    },
                    {
                        "kind": "banana-elf-sealed-return",
                        "submission_id": right["submission_id"],
                        "returner_label": right["returner_label"],
                        "reseed_id": right_return["reseed"]["reseed_id"],
                        "facet": right_door.get("target", {}).get("facet"),
                    },
                ],
                "target": {
                    "fork_id": revealed["fork_id"],
                    "left_submission_id": left["submission_id"],
                    "right_submission_id": right["submission_id"],
                    "move": "let-meet-without-merging",
                    "novelty": "proposal-only",
                },
                "effect": "none",
                "laws": [
                    "RECOMMENDATION != SELECTION",
                    "DOOR != CROSSING",
                    "AVAILABILITY != OBLIGATION",
                    "AGREEMENT != RELATION",
                    "DIFFERENCE != FAILURE",
                    "PAIR != CONSENSUS",
                    "RELATION != MERGE",
                ],
            }
            doors.append(_door(body))

        silence_body = {
            "schema": "workbench.field-station-door/v0",
            "kind": "hold-fork-silence",
            "label": "Hold the revealed fork without composing it",
            "why": (
                "Independent returns may remain adjacent without being forced into "
                "a synthesis."
            ),
            "lane": "silence",
            "adapter": "BANANA ELF / HOLD",
            "evidence": [{
                "kind": "banana-elf-fork",
                "fork_id": revealed["fork_id"],
                "take_descendants": len(takes),
            }],
            "target": None,
            "effect": "none",
            "laws": [
                "RECOMMENDATION != SELECTION",
                "DOOR != CROSSING",
                "AVAILABILITY != OBLIGATION",
                "RELATION != REQUIREMENT",
            ],
        }
        doors.append(_door(silence_body))

        body = {
            "schema": "workbench.field-station-state/v0",
            "read_only": True,
            "fork_id": revealed["fork_id"],
            "source_field_state_id": revealed["source_field_state_id"],
            "source_signed_receipt_id": revealed["source_consequence"].get(
                "signed_receipt_id"
            ),
            "nearby_doors": doors,
            "laws": [
                "REVEAL != RANKING",
                "PAIR != CONSENSUS",
                "AGREEMENT != RELATION",
                "DIFFERENCE != FAILURE",
                "RELATION != MERGE",
                "RECURSION REQUIRES FRESH WITNESS",
            ],
        }
        return _field(body)

    def compose_relation_return(
        self,
        fork_id: str,
        expected_field_state_id: str,
        door_id: str,
        disposition: str,
        note: str = "",
    ) -> dict:
        relation = self.relation_field(fork_id)
        if relation.get("field_state_id") != expected_field_state_id:
            raise ValueError("Banana-Elf relation field changed; refresh before returning")
        return compose_field_return(
            relation,
            door_id,
            disposition,
            note,
        )
