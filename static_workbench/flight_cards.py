"""Flight Card Studio -> HOUSE candidate boundary: inspect, never execute.

This v0 wire format is proposed by Workbench; Lovable is not yet integrated.
No project adapters, tool calls, permission grants, or journal writes occur here.
"""
from __future__ import annotations

import hashlib
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any
from uuid import UUID

SCHEMA = "house.flight-card-candidate/v0"
RETURN_SCHEMA = "house.flight-card-self-report/v0"
CLASSES = {"observed", "reported", "derived", "unresolved"}
OUTCOMES = {"attempted", "partial", "scoped_complete", "scope_uncertain", "refused", "unresolved"}
MAX_BYTES = 131_072


class FlightCardError(ValueError):
    """Reject a malformed or over-authoritative external candidate."""


def _fail(where: str, message: str) -> None:
    raise FlightCardError(f"{where}: {message}")


def _obj(value: Any, where: str, required: set[str], optional: set[str] = frozenset()) -> dict:
    if not isinstance(value, dict):
        _fail(where, "expected object")
    if missing := required - value.keys():
        _fail(where, f"missing fields {sorted(missing)}")
    if extra := value.keys() - required - optional:
        _fail(where, f"unknown fields {sorted(extra)}")
    return value


def _text(value: Any, where: str, limit: int = 4000, *, blank: bool = False) -> str:
    if not isinstance(value, str) or len(value) > limit or (not blank and not value.strip()):
        _fail(where, f"expected {'possibly blank ' if blank else 'nonblank '}text <= {limit} chars")
    return value


def _uuid(value: Any, where: str) -> str:
    token = _text(value, where, 40)
    try:
        canonical = str(UUID(token))
    except (ValueError, AttributeError):
        _fail(where, "expected UUID")
    if token != canonical:
        _fail(where, "expected canonical lowercase UUID")
    return token


def _date(value: Any, where: str, *, optional: bool = False) -> None:
    if optional and value is None:
        return
    token = _text(value, where, 48)
    try:
        stamp = datetime.fromisoformat(token.replace("Z", "+00:00"))
    except ValueError:
        _fail(where, "expected ISO timestamp")
    if stamp.tzinfo is None or stamp.utcoffset() is None:
        _fail(where, "timestamp must contain timezone")


def _list(value: Any, where: str, limit: int = 32, *, allow_empty: bool = True) -> list:
    if not isinstance(value, list) or len(value) > limit or (not allow_empty and not value):
        _fail(where, f"expected list of 0..{limit} entries" if allow_empty else "expected nonempty list")
    return value


def _strings(value: Any, where: str, limit: int = 32) -> None:
    for i, item in enumerate(_list(value, where, limit)):
        _text(item, f"{where}[{i}]", 1000)


def _digest(value: Any) -> str:
    canonical = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _bounded_json(value: Any) -> None:
    try:
        encoded = json.dumps(value, ensure_ascii=False, allow_nan=False)
    except (TypeError, ValueError) as error:
        raise FlightCardError("candidate: not JSON-serializable") from error
    if len(encoded.encode("utf-8")) > MAX_BYTES:
        _fail("candidate", f"exceeds {MAX_BYTES} bytes")


