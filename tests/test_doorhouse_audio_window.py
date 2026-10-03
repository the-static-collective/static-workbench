from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict


WINDOW_ID = "autodisco-audio-window-v0:" + "1" * 64
PAIR_ID = "autodisco-audio-look-twice-pair-v0:" + "2" * 64
AUDIO_SHA = "3" * 64


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


def materialized(window_id=WINDOW_ID, label="window-001"):
    return {
        "schema": "workbench.audio-window-materialized/v0",
        "window_id": window_id,
        "source_path": "/tmp/source.wav",
        "audio_path": "/tmp/window.wav",
        "audio_sha256": AUDIO_SHA,
        "audio_size_bytes": 176444,
        "window": {
            "schema": "autodisco.audio-window/v0",
            "source": {
                "sha256": "4" * 64,
                "media_type": "audio/wav",
                "basename": "source.wav",
            },
            "requested_bounds": {"start_ms": 1000, "end_ms": 2000},
            "canonical_audio": {
                "media_type": "audio/wav",
                "sha256": AUDIO_SHA,
                "size_bytes": 176444,
                "sample_rate_hz": 44100,
                "channels": 2,
                "bits_per_sample": 16,
                "frame_count": 44100,
                "duration_ms": 1000,
                "base64_sha256": "5" * 64,
            },
            "extraction": {
                "method": "direct-canonical-wav-slice",
                "start_frame": 44100,
                "end_frame": 88200,
                "actual_start_ms": 1000,
                "actual_end_ms": 2000,
            },
            "declared_metadata": {"window_label": label},
            "laws": ["WINDOW != WHOLE TRACK"],
            "window_id": window_id,
        },
        "laws": ["WINDOW DIGEST BINDS HEARD BYTES"],
    }


def pair(window_id=WINDOW_ID):
    ref = {
        "window_id": window_id,
        "source_sha256": "4" * 64,
        "audio_sha256": AUDIO_SHA,
        "media_type": "audio/wav",
        "requested_bounds": {"start_ms": 1000, "end_ms": 2000},
        "duration_ms": 1000,
        "declared_metadata": {"window_label": "window-001"},
    }
    packets = []
    for listener_id, role in [("static-sam", "Static Sam"), ("juniper", "Juniper")]:
        packets.append({
            "schema": "autodisco.audio-look-twice-first-packet/v0",
            "listener": {"id": listener_id, "role": role, "brief": "isolated"},
            "window_ref": ref,
            "prohibitions": ["NO WHOLE TRACK", "NO OTHER LISTENER RESPONSE"],
            "packet_id": f"autodisco-audio-look-twice-first-v0:{listener_id}",
        })
    return {
        "schema": "autodisco.audio-look-twice-pair/v0",
        "window_ref": ref,
        "packets": packets,
        "laws": ["FIRST LISTEN PRECEDES CROSS-READ"],
        "pair_id": PAIR_ID,
    }


def sealed(listener_id: str, packet_id: str):
    return {
        "schema": "autodisco.audio-look-twice-first-response/v0",
        "pair_id": PAIR_ID,
        "packet_id": packet_id,
        "listener": {
            "id": listener_id,
            "role": "Static Sam" if listener_id == "static-sam" else "Juniper",
            "brief": "isolated",
        },
        "window_id": WINDOW_ID,
        "audio_sha256": AUDIO_SHA,
        "model_used": "gemini-live-test",
        "response_sha256": ("6" if listener_id == "static-sam" else "7") * 64,
        "response": {
            "observations": [
                {"mode": "OBSERVED", "text": "A pulse repeats in stereo."},
                {"mode": "INTERPRETATION", "text": f"{listener_id} hears anticipation."},
            ],
            "lingering_intrigue": True,
            "closing_line": "The window ends before the phrase resolves.",
        },
        "laws": ["SEALED != SHARED"],
        "first_response_id": (
            "autodisco-audio-look-twice-response-v0:"
            + (("8" if listener_id == "static-sam" else "9") * 64)
        ),
    }


def encounter(status="two-first-responses-sealed"):
    p = pair()
    if status == "packets-only":
        return {
            "schema": "autodisco.audio-look-twice-encounter-result/v0",
            "status": status,
            "pair_id": PAIR_ID,
            "window_id": WINDOW_ID,
            "first_responses": [],
            "model_used": None,
            "laws": ["SIMULATION != FIRST LISTEN"],
        }
    return {
        "schema": "autodisco.audio-look-twice-encounter-result/v0",
        "status": status,
        "pair_id": PAIR_ID,
        "window_id": WINDOW_ID,
        "first_responses": [
            sealed("static-sam", p["packets"][0]["packet_id"]),
            sealed("juniper", p["packets"][1]["packet_id"]),
        ],
        "model_used": "gemini-live-test",
        "laws": ["SEALED != SHARED"],
    }


def dialogue_packet():
    firsts = encounter()["first_responses"]
    return {
        "schema": "autodisco.audio-look-twice-dialogue-packet/v0",
        "pair_id": PAIR_ID,
        "window_ref": pair()["window_ref"],
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
        "dialogue_packet_id": "autodisco-audio-look-twice-dialogue-v0:" + "a" * 64,
    }


