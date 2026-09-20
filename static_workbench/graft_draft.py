"""GRAFT 003: source-bound, human-editable candidate draft and unrun experiment plan.

A deterministic starter is an editable sketch, not evidence of a working
implementation or an instruction to run code from source material.
"""
from __future__ import annotations

from typing import Any

from .creator_shelf import CreatorShelf
from .graft_round import get_candidate
from .graft_witness import GraftWitnessError

FIELD_LIMITS = {
    "title": 160,
    "body": 8192,
    "assumptions": 2000,
    "unresolved": 2000,
}
EXPERIMENT_FIELDS = ("input", "procedure", "observable", "stop_condition")


def candidate_context(shelf: CreatorShelf, candidate_sha256: str) -> dict[str, Any]:
    resolved = shelf.get_graft_candidate(candidate_sha256)
    if resolved is None:
        raise GraftWitnessError("Choose a candidate from an existing saved GRAFT round")
    round_data = resolved["round"]
    return get_candidate(
        shelf, round_data["ride_id"], round_data["ride_sha256"], candidate_sha256,
    )


def starter(shelf: CreatorShelf, candidate_sha256: str) -> dict[str, Any]:
    found = candidate_context(shelf, candidate_sha256)
    card, parent = found["candidate"], found["round"]
    declared = parent["declarations"]
    variant = card["variant"]
    mechanism = {
        "clean_hit": (
            "Prototype a direct, local adapter between the flexible mechanism and the "
            "human-selected intruder. Keep the preserved property as an explicit input "
            "constraint; do not treat textual resemblance as compatibility."
        ),
        "side_door": (
            "Prototype a two-part handoff instead of combining the systems. Keep each "
            "source identity separate and inspect whether the handoff loses provenance."
        ),
        "wrong_turn": (
            "Prototype a negative control or a deliberate HOLD. Preserve the original "
            "capability independently if this particular crossing does not work."
        ),
    }[variant]
    return {
        "title": f"{card['title']}: {declared['bend']}"[:FIELD_LIMITS["title"]],
        "body": (
            f"WORKING HYPOTHESIS — {card['title']}\n"
            f"KEEP (human declared): {declared['keep']}\n"
            f"BEND (human declared): {declared['bend']}\n"
            f"INTRUDER (human declared): {declared['intruder']}\n"
            f"Relation lane (unverified): {declared['relation_lane']}\n"
            f"Transformation move: {declared['move']}\n\n"
            f"Candidate question: {card['transformation_question']}\n\n"
            f"Mechanism sketch (proposal only): {mechanism}\n\n"
            "Editable design: Describe the actual inputs, interface, outputs and "
            "explicit human decision boundary for ONE small experiment."
        )[:FIELD_LIMITS["body"]],
        "experiment": {
            "input": "Choose a small, synthetic fixture; identify each proposed input and its source.",
            "procedure": f"Describe one reversible local test of this candidate: {card['next_act_question']}",
            "observable": "Before the test, name the exact result to record, including what would count as no change.",
            "stop_condition": "Stop before any project write, external publication, disclosure or unapproved real-world action.",
        },
        "assumptions": "What must be true for the proposed mechanism to operate? Mark every unverified dependency.",
        "unresolved": card["pressure_question"],
    }


def _text(name: str, value: Any, maximum: int) -> str:
    if (not isinstance(value, str) or not value.strip() or len(value) > maximum
        or any(ord(ch) < 32 and ch not in "\n\t" for ch in value)):
        raise GraftWitnessError(f"{name} must be nonblank human-editable text of at most {maximum} characters")
    return value.strip()


def prepare(shelf: CreatorShelf, candidate_sha256: str, title: Any, body: Any,
            experiment: Any, assumptions: Any, unresolved: Any) -> dict[str, Any]:
    found = candidate_context(shelf, candidate_sha256)
    if not isinstance(experiment, dict) or set(experiment) != set(EXPERIMENT_FIELDS):
        raise GraftWitnessError("Experiment requires exactly input, procedure, observable, and stop_condition")
    plan = {name: _text(name, experiment[name], 1200) for name in EXPERIMENT_FIELDS}
    round_data = found["round"]
    return {
        "schema": "house.graft-working-draft/v0.1",
        "candidate_sha256": candidate_sha256,
        "round_sha256": found["round_sha256"],
        "ride_id": round_data["ride_id"],
        "ride_sha256": round_data["ride_sha256"],
        "source_refs": round_data["source_refs"],
        "candidate_question": found["candidate"]["transformation_question"],
        "title": _text("title", title, FIELD_LIMITS["title"]),
        "body": _text("body", body, FIELD_LIMITS["body"]),
        "experiment": plan,
        "assumptions": _text("assumptions", assumptions, FIELD_LIMITS["assumptions"]),
        "unresolved": _text("unresolved", unresolved, FIELD_LIMITS["unresolved"]),
        "status": "PROPOSED_UNRUN", "authority": "none", "promotion": "NONE",
        "non_claims": [
            "This is an editable working proposal, not an implementation or an observed experiment.",
            "This plan does not execute code, change project files, record fulfillment or imply a volunteer commitment.",
            "An attached Dogram calculation concerns only its separately reviewed declared graph.",
        ],
    }


def open_draft(shelf: CreatorShelf, candidate_sha256: str) -> dict[str, Any]:
    # Verify the candidate and parent on every read, even when a revision exists.
    candidate_context(shelf, candidate_sha256)
    stored = shelf.latest_graft_draft(candidate_sha256)
    if stored is not None:
        return stored
    return {
        "candidate_sha256": candidate_sha256,
        "revision": 0, "draft_sha256": None,
        "draft": prepare(shelf, candidate_sha256, **starter(shelf, candidate_sha256)),
        "saved": False,
    }


def save_draft(shelf: CreatorShelf, candidate_sha256: str, expected_revision: int,
               expected_draft_sha256: str | None, title: Any, body: Any,
               experiment: Any, assumptions: Any, unresolved: Any) -> dict[str, Any]:
    if type(expected_revision) is not int or expected_revision < 0:
        raise GraftWitnessError("Expected revision must be a nonnegative integer")
    data = prepare(shelf, candidate_sha256, title, body, experiment, assumptions, unresolved)
    return shelf.save_graft_draft(data, expected_revision, expected_draft_sha256)
