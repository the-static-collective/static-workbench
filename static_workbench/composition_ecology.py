"""COMPOSITION-ECOLOGY-001: inert, deterministic descendants of exact Loom inputs.

Builds on Capability Loom's validated two-artifact preview. The proposals are
design questions, not functioning adapters, compatibility evidence or permission.
No file access, subprocess, network, database writes or untrusted code execution.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .capability_loom import preview_composition
from .capability_returns import CapabilityReturnLedger

FORMAT = "house.composition-ecology/v0"
OPERATORS = ("BRAID", "CROSS", "MUTATE")


def _digest(value: dict[str, Any]) -> str:
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         allow_nan=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _ref(input_: dict[str, Any]) -> dict[str, str]:
    # Return identity is Workbench-local and does not authenticate the source.
    return {
        "return_id": input_["return_id"],
        "return_digest": input_["return_digest"],
        "owner": input_["owner"],
        "artifact_ref": input_["artifact_ref"],
    }


def _pack(input_: dict[str, Any]) -> dict[str, Any]:
    """A descriptive CapabilityPack; no invented I/O types or executable API."""
    return {
        "format": "house.capability-pack/v0",
        "identity": _ref(input_),
        "kind": input_["kind"],
        "source_owner": input_["source_owner"],
        "source_ref": input_["source_ref"],
        "reported_capability_state": input_["reported_capability_state"],
        "reported_evidence_refs": input_["reported_evidence_refs"],
        "input_contract": "unknown",
        "output_contract": "unknown",
        "runtime_adapter": "not_declared",
        "compatibility": "not_evaluated",
        "source_authenticity": "not_verified",
        "authorization": "not_evaluated",
        "nonclaims": list(input_["return_nonclaims"]),
    }


def _candidate(operator: str, loom: dict[str, Any]) -> dict[str, Any]:
    first, second = loom["inputs"]
    parents = [_ref(first), _ref(second)]
    if operator == "BRAID":
        roles = ["sequential_source", "sequential_source"]
        phases = [
            {"action": "inspect_declared_contract", "parents": [0]},
            {"action": "inspect_declared_contract", "parents": [1]},
            {"action": "compare_outputs_without_conflating_sources", "parents": [0, 1]},
        ]
        hypothesis = "Could two independently validated steps be connected in sequence?"
        inheritance = {"parent_0": "identity_only", "parent_1": "identity_only"}
        influence = ["human_question", "parent_0", "parent_1"]
    elif operator == "CROSS":
        roles = ["potential_capability_donor", "potential_capability_donor"]
        phases = [
            {"action": "discover_input_output_contracts", "parents": [0, 1]},
            {"action": "design_explicit_bounded_adapter", "parents": [0, 1]},
            {"action": "test_new_combined_fixture_separately", "parents": [0, 1]},
        ]
        hypothesis = "Could a separately designed adapter combine distinct declared capabilities?"
        inheritance = {"parent_0": "identity_only", "parent_1": "identity_only"}
        influence = ["human_question", "parent_0", "parent_1"]
    elif operator == "MUTATE":
        roles = ["proposed_base", "influence_only"]
        phases = [
            {"action": "inspect_base_constraints", "parents": [0]},
            {"action": "declare_one_bounded_change_influenced_by_second_source", "parents": [0, 1]},
            {"action": "compare_descendant_to_unchanged_base", "parents": [0]},
        ]
        hypothesis = "Could one explicitly declared change be made while leaving the base intact?"
        inheritance = {"parent_0": "identity_only", "parent_1": "influence_only"}
        influence = ["human_question", "parent_0", "parent_1"]
    else:
        raise ValueError("undeclared composition operator")

    proposal = {
        "format": "house.composition-candidate/v0",
        "operator": operator,
        "state": "inert_unrun",
        "question": loom["question"],
        "parent_loom_digest": loom["proposal_digest"],
        "parents": parents,
        "parent_roles": roles,
        "hypothesis": hypothesis,
        "phases": phases,
        "inheritance": inheritance,
        "context_diet": {
            "available": ["human_question", "parent_0", "parent_1"],
            "used_as_proposal_influence": influence,
            "ignored": [],
            "unavailable": ["verified_io_contracts", "project_authorization", "verified_outcomes"],
        },
        "compatibility": "not_evaluated",
        "verification": "not_evaluated",
        "authorization": "not_evaluated",
        "execution": "not_attempted",
        "declared_effects": [],
        "nonclaims": [
            "The selected inputs are separately self-reported; source authenticity is unverified.",
            "An operator describes a proposed relationship, not a proven or executable composition.",
            "Human attention or candidate selection is not permission for any project effect.",
            "No capability, I/O contract, or authorization is inherited from the named parents.",
        ],
    }
    proposal["candidate_digest"] = _digest(proposal)
    return proposal


def preview_ecology(ledger: CapabilityReturnLedger, request: dict[str, Any]) -> dict[str, Any]:
    """Validate source selections with the existing Loom; derive three inert plans."""
    loom = preview_composition(ledger, request)
    packs = [_pack(input_) for input_ in loom["inputs"]]
    proposals = [_candidate(op, loom) for op in OPERATORS]
    envelope = {
        "format": FORMAT,
        "state": "inert_unrun",
        "source_loom_digest": loom["proposal_digest"],
        "question": loom["question"],
        "capability_packs": packs,
        "candidates": proposals,
        "human_continuation": "not_selected",
        "compatibility": "not_evaluated",
        "verification": "not_evaluated",
        "authorization": "not_evaluated",
        "execution": "not_attempted",
        "declared_effects": [],
        "nonclaims": [
            "A preview is not an execution plan, project-owned receipt, or verified compatibility.",
            "No candidate was kept, tested, persisted, executed, merged or published.",
        ],
    }
    envelope["ecology_digest"] = _digest(envelope)
    return envelope
