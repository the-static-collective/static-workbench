from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

_MAX_JSON_BYTES = 2 * 1024 * 1024
_MAX_JOURNAL_BYTES = 10 * 1024 * 1024
_MAX_RECORDS = 5000
_SHA256_PREFIX = "sha256:"


class RoadDeskError(ValueError):
    pass


def _read_json(path: Path, *, max_bytes: int = _MAX_JSON_BYTES) -> dict[str, Any]:
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise RoadDeskError(f"expected regular JSON file: {path.name}")
    if path.stat().st_size > max_bytes:
        raise RoadDeskError(f"JSON file exceeds bounded read: {path.name}")
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoadDeskError(f"invalid JSON file: {path.name}") from exc
    if not isinstance(value, dict):
        raise RoadDeskError(f"expected JSON object: {path.name}")
    return value


def _digest_from_address(address: object) -> str:
    if not isinstance(address, str) or not address.startswith(_SHA256_PREFIX):
        raise RoadDeskError("House identity_ref must be a sha256 address")
    digest = address[len(_SHA256_PREFIX):]
    if len(digest) != 64 or any(char not in "0123456789abcdef" for char in digest):
        raise RoadDeskError("House identity_ref must be lowercase sha256")
    return digest


def _artifact_path(root: Path, address: str) -> Path:
    digest = _digest_from_address(address)
    return root / "tranchnode" / "objects" / "sha256" / digest[:2] / digest[2:4] / digest


def _read_identity(root: Path, house: dict[str, Any]) -> tuple[dict[str, Any], bool]:
    identity_ref = house.get("identity_ref")
    if not isinstance(identity_ref, str):
        raise RoadDeskError("House identity_ref missing")
    path = _artifact_path(root, identity_ref)
    if not path.exists() or not path.is_file() or path.is_symlink():
        raise RoadDeskError("House identity artifact is unavailable")
    data = path.read_bytes()
    if len(data) > _MAX_JSON_BYTES:
        raise RoadDeskError("House identity artifact exceeds bounded read")
    digest = hashlib.sha256(data).hexdigest()
    address_ok = identity_ref == f"sha256:{digest}"
    try:
        identity = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RoadDeskError("House identity artifact is not valid UTF-8 JSON") from exc
    if not isinstance(identity, dict):
        raise RoadDeskError("House identity artifact must be a JSON object")
    return identity, address_ok


def _journal(root: Path) -> list[dict[str, Any]]:
    path = root / "relatte-receiver" / "journal.jsonl"
    if not path.exists():
        return []
    if not path.is_file() or path.is_symlink():
        raise RoadDeskError("receiver journal must be a regular file")
    if path.stat().st_size > _MAX_JOURNAL_BYTES:
        raise RoadDeskError("receiver journal exceeds bounded read")
    records: list[dict[str, Any]] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        if len(records) >= _MAX_RECORDS:
            raise RoadDeskError("receiver journal exceeds bounded record count")
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise RoadDeskError("receiver journal contains invalid JSON") from exc
        if not isinstance(value, dict):
            raise RoadDeskError("receiver journal event must be an object")
        records.append(value)
    return records


def _crossing_summaries(root: Path) -> list[dict[str, Any]]:
    inbox = root / "inbox"
    if not inbox.exists():
        return []
    if not inbox.is_dir() or inbox.is_symlink():
        raise RoadDeskError("RoadKit inbox must be a regular directory")
    result: list[dict[str, Any]] = []
    for path in sorted(inbox.glob("*.json"))[:500]:
        if path.is_symlink() or not path.is_file():
            continue
        crossing = _read_json(path)
        payloads = crossing.get("payload_refs")
        result.append(
            {
                "crossing_id": crossing.get("crossing_id"),
                "source_particular": crossing.get("source_particular"),
                "source_world": crossing.get("source_world"),
                "declared_kind": crossing.get("declared_kind"),
                "requested_effect": crossing.get("requested_effect"),
                "payload_count": len(payloads) if isinstance(payloads, list) else 0,
                "has_return_address": isinstance(crossing.get("return_address"), str),
            }
        )
    return result


def _count_json_files(path: Path) -> int:
    if not path.exists():
        return 0
    if not path.is_dir() or path.is_symlink():
        raise RoadDeskError(f"{path.name} must be a regular directory")
    return sum(1 for item in path.glob("*.json") if item.is_file() and not item.is_symlink())


