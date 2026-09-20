"""GROUNDKEEPER-001: bounded deterministic ground-to-instrument feedback laboratory.

Experimental HOUSE-owned simulation. This is NOT TranchNOSE's optical field,
a live sensor driver, a daemon, or an authorized project adapter.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import math
from pathlib import Path
from typing import Any

SCHEMA = "house.groundkeeper-field-lab/v0.1"
EDGES = ("ground>sound", "ground>visual", "sound>visual", "visual>sound")
BASE = {"ground>sound": 0.8, "sound>visual": 0.7, "visual>sound": 0.2}
MAX_SAMPLES = 256
NOTES = ("C3", "D3", "E3", "G3", "A3", "C4", "D4", "E4")


class GroundkeeperError(ValueError):
    """An untrusted signal or graph violates the experimental boundary."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(canonical(value)).hexdigest()


def checked_samples(values: Any) -> list[float]:
    if not isinstance(values, (list, tuple)) or not 8 <= len(values) <= MAX_SAMPLES:
        raise GroundkeeperError("Provide between 8 and 256 normalized samples")
    if any(type(v) not in (float, int) or not math.isfinite(v) or abs(v) > 1 for v in values):
        raise GroundkeeperError("Samples must be finite numbers between -1 and 1")
    return [round(float(v), 6) for v in values]


def synthetic_ground(seed: str = "static-first-ignition", count: int = 64) -> list[float]:
    if not isinstance(seed, str) or not 1 <= len(seed) <= 128 or any(ord(c) < 32 for c in seed):
        raise GroundkeeperError("Seed must be printable and 1 to 128 characters")
    if type(count) is not int or not 8 <= count <= MAX_SAMPLES:
        raise GroundkeeperError("Sample count outside 8..256")
    phase = int(hashlib.sha256(seed.encode("utf-8")).hexdigest()[:8], 16) / 2**32
    return checked_samples([
        0.50 * math.sin(2 * math.pi * (i / 17 + phase))
        + 0.19 * math.sin(2 * math.pi * (i / 7 + phase / 3))
        + (0.19 if i % 23 == 0 else 0)
        for i in range(count)
    ])


def checked_graph(graph: Any) -> dict[str, float]:
    if not isinstance(graph, dict) or not graph or len(graph) > len(EDGES):
        raise GroundkeeperError("Expected a nonempty bounded directed graph")
    if any(key not in EDGES or type(weight) not in (int, float)
           or not math.isfinite(weight) or abs(weight) > 1 for key, weight in graph.items()):
        raise GroundkeeperError("Unknown edge or nonfinite/out-of-range weight")
    if "ground>sound" not in graph or "sound>visual" not in graph:
        raise GroundkeeperError("The ground-to-sound-to-visual observation path is required")
    return {key: round(float(graph[key]), 6) for key in sorted(graph)}


def simulate(samples: list[float], graph: dict[str, float]) -> dict[str, Any]:
    """All connections consume prior-tick state: feedback cannot form zero-delay loops."""
    sound = visual = 0.0
    states: list[list[float]] = []
    notes: list[dict[str, Any]] = []
    frames: list[dict[str, Any]] = []
    for tick, ground in enumerate(samples):
        next_sound = math.tanh(
            0.54 * sound + graph["ground>sound"] * ground
            + graph.get("visual>sound", 0.0) * visual
        )
        next_visual = math.tanh(
            0.47 * visual + graph["sound>visual"] * sound
            + graph.get("ground>visual", 0.0) * ground
        )
        sound, visual = round(next_sound, 6), round(next_visual, 6)
        states.append([sound, visual])
        if tick % 4 == 0:
            # Musical mapping is a declared artistic transformation, not a detected note.
            index = min(7, int((sound + 1) * 4))
            notes.append({"tick": tick, "note": NOTES[index], "velocity": round(abs(sound), 4)})
        if tick % 8 == 0:
            pixels = [
                [round((1 + math.sin((x + 1) * sound * 3
                                      + (y + 1) * visual * 2 + tick / 8)) / 2, 3)
                 for x in range(8)] for y in range(8)
            ]
            frames.append({"tick": tick, "pixels": pixels})
    return {
        "states_digest": digest(states),
        "final_state": states[-1],
        "mean_abs_sound": round(sum(abs(s[0]) for s in states) / len(states), 6),
        "mean_abs_visual": round(sum(abs(s[1]) for s in states) / len(states), 6),
        "notes": notes,
        "frames": frames,
        "_states": states,  # Only consumed by the local comparator; not a public receipt field.
    }


def proposals(base: dict[str, float]) -> list[dict[str, Any]]:
    """Finite, declared topology experiments. No model and no arbitrary code generation."""
    changes = [
        ("add_environmental_visual_path", "ground>visual", 0.3),
        ("ablate_visual_feedback", "visual>sound", None),
        ("strengthen_visual_feedback", "visual>sound", 0.45),
    ]
    out = []
    for name, edge, weight in changes:
        candidate = dict(base)
        if weight is None:
            candidate.pop(edge, None)
        else:
            candidate[edge] = weight
        candidate = checked_graph(candidate)
        if candidate != base:
            out.append({"name": name, "edge": edge, "declared_weight": weight,
                        "graph": candidate, "graph_digest": digest(candidate)})
    return out


