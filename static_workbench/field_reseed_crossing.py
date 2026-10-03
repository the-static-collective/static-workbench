"""FIELD-RESEED-CROSSING-001: Workbench -> reLATTE -> GHoT HOLD/admission.

The Workbench owns the human TAKE receipt. reLATTE owns portable crossing and
RECEIVE/HOLD evidence. GHoT owns receiver-local admission. No stage silently
converts the reseed into execution.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any

from .repos import RepoStatus


RELATTE_REVISION = "87006f3265103a8abe387d81597c58aeb39b0beb"
GHOT_REVISION = "fa3a2d81b5cebc3532c9f7f6b950039186cc37c3"
GHOT_RECEIVER_WORLD = "world:ghot:field-reseed-inbox"
GHOT_RECEIVER_PARTICULAR = "particular:ghot:field-reseed-inbox"


class FieldReseedCrossingError(RuntimeError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _compatible(repo: RepoStatus, expected: str) -> bool:
    if repo.dirty:
        return False
    return isinstance(repo.head, str) and expected.startswith(repo.head)


def _find_pinned(
    repos: list[RepoStatus],
    name: str,
    expected: str,
    required_path: str,
) -> Path:
    for repo in repos:
        if repo.name.casefold() != name.casefold():
            continue
        root = Path(repo.path)
        if not _compatible(repo, expected):
            raise FieldReseedCrossingError(
                f"{name} checkout must be clean and pinned to {expected}"
            )
        if not (root / required_path).is_file():
            raise FieldReseedCrossingError(
                f"{name} pinned checkout is missing {required_path}"
            )
        return root
    raise FieldReseedCrossingError(
        f"A clean local {name} checkout pinned to {expected} is required."
    )


def _verified_take(field_return: dict) -> tuple[str, dict]:
    if field_return.get("schema") != "workbench.field-return/v0":
        raise FieldReseedCrossingError("unsupported Field Return schema")
    if field_return.get("disposition") != "take":
        raise FieldReseedCrossingError("only TAKE returns carry a reseed")
    receipt_id = field_return.get("receipt_id")
    reseed = field_return.get("reseed")
    if not isinstance(receipt_id, str) or not isinstance(reseed, dict):
        raise FieldReseedCrossingError("TAKE return is missing its reseed")
    if reseed.get("schema") != "workbench.field-reseed/v0":
        raise FieldReseedCrossingError("unsupported field reseed schema")
    if reseed.get("source_return_id") != receipt_id:
        raise FieldReseedCrossingError("field reseed is not bound to this return")
    if reseed.get("status") != "proposal-only" or reseed.get("effect") != "none":
        raise FieldReseedCrossingError("field reseed is not proposal-only")
    reseed_id = reseed.get("reseed_id")
    if not isinstance(reseed_id, str) or not reseed_id.startswith("field-reseed-v0:"):
        raise FieldReseedCrossingError("field reseed identity is missing")
    body = {key: value for key, value in reseed.items() if key != "reseed_id"}
    if reseed_id != "field-reseed-v0:" + _digest(body):
        raise FieldReseedCrossingError("field reseed identity mismatch")
    return receipt_id, json.loads(_canonical(reseed))


def _base_time(field_return: dict) -> datetime:
    raw = field_return.get("stored_at")
    try:
        value = datetime.fromisoformat(str(raw))
        if value.tzinfo is None:
            value = value.replace(tzinfo=timezone.utc)
        return value.astimezone(timezone.utc)
    except (TypeError, ValueError) as exc:
        raise FieldReseedCrossingError(
            "persisted Field Return timestamp is required before crossing"
        ) from exc


def build_relatte_request(field_return: dict, state_dir: Path) -> dict:
    receipt_id, reseed = _verified_take(field_return)
    reseed_id = reseed["reseed_id"]
    base_time = _base_time(field_return)
    stamps = []
    for index in range(1, 5):
        moment = base_time + timedelta(milliseconds=index)
        stamps.append(moment.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z")

    slug = reseed_id.split(":", 1)[1]
    root = Path(state_dir)
    return {
        "schema": "relatte.opaque-roundtrip-request/v0",
        "spec": {
            "schema": "relatte.opaque-organ-spec/v0",
            "family_ref": "organ:static-workbench/field-return",
            "donor_contract_ref": (
                "github:the-static-collective/static-workbench"
                "#docs/field-return-001.md"
            ),
            "artifact_kind": "workbench-field-reseed",
            "source_world": "world:static-workbench:field-station",
            "source_particular": f"particular:field-return:{receipt_id}",
            "source_history_head": "sha256:" + _digest(reseed),
            "payload_refs": [{
                "address": "sha256:" + _digest(reseed),
                "role": "field-reseed",
                "media_type": "application/json",
            }],
            "donor_claims": {
                "field_return_id": receipt_id,
                "reseed_id": reseed_id,
                "field_state_id": reseed.get("field_state_id"),
                "human_take": True,
                "donor_authority_transferred": False,
            },
            "requested_effect": {
                "kind": "candidate-field-reseed-ingress",
                "authority": "receiver-local",
            },
            "return_address": f"workbench:field-return:{receipt_id}",
            "created_at": stamps[0],
        },
        "receiver_root": str(root / "field-reseed-relatte-receiver"),
        "receiver": {
            "world_id": GHOT_RECEIVER_WORLD,
            "receiver_particular": GHOT_RECEIVER_PARTICULAR,
            "contract_ref": "contract:ghot-field-reseed-inbox/v0",
        },
        "bundle_path": str(root / "field-reseed-relatte-bundles" / f"{slug}.json"),
        "result_path": str(root / "field-reseed-relatte-results" / f"{slug}.json"),
        "disposition": "HOLD",
        "transport_created_at": stamps[1],
        "received_at": stamps[2],
        "disposed_at": stamps[3],
        "route_note": "Static Workbench Field Return -> reLATTE R14 -> GHoT Field Reseed Receiver",
    }


def _run_json(
    command: list[str],
    cwd: Path,
    payload: dict,
    env: dict[str, str],
    label: str,
    timeout: float = 20.0,
) -> dict:
    try:
        completed = subprocess.run(
            command,
            cwd=cwd,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env=env,
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise FieldReseedCrossingError(f"{label} could not run: {exc}") from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise FieldReseedCrossingError(
            f"{label} refused the crossing: {detail or 'unknown error'}"
        )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise FieldReseedCrossingError(f"{label} returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise FieldReseedCrossingError(f"{label} returned non-object JSON")
    return value


def _verify_relatte(result: dict, reseed: dict) -> None:
    if result.get("schema") != "relatte.opaque-roundtrip-result/v0":
        raise FieldReseedCrossingError("unexpected reLATTE result schema")
    crossing = result.get("crossing")
    received = result.get("receive_receipt")
    disposition = result.get("disposition_receipt")
    if not all(isinstance(item, dict) for item in (crossing, received, disposition)):
        raise FieldReseedCrossingError("reLATTE result is incomplete")
    crossing_id = crossing.get("crossing_id")
    if received.get("crossing_id") != crossing_id or disposition.get("crossing_id") != crossing_id:
        raise FieldReseedCrossingError("reLATTE receipt binding mismatch")
    if received.get("kind") != "RECEIVED" or received.get("semantic_effect") != "none":
        raise FieldReseedCrossingError("reLATTE RECEIVE boundary was not preserved")
    if received.get("world_id") != GHOT_RECEIVER_WORLD:
        raise FieldReseedCrossingError("reLATTE delivered to the wrong receiver world")
    if disposition.get("kind") != "R3_HOLD" or disposition.get("semantic_effect") != "none":
        raise FieldReseedCrossingError("reLATTE did not return the reseed in HOLD")
    adapter = crossing.get("extensions", {}).get("organ_adapter", {})
    if adapter.get("family_ref") != "organ:static-workbench/field-return":
        raise FieldReseedCrossingError("reLATTE changed donor family identity")
    if adapter.get("donor_claims", {}).get("reseed_id") != reseed.get("reseed_id"):
        raise FieldReseedCrossingError("reLATTE changed reseed identity")
    if not any(
        isinstance(ref, dict)
        and ref.get("address") == "sha256:" + _digest(reseed)
        and ref.get("role") == "field-reseed"
        for ref in crossing.get("payload_refs", [])
    ):
        raise FieldReseedCrossingError("reLATTE changed the reseed payload reference")


def cross_field_reseed(
    field_return: dict,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    receipt_id, reseed = _verified_take(field_return)
    relatte = _find_pinned(
        repos, "reLATTE", RELATTE_REVISION, "scripts/opaque-roundtrip.ts"
    )
    ghot = _find_pinned(
        repos, "GHoT", GHOT_REVISION, "ghot/field_reseed_receiver.py"
    )

    request = build_relatte_request(field_return, state_dir)
    relatte_result = _run_json(
        ["node", "--experimental-strip-types", str(relatte / "scripts" / "opaque-roundtrip.ts")],
        relatte,
        request,
        {**os.environ, "LC_ALL": "C"},
        "reLATTE R14",
    )
    _verify_relatte(relatte_result, reseed)

    ghot_home = Path(state_dir) / "field-reseed-ghot"
    ghot_home.mkdir(parents=True, exist_ok=True)
    ghot_hold = _run_json(
        ["python3", str(ghot / "ghot" / "field_reseed_receiver.py")],
        ghot,
        {
            "action": "receive",
            "reseed": reseed,
            "relatte_result": relatte_result,
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Field Reseed Receiver",
    )
    if (
        ghot_hold.get("schema") != "ghot.field-reseed-hold/v0"
        or ghot_hold.get("status") != "HOLD"
        or ghot_hold.get("semantic_effect") != "none"
        or ghot_hold.get("reseed_id") != reseed["reseed_id"]
    ):
        raise FieldReseedCrossingError("GHoT did not preserve receiver-local HOLD")

    return {
        "schema": "workbench.field-reseed-crossing/v0",
        "field_return_id": receipt_id,
        "reseed_id": reseed["reseed_id"],
        "status": "RECEIVED_THEN_HELD",
        "semantic_effect": "none",
        "pins": {
            "relatte": RELATTE_REVISION,
            "ghot": GHOT_REVISION,
        },
        "relatte": relatte_result,
        "ghot_hold": ghot_hold,
        "laws": [
            "TAKE != CROSSING",
            "CROSSING != ADMISSION",
            "RECEIVE != ADMISSION",
            "HOLD != EXECUTION",
            "TRANSPORT != AUTHORITY",
        ],
    }


def admit_field_reseed(
    crossing: dict,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    if (
        crossing.get("schema") != "workbench.field-reseed-crossing/v0"
        or crossing.get("status") != "RECEIVED_THEN_HELD"
        or crossing.get("semantic_effect") != "none"
    ):
        raise FieldReseedCrossingError("verified field reseed HOLD is required")
    hold = crossing.get("ghot_hold")
    if not isinstance(hold, dict):
        raise FieldReseedCrossingError("GHoT HOLD witness is missing")

    ghot = _find_pinned(
        repos, "GHoT", GHOT_REVISION, "ghot/field_reseed_receiver.py"
    )
    ghot_home = Path(state_dir) / "field-reseed-ghot"
    admission = _run_json(
        ["python3", str(ghot / "ghot" / "field_reseed_receiver.py")],
        ghot,
        {
            "action": "admit",
            "hold_id": hold.get("hold_id"),
            "selection_source": "workbench-user-explicit",
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Field Reseed Receiver",
    )
    if (
        admission.get("schema") != "ghot.field-reseed-admission/v0"
        or admission.get("status") != "ADMITTED"
        or admission.get("semantic_effect") != "local-inbox-only"
        or admission.get("reseed_id") != crossing.get("reseed_id")
        or admission.get("hold_id") != hold.get("hold_id")
    ):
        raise FieldReseedCrossingError("GHoT admission witness is invalid")
    intent = admission.get("intent")
    if (
        not isinstance(intent, dict)
        or intent.get("schema") != "ghot.carried-intent/v0"
        or intent.get("status") != "admitted-not-assigned"
        or intent.get("effect") != "local-inbox-only"
    ):
        raise FieldReseedCrossingError("GHoT admission silently crossed into assignment")

    return {
        "schema": "workbench.field-reseed-admission/v0",
        "field_return_id": crossing.get("field_return_id"),
        "reseed_id": crossing.get("reseed_id"),
        "status": "ADMITTED_NOT_ASSIGNED",
        "semantic_effect": "local-inbox-only",
        "ghot_admission": admission,
        "pins": {
            "ghot": GHOT_REVISION,
        },
        "laws": [
            "ADMISSION != ASSIGNMENT",
            "ASSIGNMENT != EXECUTION",
            "RECEIVER CONSEQUENCE != DONOR CONSEQUENCE",
        ],
    }