def road_desk_status(house_root: Path | None) -> dict[str, Any]:
    laws = [
        "OBSERVATION != AUTHORITY",
        "VISIBLE HOLD != ACCEPTANCE",
        "UI != ROADKIT EXECUTION",
        "RECEIPT PARSED != SIGNATURE VERIFIED",
        "PULLED != ADMITTED",
    ]
    if house_root is None:
        return {
            "schema": "static-workbench.road-desk/v0",
            "configured": False,
            "present": False,
            "verification": "not_evaluated",
            "house": None,
            "identity": None,
            "summary": {"inbox": 0, "outbox": 0, "foreign_holds": 0, "admits": 0},
            "foreign_crossings": [],
            "laws": laws,
            "operator_note": "Configure roadkit_house_root to observe one local RoadKit House. Workbench does not run pull or accept.",
        }

    root = house_root.expanduser().resolve(strict=False)
    house_path = root / "house.json"
    if not house_path.exists():
        return {
            "schema": "static-workbench.road-desk/v0",
            "configured": True,
            "present": False,
            "root": str(root),
            "verification": "not_evaluated",
            "house": None,
            "identity": None,
            "summary": {"inbox": 0, "outbox": 0, "foreign_holds": 0, "admits": 0},
            "foreign_crossings": [],
            "laws": laws,
            "operator_note": "Configured RoadKit House root is not initialized.",
        }

    house = _read_json(house_path)
    if house.get("schema") != "static.roadkit-house/v0":
        raise RoadDeskError("configured root is not a ROADKIT-001 House")

    receiver = _read_json(root / "relatte-receiver" / "receiver.json")
    if (
        receiver.get("world_id") != house.get("world_id")
        or receiver.get("receiver_particular") != house.get("house_id")
    ):
        raise RoadDeskError("RoadKit House and receiver identity disagree")

    identity, identity_address_verified = _read_identity(root, house)
    identity_matches_house = (
        identity.get("schema") == "static.house-identity/v0"
        and identity.get("house_id") == house.get("house_id")
        and identity.get("world_id") == house.get("world_id")
        and identity.get("authority") == "self-asserted-local"
    )

    events = _journal(root)
    holds: list[dict[str, Any]] = []
    admits: list[dict[str, Any]] = []
    for event in events:
        receipt = event.get("receipt")
        if not isinstance(receipt, dict):
            continue
        kind = receipt.get("kind")
        item = {
            "crossing_id": receipt.get("crossing_id"),
            "receipt_id": receipt.get("receipt_id"),
            "semantic_effect": receipt.get("semantic_effect"),
            "created_at": receipt.get("created_at"),
        }
        if kind == "R3_HOLD":
            holds.append(item)
        elif kind == "R3_ADMIT":
            admits.append(item)

    foreign_crossings = _crossing_summaries(root)
    inbox_ids = {
        item["crossing_id"]
        for item in foreign_crossings
        if isinstance(item.get("crossing_id"), str)
    }
    foreign_holds = [item for item in holds if item.get("crossing_id") in inbox_ids]

    return {
        "schema": "static-workbench.road-desk/v0",
        "configured": True,
        "present": True,
        "root": str(root),
        "verification": "identity_content_address_checked; receipt_signatures_not_reverified",
        "house": {
            "house_id": house.get("house_id"),
            "world_id": house.get("world_id"),
            "label": house.get("label"),
            "identity_ref": house.get("identity_ref"),
            "authority": house.get("authority"),
        },
        "identity": {
            "schema": identity.get("schema"),
            "house_id": identity.get("house_id"),
            "world_id": identity.get("world_id"),
            "label": identity.get("label"),
            "authority": identity.get("authority"),
            "address_verified": identity_address_verified,
            "matches_house": identity_matches_house,
            "signing_public_key_present": isinstance(identity.get("signing_public_key"), dict),
        },
        "summary": {
            "inbox": len(foreign_crossings),
            "outbox": _count_json_files(root / "outbox"),
            "foreign_holds": len(foreign_holds),
            "admits": len(admits),
        },
        "foreign_crossings": foreign_crossings,
        "foreign_hold_receipts": foreign_holds[-100:],
        "admit_receipts": admits[-100:],
        "laws": laws,
        "operator_note": "Road Desk is observational. Pull and accept remain explicit RoadKit operator actions outside Workbench.",
    }