def make_receipt(samples: Any = None, *, seed: str = "static-first-ignition",
                 source_label: str = "synthetic-ground") -> dict[str, Any]:
    if not isinstance(source_label, str) or not 1 <= len(source_label) <= 128 or any(
        ord(c) < 32 for c in source_label
    ):
        raise GroundkeeperError("Source label must be printable and 1 to 128 characters")
    is_synthetic = samples is None
    values = synthetic_ground(seed) if is_synthetic else checked_samples(samples)
    base = checked_graph(BASE)
    baseline = simulate(values, base)
    records = []
    for candidate in proposals(base):
        other = simulate(values, candidate["graph"])
        delta = sum(
            abs(a[0] - b[0]) + abs(a[1] - b[1])
            for a, b in zip(baseline["_states"], other["_states"])
        ) / len(values)
        records.append({
            **candidate,
            "observed_in_simulation": {
                "mean_absolute_state_delta": round(delta, 6),
                "sound_energy_delta": round(other["mean_abs_sound"] - baseline["mean_abs_sound"], 6),
                "visual_energy_delta": round(other["mean_abs_visual"] - baseline["mean_abs_visual"], 6),
                "states_digest": other["states_digest"],
                "final_state": other["final_state"],
            },
            "disposition": "UNREVIEWED_EXPERIMENT",
        })
    baseline.pop("_states")
    packet = {
        "schema": SCHEMA,
        "implementation": "groundkeeper-pure-python-v0.1",
        "source": {
            "kind": "synthetic" if is_synthetic else "provided-unverified",
            "label": source_label,
            "seed": seed if is_synthetic else None,
            "sample_count": len(values),
            "samples_digest": digest(values),
            "samples": values,
        },
        "simulation": {
            "graph": base, "graph_digest": digest(base),
            "tick_rule": "all edges consume previous-tick state",
            "baseline": baseline, "candidates": records,
        },
        "status": "EXPERIMENTAL_LOCAL_SIMULATION",
        "authority": "none",
        "promotion": "NONE",
        "non_claims": [
            "No live sensor was read, and provided samples have no verified physical provenance.",
            "No TranchNOSE optical field object or independent relational-memory primitive was demonstrated.",
            "Candidate differences do not rank creative merit, justify admission, or authorize execution.",
            "No project state, hardware settings, software packages, or external services were changed.",
        ],
    }
    return {**packet, "receipt_digest": digest(packet)}


def replay(receipt: Any) -> bool:
    if not isinstance(receipt, dict) or receipt.get("schema") != SCHEMA:
        raise GroundkeeperError("Not a GROUNDKEEPER-001 receipt")
    body = {key: value for key, value in receipt.items() if key != "receipt_digest"}
    if set(receipt) != set(body) | {"receipt_digest"} or digest(body) != receipt["receipt_digest"]:
        raise GroundkeeperError("Receipt digest mismatch")
    source = receipt["source"]
    if source["samples_digest"] != digest(source["samples"]):
        raise GroundkeeperError("Source sample digest mismatch")
    if source["kind"] == "synthetic":
        actual = make_receipt(seed=source["seed"], source_label=source["label"])
    elif source["kind"] == "provided-unverified":
        actual = make_receipt(source["samples"], source_label=source["label"])
    else:
        raise GroundkeeperError("Unknown source kind")
    if canonical(actual) != canonical(receipt):
        raise GroundkeeperError("Exact experiment replay mismatch")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Run a bounded GROUNDKEEPER field-lab experiment")
    parser.add_argument("--seed", default="static-first-ignition")
    parser.add_argument("--samples-json", type=Path, help="explicit JSON input: {\"samples\":[...],\"label\":\"...\"}")
    parser.add_argument("--output", type=Path, help="new receipt file; existing files are never overwritten")
    parser.add_argument("--replay", type=Path, help="verify an existing experiment receipt instead of running")
    args = parser.parse_args()
    try:
        if args.replay:
            with args.replay.open("rb") as handle:
                raw = handle.read(131073)
            if len(raw) > 131072:
                raise GroundkeeperError("Receipt exceeds 128 KiB")
            replay(json.loads(raw))
            print("GROUNDKEEPER-001: exact replay OK")
            return
        if args.samples_json:
            with args.samples_json.open("rb") as handle:
                raw = handle.read(65537)
            if len(raw) > 65536:
                raise GroundkeeperError("Input exceeds 64 KiB")
            input_packet = json.loads(raw)
            if not isinstance(input_packet, dict) or set(input_packet) != {"samples", "label"}:
                raise GroundkeeperError("Expected exactly samples and label")
            packet = make_receipt(input_packet["samples"], source_label=input_packet["label"])
        else:
            packet = make_receipt(seed=args.seed)
        output = canonical(packet).decode("utf-8") + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as handle:
                handle.write(output)
            print(f"GROUNDKEEPER-001: wrote {args.output}")
        else:
            print(output, end="")
    except (GroundkeeperError, OSError, ValueError, TypeError, KeyError) as exc:
        parser.exit(2, f"GROUNDKEEPER-001 refused: {exc}\n")


if __name__ == "__main__":
    main()
