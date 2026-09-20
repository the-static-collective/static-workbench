"""FORK!-inspired, deterministic proposal table for a saved native HOUSE ride.

No source interpretation or retrieval: KEEP/BEND/INTRUDER and relation lane are
human declarations, not inferred properties of fuel, persons or projects.
"""
from __future__ import annotations

from typing import Any

from .creator_shelf import CreatorConflict, CreatorShelf
from .graft_witness import GraftWitnessError, _ride, sha

MOVES = ("fuse", "invert", "continue", "wildcard")
LANES = ("semantic", "lineage", "active_tension", "human_link", "rejected_parallel")
CARDS = ("clean_hit", "side_door", "wrong_turn")


def _declaration(name: str, value: Any) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > 400:
        raise GraftWitnessError(f"{name} must be a human-entered, nonempty statement of at most 400 characters")
    if any(ord(char) < 32 and char not in "\n\t" for char in value):
        raise GraftWitnessError(f"{name} contains control characters")
    return value.strip()


def _candidate(move: str, variant: str, keep: str, bend: str,
               intruder: str, question: str) -> dict[str, Any]:
    """The variants are deliberately *questions*, never claimed generated artifacts."""
    if variant == "clean_hit":
        transformation = {
            "fuse": f"How might {intruder} become a component of {bend} while retaining {keep}?",
            "invert": f"What happens if {intruder} performs the role normally assigned to {bend}, while retaining {keep}?",
            "continue": f"What is the next limited step after {bend} if {intruder} enters and {keep} remains a constraint?",
            "wildcard": f"What unexpected, testable third thing might emerge if {intruder} meets {bend} under the constraint {keep}?",
        }[move]
        act = "Describe one minimal, reversible fixture and a separately observable output."
        tension = "What specific property of KEEP could the new mechanism accidentally erase?"
    elif variant == "side_door":
        transformation = {
            "fuse": f"Instead of merging products, can {intruder} act as an interface between {bend} and a new receiving context without dropping {keep}?",
            "invert": f"Can {bend} be made an input to {intruder}, rather than the other way around, while {keep} remains explicit?",
            "continue": f"Could {intruder} enable a smaller preparatory act before continuing {bend}, without claiming {keep} has been proven?",
            "wildcard": f"What indirect bridge could connect {intruder} and {bend} while leaving their identities—and {keep}—separate?",
        }[move]
        act = "Specify a two-part handoff using only synthetic data; inspect where provenance could be lost."
        tension = "What source boundary would this indirect bridge risk crossing?"
    else:
        transformation = {
            "fuse": f"Suppose {intruder} and {bend} cannot be combined at all. What small comparison could still explore {keep}?",
            "invert": f"What if {intruder} reverses the purpose of {bend}? What contradiction would that expose about {keep}?",
            "continue": f"What if {intruder} makes continuation of {bend} inappropriate? How could an explicit hold preserve {keep}?",
            "wildcard": f"If {intruder} makes {bend} fail, which part of {keep} deserves preservation outside the failed proposal?",
        }[move]
        act = "Design a negative control or stopping condition; preserve the rejected branch if it fails."
        tension = "Which attractive explanation could be disproved by a concrete counterexample?"
    return {
        "variant": variant,
        "move": move,
        "title": {"clean_hit": "Direct graft", "side_door": "Side-door graft",
                  "wrong_turn": "Productive wrong turn"}[variant],
        "transformation_question": transformation,
        "next_act_question": act,
        "pressure_question": tension,
        "human_question": question,
        "status": "PROPOSAL_ONLY",
    }


def build_round(shelf: CreatorShelf, ride_id: int, ride_sha256: str, keep: Any,
                bend: Any, intruder: Any, move: str, relation_lane: str,
                question: Any = "") -> dict[str, Any]:
    ride = _ride(shelf, ride_id, ride_sha256)
    if move not in MOVES or relation_lane not in LANES:
        raise GraftWitnessError("Choose one supported transformation and one explicitly declared relation lane")
    if not isinstance(question, str) or len(question) > 400:
        raise GraftWitnessError("Human question must be at most 400 characters")
    declarations = {
        "keep": _declaration("KEEP", keep),
        "bend": _declaration("BEND", bend),
        "intruder": _declaration("INTRUDER", intruder),
        "move": move, "relation_lane": relation_lane,
        "human_question": question.strip(),
    }
    cards = [_candidate(move, variant, declarations["keep"], declarations["bend"],
                        declarations["intruder"], declarations["human_question"]) for variant in CARDS]
    candidates = [
        {**card, "candidate_sha256": sha({
            "ride_sha256": ride_sha256, "declarations": declarations, "card": card,
        })}
        for card in cards
    ]
    return {
        "schema": "house.graft-proposal-round/v0.1",
        "ride_id": ride_id, "ride_sha256": ride_sha256,
        "fuel_sha256": ride["fuel_sha256"],
        "source_refs": ride.get("source_refs", []),
        "declarations": declarations,
        "candidates": candidates,
        "authority": "none", "promotion": "NONE",
        "non_claims": [
            "KEEP, BEND, INTRUDER and relation lane are human declarations, not observations.",
            "Candidate questions are deterministic transformation prompts, not completed ideas or working implementations.",
            "No source files were modified, no candidate was selected, and no participation commitment was made.",
        ],
    }


def preview_round(shelf: CreatorShelf, **kwargs: Any) -> dict[str, Any]:
    packet = build_round(shelf, **kwargs)
    return {"round_sha256": sha(packet), "round": packet,
            "notice": "Review all human declarations, source references, and candidate questions before saving."}


def save_round(shelf: CreatorShelf, expected_round_sha256: str, **kwargs: Any) -> dict[str, Any]:
    packet = build_round(shelf, **kwargs)
    if sha(packet) != expected_round_sha256:
        raise GraftWitnessError("GRAFT proposal round changed since preview; review again")
    return shelf.save_graft_round(packet)


def get_candidate(shelf: CreatorShelf, ride_id: int, ride_sha256: str,
                  candidate_sha256: str) -> dict[str, Any]:
    _ride(shelf, ride_id, ride_sha256)
    resolved = shelf.get_graft_candidate(candidate_sha256)
    if resolved is None or resolved["round"]["ride_id"] != ride_id or resolved["round"]["ride_sha256"] != ride_sha256:
        raise GraftWitnessError("Candidate is absent or belongs to a different native ride")
    round_data = resolved["round"]
    candidate = resolved["candidate"]
    card = {k: v for k, v in candidate.items() if k != "candidate_sha256"}
    if sha({"ride_sha256": ride_sha256, "declarations": round_data["declarations"],
            "card": card}) != candidate_sha256:
        raise GraftWitnessError("Stored candidate identity is invalid")
    return resolved
