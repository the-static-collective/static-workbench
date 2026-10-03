from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

from .repos import RepoStatus


class GHotApertureError(RuntimeError):
    pass


def _find_ghot(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        if repo.name.lower() == "ghot":
            root = Path(repo.path)
            bridge = root / "ghot" / "body_choice.py"
            if bridge.is_file():
                return root
    raise GHotApertureError(
        "A local GHoT checkout with ghot/body_choice.py is required."
    )


def _run_bridge(root: Path, request: dict, timeout: float = 12.0) -> dict:
    bridge = root / "ghot" / "body_choice.py"
    try:
        completed = subprocess.run(
            ["python3", str(bridge)],
            cwd=root,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise GHotApertureError(f"GHoT body-choice bridge could not run: {exc}") from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise GHotApertureError(
            f"GHoT refused the request: {detail or 'unknown error'}"
        )
    try:
        value = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise GHotApertureError("GHoT body-choice bridge returned invalid JSON") from exc
    if not isinstance(value, dict):
        raise GHotApertureError("GHoT body-choice bridge returned a non-object")
    return value


def discover_ghot_bodies(
    receipt: dict,
    relatte_witness: dict,
    repos: list[RepoStatus],
) -> dict:
    if relatte_witness.get("status") != "RECEIVED_THEN_HELD":
        raise GHotApertureError("reLATTE HOLD witness is required before GHoT discovery")
    if relatte_witness.get("semantic_effect") != "none":
        raise GHotApertureError("reLATTE witness has an unexpected semantic effect")

    root = _find_ghot(repos)
    offer = _run_bridge(root, {
        "action": "offer",
        "capability": "system.hash",
        "timeout": 0.5,
    })
    if offer.get("kind") != "ghot.body-choice.offer" or offer.get("version") != "0":
        raise GHotApertureError("unexpected GHoT body-choice offer")
    if offer.get("capability") != "system.hash":
        raise GHotApertureError("GHoT offered the wrong capability")
    if "selected" in offer:
        raise GHotApertureError("GHoT body offer selected a body before user assignment")
    candidates = offer.get("candidates")
    if not isinstance(candidates, list):
        raise GHotApertureError("GHoT body offer has no candidate list")
    return offer


def assign_ghot_body(
    receipt: dict,
    relatte_witness: dict,
    offer: dict,
    selected_node_id: str,
    repos: list[RepoStatus],
) -> dict:
    if relatte_witness.get("status") != "RECEIVED_THEN_HELD":
        raise GHotApertureError("reLATTE HOLD witness is required before GHoT assignment")
    if not isinstance(selected_node_id, str) or not selected_node_id:
        raise GHotApertureError("selected GHoT body id is required")

    artifact = receipt.get("snapshot", {}).get("artifact")
    artifact_sha = receipt.get("snapshot", {}).get("artifact_sha256")
    if not isinstance(artifact, dict) or not isinstance(artifact_sha, str):
        raise GHotApertureError("local crossing artifact is unavailable")

    root = _find_ghot(repos)
    result = _run_bridge(root, {
        "action": "assign",
        "offer": offer,
        "selected_node_id": selected_node_id,
        "selection_source": "doorhouse-user-explicit",
        "timeout": 0.5,
        "payload": {
            "kind": "workbench.ghot-hash-input/v0",
            "local_receipt_id": receipt.get("id"),
            "local_receipt_sha256": receipt.get("sha256"),
            "local_artifact_sha256": artifact_sha,
            "relatte_crossing_id": relatte_witness.get("crossing_id"),
            "relatte_hold_receipt_id": relatte_witness.get("hold_receipt_id"),
            "artifact": artifact,
        },
    })

    if result.get("kind") != "ghot.body-choice.result" or result.get("version") != "0":
        raise GHotApertureError("unexpected GHoT assignment result")
    assignment = result.get("assignment")
    execution = result.get("execution")
    if not isinstance(assignment, dict) or not isinstance(execution, dict):
        raise GHotApertureError("GHoT assignment result is incomplete")
    if assignment.get("offer_id") != offer.get("offer_id"):
        raise GHotApertureError("GHoT assignment changed the body offer")
    if assignment.get("selected_node_id") != selected_node_id:
        raise GHotApertureError("GHoT executed on a different selected body")
    ghot_receipt = execution.get("receipt")
    if not isinstance(ghot_receipt, dict):
        raise GHotApertureError("GHoT execution receipt is missing")
    if ghot_receipt.get("executor_node_id") != selected_node_id:
        raise GHotApertureError("GHoT receipt names a different executor body")
    if ghot_receipt.get("capability") != "system.hash":
        raise GHotApertureError("GHoT receipt names the wrong capability")
    if ghot_receipt.get("status") != "ok" or result.get("status") != "ok":
        raise GHotApertureError(
            f"GHoT execution failed: {ghot_receipt.get('error') or result.get('status')}"
        )
    return result
