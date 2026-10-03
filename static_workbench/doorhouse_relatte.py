from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .repos import RepoStatus


class RelatteApertureError(RuntimeError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _find_relatte(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        if repo.name.lower() == "relatte":
            root = Path(repo.path)
            bridge = root / "scripts" / "opaque-roundtrip.ts"
            if bridge.is_file():
                return root
    raise RelatteApertureError(
        "A local reLATTE checkout with scripts/opaque-roundtrip.ts is required."
    )


def build_relatte_request(receipt: dict, state_dir: Path) -> dict:
    snapshot = receipt.get("snapshot")
    if not isinstance(snapshot, dict):
        raise RelatteApertureError("local receipt snapshot is missing")
    artifact = snapshot.get("artifact")
    world = snapshot.get("world")
    envelope = snapshot.get("envelope")
    if not isinstance(artifact, dict) or not isinstance(world, dict) or not isinstance(envelope, dict):
        raise RelatteApertureError("local receipt does not contain a complete crossing snapshot")

    artifact_sha = snapshot.get("artifact_sha256")
    if not isinstance(artifact_sha, str) or len(artifact_sha) != 64:
        raise RelatteApertureError("local artifact digest is unavailable")

    receipt_id = receipt.get("id")
    receipt_sha = receipt.get("sha256")
    if not isinstance(receipt_id, str) or len(receipt_id) != 32:
        raise RelatteApertureError("invalid local receipt id")
    if not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
        raise RelatteApertureError("invalid local receipt digest")

    created = _now()
    base = Path(state_dir)
    return {
        "schema": "relatte.opaque-roundtrip-request/v0",
        "spec": {
            "schema": "relatte.opaque-organ-spec/v0",
            "family_ref": "organ:static-workbench/house-remembers-doors",
            "donor_contract_ref": (
                "github:the-static-collective/static-workbench"
                "#docs/HOUSE-REMEMBERS-DOORS-001.md"
            ),
            "artifact_kind": "doorhouse-selected-crossing-artifact",
            "source_world": "world:static-workbench:doorhouse",
            "source_particular": f"particular:doorhouse:receipt:{receipt_id}",
            "source_history_head": f"sha256:{receipt_sha}",
            "payload_refs": [{
                "address": f"sha256:{artifact_sha}",
                "role": "local-crossing-artifact",
                "media_type": "application/json",
            }],
            "donor_claims": {
                "local_receipt_id": receipt_id,
                "local_receipt_sha256": receipt_sha,
                "proposal_selected_locally": True,
                "local_crossing_completed": True,
                "donor_authority_transferred": False,
                "world_before": world.get("before"),
                "world_after": world.get("after"),
                "local_authority": envelope.get("authority"),
            },
            "requested_effect": {
                "kind": "candidate-crossing-witness-ingress",
                "authority": "receiver-local",
            },
            "return_address": f"workbench:doorhouse:receipt:{receipt_id}",
            "created_at": created,
        },
        "receiver_root": str(base / "doorhouse-relatte-receiver"),
        "receiver": {
            "world_id": "world:doorhouse-relatte-hold",
            "receiver_particular": "particular:doorhouse-relatte-hold",
            "contract_ref": "contract:doorhouse-relatte-hold/v0",
        },
        "bundle_path": str(base / "doorhouse-relatte-bundles" / f"{receipt_id}.json"),
        "result_path": str(base / "doorhouse-relatte-results" / f"{receipt_id}.json"),
        "disposition": "HOLD",
        "transport_created_at": _now(),
        "received_at": _now(),
        "disposed_at": _now(),
        "route_note": "Static Workbench DoorHouse -> generic reLATTE local receiver",
    }


def run_relatte_aperture(
    receipt: dict,
    state_dir: Path,
    repos: list[RepoStatus],
    timeout: float = 20.0,
) -> dict:
    relatte = _find_relatte(repos)
    request = build_relatte_request(receipt, state_dir)
    bridge = relatte / "scripts" / "opaque-roundtrip.ts"

    try:
        completed = subprocess.run(
            ["node", "--experimental-strip-types", str(bridge)],
            cwd=relatte,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise RelatteApertureError(f"reLATTE bridge could not run: {exc}") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise RelatteApertureError(
            f"reLATTE bridge refused the crossing: {detail or 'unknown error'}"
        )

    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RelatteApertureError("reLATTE bridge returned invalid JSON") from exc

    if result.get("schema") != "relatte.opaque-roundtrip-result/v0":
        raise RelatteApertureError("unexpected reLATTE result schema")
    crossing = result.get("crossing")
    received = result.get("receive_receipt")
    disposition = result.get("disposition_receipt")
    if not isinstance(crossing, dict) or not isinstance(received, dict) or not isinstance(disposition, dict):
        raise RelatteApertureError("reLATTE result is incomplete")
    if crossing.get("crossing_id") != received.get("crossing_id"):
        raise RelatteApertureError("reLATTE RECEIVE receipt does not match crossing")
    if crossing.get("crossing_id") != disposition.get("crossing_id"):
        raise RelatteApertureError("reLATTE disposition receipt does not match crossing")
    if received.get("kind") != "RECEIVED" or received.get("semantic_effect") != "none":
        raise RelatteApertureError("reLATTE RECEIVE boundary was not preserved")
    if disposition.get("kind") != "R3_HOLD" or disposition.get("semantic_effect") != "none":
        raise RelatteApertureError("reLATTE crossing was not returned in HOLD")

    adapter = crossing.get("extensions", {}).get("organ_adapter", {})
    if adapter.get("family_ref") != "organ:static-workbench/house-remembers-doors":
        raise RelatteApertureError("reLATTE crossing changed donor family identity")

    return result
