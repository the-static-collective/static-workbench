"""HOUSE-FLYWHEEL-003: deterministic, inert two-artifact composition preview.

A human explicitly selects two exact references. This module only inspects
Workbench-owned, self-reported records and constructs a frozen question card.
It does NOT establish compatibility, gain, authorization, or project effects.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .capability_returns import CapabilityReturnLedger

SELECTION_KEYS = frozenset({"return_id", "local_digest", "owner", "artifact_ref"})
REQUEST_KEYS = frozenset({"selections", "question"})


def _identity(value: Any, name: str) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 512:
        raise ValueError(f"{name} must be nonblank text at most 512 characters long")
    return value


def preview_composition(ledger: CapabilityReturnLedger, request: dict[str, Any]) -> dict[str, Any]:
    """Freeze one user-supplied, source-distinct pair without promoting a claim."""
    if not isinstance(request, dict) or set(request) != REQUEST_KEYS:
        raise ValueError("expected exactly selections and question")
    selections = request["selections"]
    if not isinstance(selections, list) or len(selections) != 2:
        raise ValueError("select exactly two artifacts")
    question = request["question"]
    if not isinstance(question, str) or len(question) > 512:
        raise ValueError("question must be text of at most 512 characters")
    if not question.strip():
        raise ValueError("supply a concrete question about this proposed composition")

    captured = []
    seen: set[tuple[str, str]] = set()
    for selection in selections:
        if not isinstance(selection, dict) or set(selection) != SELECTION_KEYS:
            raise ValueError("invalid selection fields")
        for key in SELECTION_KEYS:
            _identity(selection[key], key)
        record = ledger.get(selection["return_id"])
        if record is None:
            raise ValueError("selected return is missing; refresh before proposing")
        if record.local_digest != selection["local_digest"]:
            raise ValueError("selected return changed; refresh before proposing")
        matches = [
            artifact for artifact in record.packet["artifacts"]
            if artifact["owner"] == selection["owner"] and artifact["artifact_ref"] == selection["artifact_ref"]
        ]
        if len(matches) != 1:
            raise ValueError("selected artifact is not present in exact reported return")
        key = (selection["owner"], selection["artifact_ref"])
        if key in seen:
            raise ValueError("same project-owned artifact identity selected twice")
        seen.add(key)
        artifact = matches[0]
        captured.append({
            "return_id": record.packet["return_id"],
            "return_digest": record.local_digest,
            "flight_ref": record.packet["flight_ref"],
            "source_owner": record.packet["source_owner"],
            "source_ref": record.packet["source_ref"],
            "owner": artifact["owner"],
            "artifact_ref": artifact["artifact_ref"],
            "kind": artifact["kind"],
            "reported_capability_state": artifact["capability_state"],
            "reported_evidence_refs": list(artifact["evidence_refs"]),
            "reported_effect_state": record.packet["effect_state"],
            "return_nonclaims": list(record.packet["nonclaims"]),
        })

    proposal = {
        "format": "house.capability-loom-proposal/v0",
        "state": "inert_unrun",
        "question": question,
        "inputs": captured,
        "compatibility": "not_evaluated",
        "verification": "not_evaluated",
        "execution": "not_attempted",
        "authorization": "not_evaluated",
        "declared_effects": [],
        "proposed_observables": [
            "Can both exact owner-scoped artifacts be used in one independently authorized fixture?",
            "Which inputs, version pins, permissions, and stop conditions would a real test require?",
            "What reuse, effort, costs, and failures can a later experiment actually measure?",
        ],
        "nonclaims": [
            "Selection establishes interest, not compatibility, source authenticity, human-value rank, or permission.",
            "Reported evidence is not project-native verification; distinct sources and artifacts are not merged.",
            "This preview neither executes nor records a completed flight, and does not authorize descendants.",
        ],
    }
    canonical = json.dumps(proposal, sort_keys=True, ensure_ascii=False, separators=(",", ":"))
    proposal["proposal_digest"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    return proposal
