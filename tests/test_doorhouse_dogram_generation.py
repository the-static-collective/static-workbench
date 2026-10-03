from pathlib import Path
import hashlib
import json

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict


PARENT_WINDOW = "autodisco-audio-window-v0:" + "1" * 64
CHILD_WINDOW = "autodisco-audio-window-v0:" + "2" * 64
PARENT_PAIR = "autodisco-audio-look-twice-pair-v0:" + "3" * 64
CHILD_PAIR = "autodisco-audio-look-twice-pair-v0:" + "4" * 64
PARENT_SHA = "5" * 64
CHILD_SHA = "6" * 64
PROPOSAL_RECEIPT = "sha256:" + "7" * 64


def config_for(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def crossed_receipt(store: DoorHouse):
    state = store.enter()
    letter = state["letters"][0]
    store.open_letter(letter["id"])
    state = store.state()
    door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
    store.select(door["id"], 0)
    state = store.cross(door["id"], 0)
    return state["receipts"][0]


def window(window_id, audio_sha, *, lineage=None):
    result = {
        "schema": "workbench.audio-window-materialized/v0",
        "window_id": window_id,
        "source_path": "/tmp/source.wav",
        "audio_path": "/tmp/window.wav",
        "audio_sha256": audio_sha,
        "audio_size_bytes": 176444,
        "window": {
            "schema": "autodisco.audio-window/v0",
            "source": {
                "sha256": "8" * 64,
                "media_type": "audio/wav",
                "basename": "source.wav",
            },
            "requested_bounds": {"start_ms": 0, "end_ms": 1000},
            "canonical_audio": {
                "media_type": "audio/wav",
                "sha256": audio_sha,
                "size_bytes": 176444,
                "sample_rate_hz": 44100,
                "channels": 2,
                "bits_per_sample": 16,
                "frame_count": 44100,
                "duration_ms": 1000,
                "base64_sha256": "9" * 64,
            },
            "extraction": {
                "method": "direct-canonical-wav-slice",
                "start_frame": 0,
                "end_frame": 44100,
                "actual_start_ms": 0,
                "actual_end_ms": 1000,
            },
            "declared_metadata": {"window_label": window_id[-8:]},
            "laws": ["WINDOW != WHOLE TRACK"],
            "window_id": window_id,
        },
        "laws": ["WINDOW DIGEST BINDS HEARD BYTES"],
    }
    if lineage is not None:
        result["source_lineage"] = lineage
    return result


def pair(window_id, audio_sha, pair_id):
    ref = {
        "window_id": window_id,
        "source_sha256": "8" * 64,
        "audio_sha256": audio_sha,
        "media_type": "audio/wav",
        "requested_bounds": {"start_ms": 0, "end_ms": 1000},
        "duration_ms": 1000,
        "declared_metadata": {"window_label": "fixture"},
    }
    packets = []
    for listener_id, role in [("static-sam", "Static Sam"), ("juniper", "Juniper")]:
        packets.append({
            "schema": "autodisco.audio-look-twice-first-packet/v0",
            "listener": {"id": listener_id, "role": role, "brief": "isolated"},
            "window_ref": ref,
            "prohibitions": ["NO OTHER LISTENER RESPONSE"],
            "packet_id": f"packet:{pair_id}:{listener_id}",
        })
    return {
        "schema": "autodisco.audio-look-twice-pair/v0",
        "window_ref": ref,
        "packets": packets,
        "laws": ["FIRST LISTEN PRECEDES CROSS-READ"],
        "pair_id": pair_id,
    }


def encounter(window_id, audio_sha, pair_id):
    p = pair(window_id, audio_sha, pair_id)
    firsts = []
    for index, packet in enumerate(p["packets"]):
        listener = packet["listener"]
        firsts.append({
            "schema": "autodisco.audio-look-twice-first-response/v0",
            "pair_id": pair_id,
            "packet_id": packet["packet_id"],
            "listener": listener,
            "window_id": window_id,
            "audio_sha256": audio_sha,
            "model_used": "fixture-model",
            "response_sha256": str(index + 1) * 64,
            "response": {
                "observations": [
                    {"mode": "OBSERVED", "text": "fixture observation"}
                ],
                "lingering_intrigue": True,
                "closing_line": "fixture closing line",
            },
            "laws": ["SEALED != SHARED"],
            "first_response_id": (
                "autodisco-audio-look-twice-response-v0:"
                + (("1" if listener["id"] == "static-sam" else "2") * 64)
            ),
        })
    return {
        "schema": "autodisco.audio-look-twice-encounter-result/v0",
        "status": "two-first-responses-sealed",
        "pair_id": pair_id,
        "window_id": window_id,
        "first_responses": firsts,
        "model_used": "fixture-model",
        "laws": ["SEALED != SHARED"],
    }


def dialogue(window_id, audio_sha, pair_id):
    firsts = encounter(window_id, audio_sha, pair_id)["first_responses"]
    packet = {
        "schema": "autodisco.audio-look-twice-dialogue-packet/v0",
        "pair_id": pair_id,
        "window_ref": pair(window_id, audio_sha, pair_id)["window_ref"],
        "sealed_first_responses": [
            {
                "first_response_id": item["first_response_id"],
                "listener": item["listener"],
                "response_sha256": item["response_sha256"],
                "response": item["response"],
            }
            for item in firsts
        ],
        "rules": ["AUDIO WINDOW IS NOT REOPENED"],
        "dialogue_packet_id": "dialogue-packet:" + pair_id,
    }
    return {
        "schema": "autodisco.audio-look-twice-dialogue-result/v0",
        "status": "dialogue-sealed",
        "dialogue_packet": packet,
        "dialogue": {
            "turns": [
                {"listener_id": "static-sam", "text": "fixture A"},
                {"listener_id": "juniper", "text": "fixture B"},
            ],
            "convergences": ["fixture convergence"],
            "differences": ["fixture difference"],
            "lingering_intrigue": True,
            "intrigue_statement": "fixture intrigue",
            "door_seed": "fixture next",
        },
        "dialogue_sha256": "a" * 64,
        "model_used": "fixture-model",
        "laws": ["DOOR SEED != CROSSING"],
        "dialogue_id": "dialogue:" + pair_id,
    }


def phono_answer():
    return {
        "schema": "workbench.phonograph-field-answer/v0",
        "status": "proposal-ready",
        "window_id": PARENT_WINDOW,
        "audio_sha256": PARENT_SHA,
        "seed": "fixture",
        "proposal_receipt_hash": PROPOSAL_RECEIPT,
        "signal_evidence_hash": "sha256:" + "b" * 64,
        "proposal_hash": "sha256:" + "c" * 64,
        "resolved_performance_hash": "sha256:" + "d" * 64,
        "proposal": {
            "authority": "proposal",
            "subject": "field-answer-musical-object",
        },
        "signal_profile": {
            "authority": "evidence",
            "subject": "bounded-pcm-signal-profile",
        },
        "midi": {"sha256": "sha256:" + "e" * 64, "path": "/tmp/answer.mid"},
        "audition": {
            "sha256": "sha256:" + "f" * 64,
            "path": "/tmp/audition.wav",
        },
        "phonograph_receipt": {"status": "proposal-ready"},
        "receipt_path": "/tmp/phono-receipt.json",
        "laws": [
            "SIGNAL FACT != MUSICAL MEANING",
            "PROPOSAL != SOURCE EVIDENCE",
            "AUDITION != ADMISSION",
            "FIELD ANSWER != HOUSE CROSSING",
        ],
    }


def seed_generation(store: DoorHouse, receipt_id: str, *, child_dialogue=True):
    parent = window(PARENT_WINDOW, PARENT_SHA)
    store.record_audio_window(receipt_id, parent)
    store.record_audio_look_twice_pair(
        receipt_id, pair(PARENT_WINDOW, PARENT_SHA, PARENT_PAIR)
    )
    store.record_audio_look_twice_encounters(
        receipt_id, encounter(PARENT_WINDOW, PARENT_SHA, PARENT_PAIR)
    )
    store.record_audio_look_twice_dialogue(
        receipt_id, dialogue(PARENT_WINDOW, PARENT_SHA, PARENT_PAIR)
    )

    answer = phono_answer()
    store.record_phonograph_field_answer(receipt_id, answer)
    lineage = {
        "schema": "workbench.phonograph-reentry-lineage/v0",
        "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
        "human_action": "explicit-admit",
        "parent_window_id": PARENT_WINDOW,
        "parent_audio_sha256": PARENT_SHA,
        "proposal_receipt_hash": PROPOSAL_RECEIPT,
        "proposal_hash": answer["proposal_hash"],
        "resolved_performance_hash": answer["resolved_performance_hash"],
        "audition_sha256": answer["audition"]["sha256"],
        "audition_frame_count": 44100,
        "admitted_start_ms": 0,
        "admitted_end_ms": 1000,
        "trimmed_submillisecond_tail": False,
    }
    child = window(CHILD_WINDOW, CHILD_SHA, lineage=lineage)
    store.record_audio_window(receipt_id, child)
    store.record_phonograph_reentry(
        receipt_id, PARENT_WINDOW, answer, child
    )
    store.record_audio_look_twice_pair(
        receipt_id, pair(CHILD_WINDOW, CHILD_SHA, CHILD_PAIR)
    )
    store.record_audio_look_twice_encounters(
        receipt_id, encounter(CHILD_WINDOW, CHILD_SHA, CHILD_PAIR)
    )
    if child_dialogue:
        store.record_audio_look_twice_dialogue(
            receipt_id, dialogue(CHILD_WINDOW, CHILD_SHA, CHILD_PAIR)
        )
    return parent, child


def dogram_result(tmp_path: Path, receipt_id: str):
    slug = hashlib.sha256(CHILD_WINDOW.encode("utf-8")).hexdigest()[:24]
    root = tmp_path / "doorhouse-dogram" / receipt_id / slug
    root.mkdir(parents=True, exist_ok=True)
    dogram_receipt = {
        "schema": "dogram.generation-delta-receipt/v0",
        "specimen": "GENERATION-DELTA-001",
        "status": "OK",
        "transform": {
            "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
            "human_action": "explicit-admit",
            "parent_window_id": PARENT_WINDOW,
            "child_window_id": CHILD_WINDOW,
            "proposal_receipt_hash": PROPOSAL_RECEIPT,
            "audition_sha256": "sha256:" + "f" * 64,
        },
        "parent": {
            "window_id": PARENT_WINDOW,
            "audio_sha256": "sha256:" + PARENT_SHA,
            "profile": {},
        },
        "child": {
            "window_id": CHILD_WINDOW,
            "audio_sha256": "sha256:" + CHILD_SHA,
            "profile": {},
        },
        "delta": {
            "axes": {"peak_q15": 120},
            "changed_axes": ["peak_q15"],
            "unchanged_axes": [],
            "classification": "MEASURED_CHANGE",
        },
        "residuals": ["semantic_meaning_not_measured"],
        "laws": [
            "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
            "DELTA != VALUE",
            "MEASURED CHANGE != MUSICAL MEANING",
            "RESIDUAL != FAILURE",
            "DESCENDANT != PARENT",
            "ANCESTRY != AUTHORITY",
            "DO NOT DECIDE WHAT IT MEANS",
        ],
        "receipt_hash": "sha256:" + "0" * 64,
    }
    receipt_path = root / "generation-delta.json"
    receipt_path.write_text(
        json.dumps(dogram_receipt, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="utf-8",
    )
    return {
        "schema": "workbench.dogram-generation-delta/v0",
        "status": "measured",
        "parent_window_id": PARENT_WINDOW,
        "child_window_id": CHILD_WINDOW,
        "proposal_receipt_hash": PROPOSAL_RECEIPT,
        "dogram_receipt_hash": dogram_receipt["receipt_hash"],
        "classification": "MEASURED_CHANGE",
        "changed_axes": ["peak_q15"],
        "unchanged_axes": [],
        "delta": dogram_receipt["delta"],
        "residuals": dogram_receipt["residuals"],
        "dogram_receipt": dogram_receipt,
        "receipt_path": str(receipt_path),
        "laws": [
            "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
            "DELTA != VALUE",
            "MEASURED CHANGE != MUSICAL MEANING",
            "RESIDUAL != FAILURE",
            "SIGNAL DELTA != LISTENER DELTA",
            "MEASUREMENT != ADMISSION",
        ],
    }


def test_house_accepts_delta_only_after_both_generations_are_witnessed(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    seed_generation(store, receipt["id"], child_dialogue=False)
    result = dogram_result(tmp_path, receipt["id"])

    with pytest.raises(DoorHouseConflict, match="both parent and descendant"):
        store.record_dogram_generation_delta(receipt["id"], result)

    store.record_audio_look_twice_dialogue(
        receipt["id"], dialogue(CHILD_WINDOW, CHILD_SHA, CHILD_PAIR)
    )
    state = store.record_dogram_generation_delta(receipt["id"], result)
    witness = next(
        item for item in state["external_witnesses"]
        if item["kind"] == "dogram_generation_delta:" + CHILD_WINDOW
    )
    assert witness["snapshot"]["classification"] == "MEASURED_CHANGE"
    assert witness["snapshot"]["changed_axes"] == ["peak_q15"]
    assert "DOGRAM RECEIPT != MUSICAL VERDICT" in witness["snapshot"]["laws"]


def test_api_measurement_and_receipt_read_are_bounded(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    seed_generation(store, receipt["id"], child_dialogue=True)
    result = dogram_result(config.state_dir, receipt["id"])

    monkeypatch.setattr(
        app_module,
        "run_dogram_generation_delta",
        lambda parent, child, reentry, repos, state_dir, receipt_id: result,
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        measured = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/dogram/"
            f"{CHILD_WINDOW}/generation-delta",
            json={},
            headers=headers,
        )
        assert measured.status_code == 200

        before = client.get("/api/doorhouse/state").json()
        read = client.get(
            f"/api/doorhouse/receipts/{receipt['id']}/dogram/"
            f"{CHILD_WINDOW}/generation-delta.json"
        )
        after = client.get("/api/doorhouse/state").json()

        assert read.status_code == 200
        payload = read.json()
        assert payload["specimen"] == "GENERATION-DELTA-001"
        assert payload["delta"]["classification"] == "MEASURED_CHANGE"
        assert before["world_version"] == after["world_version"]
        assert len(before["external_witnesses"]) == len(after["external_witnesses"])


def test_direct_api_measurement_refuses_before_child_cross_read(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    seed_generation(store, receipt["id"], child_dialogue=False)

    called = {"value": False}

    def should_not_run(*args, **kwargs):
        called["value"] = True
        raise AssertionError("Dogram should not run before witness gate")

    monkeypatch.setattr(app_module, "run_dogram_generation_delta", should_not_run)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        response = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/dogram/"
            f"{CHILD_WINDOW}/generation-delta",
            json={},
            headers={"x-workbench-session": token},
        )
        assert response.status_code == 409
        assert "both parent and descendant" in response.json()["detail"]
        assert called["value"] is False
