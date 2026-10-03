"""Bounded Dogram GENERATION-DELTA-001 aperture for admitted audio descendants."""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

from .doorhouse_autodisco import AutodiscoApertureError, inflate_audio_window
from .repos import RepoStatus


class DogramGenerationError(RuntimeError):
    pass


def _find_dogram(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        if repo.name.casefold() == "dogram":
            root = Path(repo.path)
            script = root / "scripts" / "generation_delta.py"
            if not script.is_file():
                raise DogramGenerationError(
                    "Dogram checkout lacks GENERATION-DELTA-001"
                )
            return root
    raise DogramGenerationError(
        "Dogram checkout is not available under configured roots"
    )


def dogram_generation_delta_available(repos: list[RepoStatus]) -> dict:
    for repo in repos:
        if repo.name.casefold() != "dogram":
            continue
        script = Path(repo.path) / "scripts" / "generation_delta.py"
        return {
            "checkout_present": True,
            "available": script.is_file(),
            "repo_head": repo.head,
            "repo_branch": repo.branch,
            "capability": "generation-delta-001" if script.is_file() else None,
        }
    return {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }


def _window_packet(materialized: dict) -> dict:
    try:
        window = inflate_audio_window(materialized)
    except AutodiscoApertureError as exc:
        raise DogramGenerationError(str(exc)) from exc
    canonical = window.get("canonical_audio")
    if not isinstance(canonical, dict):
        raise DogramGenerationError("audio window canonical carrier is missing")
    return {
        "window_id": window.get("window_id"),
        "audio_sha256": canonical.get("sha256"),
        "media_type": canonical.get("media_type"),
        "base64": canonical.get("base64"),
    }


def run_dogram_generation_delta(
    parent_window: dict,
    child_window: dict,
    reentry: dict,
    repos: list[RepoStatus],
    state_dir: Path,
    receipt_id: str,
) -> dict:
    root = _find_dogram(repos)
    if (
        not isinstance(reentry, dict)
        or reentry.get("schema") != "workbench.phonograph-reentry/v0"
        or reentry.get("status") != "admitted-as-audio-specimen"
    ):
        raise DogramGenerationError("Phonograph re-entry witness is required")

    parent_id = parent_window.get("window_id")
    child_id = child_window.get("window_id")
    if (
        reentry.get("parent_window_id") != parent_id
        or reentry.get("child_window_id") != child_id
    ):
        raise DogramGenerationError(
            "Dogram generation relation does not bind the supplied windows"
        )
    proposal_receipt_hash = reentry.get("proposal_receipt_hash")
    audition_sha256 = reentry.get("audition_sha256")
    if (
        not isinstance(proposal_receipt_hash, str)
        or not proposal_receipt_hash.startswith("sha256:")
        or not isinstance(audition_sha256, str)
        or not audition_sha256.startswith("sha256:")
    ):
        raise DogramGenerationError("Phonograph re-entry lineage is incomplete")

    request = {
        "schema": "dogram.generation-delta-request/v0",
        "transform": {
            "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
            "human_action": "explicit-admit",
            "parent_window_id": parent_id,
            "child_window_id": child_id,
            "proposal_receipt_hash": proposal_receipt_hash,
            "audition_sha256": audition_sha256,
        },
        "parent": _window_packet(parent_window),
        "child": _window_packet(child_window),
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.generation_delta"],
            cwd=root,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=60.0,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DogramGenerationError(
            f"Dogram GENERATION-DELTA-001 could not run: {exc}"
        ) from exc

    if completed.returncode != 0:
        raise DogramGenerationError(
            "Dogram GENERATION-DELTA-001 refused the transform: "
            + (completed.stderr.strip() or "unknown error")
        )
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise DogramGenerationError(
            "Dogram GENERATION-DELTA-001 returned invalid JSON"
        ) from exc

    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != "dogram.generation-delta-receipt/v0"
        or receipt.get("specimen") != "GENERATION-DELTA-001"
        or receipt.get("status") != "OK"
    ):
        raise DogramGenerationError("unexpected Dogram generation-delta receipt")

    transform = receipt.get("transform")
    delta = receipt.get("delta")
    if (
        not isinstance(transform, dict)
        or transform.get("parent_window_id") != parent_id
        or transform.get("child_window_id") != child_id
        or transform.get("proposal_receipt_hash") != proposal_receipt_hash
        or not isinstance(delta, dict)
        or delta.get("classification") not in {
            "MEASURED_CHANGE",
            "NO_MEASURED_CHANGE",
        }
    ):
        raise DogramGenerationError(
            "Dogram receipt changed generation identity or classification"
        )

    required_laws = {
        "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
        "DELTA != VALUE",
        "MEASURED CHANGE != MUSICAL MEANING",
        "RESIDUAL != FAILURE",
        "DESCENDANT != PARENT",
    }
    if not required_laws.issubset(set(receipt.get("laws") or [])):
        raise DogramGenerationError("Dogram receipt omitted required laws")

    receipt_hash = receipt.get("receipt_hash")
    if not isinstance(receipt_hash, str) or not receipt_hash.startswith("sha256:"):
        raise DogramGenerationError("Dogram receipt identity is missing")

    slug = hashlib.sha256(child_id.encode("utf-8")).hexdigest()[:24]
    target = Path(state_dir) / "doorhouse-dogram" / receipt_id / slug
    target.mkdir(parents=True, exist_ok=True)
    receipt_path = target / "generation-delta.json"
    payload = json.dumps(
        receipt,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"
    if receipt_path.exists():
        if receipt_path.read_text(encoding="utf-8") != payload:
            raise DogramGenerationError(
                "existing Dogram generation receipt conflicts with measured transform"
            )
    else:
        receipt_path.write_text(payload, encoding="utf-8")

    return {
        "schema": "workbench.dogram-generation-delta/v0",
        "status": "measured",
        "parent_window_id": parent_id,
        "child_window_id": child_id,
        "proposal_receipt_hash": proposal_receipt_hash,
        "dogram_receipt_hash": receipt_hash,
        "classification": delta["classification"],
        "changed_axes": list(delta.get("changed_axes") or []),
        "unchanged_axes": list(delta.get("unchanged_axes") or []),
        "delta": delta,
        "residuals": list(receipt.get("residuals") or []),
        "dogram_receipt": receipt,
        "receipt_path": str(receipt_path),
        "laws": [
            "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
            "DELTA != VALUE",
            "MEASURED CHANGE != MUSICAL MEANING",
            "RESIDUAL != FAILURE",
            "SIGNAL DELTA != LISTENER DELTA",
            "MEASUREMENT != ADMISSION",
        ],
    }
