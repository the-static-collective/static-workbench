from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from .repos import RepoStatus


CREATIVE_CAPABILITY = "creative.toaster.witness-sigil"
TOASTER_ADAPTER_ID = "haunted-toaster.witness-sigil"


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


def _find_toaster_manifest(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        root = Path(repo.path)
        manifest = root / "integrations" / "ghot" / "adapter-manifest.json"
        if not manifest.is_file():
            continue
        try:
            value = json.loads(manifest.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if (
            value.get("schema") == "ghot.external-adapter-manifest/v0"
            and value.get("adapter_id") == TOASTER_ADAPTER_ID
        ):
            return manifest
    raise GHotApertureError(
        "A local Haunted Toaster checkout with its GHoT adapter manifest is required."
    )


def _bridge_env(repos: list[RepoStatus], state_dir: Path) -> dict[str, str]:
    manifest = _find_toaster_manifest(repos)
    ghot_home = Path(state_dir) / "doorhouse-ghot"
    ghot_home.mkdir(parents=True, exist_ok=True)
    return {
        **os.environ,
        "LC_ALL": "C",
        "GHOT_HOME": str(ghot_home),
        "GHOT_ADAPTER_MANIFESTS": str(manifest),
    }


def _run_bridge(
    root: Path,
    request: dict,
    repos: list[RepoStatus],
    state_dir: Path,
    timeout: float = 20.0,
) -> dict:
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
            env=_bridge_env(repos, state_dir),
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
    state_dir: Path,
) -> dict:
    if relatte_witness.get("status") != "RECEIVED_THEN_HELD":
        raise GHotApertureError("reLATTE HOLD witness is required before GHoT discovery")
    if relatte_witness.get("semantic_effect") != "none":
        raise GHotApertureError("reLATTE witness has an unexpected semantic effect")

    root = _find_ghot(repos)
    offer = _run_bridge(
        root,
        {
            "action": "offer",
            "capability": CREATIVE_CAPABILITY,
            "timeout": 0.5,
        },
        repos,
        state_dir,
    )
    if offer.get("kind") != "ghot.body-choice.offer" or offer.get("version") != "0":
        raise GHotApertureError("unexpected GHoT body-choice offer")
    if offer.get("capability") != CREATIVE_CAPABILITY:
        raise GHotApertureError("GHoT offered the wrong capability")
    if "selected" in offer:
        raise GHotApertureError("GHoT body offer selected a body before user assignment")
    candidates = offer.get("candidates")
    if not isinstance(candidates, list):
        raise GHotApertureError("GHoT body offer has no candidate list")
    return offer


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _materialize_toaster_artifact(
    donor: dict,
    state_dir: Path,
    receipt_id: str,
) -> dict:
    artifact = donor.get("artifact")
    toaster_receipt = donor.get("receipt")
    if not isinstance(artifact, dict) or not isinstance(toaster_receipt, dict):
        raise GHotApertureError("Haunted Toaster adapter result is incomplete")

    svg_text = artifact.get("svg_text")
    recipe_text = artifact.get("recipe_text")
    receipt_text = artifact.get("receipt_text")
    if not all(isinstance(item, str) for item in (svg_text, recipe_text, receipt_text)):
        raise GHotApertureError("Haunted Toaster did not return portable artifact bytes")

    expected = {
        "svg": artifact.get("svg_sha256"),
        "recipe": artifact.get("recipe_sha256"),
        "receipt": artifact.get("receipt_sha256"),
    }
    actual = {
        "svg": _sha256_text(svg_text),
        "recipe": _sha256_text(recipe_text),
        "receipt": _sha256_text(receipt_text),
    }
    if expected != actual:
        raise GHotApertureError("Haunted Toaster artifact hashes changed in transit")

    target = Path(state_dir) / "doorhouse-creative" / receipt_id
    target.mkdir(parents=True, exist_ok=True)
    svg_path = target / "witness.sigil.svg"
    recipe_path = target / "witness.recipe.json"
    toaster_receipt_path = target / "witness.toaster-receipt.json"
    svg_path.write_text(svg_text, encoding="utf-8")
    recipe_path.write_text(recipe_text, encoding="utf-8")
    toaster_receipt_path.write_text(receipt_text, encoding="utf-8")

    return {
        "kind": "workbench.materialized-toaster-artifact/v0",
        "svg_path": str(svg_path),
        "svg_sha256": actual["svg"],
        "recipe_path": str(recipe_path),
        "recipe_sha256": actual["recipe"],
        "toaster_receipt_path": str(toaster_receipt_path),
        "toaster_receipt_sha256": actual["receipt"],
        "instrument": toaster_receipt.get("instrument"),
        "source_digest_sha256": toaster_receipt.get("source_digest_sha256"),
    }


def assign_ghot_body(
    receipt: dict,
    relatte_witness: dict,
    offer: dict,
    selected_node_id: str,
    repos: list[RepoStatus],
    state_dir: Path,
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
    result = _run_bridge(
        root,
        {
            "action": "assign",
            "offer": offer,
            "selected_node_id": selected_node_id,
            "selection_source": "doorhouse-user-explicit",
            "timeout": 0.5,
            "payload": {
                "digest": artifact_sha,
                "basename": f"doorhouse-{receipt.get('id')}",
            },
        },
        repos,
        state_dir,
    )

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
    if ghot_receipt.get("capability") != CREATIVE_CAPABILITY:
        raise GHotApertureError("GHoT receipt names the wrong capability")
    if ghot_receipt.get("status") != "ok" or result.get("status") != "ok":
        raise GHotApertureError(
            f"GHoT execution failed: {ghot_receipt.get('error') or result.get('status')}"
        )

    wrapped = ghot_receipt.get("output")
    if not isinstance(wrapped, dict):
        raise GHotApertureError("GHoT external adapter output is missing")
    if (
        wrapped.get("kind") != "ghot.external-adapter.result"
        or wrapped.get("adapter_id") != TOASTER_ADAPTER_ID
        or wrapped.get("capability") != CREATIVE_CAPABILITY
    ):
        raise GHotApertureError("GHoT returned the wrong external adapter result")
    donor = wrapped.get("result")
    if not isinstance(donor, dict):
        raise GHotApertureError("Haunted Toaster donor result is missing")
    if (
        donor.get("kind") != "haunted-toaster.ghot-adapter-result"
        or donor.get("capability") != CREATIVE_CAPABILITY
        or donor.get("status") != "ok"
    ):
        raise GHotApertureError("Haunted Toaster donor result is invalid")

    materialized = _materialize_toaster_artifact(
        donor,
        Path(state_dir),
        str(receipt.get("id")),
    )
    if materialized["source_digest_sha256"] != artifact_sha:
        raise GHotApertureError("Haunted Toaster projected a different source digest")

    result["workbench_materialized"] = materialized
    return result
