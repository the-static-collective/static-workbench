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
GHOT_REVISION = "e35dd470384d864b7b0b629a68dad570875a7df0"
GHOT_RECEIVER_WORLD = "world:ghot:field-reseed-inbox"
GHOT_RECEIVER_PARTICULAR = "particular:ghot:field-reseed-inbox"


class FieldReseedCrossingError(RuntimeError):
    pass


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _tracked_checkout_matches(root: Path, expected: str) -> bool:
    try:
        head = subprocess.run(
            ["git", "-C", str(root), "rev-parse", "HEAD"],
            text=True,
            capture_output=True,
            check=False,
            timeout=5,
            env={**os.environ, "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"},
        )
        if head.returncode != 0 or head.stdout.strip() != expected:
            return False
        for args in (
            ["diff", "--quiet", expected, "--"],
            ["diff", "--cached", "--quiet", expected, "--"],
        ):
            result = subprocess.run(
                ["git", "-C", str(root), *args],
                text=True,
                capture_output=True,
                check=False,
                timeout=5,
                env={**os.environ, "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"},
            )
            if result.returncode != 0:
                return False
        return True
    except (OSError, subprocess.SubprocessError):
        return False


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
        if not _tracked_checkout_matches(root, expected):
            raise FieldReseedCrossingError(
                f"{name} tracked checkout must exactly match pinned revision {expected}"
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



def offer_field_reseed_assignment(
    admission: dict,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    if (
        admission.get("schema") != "workbench.field-reseed-admission/v0"
        or admission.get("status") != "ADMITTED_NOT_ASSIGNED"
    ):
        raise FieldReseedCrossingError(
            "verified admitted carried intent is required before assignment offer"
        )
    ghot_admission = admission.get("ghot_admission")
    intent = (
        ghot_admission.get("intent")
        if isinstance(ghot_admission, dict)
        else None
    )
    if (
        not isinstance(intent, dict)
        or intent.get("schema") != "ghot.carried-intent/v0"
        or intent.get("status") != "admitted-not-assigned"
    ):
        raise FieldReseedCrossingError("GHoT carried intent is unavailable")

    ghot = _find_pinned(
        repos,
        "GHoT",
        GHOT_REVISION,
        "ghot/carried_intent_assignment.py",
    )
    ghot_home = Path(state_dir) / "field-reseed-ghot"
    offered = _run_json(
        ["python3", str(ghot / "ghot" / "carried_intent_assignment.py")],
        ghot,
        {
            "action": "offer",
            "intent_id": intent.get("intent_id"),
            "timeout": 0.5,
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Carried Intent Assignment",
    )
    if (
        offered.get("schema")
        != "ghot.carried-intent-assignment-offer/v0"
        or offered.get("intent_id") != intent.get("intent_id")
        or not isinstance(offered.get("offer_id"), str)
        or not isinstance(offered.get("bodies"), list)
    ):
        raise FieldReseedCrossingError("GHoT assignment offer is invalid")
    if "selected" in offered or '"score"' in _canonical(offered):
        raise FieldReseedCrossingError(
            "GHoT assignment offer silently ranked or selected a receiver"
        )

    return {
        "schema": "workbench.field-reseed-assignment-offer/v0",
        "field_return_id": admission.get("field_return_id"),
        "reseed_id": admission.get("reseed_id"),
        "intent_id": intent.get("intent_id"),
        "status": "OFFER_READY",
        "semantic_effect": "none",
        "ghot_offer": offered,
        "pins": {"ghot": GHOT_REVISION},
        "laws": [
            "ADMISSION != ASSIGNMENT",
            "OFFER != ASSIGNMENT",
            "BODY AVAILABILITY != SELECTION",
            "NO SCORE != NO INFORMATION",
        ],
    }


def assign_field_reseed_intent(
    admission: dict,
    assignment_offer: dict,
    selected_node_id: str,
    capability: str,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    if (
        admission.get("schema") != "workbench.field-reseed-admission/v0"
        or admission.get("status") != "ADMITTED_NOT_ASSIGNED"
    ):
        raise FieldReseedCrossingError(
            "verified admitted carried intent is required before assignment"
        )
    if (
        assignment_offer.get("schema")
        != "workbench.field-reseed-assignment-offer/v0"
        or assignment_offer.get("status") != "OFFER_READY"
        or assignment_offer.get("semantic_effect") != "none"
    ):
        raise FieldReseedCrossingError(
            "verified GHoT assignment offer is required before assignment"
        )

    ghot_admission = admission.get("ghot_admission")
    intent = (
        ghot_admission.get("intent")
        if isinstance(ghot_admission, dict)
        else None
    )
    if not isinstance(intent, dict):
        raise FieldReseedCrossingError("GHoT carried intent is unavailable")
    intent_id = intent.get("intent_id")
    if assignment_offer.get("intent_id") != intent_id:
        raise FieldReseedCrossingError(
            "assignment offer is bound to another carried intent"
        )
    ghot_offer = assignment_offer.get("ghot_offer")
    if not isinstance(ghot_offer, dict):
        raise FieldReseedCrossingError("GHoT assignment offer payload is missing")

    ghot = _find_pinned(
        repos,
        "GHoT",
        GHOT_REVISION,
        "ghot/carried_intent_assignment.py",
    )
    ghot_home = Path(state_dir) / "field-reseed-ghot"
    assigned = _run_json(
        ["python3", str(ghot / "ghot" / "carried_intent_assignment.py")],
        ghot,
        {
            "action": "assign",
            "intent_id": intent_id,
            "offer": ghot_offer,
            "selected_node_id": str(selected_node_id),
            "capability": str(capability),
            "selection_source": "workbench-user-explicit",
            "timeout": 0.5,
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Carried Intent Assignment",
    )
    if (
        assigned.get("schema") != "ghot.carried-intent-assignment/v0"
        or assigned.get("intent_id") != intent_id
        or assigned.get("status") != "ASSIGNED_NOT_EXECUTED"
        or assigned.get("semantic_effect") != "assignment-only"
        or assigned.get("selected_node_id") != selected_node_id
        or assigned.get("capability") != capability
    ):
        raise FieldReseedCrossingError(
            "GHoT assignment did not preserve assignment-only boundary"
        )

    return {
        "schema": "workbench.field-reseed-assignment/v0",
        "field_return_id": admission.get("field_return_id"),
        "reseed_id": admission.get("reseed_id"),
        "intent_id": intent_id,
        "status": "ASSIGNED_NOT_EXECUTED",
        "semantic_effect": "receiver-assignment-only",
        "ghot_assignment": assigned,
        "pins": {"ghot": GHOT_REVISION},
        "laws": [
            "OFFER != ASSIGNMENT",
            "ASSIGNMENT != EXECUTION",
            "ASSIGNMENT != TASK",
            "DISPATCH REQUIRES A NEW EXPLICIT CROSSING",
            "RECEIVER CONSEQUENCE != DONOR CONSEQUENCE",
        ],
    }



def dispatch_field_reseed_intent(
    assignment: dict,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    if (
        assignment.get("schema") != "workbench.field-reseed-assignment/v0"
        or assignment.get("status") != "ASSIGNED_NOT_EXECUTED"
        or assignment.get("semantic_effect") != "receiver-assignment-only"
    ):
        raise FieldReseedCrossingError(
            "verified assignment-only receipt is required before dispatch"
        )
    ghot_assignment = assignment.get("ghot_assignment")
    if (
        not isinstance(ghot_assignment, dict)
        or ghot_assignment.get("schema")
        != "ghot.carried-intent-assignment/v0"
        or ghot_assignment.get("status") != "ASSIGNED_NOT_EXECUTED"
    ):
        raise FieldReseedCrossingError("GHoT assignment-only receipt is invalid")
    intent_id = assignment.get("intent_id")
    if ghot_assignment.get("intent_id") != intent_id:
        raise FieldReseedCrossingError(
            "GHoT assignment is bound to another carried intent"
        )

    ghot = _find_pinned(
        repos,
        "GHoT",
        GHOT_REVISION,
        "ghot/carried_intent_dispatch.py",
    )
    ghot_home = Path(state_dir) / "field-reseed-ghot"
    result = _run_json(
        ["python3", str(ghot / "ghot" / "carried_intent_dispatch.py")],
        ghot,
        {
            "action": "dispatch",
            "intent_id": intent_id,
            "dispatch_source": "workbench-user-explicit",
            "timeout": 0.5,
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Carried Intent Dispatch",
        timeout=45.0,
    )
    if (
        result.get("schema") != "ghot.carried-intent-dispatch-result/v0"
        or result.get("intent_id") != intent_id
        or result.get("assignment_id") != ghot_assignment.get("assignment_id")
        or result.get("selected_node_id")
        != ghot_assignment.get("selected_node_id")
        or result.get("capability") != ghot_assignment.get("capability")
        or result.get("status") not in {"EXECUTED", "EXECUTION_ERROR"}
        or result.get("semantic_effect") != "receiver-local-consequence"
    ):
        raise FieldReseedCrossingError(
            "GHoT dispatch did not preserve the assigned execution boundary"
        )
    crossing = result.get("crossing")
    receipt = result.get("signed_receipt")
    execution = result.get("execution")
    if (
        not isinstance(crossing, dict)
        or crossing.get("schema") != "relatte.crossing-envelope/v0"
        or not isinstance(receipt, dict)
        or receipt.get("schema") != "relatte.receipt/v0"
        or receipt.get("crossing_id") != crossing.get("crossing_id")
        or receipt.get("kind") != "EXECUTED"
        or not isinstance(execution, dict)
    ):
        raise FieldReseedCrossingError(
            "GHoT dispatch consequence evidence is incomplete"
        )
    task = execution.get("task")
    raw_receipt = execution.get("receipt")
    if (
        not isinstance(task, dict)
        or not isinstance(raw_receipt, dict)
        or task.get("capability") != ghot_assignment.get("capability")
        or raw_receipt.get("task_id") != task.get("task_id")
        or raw_receipt.get("capability") != ghot_assignment.get("capability")
    ):
        raise FieldReseedCrossingError(
            "GHoT execution evidence changed assigned capability identity"
        )

    return {
        "schema": "workbench.field-reseed-dispatch/v0",
        "field_return_id": assignment.get("field_return_id"),
        "reseed_id": assignment.get("reseed_id"),
        "intent_id": intent_id,
        "assignment_id": ghot_assignment.get("assignment_id"),
        "status": result.get("status"),
        "semantic_effect": "receiver-local-consequence",
        "ghot_dispatch": result,
        "pins": {"ghot": GHOT_REVISION},
        "laws": [
            "ASSIGNMENT != EXECUTION",
            "DISPATCH != SUCCESS",
            "EXECUTION != RECEIPT",
            "RECEIPT != TRUTH",
            "EXECUTOR CONSEQUENCE != DONOR AUTHORITY",
        ],
    }


def read_field_reseed_dispatch_status(
    assignment: dict,
    state_dir: Path,
    repos: list[RepoStatus],
) -> dict:
    ghot_assignment = assignment.get("ghot_assignment")
    if not isinstance(ghot_assignment, dict):
        raise FieldReseedCrossingError("GHoT assignment-only receipt is missing")
    intent_id = assignment.get("intent_id")
    ghot = _find_pinned(
        repos,
        "GHoT",
        GHOT_REVISION,
        "ghot/carried_intent_dispatch.py",
    )
    ghot_home = Path(state_dir) / "field-reseed-ghot"
    status = _run_json(
        ["python3", str(ghot / "ghot" / "carried_intent_dispatch.py")],
        ghot,
        {
            "action": "status",
            "intent_id": intent_id,
        },
        {**os.environ, "LC_ALL": "C", "GHOT_HOME": str(ghot_home)},
        "GHoT Carried Intent Dispatch Status",
    )
    if (
        status.get("schema") != "ghot.carried-intent-dispatch-status/v0"
        or status.get("intent_id") != intent_id
        or status.get("assignment_id") != ghot_assignment.get("assignment_id")
    ):
        raise FieldReseedCrossingError("GHoT dispatch status is invalid")
    return {
        "schema": "workbench.field-reseed-dispatch/v0",
        "field_return_id": assignment.get("field_return_id"),
        "reseed_id": assignment.get("reseed_id"),
        "intent_id": intent_id,
        "assignment_id": ghot_assignment.get("assignment_id"),
        "status": status.get("status"),
        "semantic_effect": (
            "unknown"
            if status.get("status") == "DISPATCH_OUTCOME_UNKNOWN"
            else "none"
            if status.get("status") == "ASSIGNED_NOT_EXECUTED"
            else "receiver-local-consequence"
        ),
        "ghot_dispatch_status": status,
        "pins": {"ghot": GHOT_REVISION},
        "laws": [
            "STATUS != AUTHORITY",
            "AMBIGUOUS OUTCOME != SAFE RETRY",
            "ASSIGNMENT != EXECUTION",
        ],
    }
