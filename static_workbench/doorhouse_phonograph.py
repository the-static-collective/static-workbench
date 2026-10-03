"""Bounded Haunted Phonograph FIELD ANSWER aperture for the House."""
from __future__ import annotations

import base64
import hashlib
import json
import os
import subprocess
import wave
from pathlib import Path

from .doorhouse_autodisco import (
    AutodiscoApertureError,
    build_audio_window,
    inflate_audio_window,
)
from .repos import RepoStatus


class PhonographApertureError(RuntimeError):
    pass


def _find_phonograph(repos: list[RepoStatus]) -> Path:
    matches = [
        Path(repo.path)
        for repo in repos
        if repo.name.casefold() == "the-haunted-phonography"
    ]
    if not matches:
        raise PhonographApertureError(
            "Haunted Phonograph checkout is not available under configured roots"
        )
    root = matches[0]
    script = root / "scripts" / "field-answer.mjs"
    if not script.is_file():
        raise PhonographApertureError(
            "Haunted Phonograph checkout lacks FIELD ANSWER 001"
        )
    return root


def phonograph_field_answer_available(repos: list[RepoStatus]) -> dict:
    for repo in repos:
        if repo.name.casefold() != "the-haunted-phonography":
            continue
        script = Path(repo.path) / "scripts" / "field-answer.mjs"
        return {
            "checkout_present": True,
            "available": script.is_file(),
            "repo_head": repo.head,
            "repo_branch": repo.branch,
            "capability": "field-answer-001" if script.is_file() else None,
        }
    return {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _decode_artifact(
    item: dict,
    *,
    field: str,
    prefix: str = "sha256:",
) -> bytes:
    if not isinstance(item, dict):
        raise PhonographApertureError(f"Phonograph {field} artifact is missing")
    encoded = item.get("base64")
    expected = item.get("sha256")
    expected_length = item.get("byte_length")
    if (
        not isinstance(encoded, str)
        or not isinstance(expected, str)
        or not expected.startswith(prefix)
        or not isinstance(expected_length, int)
        or expected_length <= 0
    ):
        raise PhonographApertureError(
            f"Phonograph {field} artifact identity is incomplete"
        )
    try:
        raw = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise PhonographApertureError(
            f"Phonograph {field} artifact base64 is invalid"
        ) from exc
    if len(raw) != expected_length:
        raise PhonographApertureError(
            f"Phonograph {field} artifact length changed in transit"
        )
    if prefix + _sha256_bytes(raw) != expected:
        raise PhonographApertureError(
            f"Phonograph {field} artifact digest changed in transit"
        )
    return raw


def run_phonograph_field_answer(
    materialized_audio: dict,
    repos: list[RepoStatus],
    state_dir: Path,
    receipt_id: str,
) -> dict:
    root = _find_phonograph(repos)
    try:
        window = inflate_audio_window(materialized_audio)
    except AutodiscoApertureError as exc:
        raise PhonographApertureError(str(exc)) from exc

    canonical = window.get("canonical_audio")
    source = window.get("source")
    if not isinstance(canonical, dict) or not isinstance(source, dict):
        raise PhonographApertureError("audio-window witness is incomplete")

    seed = "house-field-answer-v0:" + hashlib.sha256(
        str(window.get("window_id")).encode("utf-8")
    ).hexdigest()
    request = {
        "schema": "haunted-phonograph/field-answer-request/v0",
        "window": {
            "window_id": window.get("window_id"),
            "audio_sha256": canonical.get("sha256"),
            "source_sha256": source.get("sha256"),
            "requested_bounds": window.get("requested_bounds"),
            "duration_ms": canonical.get("duration_ms"),
            "media_type": canonical.get("media_type"),
            "base64": canonical.get("base64"),
        },
        "seed": seed,
    }

    try:
        completed = subprocess.run(
            ["node", str(root / "scripts" / "field-answer.mjs")],
            cwd=root,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=60.0,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise PhonographApertureError(
            f"Haunted Phonograph FIELD ANSWER could not run: {exc}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise PhonographApertureError(
            "Haunted Phonograph FIELD ANSWER refused the request: "
            + (detail or "unknown error")
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise PhonographApertureError(
            "Haunted Phonograph FIELD ANSWER returned invalid JSON"
        ) from exc

    if (
        not isinstance(result, dict)
        or result.get("schema") != "haunted-phonograph/field-answer-result/v0"
        or result.get("status") != "proposal-ready"
    ):
        raise PhonographApertureError(
            "unexpected Haunted Phonograph FIELD ANSWER result"
        )

    window_ref = result.get("source_window_ref")
    evidence = result.get("evidence")
    proposal = result.get("proposal")
    receipt = result.get("receipt")
    if (
        not isinstance(window_ref, dict)
        or window_ref.get("window_id") != materialized_audio.get("window_id")
        or window_ref.get("audio_sha256") != materialized_audio.get("audio_sha256")
        or not isinstance(evidence, dict)
        or evidence.get("signal_profile", {}).get("authority") != "evidence"
        or not isinstance(proposal, dict)
        or proposal.get("authority") != "proposal"
        or not isinstance(receipt, dict)
        or receipt.get("status") != "proposal-ready"
    ):
        raise PhonographApertureError(
            "Phonograph FIELD ANSWER lost evidence/proposal or source binding"
        )

    laws = set(receipt.get("laws") or [])
    required_laws = {
        "SIGNAL FACT != MUSICAL MEANING",
        "PROPOSAL != SOURCE EVIDENCE",
        "AUDITION != ADMISSION",
    }
    if not required_laws.issubset(laws):
        raise PhonographApertureError(
            "Phonograph FIELD ANSWER omitted required authority laws"
        )

    midi_bytes = _decode_artifact(result.get("midi"), field="MIDI")
    audition_bytes = _decode_artifact(result.get("audition"), field="audition")
    if not midi_bytes.startswith(b"MThd"):
        raise PhonographApertureError("Phonograph MIDI projection is not SMF")
    if (
        not audition_bytes.startswith(b"RIFF")
        or audition_bytes[8:12] != b"WAVE"
    ):
        raise PhonographApertureError("Phonograph audition is not WAV")

    proposal_id = receipt.get("receipt_hash")
    if not isinstance(proposal_id, str) or not proposal_id.startswith("sha256:"):
        raise PhonographApertureError("Phonograph proposal receipt identity is missing")
    proposal_slug = proposal_id.split(":", 1)[1][:24]
    target = (
        Path(state_dir)
        / "doorhouse-phonograph"
        / receipt_id
        / proposal_slug
    )
    target.mkdir(parents=True, exist_ok=True)
    midi_path = target / "answer.mid"
    audition_path = target / "audition.wav"
    receipt_path = target / "receipt.json"

    def write_or_verify(path: Path, raw: bytes) -> None:
        if path.exists():
            if path.read_bytes() != raw:
                raise PhonographApertureError(
                    f"existing Phonograph artifact conflicts: {path.name}"
                )
            return
        path.write_bytes(raw)

    write_or_verify(midi_path, midi_bytes)
    write_or_verify(audition_path, audition_bytes)

    persisted_result = json.loads(json.dumps(result))
    persisted_result["midi"].pop("base64", None)
    persisted_result["audition"].pop("base64", None)
    receipt_text = json.dumps(
        persisted_result,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ) + "\n"
    write_or_verify(receipt_path, receipt_text.encode("utf-8"))

    return {
        "schema": "workbench.phonograph-field-answer/v0",
        "status": "proposal-ready",
        "window_id": materialized_audio.get("window_id"),
        "audio_sha256": materialized_audio.get("audio_sha256"),
        "seed": seed,
        "proposal_receipt_hash": proposal_id,
        "signal_evidence_hash": evidence.get("signal_profile_hash"),
        "proposal_hash": receipt.get("proposal_hash"),
        "resolved_performance_hash": receipt.get("resolved_performance_hash"),
        "proposal": proposal,
        "signal_profile": evidence.get("signal_profile"),
        "midi": {
            **{k: v for k, v in result["midi"].items() if k != "base64"},
            "path": str(midi_path),
        },
        "audition": {
            **{k: v for k, v in result["audition"].items() if k != "base64"},
            "path": str(audition_path),
        },
        "phonograph_receipt": receipt,
        "receipt_path": str(receipt_path),
        "laws": [
            "SIGNAL FACT != MUSICAL MEANING",
            "PROPOSAL != SOURCE EVIDENCE",
            "RESPONSE != REMIX",
            "AUDITION != ADMISSION",
            "FIELD ANSWER != HOUSE CROSSING",
            "MUSICAL POSSIBILITY != RECOMMENDATION",
        ],
    }


def admit_phonograph_answer_as_audio_window(
    answer: dict,
    repos: list[RepoStatus],
    state_dir: Path,
    receipt_id: str,
) -> dict:
    if (
        not isinstance(answer, dict)
        or answer.get("schema") != "workbench.phonograph-field-answer/v0"
        or answer.get("status") != "proposal-ready"
    ):
        raise PhonographApertureError(
            "a receipted Haunted Phonograph proposal is required for admission"
        )

    audition = answer.get("audition")
    if not isinstance(audition, dict) or not isinstance(audition.get("path"), str):
        raise PhonographApertureError("Phonograph audition artifact is missing")
    audition_path = Path(audition["path"]).resolve()
    if not audition_path.is_file():
        raise PhonographApertureError("Phonograph audition WAV is missing")
    expected_sha = audition.get("sha256")
    if not isinstance(expected_sha, str) or not expected_sha.startswith("sha256:"):
        raise PhonographApertureError("Phonograph audition digest is missing")
    audition_bytes = audition_path.read_bytes()
    if "sha256:" + _sha256_bytes(audition_bytes) != expected_sha:
        raise PhonographApertureError(
            "Phonograph audition no longer matches its receipted digest"
        )

    try:
        with wave.open(str(audition_path), "rb") as wav:
            channels = wav.getnchannels()
            sample_width = wav.getsampwidth()
            sample_rate = wav.getframerate()
            frame_count = wav.getnframes()
            compression = wav.getcomptype()
    except (wave.Error, OSError) as exc:
        raise PhonographApertureError(
            "Phonograph audition is not a readable PCM WAV"
        ) from exc

    if (
        channels != 2
        or sample_width != 2
        or sample_rate != 44_100
        or compression != "NONE"
        or frame_count <= 0
    ):
        raise PhonographApertureError(
            "Phonograph re-entry requires canonical 44.1kHz stereo 16-bit PCM WAV"
        )

    # AUDIO WINDOW v0 accepts integer-millisecond bounds. Use the largest
    # complete integer-millisecond prefix so re-entry never claims bytes past EOF.
    end_ms = (frame_count * 1000) // sample_rate
    if end_ms <= 0:
        raise PhonographApertureError("Phonograph audition is too short to re-enter")

    parent_window_id = answer.get("window_id")
    proposal_receipt_hash = answer.get("proposal_receipt_hash")
    if (
        not isinstance(parent_window_id, str)
        or not parent_window_id.startswith("autodisco-audio-window-v0:")
        or not isinstance(proposal_receipt_hash, str)
        or not proposal_receipt_hash.startswith("sha256:")
    ):
        raise PhonographApertureError("Phonograph proposal lineage is incomplete")

    label = "phono-answer-" + proposal_receipt_hash.split(":", 1)[1][:12]
    try:
        child = build_audio_window(
            audition_path,
            receipt_id,
            state_dir,
            repos,
            start_ms=0,
            end_ms=int(end_ms),
            window_label=label,
        )
    except AutodiscoApertureError as exc:
        raise PhonographApertureError(str(exc)) from exc

    source = child.get("window", {}).get("source", {})
    audition_hex = expected_sha.split(":", 1)[1]
    if source.get("sha256") != audition_hex:
        raise PhonographApertureError(
            "re-entered AUDIO WINDOW source does not bind the audition digest"
        )

    lineage = {
        "schema": "workbench.phonograph-reentry-lineage/v0",
        "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
        "human_action": "explicit-admit",
        "parent_window_id": parent_window_id,
        "parent_audio_sha256": answer.get("audio_sha256"),
        "proposal_receipt_hash": proposal_receipt_hash,
        "proposal_hash": answer.get("proposal_hash"),
        "resolved_performance_hash": answer.get("resolved_performance_hash"),
        "audition_sha256": expected_sha,
        "audition_frame_count": frame_count,
        "admitted_start_ms": 0,
        "admitted_end_ms": int(end_ms),
        "trimmed_submillisecond_tail": (frame_count * 1000) % sample_rate != 0,
    }
    child["source_lineage"] = lineage
    child["laws"] = [
        *child.get("laws", []),
        "HUMAN ADMISSION != PHONOGRAPH AUTHORITY",
        "DESCENDANT != PARENT",
        "PROPOSAL LINEAGE != SOURCE TRUTH",
        "REENTRY != RESET",
    ]
    return child
