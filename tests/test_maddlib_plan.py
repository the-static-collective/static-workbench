"""FLIGHT-001: exact source, scope and refusal fixtures for non-executing planning."""
from __future__ import annotations

import copy

import pytest

from static_workbench.config import RootConfig
from static_workbench.creator_shelf import CreatorShelf
from static_workbench.maddlib_plan import preview_maddlib, evaluate_maddlib_preview


def setup(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "first.txt").write_text("house takes attendance", encoding="utf-8")
    (root / "second.txt").write_text("attendance in the house", encoding="utf-8")
    return (RootConfig("local", root),), CreatorShelf(tmp_path / "creator.sqlite3"), root


def intent(*paths):
    return {"fuels": [{"kind": "file", "root_id": "local", "path": p} for p in paths],
            "mode": "braid", "seed": "first", "question": "What changes?"}


def test_exact_inputs_produce_one_deterministic_unsaved_ride(tmp_path):
    roots, shelf, _ = setup(tmp_path)
    proposal = preview_maddlib(roots, shelf, intent("first.txt", "second.txt"))
    assert proposal == preview_maddlib(roots, shelf, intent("first.txt", "second.txt"))
    assert proposal["declared_effects"] == []
    result = evaluate_maddlib_preview(roots, shelf, proposal)
    assert result == evaluate_maddlib_preview(roots, shelf, proposal)
    assert result["ride"]["fuel_sha256"] == proposal["fuel_preview"]["fuel_sha256"]
    assert result["execution"] == "pure_computation_only"
    assert result["persistence"] == "not_attempted"
    assert result["authority"] == "none"
    assert result["ride"]["promotion"] == "NONE"


def test_changed_source_refuses_without_replacing_reviewed_fuel(tmp_path):
    roots, shelf, root = setup(tmp_path)
    plan = preview_maddlib(roots, shelf, intent("first.txt"))
    (root / "first.txt").write_text("changed", encoding="utf-8")
    with pytest.raises(ValueError, match="stale"):
        evaluate_maddlib_preview(roots, shelf, plan)


@pytest.mark.parametrize("change", [
    lambda x: x.update(plan_sha256="0" * 64),
    lambda x: x.update(authority="root"),
    lambda x: x.update(declared_effects=["host_mutate"]),
    lambda x: x["intent"].update(mode="pressure"),
    lambda x: x["fuel_preview"]["fuels"][0].update(excerpt="invented"),
    lambda x: x.update(approved=True),
])
def test_mutation_and_authority_smuggling_refuse(tmp_path, change):
    roots, shelf, _ = setup(tmp_path)
    plan = copy.deepcopy(preview_maddlib(roots, shelf, intent("first.txt")))
    change(plan)
    with pytest.raises(ValueError):
        evaluate_maddlib_preview(roots, shelf, plan)


@pytest.mark.parametrize("bad", [
    {"fuels": [], "mode": "braid", "seed": "", "question": ""},
    {"fuels": [{"kind": "file", "root_id": "local", "path": "../escape"}],
     "mode": "braid", "seed": "", "question": ""},
    {"fuels": [{"kind": "file", "root_id": "local", "path": "first.txt",
                "authorization": "granted"}], "mode": "braid", "seed": "", "question": ""},
    {"fuels": [{"kind": "file", "root_id": "local", "path": "first.txt"}],
     "mode": "arbitrary_shell", "seed": "", "question": ""},
    {"fuels": [{"kind": "file", "root_id": "local", "path": "first.txt"}],
     "mode": "braid", "seed": 1, "question": ""},
])
def test_missing_unsafe_or_unrecognized_intents_refuse(tmp_path, bad):
    roots, shelf, _ = setup(tmp_path)
    with pytest.raises(ValueError):
        preview_maddlib(roots, shelf, bad)