def dialogue(status="dialogue-sealed", intrigue=True):
    if status == "dialogue-packet-only":
        return {
            "schema": "autodisco.audio-look-twice-dialogue-result/v0",
            "status": status,
            "dialogue_packet": dialogue_packet(),
            "dialogue": None,
            "model_used": None,
            "laws": ["SIMULATION != AUDIO DIALOGUE"],
        }
    body = {
        "turns": [
            {"listener_id": "static-sam", "text": "I heard the cutoff as structure."},
            {"listener_id": "juniper", "text": "I heard the same cutoff as emotional pressure."},
        ],
        "convergences": ["Both hear an unresolved ending."],
        "differences": ["They disagree about what kind of unresolvedness it is."],
        "lingering_intrigue": intrigue,
        "intrigue_statement": "The unresolved ending survives both readings." if intrigue else "",
        "door_seed": "What happens in the next thirty seconds?" if intrigue else None,
    }
    return {
        "schema": "autodisco.audio-look-twice-dialogue-result/v0",
        "status": status,
        "dialogue_packet": dialogue_packet(),
        "dialogue": body,
        "dialogue_sha256": "b" * 64,
        "model_used": "gemini-live-test",
        "laws": ["DOOR SEED != CROSSING"],
        "dialogue_id": "autodisco-audio-look-twice-dialogue-result-v0:" + "c" * 64,
    }


def test_audio_window_pair_and_first_listens_are_separate_witnesses(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)

    state = store.record_audio_window(receipt["id"], materialized())
    assert any(w["kind"].startswith("audio_window:") for w in state["external_witnesses"])

    state = store.record_audio_look_twice_pair(receipt["id"], pair())
    assert any(w["kind"].startswith("audio_look_twice_pair:") for w in state["external_witnesses"])
    assert store.audio_look_twice_first_responses(receipt["id"], PAIR_ID) == []

    state = store.record_audio_look_twice_encounters(receipt["id"], encounter())
    firsts = [
        w for w in state["external_witnesses"]
        if w["kind"].startswith("audio_look_twice_first:")
    ]
    assert len(firsts) == 2
    assert {w["snapshot"]["listener"]["id"] for w in firsts} == {
        "static-sam", "juniper"
    }
    newest = state["letters"][0]
    assert newest["body"] is None
    assert "same slice" in newest["title"].lower()


def test_audio_packets_only_preserves_zero_first_listens(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    store.record_audio_look_twice_pair(receipt["id"], pair())
    state = store.record_audio_look_twice_encounters(
        receipt["id"], encounter("packets-only")
    )
    assert store.audio_look_twice_first_responses(receipt["id"], PAIR_ID) == []
    assert not any(
        w["kind"].startswith("audio_look_twice_first:")
        for w in state["external_witnesses"]
    )


def test_audio_cross_read_refused_before_two_first_listens(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    store.record_audio_look_twice_pair(receipt["id"], pair())
    with pytest.raises(DoorHouseConflict, match="two sealed audio first listens"):
        store.record_audio_look_twice_dialogue(receipt["id"], dialogue())


def test_audio_dialogue_packet_only_does_not_invent_exchange(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    store.record_audio_look_twice_pair(receipt["id"], pair())
    store.record_audio_look_twice_encounters(receipt["id"], encounter())
    state = store.record_audio_look_twice_dialogue(
        receipt["id"], dialogue("dialogue-packet-only")
    )
    assert any(
        w["kind"].startswith("audio_look_twice_dialogue_packet:")
        for w in state["external_witnesses"]
    )
    assert not any(
        w["kind"].startswith("audio_look_twice_dialogue:")
        for w in state["external_witnesses"]
    )


def test_audio_intrigue_opens_new_sealed_letter_idempotently(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    store.record_audio_look_twice_pair(receipt["id"], pair())
    store.record_audio_look_twice_encounters(receipt["id"], encounter())

    result = dialogue()
    state = store.record_audio_look_twice_dialogue(receipt["id"], result)
    newest = state["letters"][0]
    assert newest["body"] is None
    assert newest["title"] == "They heard it twice. Something was still ringing."

    count = len(state["letters"])
    replay = store.record_audio_look_twice_dialogue(receipt["id"], result)
    assert len(replay["letters"]) == count


def test_audio_window_api_confines_source_to_configured_root(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    inside = config.roots[0].path / "song.wav"
    inside.write_bytes(b"fixture")

    monkeypatch.setattr(
        app_module,
        "build_audio_window",
        lambda source, receipt_id, state_dir, repos, **kwargs: materialized(),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        ok = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/audio-window",
            json={
                "root_id": "static",
                "relative_path": "song.wav",
                "start_ms": 0,
                "end_ms": 1000,
                "window_label": "specimen",
            },
            headers=headers,
        )
        assert ok.status_code == 200

        outside = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/audio-window",
            json={
                "root_id": "static",
                "relative_path": "../escape.wav",
                "start_ms": 0,
                "end_ms": 1000,
                "window_label": "escape",
            },
            headers=headers,
        )
        assert outside.status_code == 400


def test_audio_dialogue_api_stays_locked_after_packet_only_encounters(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())

    monkeypatch.setattr(
        app_module,
        "prepare_audio_look_twice",
        lambda materialized_value, repos: pair(),
    )
    monkeypatch.setattr(
        app_module,
        "run_audio_look_twice_encounters",
        lambda materialized_value, pair_value, repos: encounter("packets-only"),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        prepared = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/audio-look-twice/prepare",
            json={},
            headers=headers,
        )
        assert prepared.status_code == 200

        heard = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/audio-look-twice/encounters",
            json={},
            headers=headers,
        )
        assert heard.status_code == 200

        cross_read = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/autodisco/audio-look-twice/dialogue",
            json={},
            headers=headers,
        )
        assert cross_read.status_code == 409
