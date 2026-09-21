"""HOUSE-FLYWHEEL-001: local, non-executing capability return ledger.

An imported return is a *reported* observation, not independent proof of a
project effect, authorization, source authenticity, or reusable capability.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

MAX_PACKET_BYTES = 32768
MAX_ARTIFACTS = 32
_EFFECT_STATES = frozenset({"attempted", "partial", "scoped_complete", "scope_uncertain", "refused", "unresolved"})
_CAPABILITY_STATES = frozenset({"proposed", "reported", "unresolved"})
_KEYS = frozenset({
    "return_id", "flight_ref", "source_owner", "source_ref", "effect_state",
    "parent_effect_ref", "artifacts", "capability_delta", "evidence_refs",
    "resource_costs", "nonclaims", "proposed_next",
})
_ARTIFACT_KEYS = frozenset({"artifact_ref", "owner", "kind", "capability_state", "evidence_refs"})


def _string(value: Any, name: str, *, optional: bool = False) -> str | None:
    if optional and value is None:
        return None
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f"{name} must be a nonblank string of at most 512 characters")
    return value


def _strings(value: Any, name: str, *, maximum: int = 32) -> list[str]:
    if not isinstance(value, list) or len(value) > maximum:
        raise ValueError(f"{name} must be a list of at most {maximum} strings")
    return [_string(item, name) for item in value]


def validate_packet(packet: dict[str, Any]) -> tuple[str, str]:
    """Return canonical JSON and its local integrity digest, never an authority proof."""
    if not isinstance(packet, dict) or set(packet) != _KEYS:
        raise ValueError("capability return must contain the exact v0 field set")
    for field in ("return_id", "flight_ref", "source_owner", "source_ref", "capability_delta", "resource_costs"):
        _string(packet[field], field)
    _string(packet["parent_effect_ref"], "parent_effect_ref", optional=True)
    if not isinstance(packet["effect_state"], str) or packet["effect_state"] not in _EFFECT_STATES:
        raise ValueError("effect_state is not declared in the v0 vocabulary")
    for field in ("evidence_refs", "nonclaims", "proposed_next"):
        _strings(packet[field], field)
    artifacts = packet["artifacts"]
    if not isinstance(artifacts, list) or len(artifacts) > MAX_ARTIFACTS:
        raise ValueError("artifacts must be a bounded list")
    seen: set[tuple[str, str]] = set()
    for artifact in artifacts:
        if not isinstance(artifact, dict) or set(artifact) != _ARTIFACT_KEYS:
            raise ValueError("artifact has invalid fields")
        for field in ("artifact_ref", "owner", "kind"):
            _string(artifact[field], field)
        if not isinstance(artifact["capability_state"], str) or artifact["capability_state"] not in _CAPABILITY_STATES:
            raise ValueError("invalid capability_state")
        _strings(artifact["evidence_refs"], "artifact.evidence_refs")
        identity = (artifact["owner"], artifact["artifact_ref"])
        if identity in seen:
            raise ValueError("duplicate artifact identity in return")
        seen.add(identity)
    if not packet["nonclaims"]:
        raise ValueError("state at least one nonclaim to preserve the evidence boundary")
    try:
        canonical = json.dumps(packet, sort_keys=True, separators=(",", ":"), allow_nan=False, ensure_ascii=False)
    except (TypeError, ValueError) as exc:
        raise ValueError("packet must be finite JSON data") from exc
    if len(canonical.encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("packet exceeds size limit")
    return canonical, hashlib.sha256(canonical.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class ReturnRecord:
    id: int
    received_at: str
    local_digest: str
    packet: dict[str, Any]


class CapabilityReturnLedger:
    """Workbench-owned local SQLite ledger; writes never touch project repos."""

    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.execute("""CREATE TABLE IF NOT EXISTS capability_returns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                received_at TEXT NOT NULL,
                return_id TEXT NOT NULL UNIQUE,
                local_digest TEXT NOT NULL,
                packet_json TEXT NOT NULL
            )""")

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.db_path, timeout=5)
        connection.row_factory = sqlite3.Row
        return connection

    @staticmethod
    def _record(row: sqlite3.Row) -> ReturnRecord:
        return ReturnRecord(int(row["id"]), str(row["received_at"]),
                            str(row["local_digest"]), json.loads(row["packet_json"]))

    def append(self, packet: dict[str, Any]) -> ReturnRecord:
        canonical, digest = validate_packet(packet)
        # The first accepted revision of an externally declared return_id is immutable.
        # Identical replay is idempotent; conflicting replays cannot replace history.
        with self._connect() as db:
            row = db.execute("SELECT * FROM capability_returns WHERE return_id = ?", (packet["return_id"],)).fetchone()
            if row is not None:
                if row["local_digest"] != digest or row["packet_json"] != canonical:
                    raise ValueError("return_id already exists with different content")
                return self._record(row)
            try:
                db.execute("INSERT INTO capability_returns(received_at,return_id,local_digest,packet_json) VALUES (?,?,?,?)",
                           (datetime.now(timezone.utc).isoformat(), packet["return_id"], digest, canonical))
            except sqlite3.IntegrityError as exc:
                # A concurrent writer won. Force an explicit reconciliation/replay.
                raise ValueError("concurrent return_id write; re-read before retry") from exc
            row = db.execute("SELECT * FROM capability_returns WHERE return_id = ?", (packet["return_id"],)).fetchone()
        return self._record(row)

    def latest(self, limit: int = 100) -> list[ReturnRecord]:
        if isinstance(limit, bool) or not isinstance(limit, int) or not 1 <= limit <= 100:
            raise ValueError("limit must be an integer from 1 to 100")
        with self._connect() as db:
            rows = db.execute("SELECT * FROM capability_returns ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [self._record(row) for row in rows]

    def get(self, return_id: str) -> ReturnRecord | None:
        _string(return_id, "return_id")
        with self._connect() as db:
            row = db.execute("SELECT * FROM capability_returns WHERE return_id = ?", (return_id,)).fetchone()
        return None if row is None else self._record(row)
