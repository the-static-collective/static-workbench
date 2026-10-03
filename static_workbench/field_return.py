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
            db.execute(
                """
                CREATE TABLE IF NOT EXISTS field_return_receivers (
                    receipt_id TEXT PRIMARY KEY,
                    crossing_json TEXT,
                    admission_json TEXT
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

    def get(self, receipt_id: str) -> dict:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT stored_at, receipt_json
                FROM field_returns
                WHERE receipt_id = ?
                """,
                (str(receipt_id),),
            ).fetchone()
        if row is None:
            raise ValueError("field return not found")
        return {
            "stored_at": str(row["stored_at"]),
            **json.loads(str(row["receipt_json"])),
        }

    def receiver(self, receipt_id: str) -> dict | None:
        with self._connect() as db:
            row = db.execute(
                """
                SELECT crossing_json, admission_json
                FROM field_return_receivers
                WHERE receipt_id = ?
                """,
                (str(receipt_id),),
            ).fetchone()
        if row is None:
            return None
        crossing = (
            json.loads(str(row["crossing_json"]))
            if row["crossing_json"] is not None
            else None
        )
        admission = (
            json.loads(str(row["admission_json"]))
            if row["admission_json"] is not None
            else None
        )
        return {
            "crossing": crossing,
            "admission": admission,
            "status": (
                "ADMITTED_NOT_ASSIGNED"
                if admission is not None
                else "RECEIVED_THEN_HELD"
                if crossing is not None
                else None
            ),
        }

    def save_crossing(self, receipt_id: str, crossing: dict) -> dict:
        existing = self.get(receipt_id)
        if existing.get("disposition") != "take" or not isinstance(existing.get("reseed"), dict):
            raise ValueError("only TAKE returns can cross a reseed")
        if crossing.get("schema") != "workbench.field-reseed-crossing/v0":
            raise ValueError("unsupported field reseed crossing schema")
        if crossing.get("field_return_id") != receipt_id:
            raise ValueError("field reseed crossing is bound to another return")
        if crossing.get("reseed_id") != existing["reseed"].get("reseed_id"):
            raise ValueError("field reseed crossing changed reseed identity")
        payload = _canonical(crossing)
        with self._connect() as db:
            row = db.execute(
                "SELECT crossing_json FROM field_return_receivers WHERE receipt_id = ?",
                (receipt_id,),
            ).fetchone()
            if row is not None and row["crossing_json"] is not None:
                if str(row["crossing_json"]) != payload:
                    raise ValueError("a different crossing is already stored for this return")
            else:
                db.execute(
                    """
                    INSERT INTO field_return_receivers(receipt_id, crossing_json, admission_json)
                    VALUES (?, ?, NULL)
                    ON CONFLICT(receipt_id) DO UPDATE SET crossing_json=excluded.crossing_json
                    """,
                    (receipt_id, payload),
                )
        result = self.receiver(receipt_id)
        if result is None or result["crossing"] is None:
            raise RuntimeError("field reseed crossing did not persist")
        return result

    def save_admission(self, receipt_id: str, admission: dict) -> dict:
        receiver = self.receiver(receipt_id)
        if receiver is None or not isinstance(receiver.get("crossing"), dict):
            raise ValueError("field reseed crossing HOLD is required before admission")
        if admission.get("schema") != "workbench.field-reseed-admission/v0":
            raise ValueError("unsupported field reseed admission schema")
        if admission.get("field_return_id") != receipt_id:
            raise ValueError("field reseed admission is bound to another return")
        if admission.get("reseed_id") != receiver["crossing"].get("reseed_id"):
            raise ValueError("field reseed admission changed reseed identity")
        payload = _canonical(admission)
        with self._connect() as db:
            row = db.execute(
                "SELECT admission_json FROM field_return_receivers WHERE receipt_id = ?",
                (receipt_id,),
            ).fetchone()
            if row is not None and row["admission_json"] is not None:
                if str(row["admission_json"]) != payload:
                    raise ValueError("a different admission is already stored for this return")
            else:
                db.execute(
                    """
                    UPDATE field_return_receivers
                    SET admission_json = ?
                    WHERE receipt_id = ?
                    """,
                    (payload, receipt_id),
                )
        result = self.receiver(receipt_id)
        if result is None or result["admission"] is None:
            raise RuntimeError("field reseed admission did not persist")
        return result

    def latest(self, limit: int = 50) -> list[dict]:
        bounded = max(1, min(int(limit), 200))
        with self._connect() as db:
            rows = db.execute(
                """
                SELECT r.stored_at, r.receipt_json, x.crossing_json, x.admission_json
                FROM field_returns r
                LEFT JOIN field_return_receivers x ON x.receipt_id = r.receipt_id
                ORDER BY r.stored_at DESC, r.receipt_id DESC
                LIMIT ?
                """,
                (bounded,),
            ).fetchall()
        result = []
        for row in rows:
            item = {
                "stored_at": str(row["stored_at"]),
                **json.loads(str(row["receipt_json"])),
            }
            crossing = (
                json.loads(str(row["crossing_json"]))
                if row["crossing_json"] is not None
                else None
            )
            admission = (
                json.loads(str(row["admission_json"]))
                if row["admission_json"] is not None
                else None
            )
            if crossing is not None or admission is not None:
                item["receiver"] = {
                    "status": (
                        "ADMITTED_NOT_ASSIGNED"
                        if admission is not None
                        else "RECEIVED_THEN_HELD"
                    ),
                    "crossing": crossing,
                    "admission": admission,
                }
            result.append(item)
        return result

    def receiver_field_state(self) -> list[dict]:
        summaries = []
        for item in self.latest(200):
            receiver = item.get("receiver")
            if not isinstance(receiver, dict):
                continue
            crossing = receiver.get("crossing")
            admission = receiver.get("admission")
            if not isinstance(crossing, dict):
                continue
            hold = crossing.get("ghot_hold")
            admit = (
                admission.get("ghot_admission")
                if isinstance(admission, dict)
                else None
            )
            summaries.append({
                "stored_at": item.get("stored_at"),
                "field_return_id": item.get("receipt_id"),
                "reseed_id": crossing.get("reseed_id"),
                "status": receiver.get("status"),
                "hold_id": hold.get("hold_id") if isinstance(hold, dict) else None,
                "admission_id": (
                    admit.get("admission_id")
                    if isinstance(admit, dict)
                    else None
                ),
                "intent_id": (
                    admit.get("intent", {}).get("intent_id")
                    if isinstance(admit, dict)
                    else None
                ),
            })
        return summaries
