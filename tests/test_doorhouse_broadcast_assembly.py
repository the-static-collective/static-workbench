from pathlib import Path

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


def materialized(window_id=WINDOW_ID):
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
            "declared_metadata": {"window_label": "episode-window"},
            "laws": ["WINDOW != WHOLE TRACK"],
            "window_id": window_id,
        },
        "laws": ["WINDOW DIGEST BINDS HEARD BYTES"],
    }


def pair():
    ref = {
        "window_id": WINDOW_ID,
        "source_sha256": "4" * 64,
        "audio_sha256": AUDIO_SHA,
        "media_type": "audio/wav",
        "requested_bounds": {"start_ms": 1000, "end_ms": 2000},
        "duration_ms": 1000,
        "declared_metadata": {"window_label": "episode-window"},
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
            "closing_line": "The cutoff makes the next window feel necessary.",
        },
        "laws": ["SEALED != SHARED"],
        "first_response_id": (
            "autodisco-audio-look-twice-response-v0:"
            + (("8" if listener_id == "static-sam" else "9") * 64)
        ),
    }


def encounter():
    p = pair()
    return {
        "schema": "autodisco.audio-look-twice-encounter-result/v0",
        "status": "two-first-responses-sealed",
        "pair_id": PAIR_ID,
        "window_id": WINDOW_ID,
        "first_responses": [
            sealed("static-sam", p["packets"][0]["packet_id"]),
            sealed("juniper", p["packets"][1]["packet_id"]),
        ],
        "model_used": "gemini-live-test",
        "laws": ["SEALED != SHARED"],
    }


def dialogue():
    firsts = encounter()["first_responses"]
    packet = {
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
    body = {
        "turns": [
            {"listener_id": "static-sam", "text": "I heard architecture in the cutoff."},
            {"listener_id": "juniper", "text": "I heard emotional pressure in the same edge."},
        ],
        "convergences": ["Both hear unresolved continuation."],
        "differences": ["They locate the unresolvedness differently."],
        "lingering_intrigue": True,
        "intrigue_statement": "The next few seconds matter.",
        "door_seed": "Move the window forward and listen again.",
    }
    return {
        "schema": "autodisco.audio-look-twice-dialogue-result/v0",
        "status": "dialogue-sealed",
        "dialogue_packet": packet,
        "dialogue": body,
        "dialogue_sha256": "b" * 64,
        "model_used": "gemini-live-test",
        "laws": ["DOOR SEED != CROSSING"],
        "dialogue_id": "autodisco-audio-look-twice-dialogue-result-v0:" + "c" * 64,
    }


def seed_radio_evidence(store: DoorHouse):
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    store.record_audio_look_twice_pair(receipt["id"], pair())
    store.record_audio_look_twice_encounters(receipt["id"], encounter())
    store.record_audio_look_twice_dialogue(receipt["id"], dialogue())
    return receipt


def fake_episode(state_dir: Path, receipt_id: str, pair_id=PAIR_ID):
    episode_id = "first-signal-deadbeefcafe"
    root = state_dir / "doorhouse-radio" / receipt_id / episode_id
    root.mkdir(parents=True, exist_ok=True)
    html = "<!doctype html><title>First Signal</title><button>PLAY EPISODE</button>"
    audio = b"RIFFfake-window"
    manifest = '{"schema":"autodisco.broadcast-episode/v0"}\n'
    (root / "index.html").write_text(html, encoding="utf-8")
    (root / "window.wav").write_bytes(audio)
    (root / "episode.json").write_text(manifest, encoding="utf-8")
    return {
        "schema": "workbench.broadcast-episode-materialized/v0",
        "episode_id": episode_id,
        "episode_digest": "d" * 64,
        "title": "First Signal · episode-window",
        "station_name": "Static Collective Radio",
        "window_id": WINDOW_ID,
        "audio_sha256": AUDIO_SHA,
        "pair_id": pair_id,
        "first_response_ids": sorted(
            item["first_response_id"] for item in encounter()["first_responses"]
        ),
        "dialogue_id": dialogue()["dialogue_id"],
        "bundle_dir": str(root),
        "manifest_path": str(root / "episode.json"),
        "manifest_sha256": "e" * 64,
        "audio_path": str(root / "window.wav"),
        "html_path": str(root / "index.html"),
        "html_sha256": "f" * 64,
        "laws": ["ASSEMBLY != VOICE RENDER"],
    }


def test_episode_witness_requires_exact_pair_firsts_and_dialogue(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = seed_radio_evidence(store)

    good = fake_episode(tmp_path, receipt["id"])
    state = store.record_broadcast_episode(receipt["id"], good)
    witness = next(
        item for item in state["external_witnesses"]
        if item["kind"] == "broadcast_episode:" + good["episode_id"]
    )
    assert witness["snapshot"]["pair_id"] == PAIR_ID
    assert witness["snapshot"]["dialogue_id"] == dialogue()["dialogue_id"]
    assert state["letters"][0]["body"] is None
    assert state["letters"][0]["title"] == "The station has something you can press Play on."

    bad = fake_episode(tmp_path, receipt["id"], pair_id="wrong-pair")
    try:
        store.record_broadcast_episode(receipt["id"], bad)
    except DoorHouseConflict:
        pass
    else:
        raise AssertionError("mismatched episode pair was accepted")


def test_player_routes_are_read_only_and_bound_to_house_bundle(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = seed_radio_evidence(store)
    episode = fake_episode(config.state_dir, receipt["id"])

    monkeypatch.setattr(
        app_module,
        "assemble_broadcast_episode",
        lambda materialized_value, pair_value, firsts, packet, dialogue_value,
               repos, state_dir, receipt_id: episode,
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        assembled = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/radio/assemble",
            json={},
            headers=headers,
        )
        assert assembled.status_code == 200
        before = client.get("/api/doorhouse/state").json()

        base = (
            f"/api/doorhouse/receipts/{receipt['id']}/radio/"
            f"{episode['episode_id']}/"
        )
        player = client.get(base)
        assert player.status_code == 200
        assert "PLAY EPISODE" in player.text

        audio = client.get(base + "window.wav")
        assert audio.status_code == 200
        assert audio.content == b"RIFFfake-window"

        manifest = client.get(base + "episode.json")
        assert manifest.status_code == 200
        assert "autodisco.broadcast-episode/v0" in manifest.text

        after = client.get("/api/doorhouse/state").json()
        assert before["world_version"] == after["world_version"]
        assert len(before["letters"]) == len(after["letters"])
        assert len(before["external_witnesses"]) == len(after["external_witnesses"])


def test_episode_route_refuses_bundle_path_substitution(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = seed_radio_evidence(store)
    episode = fake_episode(config.state_dir, receipt["id"])
    episode["html_path"] = str(tmp_path / "outside.html")
    (tmp_path / "outside.html").write_text("outside", encoding="utf-8")
    store.record_broadcast_episode(receipt["id"], episode)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.get(
            f"/api/doorhouse/receipts/{receipt['id']}/radio/"
            f"{episode['episode_id']}/"
        )
        assert response.status_code == 409
