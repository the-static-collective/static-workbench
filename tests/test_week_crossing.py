"""PINCERSMASH-002: cold, offline, independently inspected cross-language carriers."""
import hashlib
import json
import subprocess
import sys

import pytest

from static_workbench.week_crossing import (
    TRACKS, NOTE_SCHEMA, WEEK_SOURCE_BLOB, EVIDENCE_SCHEMA, WeekCrossingRefused,
    inspect_notes, inspect_evidence, inspect_crossing, parse_document,
)


SONG = "70b1d32e-21b6-4340-990d-1a4ef67cfc42"


def js_bytes(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def note_parcel(track=SONG, text="A small deliberate crack in the voice.") -> dict:
    payload = {
        "schema": NOTE_SCHEMA,
        "sourceBlobSha1": WEEK_SOURCE_BLOB,
        "trackId": track,
        "notes": [{"kind": "observation", "text": text}],
    }
    return {"payload": payload, "sha256": hashlib.sha256(js_bytes(payload)).hexdigest(),
            "attestation": "UNSIGNED_HUMAN_ASSERTION"}


def docket(bytes_):
    return {
        "schema": EVIDENCE_SCHEMA, "provider": "suno", "providerTrackId": SONG,
        "assetRole": "audio_wav", "observedAt": "2026-10-11T20:00:00.000Z",
        "byteLength": len(bytes_), "sha256": hashlib.sha256(bytes_).hexdigest(),
        "sourceReceiptSha256": "a" * 64,
        "sourceMethod": "vault-local-byte-verification",
        "state": "VERIFIED_AT_SOURCE",
        "authority": "SOURCE_CLAIM_ONLY_UNTIL_INDEPENDENT_BYTES",
    }


def test_exact_witnessed_catalog_14_unique_tracks():
    assert len(TRACKS) == 14
    assert len(WEEK_SOURCE_BLOB) == 40


def test_unsigned_browser_notes_remain_hold():
    result = inspect_notes(note_parcel(text="A little moon and a little fire 🔥"))
    assert result["state"] == "HOLD"
    assert result["source"] == "UNSIGNED_HUMAN_ASSERTION"
    assert result["effect"] == "none"


def test_tampering_reordered_fields_extra_fields_invalid_sources_and_duplicate_json_refuse():
    good = note_parcel()
    cases = []
    edited = json.loads(json.dumps(good))
    edited["payload"]["notes"][0]["text"] = "rewritten"
    cases.append(edited)
    reordered = {"sha256": good["sha256"], "payload": good["payload"],
                 "attestation": good["attestation"]}
    cases.append(reordered)
    extra = {**good, "canon": True}
    cases.append(extra)
    forged = note_parcel(track="not-on-the-album")
    cases.append(forged)
    bad_kind = note_parcel()
    bad_kind["payload"]["notes"][0]["kind"] = ["observation"]
    cases.append(bad_kind)
    wrong_blob = note_parcel()
    wrong_blob["payload"]["sourceBlobSha1"] = "0" * 40
    cases.append(wrong_blob)
    for sample in cases:
        with pytest.raises(WeekCrossingRefused):
            inspect_notes(sample)
    with pytest.raises(WeekCrossingRefused, match="duplicate"):
        parse_document(b'{"payload":{},"payload":{},"sha256":null}')


def test_browser_utf16_limits_match_emoji():
    too_long = note_parcel(text="🍋" * 251)  # 502 UTF-16 code units
    with pytest.raises(WeekCrossingRefused, match="too long"):
        inspect_notes(too_long)
    accepted = note_parcel(text="🍋" * 250)
    assert inspect_notes(accepted)["noteCount"] == 1


def test_two_machine_claim_only_until_independent_bytes(tmp_path):
    payload = b"RIFF_Synthetic_crossing_not_a_real_song"
    path = tmp_path / "human-carried.wav"
    path.write_bytes(payload)
    claim = inspect_evidence(docket(payload))
    assert claim["state"] == "HOLD"
    assert claim["verifiedLocalBytes"] is False
    joined = inspect_crossing(note_parcel(), docket(payload), path)
    assert joined["state"] == "HOLD"
    assert joined["evidence"]["verifiedLocalBytes"] is True
    assert joined["notes"]["source"] == "UNSIGNED_HUMAN_ASSERTION"
    assert joined["law"] == "SOURCE_CLAIM != RECEIVER_PROOF != HUMAN_ADMISSION"
    path.write_bytes(b"modified")
    with pytest.raises(WeekCrossingRefused, match="mismatch"):
        inspect_crossing(note_parcel(), docket(payload), path)


def test_cross_track_join_refused():
    a = note_parcel(track=next(s for s in TRACKS if s != SONG))
    with pytest.raises(WeekCrossingRefused, match="different songs"):
        inspect_crossing(a, docket(b"test"))


def test_evidence_malformed_roles_and_bad_sizes_refuse():
    a = docket(b"test")
    a["assetRole"] = ["audio_wav"]
    with pytest.raises(WeekCrossingRefused):
        inspect_evidence(a)
    b = docket(b"test")
    b["byteLength"] = True
    with pytest.raises(WeekCrossingRefused):
        inspect_evidence(b)


def test_cli_cold_replay_without_network_or_side_effect(tmp_path):
    audio = b"RIFF_test_demo_only"
    notes = tmp_path / "notes.json"
    evidence = tmp_path / "docket.json"
    asset = tmp_path / "audio.wav"
    notes.write_text(json.dumps(note_parcel()), encoding="utf-8")
    evidence.write_text(json.dumps(docket(audio)), encoding="utf-8")
    asset.write_bytes(audio)
    script = __import__("pathlib").Path(__file__).resolve().parents[1] / "scripts" / "inspect_week_crossing.py"
    result = subprocess.run(
        [sys.executable, str(script), "--notes", str(notes),
         "--docket", str(evidence), "--asset", str(asset)],
        capture_output=True, text=True, timeout=15, check=False,
    )
    assert result.returncode == 0, result.stderr
    report = json.loads(result.stdout)
    assert report["state"] == "HOLD"
    assert report["evidence"]["verifiedLocalBytes"] is True
    assert list(tmp_path.iterdir()).__len__() == 3  # no writes from receiver
