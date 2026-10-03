"""FIELD-RETURN-001: explicit human disposition of a read-only Field Station door.

This module is deliberately project-effect free. It verifies the exact Field Station
state a human saw, binds one explicit disposition to one exact door, and optionally
produces a portable proposal-only reseed packet.

A return receipt is Workbench-owned continuity evidence. It is not project authority,
execution, admission, or proof that a downstream organ accepted the reseed.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


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


def _verified_field_state(field_state: dict) -> tuple[str, list[dict]]:
    if field_state.get("schema") != "workbench.field-station-state/v0":
        raise ValueError("unsupported field station schema")
    if field_state.get("read_only") is not True:
        raise ValueError("field station state must be read-only")

    supplied_id = field_state.get("field_state_id")
    if not isinstance(supplied_id, str) or not supplied_id:
        raise ValueError("field station state is missing field_state_id")

    body = {
        key: value
        for key, value in field_state.items()
        if key != "field_state_id"
    }
    expected_id = "field-station-v0:" + _digest(body)
    if supplied_id != expected_id:
        raise ValueError("field station state identity mismatch")

    doors = field_state.get("nearby_doors")
    if not isinstance(doors, list):
        raise ValueError("field station state is missing nearby_doors")
    return supplied_id, doors


def compose_field_return(
    field_state: dict,
    door_id: str,
    disposition: str,
    note: str = "",
) -> dict:
    """Bind one human disposition to one exact Field Station door.

    Dispositions are intentionally small:

    - `take`: carry this exact door forward as a proposal-only reseed.
    - `hold`: retain the possibility without producing a reseed.
    - `pass`: explicitly decline this door in this observed field.

    None of the dispositions executes a project effect.
    """
    field_state_id, doors = _verified_field_state(field_state)

    normalized = str(disposition).strip().lower()
    if normalized not in _ALLOWED_DISPOSITIONS:
        allowed = ", ".join(sorted(_ALLOWED_DISPOSITIONS))
        raise ValueError(f"unsupported field disposition; expected one of: {allowed}")

    selected = next(
        (door for door in doors if door.get("door_id") == door_id),
        None,
    )
    if selected is None:
        raise ValueError("door is not present in the verified field state")
    if selected.get("effect") != "none":
        raise ValueError("field return only accepts proposal-only doors")

    # JSON round-trip makes the returned snapshot detached from caller mutation while
    # preserving exactly the canonical data that participated in the receipt digest.
    door_snapshot = json.loads(_canonical(selected))
    human_note = str(note)

    body = {
        "schema": "workbench.field-return/v0",
        "field_state_id": field_state_id,
        "door_id": door_id,
        "disposition": normalized,
        "human_note": human_note,
        "selected_door": door_snapshot,
        "effect": "none",
        "laws": [
            "FIELD OBSERVATION != HUMAN DISPOSITION",
            "RECOMMENDATION != SELECTION",
            "SELECTION != EXECUTION",
            "DOOR != CROSSING",
            "RESEED != ADMISSION",
            "RECEIPT != AUTHORITY",
        ],
    }
    receipt_id = "field-return-v0:" + _digest(body)

    reseed = None
    if normalized == "take":
        reseed_body = {
            "schema": "workbench.field-reseed/v0",
            "source_return_id": receipt_id,
            "field_state_id": field_state_id,
            "door": door_snapshot,
            "human_note": human_note,
            "status": "proposal-only",
            "effect": "none",
            "laws": [
                "RESEED != ADMISSION",
                "TRANSPORT != AUTHORITY",
                "DOWNSTREAM INTERPRETATION != SOURCE FACT",
            ],
        }
        reseed = {
            **reseed_body,
            "reseed_id": "field-reseed-v0:" + _digest(reseed_body),
        }

    return {
        **body,
        "receipt_id": receipt_id,
        "reseed": reseed,
    }


class FieldReturnStore:
    """Durable Workbench-owned shelf for explicit Field Return receipts."""

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
                CREATE TABLE IF NOT EXISTS field_returns (
                    receipt_id TEXT PRIMARY KEY,
                    stored_at TEXT NOT NULL,
                    field_state_id TEXT NOT NULL,
                    door_id TEXT NOT NULL,
                    disposition TEXT NOT NULL,
                    receipt_json TEXT NOT NULL
                )
                """
            )

    def save(self, receipt: dict) -> dict:
        if receipt.get("schema") != "workbench.field-return/v0":
            raise ValueError("unsupported field return schema")
        receipt_id = str(receipt.get("receipt_id") or "")
        if not receipt_id:
            raise ValueError("field return is missing receipt_id")

        payload = _canonical(receipt)
        stored_at = datetime.now(timezone.utc).isoformat()
        with self._connect() as db:
            db.execute(
                """
                INSERT OR IGNORE INTO field_returns(
                    receipt_id, stored_at, field_state_id, door_id, disposition, receipt_json
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    receipt_id,
                    stored_at,
                    str(receipt.get("field_state_id") or ""),
                    str(receipt.get("door_id") or ""),
                    str(receipt.get("disposition") or ""),
                    payload,
                ),
            )
            row = db.execute(
                """
                SELECT stored_at, receipt_json
                FROM field_returns
                WHERE receipt_id = ?
                """,
                (receipt_id,),
            ).fetchone()
        if row is None:
            raise RuntimeError("field return did not persist")
        return {
            "stored_at": str(row["stored_at"]),
            **json.loads(str(row["receipt_json"])),
        }

    def latest(self, limit: int = 50) -> list[dict]:
        bounded = max(1, min(int(limit), 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT stored_at, receipt_json
                FROM field_returns
                ORDER BY stored_at DESC, receipt_id DESC
                LIMIT ?
                """,
                (bounded,),
            ).fetchall()
        return [
            {
                "stored_at": str(row["stored_at"]),
                **json.loads(str(row["receipt_json"])),
            }
            for row in rows
        ]
