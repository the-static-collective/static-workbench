"""FLIGHT-001: exact-source, non-executing MADDlib preview over HOUSE Native Maxhinal.

Pure planning/evaluation only. This is not the atomic save/approval executor
proposed in the MADDlibMaxhine design; it adds no source-derived permissions.
"""
from __future__ import annotations

from typing import Any

from .native_maxhinal import canonical, digest, preview_fuels, spin

FORMAT = "house.maddlib.plan-preview/v0.1"
MODES = frozenset(("discontinuity", "braid", "compose", "pressure", "shuffle"))
INTENT_FIELDS = frozenset(("fuels", "mode", "seed", "question"))


def _intent(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict) or set(value) != INTENT_FIELDS:
        raise ValueError("explicit fuels, mode, seed and question required; no extra fields")
    if (not isinstance(value["fuels"], list)
            or not all(isinstance(item, dict) for item in value["fuels"])):
        raise ValueError("fuel selectors must be explicit objects")
    if not isinstance(value["mode"], str) or value["mode"] not in MODES:
        raise ValueError("unsupported native HOUSE operation")
    if not isinstance(value["seed"], str) or len(value["seed"]) > 100:
        raise ValueError("invalid bounded seed")
    if not isinstance(value["question"], str) or len(value["question"]) > 400:
        raise ValueError("invalid bounded question")
    # Exact key and JSON admissibility, not a source-authentication claim.
    selectors = []
    for item in value["fuels"]:
        if item.get("kind") == "file" and set(item) == {"kind", "root_id", "path"}:
            if not isinstance(item["root_id"], str) or not isinstance(item["path"], str):
                raise ValueError("invalid file selector")
        elif item.get("kind") == "source_pack" and set(item) == {"kind", "pack_id"}:
            if not isinstance(item["pack_id"], int) or isinstance(item["pack_id"], bool):
                raise ValueError("invalid source pack selector")
        else:
            raise ValueError("unsupported or authority-bearing fuel selector")
        selectors.append(dict(item))
    return {"fuels": selectors, "mode": value["mode"],
            "seed": value["seed"], "question": value["question"]}


def preview_maddlib(roots: Any, shelf: Any, intent: Any) -> dict[str, Any]:
    """Read only explicitly selected local fuel and return a hash-bound proposal."""
    declared = _intent(intent)
    observed = preview_fuels(roots, shelf, declared["fuels"])
    body = {
        "format": FORMAT, "intent": declared, "fuel_preview": observed,
        "operation": "house.native-maxhinal.spin/v0.1",
        "expected_output": "house.native-maxhinal-ride/v0.1",
        "state": "preview_only", "authority": "none", "promotion": "NONE",
        "max_operations": 1, "declared_effects": [],
        "nonclaims": [
            "Source presence and local SHA do not establish source-owner authority.",
            "This plan is not approved, executed, persisted or reusable permission.",
            "This specimen cannot create an atomic run/ride receipt.",
        ],
    }
    return {**body, "plan_sha256": digest(canonical(body))}


def evaluate_maddlib_preview(roots: Any, shelf: Any, proposal: Any) -> dict[str, Any]:
    """Recheck source bytes and plan identity, then compute one UNSAVED creative ride.

    This function intentionally accepts no authorization argument and provides no
    persistent state or project side effects. An effectful executor is a later gate.
    """
    if not isinstance(proposal, dict) or set(proposal) != {
        "format", "intent", "fuel_preview", "operation", "expected_output",
        "state", "authority", "promotion", "max_operations", "declared_effects",
        "nonclaims", "plan_sha256",
    }:
        raise ValueError("unexpected or missing plan fields")
    expected = preview_maddlib(roots, shelf, proposal["intent"])
    if canonical(proposal) != canonical(expected):
        raise ValueError("stale, mutated or unrecognized plan; re-preview before computing")
    declared = expected["intent"]
    ride = spin(expected["fuel_preview"], declared["mode"],
                declared["seed"], declared["question"])
    if (ride["fuel_sha256"] != expected["fuel_preview"]["fuel_sha256"]
            or ride["authority"] != "none" or ride["promotion"] != "NONE"
            or ride["format"] != expected["expected_output"]):
        raise ValueError("native ride violated declared format/source/authority")
    return {
        "format": "house.maddlib.unsaved-evaluation/v0.1",
        "plan_sha256": expected["plan_sha256"],
        "ride": ride,
        "execution": "pure_computation_only",
        "persistence": "not_attempted",
        "approval": "not_requested",
        "authority": "none",
    }
