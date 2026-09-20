"""GROUNDKEEPER-001 tests: deterministic reproduction, topology deltas and refusal."""
from __future__ import annotations

import copy
import json
import math
import subprocess
import sys

import pytest

from static_workbench.groundkeeper import (
    BASE, GroundkeeperError, checked_graph, checked_samples, digest, make_receipt,
    proposals, replay, simulate, synthetic_ground,
)


def test_synthetic_first_ignition_is_deterministic_and_bounded():
    a = make_receipt()
    b = make_receipt()
    assert a == b
    assert replay(a)
    assert a["source"]["kind"] == "synthetic"
    assert a["source"]["samples_digest"] == digest(a["source"]["samples"])
    assert len(a["source"]["samples"]) == 64
    assert a["authority"] == "none" and a["promotion"] == "NONE"
    assert len(a["simulation"]["baseline"]["notes"]) == 16
    assert len(a["simulation"]["baseline"]["frames"]) == 8
    assert len(a["simulation"]["baseline"]["frames"][0]["pixels"]) == 8
    assert all(len(row) == 8 for row in a["simulation"]["baseline"]["frames"][0]["pixels"])


def test_candidate_changes_are_not_mistaken_for_admission_or_source():
    receipt = make_receipt(seed="GROUND-001")
    candidates = receipt["simulation"]["candidates"]
    assert [c["name"] for c in candidates] == [
        "add_environmental_visual_path",
        "ablate_visual_feedback",
        "strengthen_visual_feedback",
    ]
    assert all(c["disposition"] == "UNREVIEWED_EXPERIMENT" for c in candidates)
    assert all(c["graph_digest"] == digest(c["graph"]) for c in candidates)
    assert all(c["observed_in_simulation"]["mean_absolute_state_delta"] > 0 for c in candidates)
    assert "ground>visual" not in receipt["simulation"]["graph"]
    assert "ground>visual" in candidates[0]["graph"]
    assert "visual>sound" not in candidates[1]["graph"]
    assert "visual>sound" in receipt["simulation"]["graph"]
    assert receipt["source"]["kind"] == "synthetic"


def test_external_samples_are_unverified_but_replayable():
    values = [math.sin(i / 4) for i in range(32)]
    receipt = make_receipt(values, source_label="bench-contact-microphone-unverified")
    assert receipt["source"]["kind"] == "provided-unverified"
    assert receipt["source"]["seed"] is None
    assert receipt["source"]["samples"] == checked_samples(values)
    assert replay(receipt)
    assert receipt != make_receipt(seed="bench-contact-microphone-unverified")


@pytest.mark.parametrize("values", [
    [], [0] * 7, [0] * 257, [True] * 8, [0] * 7 + [float("nan")],
    [0] * 7 + [float("inf")], [0] * 7 + [1.01], "not a signal",
])
def test_bad_signal_refused(values):
    with pytest.raises(GroundkeeperError):
        checked_samples(values)


@pytest.mark.parametrize("graph", [
    {}, {"ground>sound": 0.4}, {"ground>sound": 0.4, "sound>visual": float("nan")},
    {"ground>sound": 0.4, "sound>visual": True},
    {"ground>sound": 0.4, "sound>visual": 0.2, "shell>execute": 0.4},
    {"ground>sound": 0.4, "sound>visual": 1.5},
])
def test_unknown_or_unsafe_graph_refused(graph):
    with pytest.raises(GroundkeeperError):
        checked_graph(graph)


def test_same_instruments_new_edges_change_the_state():
    values = synthetic_ground()
    baseline = simulate(values, checked_graph(BASE))
    others = [simulate(values, candidate["graph"]) for candidate in proposals(checked_graph(BASE))]
    assert all(result["states_digest"] != baseline["states_digest"] for result in others)
    assert all(result["final_state"] != baseline["final_state"] for result in others)


def test_receipt_tampering_and_relabeling_refused_even_when_rehashed():
    original = make_receipt()
    changed = copy.deepcopy(original)
    changed["source"]["samples"][0] = 0
    with pytest.raises(GroundkeeperError, match="digest"):
        replay(changed)
    changed["receipt_digest"] = digest({k: v for k, v in changed.items() if k != "receipt_digest"})
    with pytest.raises(GroundkeeperError, match="sample digest"):
        replay(changed)
    changed = copy.deepcopy(original)
    changed["source"]["kind"] = "provided-unverified"
    changed["source"]["seed"] = None
    changed["receipt_digest"] = digest({k: v for k, v in changed.items() if k != "receipt_digest"})
    with pytest.raises(GroundkeeperError, match="replay mismatch"):
        replay(changed)


def test_cli_writes_one_explicit_receipt_and_never_overwrites(tmp_path):
    output = tmp_path / "groundkeeper-001.json"
    command = [sys.executable, "-m", "static_workbench.groundkeeper", "--seed", "FIRST-FLIGHT",
               "--output", str(output)]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    content = output.read_bytes()
    assert replay(json.loads(content))
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert output.read_bytes() == content
    verify = subprocess.run(
        [sys.executable, "-m", "static_workbench.groundkeeper", "--replay", str(output)],
        capture_output=True, text=True,
    )
    assert verify.returncode == 0 and "exact replay OK" in verify.stdout


def test_cli_requires_explicit_bounded_samples_and_does_not_create_a_receipt_on_failure(tmp_path):
    source = tmp_path / "samples.json"
    output = tmp_path / "receipt.json"
    source.write_text(json.dumps({"samples": [0.1] * 8, "label": "human-supplied"}))
    command = [sys.executable, "-m", "static_workbench.groundkeeper",
               "--samples-json", str(source), "--output", str(output)]
    assert subprocess.run(command, capture_output=True).returncode == 0
    assert json.loads(output.read_text())["source"]["kind"] == "provided-unverified"
    output.unlink()
    source.write_text(json.dumps({"samples": [0.1] * 257, "label": "too many"}))
    assert subprocess.run(command, capture_output=True).returncode == 2
    assert not output.exists()
