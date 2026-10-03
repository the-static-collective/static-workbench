from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict


WINDOW_ID = "autodisco-audio-window-v0:" + "1" * 64
AUDIO_SHA = "2" * 64
PROPOSAL_RECEIPT = "sha256:" + "3" * 64


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


def materialized():
    return {
        "schema": "workbench.audio-window-materialized/v0",
        "window_id": WINDOW_ID,
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
            "declared_metadata": {"window_label": "phono-window"},
            "laws": ["WINDOW != WHOLE TRACK"],
            "window_id": WINDOW_ID,
        },
        "laws": ["WINDOW DIGEST BINDS HEARD BYTES"],
    }


def answer(state_dir: Path, receipt_id: str, window_id=WINDOW_ID):
    slug = PROPOSAL_RECEIPT.split(":", 1)[1][:24]
    root = state_dir / "doorhouse-phonograph" / receipt_id / slug
    root.mkdir(parents=True, exist_ok=True)
    midi = b"MThd" + b"midi-fixture"
    wav = b"RIFF" + b"\x00\x00\x00\x00" + b"WAVE" + b"audition-fixture"
    receipt_text = '{"schema":"haunted-phonograph/field-answer-result/v0"}\n'
    (root / "answer.mid").write_bytes(midi)
    (root / "audition.wav").write_bytes(wav)
    (root / "receipt.json").write_text(receipt_text, encoding="utf-8")
    return {
        "schema": "workbench.phonograph-field-answer/v0",
        "status": "proposal-ready",
        "window_id": window_id,
        "audio_sha256": AUDIO_SHA,
        "seed": "house-field-answer-v0:test",
        "proposal_receipt_hash": PROPOSAL_RECEIPT,
        "signal_evidence_hash": "sha256:" + "6" * 64,
        "proposal_hash": "sha256:" + "7" * 64,
        "resolved_performance_hash": "sha256:" + "8" * 64,
        "proposal": {
            "schema": "haunted-phonograph/provenance-claim/v1",
            "authority": "proposal",
            "subject": "field-answer-musical-object",
            "value": {
                "tempoBpm": 92,
                "pitches": [60, 62, 65, 63],
                "durationsQuarter": [1, 0.5, 0.75, 1],
                "velocities": [64, 72, 88, 70],
                "synthesis": "sine-plus-second-harmonic/v0",
            },
            "parentRefs": ["sha256:" + "6" * 64],
            "proposer": {"id": "field-answer-001"},
            "policy": {
                "id": "bounded-signal-contour-to-musical-proposal",
                "version": "0",
            },
        },
        "signal_profile": {
            "schema": "haunted-phonograph/provenance-claim/v1",
            "authority": "evidence",
            "subject": "bounded-pcm-signal-profile",
            "value": {
                "frameCount": 44100,
                "durationMs": 1000,
                "rmsQuartilesQ15": [1000, 2000, 3000, 2500],
                "peakQ15": 12000,
                "zeroCrossingPpm": 100000,
            },
            "sourceRefs": ["sha256:" + AUDIO_SHA],
            "method": {
                "id": "canonical-pcm-signal-profile",
                "version": "0",
            },
        },
        "midi": {
            "sha256": "sha256:" + "9" * 64,
            "byte_length": len(midi),
            "profile": "smf0-ppq480/v1",
            "path": str(root / "answer.mid"),
        },
        "audition": {
            "sha256": "sha256:" + "a" * 64,
            "byte_length": len(wav),
            "media_type": "audio/wav",
            "renderer": "sine-plus-second-harmonic/v0",
            "path": str(root / "audition.wav"),
        },
        "phonograph_receipt": {
            "schema": "haunted-phonograph/field-answer-receipt/v0",
            "status": "proposal-ready",
            "proposal_hash": "sha256:" + "7" * 64,
            "resolved_performance_hash": "sha256:" + "8" * 64,
            "laws": [
                "SIGNAL FACT != MUSICAL MEANING",
                "PROPOSAL != SOURCE EVIDENCE",
                "AUDITION != ADMISSION",
            ],
        },
        "receipt_path": str(root / "receipt.json"),
        "laws": [
            "SIGNAL FACT != MUSICAL MEANING",
            "PROPOSAL != SOURCE EVIDENCE",
            "RESPONSE != REMIX",
            "AUDITION != ADMISSION",
            "FIELD ANSWER != HOUSE CROSSING",
            "MUSICAL POSSIBILITY != RECOMMENDATION",
        ],
    }


def test_answer_witness_binds_latest_exact_audio_window(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())

    good = answer(tmp_path, receipt["id"])
    state = store.record_phonograph_field_answer(receipt["id"], good)
    witness = next(
        item for item in state["external_witnesses"]
        if item["kind"] == "phonograph_field_answer:" + WINDOW_ID
    )
    assert witness["snapshot"]["proposal"]["authority"] == "proposal"
    assert witness["snapshot"]["signal_profile"]["authority"] == "evidence"
    assert "PHONOGRAPH PROPOSAL != HOUSE ADMISSION" in witness["snapshot"]["laws"]

    wrong = answer(
        tmp_path,
        receipt["id"],
        window_id="autodisco-audio-window-v0:" + "f" * 64,
    )
    with pytest.raises(DoorHouseConflict, match="latest audio window"):
        store.record_phonograph_field_answer(receipt["id"], wrong)


def test_answer_routes_are_read_only_and_bound_to_bundle(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    result = answer(config.state_dir, receipt["id"])

    monkeypatch.setattr(
        app_module,
        "run_phonograph_field_answer",
        lambda materialized_audio, repos, state_dir, receipt_id: result,
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}

        response = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/phonograph/field-answer",
            json={},
            headers=headers,
        )
        assert response.status_code == 200

        before = client.get("/api/doorhouse/state").json()
        base = (
            f"/api/doorhouse/receipts/{receipt['id']}/phonograph/"
            f"{WINDOW_ID}/"
        )
        audition = client.get(base + "audition.wav")
        midi = client.get(base + "answer.mid")
        receipt_json = client.get(base + "receipt.json")
        after = client.get("/api/doorhouse/state").json()

        assert audition.status_code == 200
        assert audition.content.startswith(b"RIFF")
        assert midi.status_code == 200
        assert midi.content.startswith(b"MThd")
        assert receipt_json.status_code == 200

        assert before["world_version"] == after["world_version"]
        assert len(before["letters"]) == len(after["letters"])
        assert len(before["external_witnesses"]) == len(after["external_witnesses"])


def test_answer_route_refuses_path_substitution(monkeypatch, tmp_path):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    result = answer(config.state_dir, receipt["id"])
    result["audition"]["path"] = str(tmp_path / "outside.wav")
    (tmp_path / "outside.wav").write_bytes(b"RIFFxxxxWAVEoutside")
    store.record_phonograph_field_answer(receipt["id"], result)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.get(
            f"/api/doorhouse/receipts/{receipt['id']}/phonograph/"
            f"{WINDOW_ID}/audition.wav"
        )
        assert response.status_code == 409
