#!/usr/bin/env python3
"""Actual cross-repo smoke for the first bounded creative return loop."""

from __future__ import annotations

import math
import os
import struct
import tempfile
import wave
from pathlib import Path

from static_workbench.doorhouse import DoorHouse
from static_workbench.doorhouse_autodisco import (
    build_audio_window,
    prepare_audio_look_twice,
    prepare_look_twice,
    run_audio_look_twice_encounters,
    run_first_encounter,
    run_look_twice_encounters,
)
from static_workbench.doorhouse_ghot import assign_ghot_body, discover_ghot_bodies
from static_workbench.repos import RepoStatus


ROOT = Path(__file__).resolve().parent.parent
GHOT = ROOT / ".compat" / "GHoT"
TOASTER = ROOT / ".compat" / "haunted-toaster"
AUTODISCO = ROOT / ".compat" / "autodisco"


def repo(name: str, path: Path) -> RepoStatus:
    return RepoStatus(
        name=name,
        path=str(path),
        branch=None,
        detached=True,
        head=None,
        dirty=False,
        ahead=None,
        behind=None,
    )


def fake_relatte(receipt: dict) -> dict:
    crossing_id = "relatte-crossing-v0:" + "a" * 64
    return {
        "schema": "relatte.opaque-roundtrip-result/v0",
        "request_id": "relatte-opaque-roundtrip-v0:" + "b" * 64,
        "crossing": {
            "crossing_id": crossing_id,
            "extensions": {
                "organ_adapter": {
                    "donor_claims": {
                        "local_receipt_id": receipt["id"],
                        "local_receipt_sha256": receipt["sha256"],
                    }
                }
            },
        },
        "transport_frame": {"transport_id": "relatte-transport-v0:" + "c" * 64},
        "receive_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "d" * 64,
            "kind": "RECEIVED",
            "semantic_effect": "none",
            "world_id": "world:creative-smoke",
        },
        "disposition_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "e" * 64,
            "kind": "R3_HOLD",
            "semantic_effect": "none",
        },
        "receiver_snapshot": {"state_ref": "relatte-local-state-v0:" + "f" * 64},
    }


def write_test_wav(path: Path, duration_seconds: float = 2.0) -> None:
    sample_rate = 44100
    frames = int(sample_rate * duration_seconds)
    with wave.open(str(path), "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(sample_rate)
        payload = bytearray()
        for index in range(frames):
            sample = int(math.sin(index / 18.0) * 10000)
            payload.extend(struct.pack("<hh", sample, -sample))
        handle.writeframes(bytes(payload))


def main() -> int:
    for path in (GHOT, TOASTER, AUTODISCO):
        if not path.is_dir():
            raise SystemExit(f"missing integration checkout: {path}")

    repos = [
        repo("GHoT", GHOT),
        repo("the-haunted-toaster", TOASTER),
        repo("The-AutodiscoV.20.-question-marks-", AUTODISCO),
    ]

    with tempfile.TemporaryDirectory(prefix="doorhouse-creative-smoke-") as raw:
        state_dir = Path(raw) / "state"
        store = DoorHouse(state_dir / "doorhouse.sqlite3")
        state = store.enter()
        letter = state["letters"][0]
        store.open_letter(letter["id"])
        state = store.state()
        door = next(item for item in state["doors"] if item["letter_id"] == letter["id"])
        store.select(door["id"], 0)
        state = store.cross(door["id"], 0)
        receipt = state["receipts"][0]

        store.record_relatte_witness(receipt["id"], fake_relatte(receipt))
        relatte = store.require_relatte_hold(receipt["id"])

        offer = discover_ghot_bodies(receipt, relatte, repos, state_dir)
        assert offer["capability"] == "creative.toaster.witness-sigil"
        eligible = [item for item in offer["candidates"] if item.get("eligible") is True]
        assert eligible, "no body offered the Toaster witness-sigil capability"
        local = next((item for item in eligible if item.get("location") == "local"), eligible[0])

        store.record_ghot_offer(receipt["id"], offer)
        result = assign_ghot_body(
            receipt,
            relatte,
            offer,
            local["node_id"],
            repos,
            state_dir,
        )
        state = store.record_ghot_execution(
            receipt["id"],
            offer["offer_id"],
            local["node_id"],
            result,
        )
        ghot = next(
            item for item in state["external_witnesses"]
            if item["kind"] == "ghot_execution"
        )
        creative = ghot["snapshot"]["creative_artifact"]
        assert Path(creative["svg_path"]).is_file()
        assert creative["instrument"] == "witness-sigil/v0.1"

        os.environ.pop("GEMINI_API_KEY", None)
        encounter = run_first_encounter(ghot["snapshot"], repos)
        assert encounter["status"] == "packet-only"
        assert encounter["response"] is None
        final = store.record_autodisco_first_encounter(receipt["id"], encounter)
        assert any(
            item["kind"] == "autodisco_packet"
            for item in final["external_witnesses"]
        )
        assert not any(
            item["kind"] == "autodisco_first_response"
            for item in final["external_witnesses"]
        )
        assert final["letters"][0]["body"] is None

        pair = prepare_look_twice(ghot["snapshot"], repos)
        assert pair["schema"] == "autodisco.look-twice-pair/v0"
        assert len(pair["packets"]) == 2
        assert {
            item["listener"]["id"] for item in pair["packets"]
        } == {"static-sam", "juniper"}
        store.record_look_twice_pair(receipt["id"], pair)

        twice = run_look_twice_encounters(pair, repos)
        assert twice["status"] == "packets-only"
        assert twice["first_responses"] == []
        final = store.record_look_twice_encounters(receipt["id"], twice)
        assert any(
            item["kind"] == "look_twice_pair"
            for item in final["external_witnesses"]
        )
        assert not any(
            item["kind"].startswith("look_twice_first:")
            for item in final["external_witnesses"]
        )

        audio_source = Path(raw) / "radio-specimen.wav"
        write_test_wav(audio_source)
        audio = build_audio_window(
            audio_source,
            receipt["id"],
            state_dir,
            repos,
            start_ms=250,
            end_ms=1250,
            window_label="ci-window-001",
        )
        assert audio["schema"] == "workbench.audio-window-materialized/v0"
        assert Path(audio["audio_path"]).is_file()
        store.record_audio_window(receipt["id"], audio)

        audio_pair = prepare_audio_look_twice(audio, repos)
        assert audio_pair["schema"] == "autodisco.audio-look-twice-pair/v0"
        assert len(audio_pair["packets"]) == 2
        assert audio_pair["window_ref"]["audio_sha256"] == audio["audio_sha256"]
        store.record_audio_look_twice_pair(receipt["id"], audio_pair)

        audio_twice = run_audio_look_twice_encounters(
            audio,
            audio_pair,
            repos,
        )
        assert audio_twice["status"] == "packets-only"
        assert audio_twice["first_responses"] == []
        final = store.record_audio_look_twice_encounters(
            receipt["id"], audio_twice
        )
        assert any(
            item["kind"].startswith("audio_window:")
            for item in final["external_witnesses"]
        )
        assert any(
            item["kind"].startswith("audio_look_twice_pair:")
            for item in final["external_witnesses"]
        )
        assert not any(
            item["kind"].startswith("audio_look_twice_first:")
            for item in final["external_witnesses"]
        )

        print(
            "creative loop smoke ok:",
            local["node_id"],
            creative["svg_sha256"],
            encounter["packet"]["packet_id"],
            pair["pair_id"],
            audio["window_id"],
            audio_pair["pair_id"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