def validate_candidate(candidate: Any) -> dict[str, Any]:
    """Validate an export without implying truth, approval by HOUSE, or execution."""
    _bounded_json(candidate)
    card = _obj(candidate, "candidate",
                {"schema", "flight_id", "raw", "witnesses", "proposal", "approval"})
    if card["schema"] != SCHEMA:
        _fail("schema", f"expected {SCHEMA}")
    _uuid(card["flight_id"], "flight_id")
    raw = _obj(card["raw"], "raw", {"text", "source_type", "locator", "captured_at", "observer"})
    _text(raw["text"], "raw.text", 20_000)
    _text(raw["source_type"], "raw.source_type", 80)
    if raw["locator"] is not None:
        _text(raw["locator"], "raw.locator", 2000)
    _date(raw["captured_at"], "raw.captured_at")
    _text(raw["observer"], "raw.observer", 160)

    witnesses = _list(card["witnesses"], "witnesses", 64)
    seen: set[str] = set()
    for i, item in enumerate(witnesses):
        at = f"witnesses[{i}]"
        witness = _obj(item, at,
                       {"id", "class", "text", "observer", "source_locator",
                        "occurred_at", "recorded_at", "known_at", "nonclaims"})
        key = _uuid(witness["id"], f"{at}.id")
        if key in seen:
            _fail(at, "duplicate witness id")
        seen.add(key)
        if witness["class"] not in CLASSES:
            _fail(at, "unknown evidence class")
        _text(witness["text"], f"{at}.text")
        _text(witness["observer"], f"{at}.observer", 160)
        if witness["source_locator"] is not None:
            _text(witness["source_locator"], f"{at}.source_locator", 2000)
        _date(witness["occurred_at"], f"{at}.occurred_at", optional=True)
        _date(witness["recorded_at"], f"{at}.recorded_at")
        _date(witness["known_at"], f"{at}.known_at", optional=True)
        _strings(witness["nonclaims"], f"{at}.nonclaims", 12)

    proposal = _obj(card["proposal"], "proposal",
                    {"job", "tools", "effects", "fence", "unknowns", "verification"})
    _text(proposal["job"], "proposal.job")
    _strings(proposal["tools"], "proposal.tools", 16)
    _strings(proposal["effects"], "proposal.effects", 32)
    _text(proposal["fence"], "proposal.fence")
    _strings(proposal["unknowns"], "proposal.unknowns", 16)
    _text(proposal["verification"], "proposal.verification")

    approval = card["approval"]
    if approval is not None:
        _obj(approval, "approval", {"actor", "approved_at", "proposal_sha256", "effects"})
        _text(approval["actor"], "approval.actor", 160)
        _date(approval["approved_at"], "approval.approved_at")
        if approval["proposal_sha256"] != _digest(proposal):
            _fail("approval", "stale or mismatched proposal snapshot")
        if approval["effects"] != proposal["effects"]:
            _fail("approval", "approved effects differ from current proposal")
    return {
        "schema": "house.flight-card-inspection/v0",
        "flight_id": card["flight_id"],
        "candidate_sha256": _digest(card),
        "proposal_sha256": _digest(proposal),
        "witness_count": len(witnesses),
        "human_approval_claimed": approval is not None,
        "house_authorization": "not_evaluated",
        "binding": "not_evaluated",
        "execution": "not_attempted",
        "source_authenticity": "not_verified",
        "nonclaims": [
            "External human approval is a claim in the export, not HOUSE authorization.",
            "Imported observations and evidence are not independently verified.",
            "No LOADOUT binding, project mutation, or work was performed.",
        ],
    }


def self_report(candidate: Any, report: Any) -> dict[str, Any]:
    """Create a separate *human-reported* return; no verification or promotion."""
    inspection = validate_candidate(candidate)
    _bounded_json(report)
    record = _obj(report, "report",
                  {"receipt_id", "reporter", "recorded_at", "outcome",
                   "details", "evidence_locators", "nonclaims", "parent_receipt_sha256"})
    _uuid(record["receipt_id"], "report.receipt_id")
    _text(record["reporter"], "report.reporter", 160)
    _date(record["recorded_at"], "report.recorded_at")
    if record["outcome"] not in OUTCOMES:
        _fail("report.outcome", "unknown status")
    _text(record["details"], "report.details", 8000)
    _strings(record["evidence_locators"], "report.evidence_locators", 16)
    _strings(record["nonclaims"], "report.nonclaims", 16)
    parent = record["parent_receipt_sha256"]
    if parent is not None and (not isinstance(parent, str) or len(parent) != 64
                               or any(c not in "0123456789abcdef" for c in parent)):
        _fail("report.parent_receipt_sha256", "expected SHA-256 hex or null")
    return {
        "schema": RETURN_SCHEMA,
        "flight_id": inspection["flight_id"],
        "candidate_sha256": inspection["candidate_sha256"],
        "report": record,
        "report_sha256": _digest(record),
        "evidence_class": "self_reported",
        "independently_verified": False,
        "house_execution": "not_performed",
    }


def main() -> int:
    """Read a named export for inspection; print an inert JSON inspection."""
    if len(sys.argv) != 2:
        print("usage: python -m static_workbench.flight_cards CANDIDATE.json", file=sys.stderr)
        return 2
    try:
        path = Path(sys.argv[1])
        if path.stat().st_size > MAX_BYTES:
            _fail("candidate", "input file too large")
        card = json.loads(path.read_text(encoding="utf-8"))
        print(json.dumps(validate_candidate(card), indent=2))
        return 0
    except (OSError, UnicodeError, json.JSONDecodeError, FlightCardError) as error:
        print(f"Flight Card refused: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
