from pathlib import Path
import hashlib
import io
import wave

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
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as handle:
        handle.setnchannels(2)
        handle.setsampwidth(2)
        handle.setframerate(44100)
        handle.writeframes(b"\\x00\\x00\\x00\\x00" * 44100)
    wav = buffer.getvalue()
    audition_sha = hashlib.sha256(wav).hexdigest()
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
            "sha256": "sha256:" + audition_sha,
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


CHILD_WINDOW_ID = "autodisco-audio-window-v0:" + "c" * 64
CHILD_AUDIO_SHA = "d" * 64


def child_materialized(parent_answer):
    audition_hex = parent_answer["audition"]["sha256"].split(":", 1)[1]
    lineage = {
        "schema": "workbench.phonograph-reentry-lineage/v0",
        "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
        "human_action": "explicit-admit",
        "parent_window_id": WINDOW_ID,
        "parent_audio_sha256": AUDIO_SHA,
        "proposal_receipt_hash": parent_answer["proposal_receipt_hash"],
        "proposal_hash": parent_answer["proposal_hash"],
        "resolved_performance_hash": parent_answer["resolved_performance_hash"],
        "audition_sha256": parent_answer["audition"]["sha256"],
        "audition_frame_count": 44100,
        "admitted_start_ms": 0,
        "admitted_end_ms": 1000,
        "trimmed_submillisecond_tail": False,
    }
    return {
        "schema": "workbench.audio-window-materialized/v0",
        "window_id": CHILD_WINDOW_ID,
        "source_path": parent_answer["audition"]["path"],
        "audio_path": "/tmp/child-window.wav",
        "audio_sha256": CHILD_AUDIO_SHA,
        "audio_size_bytes": 176444,
        "window": {
            "schema": "autodisco.audio-window/v0",
            "source": {
                "sha256": audition_hex,
                "media_type": "audio/wav",
                "basename": "audition.wav",
            },
            "requested_bounds": {"start_ms": 0, "end_ms": 1000},
            "canonical_audio": {
                "media_type": "audio/wav",
                "sha256": CHILD_AUDIO_SHA,
                "size_bytes": 176444,
                "sample_rate_hz": 44100,
                "channels": 2,
                "bits_per_sample": 16,
                "frame_count": 44100,
                "duration_ms": 1000,
                "base64_sha256": "e" * 64,
            },
            "extraction": {
                "method": "direct-canonical-wav-slice",
                "start_frame": 0,
                "end_frame": 44100,
                "actual_start_ms": 0,
                "actual_end_ms": 1000,
            },
            "declared_metadata": {"window_label": "phono-answer-test"},
            "laws": ["WINDOW != WHOLE TRACK"],
            "window_id": CHILD_WINDOW_ID,
        },
        "source_lineage": lineage,
        "laws": [
            "WINDOW DIGEST BINDS HEARD BYTES",
            "HUMAN ADMISSION != PHONOGRAPH AUTHORITY",
            "DESCENDANT != PARENT",
            "REENTRY != RESET",
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



def test_explicit_admission_creates_descendant_and_preserves_parent_witness(
    monkeypatch, tmp_path
):
    config = config_for(tmp_path)
    store = DoorHouse(config.state_dir / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_audio_window(receipt["id"], materialized())
    parent_answer = answer(config.state_dir, receipt["id"])
    store.record_phonograph_field_answer(receipt["id"], parent_answer)
    child = child_materialized(parent_answer)

    monkeypatch.setattr(
        app_module,
        "admit_phonograph_answer_as_audio_window",
        lambda answer_value, repos, state_dir, receipt_id: child,
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        response = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/phonograph/"
            f"{WINDOW_ID}/admit-radio",
            json={},
            headers=headers,
        )
        assert response.status_code == 200
        state = response.json()

        assert any(
            item["kind"] == "phonograph_field_answer:" + WINDOW_ID
            for item in state["external_witnesses"]
        )
        reentry = next(
            item for item in state["external_witnesses"]
            if item["kind"] == "phonograph_reentry:" + CHILD_WINDOW_ID
        )
        assert reentry["snapshot"]["parent_window_id"] == WINDOW_ID
        assert reentry["snapshot"]["child_window_id"] == CHILD_WINDOW_ID
        assert reentry["snapshot"]["proposal_receipt_hash"] == PROPOSAL_RECEIPT
        assert "RECURSION REQUIRES FRESH WITNESS" in reentry["snapshot"]["laws"]

        latest = max(
            (
                item for item in state["external_witnesses"]
                if item["kind"].startswith("audio_window:")
            ),
            key=lambda item: item["created_at"],
        )
        assert latest["snapshot"]["window_id"] == CHILD_WINDOW_ID
        assert (
            latest["snapshot"]["source_lineage"]["parent_window_id"]
            == WINDOW_ID
        )

        stale = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/phonograph/"
            f"{WINDOW_ID}/admit-radio",
            json={},
            headers=headers,
        )
        assert stale.status_code == 409
        assert "current audio window" in stale.json()["detail"]
