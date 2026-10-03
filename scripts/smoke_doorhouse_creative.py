#!/usr/bin/env python3
"""Actual cross-repo smoke for the first bounded creative return loop."""

from __future__ import annotations

import math
import os
import json
import struct
import subprocess
import tempfile
import wave
from pathlib import Path

from static_workbench.doorhouse import DoorHouse
from static_workbench.doorhouse_autodisco import (
    assemble_broadcast_episode,
    build_audio_window,
    prepare_audio_look_twice,
    prepare_look_twice,
    run_audio_look_twice_encounters,
    run_first_encounter,
    run_look_twice_encounters,
)
from static_workbench.doorhouse_ghot import assign_ghot_body, discover_ghot_bodies
from static_workbench.doorhouse_phonograph import run_phonograph_field_answer
from static_workbench.repos import RepoStatus


ROOT = Path(__file__).resolve().parent.parent
GHOT = ROOT / ".compat" / "GHoT"
TOASTER = ROOT / ".compat" / "haunted-toaster"
AUTODISCO = ROOT / ".compat" / "autodisco"
PHONOGRAPH = ROOT / ".compat" / "haunted-phonograph"


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


def synthetic_audio_firsts(pair: dict) -> list[dict]:
    script = r"""
import fs from 'node:fs';
import { sealAudioFirstResponse } from './scripts/audio-look-twice.mjs';
const pair = JSON.parse(fs.readFileSync(0, 'utf8'));
const make = (label) => ({
  observations: [
    {mode:'OBSERVED', text: label + ': a repeated pulse is audible.'},
    {mode:'INTERPRETATION', text: label + ': the cutoff feels unresolved.'}
  ],
  lingering_intrigue: true,
  closing_line: label + ': I want the next window.'
});
const out = pair.packets.map((packet, index) =>
  sealAudioFirstResponse(pair, packet.packet_id, make(index === 0 ? 'Sam' : 'Juniper'), 'ci-synthetic-model')
);
process.stdout.write(JSON.stringify(out));
"""
    completed = subprocess.run(
        ["node", "--input-type=module", "-e", script],
        cwd=AUTODISCO,
        input=json.dumps(pair),
        text=True,
        capture_output=True,
        check=True,
    )
    return json.loads(completed.stdout)


def synthetic_audio_dialogue(pair: dict, firsts: list[dict]) -> dict:
    packet = {
        "schema": "autodisco.audio-look-twice-dialogue-packet/v0",
        "pair_id": pair["pair_id"],
        "window_ref": pair["window_ref"],
        "sealed_first_responses": [
            {
                "first_response_id": item["first_response_id"],
                "listener": item["listener"],
                "response_sha256": item["response_sha256"],
                "response": item["response"],
            }
            for item in firsts
        ],
        "rules": [
            "ONLY SEALED FIRST LISTENS MAY ENTER",
            "AUDIO WINDOW IS NOT REOPENED",
        ],
        "dialogue_packet_id": "autodisco-audio-look-twice-dialogue-v0:" + "a" * 64,
    }
    return {
        "schema": "autodisco.audio-look-twice-dialogue-result/v0",
        "status": "dialogue-sealed",
        "dialogue_packet": packet,
        "dialogue": {
            "turns": [
                {
                    "listener_id": "static-sam",
                    "text": "Synthetic fixture: the cutoff reads as structure.",
                },
                {
                    "listener_id": "juniper",
                    "text": "Synthetic fixture: the same edge reads as pressure.",
                },
            ],
            "convergences": ["Synthetic fixture: both point beyond the cut."],
            "differences": ["Synthetic fixture: they name the pull differently."],
            "lingering_intrigue": True,
            "intrigue_statement": "Synthetic fixture: the next window remains unresolved.",
            "door_seed": "Synthetic fixture: move the window forward.",
        },
        "dialogue_sha256": "b" * 64,
        "model_used": "ci-synthetic-model",
        "laws": [
            "SYNTHETIC FIXTURE != LIVE LISTENER EVIDENCE",
            "DOOR SEED != CROSSING",
        ],
        "dialogue_id": "autodisco-audio-look-twice-dialogue-result-v0:" + "c" * 64,
    }


def main() -> int:
    for path in (GHOT, TOASTER, AUTODISCO, PHONOGRAPH):
        if not path.is_dir():
            raise SystemExit(f"missing integration checkout: {path}")

    repos = [
        repo("GHoT", GHOT),
        repo("the-haunted-toaster", TOASTER),
        repo("The-AutodiscoV.20.-question-marks-", AUTODISCO),
        repo("the-haunted-phonography", PHONOGRAPH),
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

        phono = run_phonograph_field_answer(
            audio,
            repos,
            state_dir,
            receipt["id"],
        )
        assert phono["schema"] == "workbench.phonograph-field-answer/v0"
        assert phono["status"] == "proposal-ready"
        assert phono["window_id"] == audio["window_id"]
        assert phono["signal_profile"]["authority"] == "evidence"
        assert phono["proposal"]["authority"] == "proposal"
        assert Path(phono["audition"]["path"]).is_file()
        assert Path(phono["midi"]["path"]).is_file()
        final = store.record_phonograph_field_answer(
            receipt["id"], phono
        )
        assert any(
            item["kind"] == "phonograph_field_answer:" + audio["window_id"]
            for item in final["external_witnesses"]
        )

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

        # Explicitly synthetic fixture evidence exercises only the downstream
        # assembly boundary. The no-key proof above remains the canonical claim
        # about listener absence.
        fixture_firsts = synthetic_audio_firsts(audio_pair)
        fixture_encounter = {
            "schema": "autodisco.audio-look-twice-encounter-result/v0",
            "status": "two-first-responses-sealed",
            "pair_id": audio_pair["pair_id"],
            "window_id": audio["window_id"],
            "first_responses": fixture_firsts,
            "model_used": "ci-synthetic-model",
            "laws": ["SYNTHETIC FIXTURE != LIVE LISTENER EVIDENCE"],
        }
        store.record_audio_look_twice_encounters(
            receipt["id"], fixture_encounter
        )
        fixture_dialogue = synthetic_audio_dialogue(
            audio_pair, fixture_firsts
        )
        store.record_audio_look_twice_dialogue(
            receipt["id"], fixture_dialogue
        )
        pair_id = audio_pair["pair_id"]
        packet_witness = store.audio_look_twice_dialogue_packet(
            receipt["id"], pair_id
        )
        dialogue_witness = store.audio_look_twice_dialogue(
            receipt["id"], pair_id
        )
        episode = assemble_broadcast_episode(
            audio,
            audio_pair,
            fixture_firsts,
            packet_witness,
            dialogue_witness,
            repos,
            state_dir,
            receipt["id"],
        )
        assert episode["schema"] == "workbench.broadcast-episode-materialized/v0"
        assert episode["audio_sha256"] == audio["audio_sha256"]
        assert Path(episode["html_path"]).is_file()
        assert Path(episode["manifest_path"]).is_file()
        assert Path(episode["audio_path"]).is_file()
        final = store.record_broadcast_episode(
            receipt["id"], episode
        )
        assert any(
            item["kind"].startswith("broadcast_episode:")
            for item in final["external_witnesses"]
        )

        print(
            "creative loop smoke ok:",
            local["node_id"],
            creative["svg_sha256"],
            encounter["packet"]["packet_id"],
            pair["pair_id"],
            audio["window_id"],
            phono["proposal_receipt_hash"],
            audio_pair["pair_id"],
            episode["episode_id"],
            episode["episode_digest"],
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
