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


class DogramListenerError(RuntimeError):
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


def dogram_listener_delta_available(repos: list[RepoStatus]) -> dict:
    for repo in repos:
        if repo.name.casefold() != "dogram":
            continue
        script = Path(repo.path) / "scripts" / "listener_delta.py"
        return {
            "checkout_present": True,
            "available": script.is_file(),
            "repo_head": repo.head,
            "repo_branch": repo.branch,
            "capability": "listener-delta-001" if script.is_file() else None,
        }
    return {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }


def _find_listener_dogram(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        if repo.name.casefold() == "dogram":
            root = Path(repo.path)
            script = root / "scripts" / "listener_delta.py"
            if not script.is_file():
                raise DogramListenerError(
                    "Dogram checkout lacks LISTENER-DELTA-001"
                )
            return root
    raise DogramListenerError(
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



def run_dogram_listener_delta(
    parent_responses: list[dict],
    child_responses: list[dict],
    reentry: dict,
    generation_delta: dict,
    repos: list[RepoStatus],
    state_dir: Path,
    receipt_id: str,
) -> dict:
    root = _find_listener_dogram(repos)
    if (
        not isinstance(reentry, dict)
        or reentry.get("schema") != "workbench.phonograph-reentry/v0"
        or reentry.get("status") != "admitted-as-audio-specimen"
    ):
        raise DogramListenerError("Phonograph re-entry witness is required")
    if (
        not isinstance(generation_delta, dict)
        or generation_delta.get("schema")
            != "workbench.dogram-generation-delta/v0"
        or generation_delta.get("status") != "measured"
    ):
        raise DogramListenerError(
            "GENERATION-DELTA-001 receipt is required before listener delta"
        )

    parent_id = reentry.get("parent_window_id")
    child_id = reentry.get("child_window_id")
    proposal_receipt_hash = reentry.get("proposal_receipt_hash")
    generation_receipt_hash = generation_delta.get("dogram_receipt_hash")
    if (
        not isinstance(parent_id, str)
        or not isinstance(child_id, str)
        or parent_id == child_id
        or generation_delta.get("parent_window_id") != parent_id
        or generation_delta.get("child_window_id") != child_id
        or generation_delta.get("proposal_receipt_hash")
            != proposal_receipt_hash
        or not isinstance(proposal_receipt_hash, str)
        or not proposal_receipt_hash.startswith("sha256:")
        or not isinstance(generation_receipt_hash, str)
        or not generation_receipt_hash.startswith("sha256:")
    ):
        raise DogramListenerError(
            "listener delta lineage is not bound to the measured generation"
        )

    request = {
        "schema": "dogram.listener-delta-request/v0",
        "transform": {
            "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
            "human_action": "explicit-admit",
            "parent_window_id": parent_id,
            "child_window_id": child_id,
            "proposal_receipt_hash": proposal_receipt_hash,
            "generation_delta_receipt_hash": generation_receipt_hash,
        },
        "parent_responses": parent_responses,
        "child_responses": child_responses,
    }

    try:
        completed = subprocess.run(
            [sys.executable, "-m", "scripts.listener_delta"],
            cwd=root,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=60.0,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise DogramListenerError(
            f"Dogram LISTENER-DELTA-001 could not run: {exc}"
        ) from exc

    if completed.returncode != 0:
        raise DogramListenerError(
            "Dogram LISTENER-DELTA-001 refused the transform: "
            + (completed.stderr.strip() or "unknown error")
        )
    try:
        receipt = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise DogramListenerError(
            "Dogram LISTENER-DELTA-001 returned invalid JSON"
        ) from exc

    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != "dogram.listener-delta-receipt/v0"
        or receipt.get("specimen") != "LISTENER-DELTA-001"
        or receipt.get("status") != "OK"
    ):
        raise DogramListenerError("unexpected Dogram listener-delta receipt")

    transform = receipt.get("transform")
    cohort = receipt.get("cohort")
    if (
        not isinstance(transform, dict)
        or transform.get("parent_window_id") != parent_id
        or transform.get("child_window_id") != child_id
        or transform.get("proposal_receipt_hash")
            != proposal_receipt_hash
        or transform.get("generation_delta_receipt_hash")
            != generation_receipt_hash
        or not isinstance(cohort, dict)
        or cohort.get("classification") not in {
            "MEASURED_RESPONSE_CHANGE",
            "NO_MEASURED_RESPONSE_CHANGE",
        }
    ):
        raise DogramListenerError(
            "Dogram listener receipt changed lineage or classification"
        )

    expected_parent = {
        item.get("listener", {}).get("id"): item.get("first_response_id")
        for item in parent_responses
        if isinstance(item, dict)
    }
    expected_child = {
        item.get("listener", {}).get("id"): item.get("first_response_id")
        for item in child_responses
        if isinstance(item, dict)
    }
    listeners = receipt.get("listeners")
    if (
        not isinstance(listeners, dict)
        or set(listeners) != set(expected_parent)
        or set(listeners) != set(expected_child)
    ):
        raise DogramListenerError(
            "Dogram listener receipt changed listener identity set"
        )
    for listener_id, measured in listeners.items():
        if (
            not isinstance(measured, dict)
            or measured.get("parent", {}).get("first_response_id")
                != expected_parent[listener_id]
            or measured.get("child", {}).get("first_response_id")
                != expected_child[listener_id]
        ):
            raise DogramListenerError(
                "Dogram listener receipt changed sealed response identity"
            )

    required_laws = {
        "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
        "RESPONSE DELTA != PERSON DELTA",
        "RESPONSE DELTA != CAUSAL EFFECT",
        "SIGNAL DELTA != LISTENER DELTA",
        "LEXICAL OVERLAP != SEMANTIC AGREEMENT",
        "DELTA != VALUE",
        "RESIDUAL != FAILURE",
    }
    if not required_laws.issubset(set(receipt.get("laws") or [])):
        raise DogramListenerError("Dogram listener receipt omitted required laws")

    receipt_hash = receipt.get("receipt_hash")
    if not isinstance(receipt_hash, str) or not receipt_hash.startswith("sha256:"):
        raise DogramListenerError("Dogram listener receipt identity is missing")

    slug = hashlib.sha256(child_id.encode("utf-8")).hexdigest()[:24]
    target = Path(state_dir) / "doorhouse-dogram" / receipt_id / slug
    target.mkdir(parents=True, exist_ok=True)
    receipt_path = target / "listener-delta.json"
    payload = json.dumps(
        receipt,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"
    if receipt_path.exists():
        if receipt_path.read_text(encoding="utf-8") != payload:
            raise DogramListenerError(
                "existing Dogram listener receipt conflicts with measured transform"
            )
    else:
        receipt_path.write_text(payload, encoding="utf-8")

    return {
        "schema": "workbench.dogram-listener-delta/v0",
        "status": "measured",
        "parent_window_id": parent_id,
        "child_window_id": child_id,
        "proposal_receipt_hash": proposal_receipt_hash,
        "generation_delta_receipt_hash": generation_receipt_hash,
        "dogram_receipt_hash": receipt_hash,
        "classification": cohort["classification"],
        "listener_count": cohort.get("listener_count"),
        "changed_listener_count": cohort.get("changed_listener_count"),
        "shared_changed_axes": list(cohort.get("shared_changed_axes") or []),
        "union_changed_axes": list(cohort.get("union_changed_axes") or []),
        "shared_appeared_tokens": list(
            cohort.get("shared_appeared_tokens") or []
        ),
        "shared_disappeared_tokens": list(
            cohort.get("shared_disappeared_tokens") or []
        ),
        "shared_appeared_observations": list(
            cohort.get("shared_appeared_observations") or []
        ),
        "residuals": list(receipt.get("residuals") or []),
        "dogram_receipt": receipt,
        "receipt_path": str(receipt_path),
        "laws": [
            "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
            "RESPONSE DELTA != PERSON DELTA",
            "RESPONSE DELTA != CAUSAL EFFECT",
            "SIGNAL DELTA != LISTENER DELTA",
            "LEXICAL OVERLAP != SEMANTIC AGREEMENT",
            "DELTA != VALUE",
            "RESIDUAL != FAILURE",
            "MEASUREMENT != ADMISSION",
        ],
    }
