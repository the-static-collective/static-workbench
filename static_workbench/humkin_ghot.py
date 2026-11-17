"""HUMKIN-GHOT-002: one explicitly approved, local GHoT computation after a native reLATTE HOLD.

The adapter runs owner-native reLATTE verifier and GHoT Python functions, not substitute engines.
It never interprets HOLD as an action grant, and it never gives a guest station remote shell.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

APPROVAL = "HASH_PUBLIC_CATALOG"
MAX_SOURCE_JSON = 65536


class HumkinGhotError(RuntimeError):
    pass


def _run(argv: list[str], cwd: Path, *, data: dict | None = None) -> dict:
    try:
        result = subprocess.run(
            argv, cwd=cwd, input=json.dumps(data) if data is not None else None,
            text=True, capture_output=True, check=False, timeout=45,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise HumkinGhotError(f"Native subprocess unavailable: {type(exc).__name__}") from exc
    if result.returncode:
        raise HumkinGhotError(
            f"Native command failed: {(result.stderr or result.stdout).strip()[:300]}"
        )
    try:
        value = json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise HumkinGhotError("Native command returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise HumkinGhotError("Native command did not return an object")
    return value


def _timestamp(dt: datetime) -> str:
    return dt.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _read_manifest(public_dir: Path) -> dict:
    path = public_dir / "source-manifest.json"
    if not path.is_file() or path.stat().st_size > MAX_SOURCE_JSON:
        raise HumkinGhotError("Missing or oversized original GitHub manifest")
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise HumkinGhotError("Invalid original GitHub manifest")
    return value


def verify_origin(relatte: Path, public_dir: Path) -> tuple[dict, dict]:
    script = relatte / "scripts" / "humkin-gh-relatte-001.mjs"
    if not script.is_file():
        raise HumkinGhotError("Pinned reLATTE native catalog verifier required")
    verified = _run(
        ["node", "--experimental-strip-types", str(script), "verify", str(public_dir)],
        relatte,
    )
    manifest = _read_manifest(public_dir)
    if not (
        verified.get("public_bytes_verified") is True
        and verified.get("signed_receipts_verified") is True
        and verified.get("disposition") == "HOLD"
        and verified.get("receiver_admitted") is False
        and verified.get("source_revision") == manifest.get("revision")
        and verified.get("catalog_count") == 12
    ):
        raise HumkinGhotError("Origin was not verified into HOLD")
    files = manifest.get("files")
    if not isinstance(files, dict) or not isinstance(files.get("tracks.json"), str):
        raise HumkinGhotError("Origin has no verified catalog digest")
    return verified, manifest


def _native_ghot_hash(ghot_repo: Path, payload: str, state_dir: Path) -> dict:
    import importlib

    # Run the original GHoT reference body in this process. No LAN discovery,
    # non-local candidate, arbitrary command or external network is permitted.
    original = os.environ.get("GHOT_HOME")
    home = state_dir / "ghot-home"
    home.mkdir(parents=True, exist_ok=True)
    os.environ["GHOT_HOME"] = str(home.resolve())
    ghot_dir = str((ghot_repo / "ghot").resolve())
    if not (Path(ghot_dir) / "reference_node.py").is_file():
        raise HumkinGhotError("Original GHoT reference body required")
    sys.path.insert(0, ghot_dir)
    try:
        ghot = importlib.import_module("reference_node")
        if Path(ghot.ROOT).resolve() != home.resolve():
            raise HumkinGhotError("GHoT home was not isolated to this run")
        body = ghot.body()
        candidates = [offer for offer in body.get("offers", [])
                      if offer.get("capability") == "system.hash" and offer.get("available") is True]
        if len(candidates) != 1:
            raise HumkinGhotError("Selected local GHoT body does not offer system.hash")
        selected = body.get("node_id")
        if not isinstance(selected, str) or not selected:
            raise HumkinGhotError("Selected GHoT body has no identity")
        task, receipt = ghot.execute(
            "system.hash", payload, requester_node_id="workbench:humkin-github-002",
            constraints={
                "selected_node_id": selected,
                "selection_source": "operator-approved-experiment",
                "remote_shell": False,
                "network": "not-required",
            },
        )
        expected = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        if not (
            task.get("capability") == "system.hash"
            and task.get("input") == payload
            and receipt.get("capability") == "system.hash"
            and receipt.get("task_id") == task.get("task_id")
            and receipt.get("executor_node_id") == selected
            and receipt.get("status") == "ok"
            and receipt.get("output", {}).get("sha256") == expected
            and receipt.get("error") is None
        ):
            raise HumkinGhotError("Native GHoT execution result did not verify")
        return {
            "ghot_task_id": task["task_id"],
            "ghot_receipt_id": receipt["receipt_id"],
            "ghot_output_sha256": expected,
            "ghot_node_selected_locally": True,
            "ghot_receipt_signed": False,
        }
    finally:
        sys.path.remove(ghot_dir)
        if original is None:
            os.environ.pop("GHOT_HOME", None)
        else:
            os.environ["GHOT_HOME"] = original


def execute_catalog_hash(
    relatte: Path, ghot_repo: Path, public_dir: Path, work_dir: Path,
    approval: str | None,
) -> dict:
    if approval != APPROVAL:
        raise HumkinGhotError("Explicit HASH_PUBLIC_CATALOG approval is required")
    if (work_dir / "public" / "ghot-execution.json").exists():
        raise HumkinGhotError("Output already exists; refusing implicit repeat")
    origin, manifest = verify_origin(relatte, public_dir)
    track_hash = manifest["files"]["tracks.json"]
    payload = "humkin-catalog-ghot-v0|" + origin["source_revision"] + "|" + origin["crossing_id"] + "|" + track_hash
    ghot_result = _native_ghot_hash(ghot_repo, payload, work_dir / "private")
    execution = {
        "schema": "workbench.humkin-verified-catalog-hash/v0",
        "source_repository": "the-static-collective/HUMKIN",
        "source_revision": origin["source_revision"],
        "source_crossing_id": origin["crossing_id"],
        "source_hold_receipt_id": origin["hold_receipt_id"],
        "source_catalog_sha256": track_hash,
        "input": payload,
        "capability": "system.hash",
        **ghot_result,
        "execution_host": "ephemeral-github-runner",
        "approval": APPROVAL,
        "radio_gameplay_reward": False,
        "external_effect": False,
    }
    raw = (json.dumps(execution, sort_keys=True, separators=(",", ":")) + "\n").encode()
    execution_sha = hashlib.sha256(raw).hexdigest()
    t0 = datetime.now(timezone.utc)
    stamps = [_timestamp(t0 + timedelta(seconds=i)) for i in range(4)]
    request = {
        "schema": "relatte.opaque-roundtrip-request/v0",
        "spec": {
            "schema": "relatte.opaque-organ-spec/v0",
            "family_ref": "organ:static-workbench/humkin-catalog-ghot-result",
            "donor_contract_ref": "github:the-static-collective/static-workbench#static_workbench/humkin_ghot.py",
            "artifact_kind": "verified-local-ghot-catalog-hash",
            "source_world": "world:static-workbench:humkin-integration",
            "source_particular": "particular:workbench:ghot-execution:sha256:" + execution_sha,
            "source_history_head": "sha256:" + track_hash,
            "payload_refs": [{
                "address": "sha256:" + execution_sha,
                "role": "workbench-verified-execution-record",
                "media_type": "application/json",
            }],
            "donor_claims": {
                "source_crossing_id": origin["crossing_id"],
                "source_hold_receipt_id": origin["hold_receipt_id"],
                "source_revision": origin["source_revision"],
                "ghot_task_id": execution["ghot_task_id"],
                "ghot_receipt_id": execution["ghot_receipt_id"],
                "ghot_receipt_signed": False,
                "ghot_execution_output_sha256": execution["ghot_output_sha256"],
                "operator_approved": True,
                "human_identity_verified": False,
                "gameplay_reward_issued": False,
                "no_external_effect": True,
            },
            "requested_effect": {
                "kind": "candidate-gameplay-discovery",
                "authority": "humkin-owner-local",
            },
            "return_address": "github:the-static-collective/HUMKIN",
            "created_at": stamps[0],
        },
        "receiver_root": str((work_dir / "private" / "return-receiver").resolve()),
        "receiver": {
            "world_id": "world:relatte:humkin-workbench-return-inbox",
            "receiver_particular": "particular:relatte:humkin-ghot-hold",
            "contract_ref": "contract:humkin-ghot-result-hold/v0",
        },
        "bundle_path": str((work_dir / "private" / "return-transport.json").resolve()),
        "result_path": str((work_dir / "private" / "return-result.json").resolve()),
        "disposition": "HOLD",
        "transport_created_at": stamps[1],
        "received_at": stamps[2],
        "disposed_at": stamps[3],
        "route_note": "Workbench owns interpretation; GHoT ran one local system.hash; reLATTE signs result HOLD",
    }
    native = _run(
        ["node", "--experimental-strip-types",
         str(relatte / "scripts" / "opaque-roundtrip.ts")],
        relatte, data=request,
    )
    if not (
        native.get("schema") == "relatte.opaque-roundtrip-result/v0"
        and native.get("receive_receipt", {}).get("kind") == "RECEIVED"
        and native.get("disposition_receipt", {}).get("kind") == "R3_HOLD"
        and native.get("disposition_receipt", {}).get("semantic_effect") == "none"
        and native.get("crossing", {}).get("payload_refs", [{}])[0].get("address") == "sha256:" + execution_sha
    ):
        raise HumkinGhotError("Native reLATTE did not HOLD execution witness")
    destination = work_dir / "public"
    destination.mkdir(parents=True, exist_ok=True)
    (destination / "ghot-execution.json").write_bytes(raw)
    (destination / "relatte-return.json").write_text(
        json.dumps(native, sort_keys=True, indent=2) + "\n", encoding="utf-8"
    )
    return {
        "origin_source": origin["source_revision"],
        "origin_hold": origin["hold_receipt_id"],
        "ghot_receipt": execution["ghot_receipt_id"],
        "ghot_sha256": execution["ghot_output_sha256"],
        "return_hold": native["disposition_receipt"]["receipt_id"],
        "gameplay_reward_issued": False,
    }
