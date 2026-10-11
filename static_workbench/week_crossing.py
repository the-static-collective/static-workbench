"""PINCERSMASH-002: independent offline receiver for the webZ week note
parcel and Vault source-evidence docket. Neither carrier signs itself.

This module never admits to House, executes an organ, or stores source audio.
"""
from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any

# Witnessed webZ/week/index.html Git blob at the moment of FIELD 001.
WEEK_SOURCE_BLOB = "bc8450793454d2db3988b38029b24243d6fe97f9"
TRACKS = frozenset((
    "70b1d32e-21b6-4340-990d-1a4ef67cfc42",
    "66ce822e-be59-4511-887b-61feda608300",
    "d4a7e58e-5930-4cbb-825f-9c6c8ed6da27",
    "2ec9a56b-6916-4af7-a4dd-5031e42f0bea",
    "2ba6fe93-9d4e-4098-acc5-7e53f9d4918b",
    "02af5b55-74b7-455e-9b9f-f7a840ccac3e",
    "f180e7d1-8b2a-4f89-93f8-3c26544d4701",
    "d6dfeebd-65e7-4c0e-ba84-c092f671e495",
    "a3cac8da-9c29-43d2-bf21-ba00a2b379bc",
    "c3a86308-bc04-4abc-911e-f55b03c4d5b2",
    "5c5409ab-97c9-4035-bea0-d29e256e03fd",
    "5195c966-d1da-4e87-a9d4-b48faacf0047",
    "27efd551-733b-4192-be02-a90e3f574f53",
    "c737f489-2912-408e-a444-bb35cdf893cd",
))
NOTE_SCHEMA = "static-field/week-note-parcel/v0"
EVIDENCE_SCHEMA = "static-field/week-source-evidence/v0"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
ROLES = frozenset(("audio_mp3", "audio_wav", "artwork", "lyrics", "raw_metadata", "other"))
KINDS = frozenset(("observation", "interpretation", "question"))
MAX_DOCUMENT = 32_000


class WeekCrossingRefused(ValueError):
    """A mismatch or insufficient witness. No content is silently promoted."""


def _deny(message: str) -> None:
    raise WeekCrossingRefused(message)


def _strict_pairs(pairs: list[tuple[str, Any]]) -> dict:
    result: dict = {}
    for key, value in pairs:
        if key in result:
            _deny("duplicate JSON key")
        result[key] = value
    return result


def parse_document(data: bytes) -> dict:
    if not isinstance(data, bytes) or not data or len(data) > MAX_DOCUMENT:
        _deny("invalid document size")
    try:
        obj = json.loads(data.decode("utf-8"), object_pairs_hook=_strict_pairs,
                         parse_constant=lambda _: _deny("invalid JSON number"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise WeekCrossingRefused("unreadable JSON document") from exc
    if type(obj) is not dict:
        _deny("expected a JSON object")
    return obj


def _keys(obj: Any, keys: list[str]) -> None:
    # Browser core constructs fields in this order and refuses reordered fields.
    if type(obj) is not dict or list(obj) != keys:
        _deny("unexpected or reordered fields")


def _js_string(s: Any, limit: int | None = None) -> str:
    if type(s) is not str:
        _deny("expected a string")
    if any(0xD800 <= ord(c) <= 0xDFFF for c in s):
        _deny("unpaired surrogate refused")
    if limit is not None and len(s.encode("utf-16-le")) // 2 > limit:
        _deny("string too long")
    return s


def _compact_js(obj: Any) -> bytes:
    # Strings and arrays only: this subset of JSON.stringify is unambiguous.
    try:
        return json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    except UnicodeEncodeError:
        _deny("unpaired surrogate refused")


def inspect_notes(obj: dict) -> dict:
    _keys(obj, ["payload", "sha256", "attestation"])
    if obj["attestation"] != "UNSIGNED_HUMAN_ASSERTION" or type(obj["sha256"]) is not str or not HEX64.fullmatch(obj["sha256"]):
        _deny("invalid unsigned note envelope")
    payload = obj["payload"]
    _keys(payload, ["schema", "sourceBlobSha1", "trackId", "notes"])
    if payload["schema"] != NOTE_SCHEMA or payload["sourceBlobSha1"] != WEEK_SOURCE_BLOB:
        _deny("unsupported browser source revision")
    if type(payload["trackId"]) is not str or payload["trackId"] not in TRACKS:
        _deny("track not in the witnessed album")
    notes = payload["notes"]
    if type(notes) is not list or len(notes) > 30:
        _deny("invalid notes collection")
    for note in notes:
        _keys(note, ["kind", "text"])
        if type(note["kind"]) is not str or note["kind"] not in KINDS:
            _deny("invalid note kind")
        text = _js_string(note["text"], 500)
        if not text.strip():
            _deny("empty note")
    got = hashlib.sha256(_compact_js(payload)).hexdigest()
    if got != obj["sha256"]:
        _deny("browser note digest mismatch")
    return {"state": "HOLD", "trackId": payload["trackId"],
            "noteCount": len(notes), "source": "UNSIGNED_HUMAN_ASSERTION",
            "effect": "none", "reason": "review is required; no local admission"}


def inspect_evidence(obj: dict, asset: Path | None = None) -> dict:
    _keys(obj, ["schema", "provider", "providerTrackId", "assetRole", "observedAt",
                "byteLength", "sha256", "sourceReceiptSha256", "sourceMethod",
                "state", "authority"])
    if obj["schema"] != EVIDENCE_SCHEMA or obj["provider"] != "suno" or type(obj["providerTrackId"]) is not str or obj["providerTrackId"] not in TRACKS:
        _deny("unsupported source identity")
    if type(obj["assetRole"]) is not str or obj["assetRole"] not in ROLES or obj["sourceMethod"] != "vault-local-byte-verification" or obj["state"] != "VERIFIED_AT_SOURCE":
        _deny("unsupported source claim")
    if obj["authority"] != "SOURCE_CLAIM_ONLY_UNTIL_INDEPENDENT_BYTES":
        _deny("unsupported authority claim")
    if type(obj["byteLength"]) is not int or obj["byteLength"] < 0:
        _deny("invalid expected byte length")
    for key in ("sha256", "sourceReceiptSha256"):
        if type(obj[key]) is not str or not HEX64.fullmatch(obj[key]):
            _deny("invalid source digest")
    if not isinstance(obj["observedAt"], str) or not re.fullmatch(
        r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", obj["observedAt"]
    ):
        _deny("invalid observedAt")
    if asset is None:
        return {"state": "HOLD", "trackId": obj["providerTrackId"],
                "verifiedLocalBytes": False, "source": "UNVERIFIED_SOURCE_CLAIM",
                "effect": "none"}
    if asset.is_symlink() or not asset.is_file():
        _deny("receiver asset absent or symlinked")
    digest = hashlib.sha256()
    size = 0
    with asset.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            size += len(block)
            digest.update(block)
    if size != obj["byteLength"] or digest.hexdigest() != obj["sha256"]:
        _deny("independent receiver bytes mismatch")
    return {"state": "HOLD", "trackId": obj["providerTrackId"],
            "verifiedLocalBytes": True,
            "source": "INDEPENDENT_RECEIVER_SHA256_MATCH",
            "effect": "none", "byteLength": size, "sha256": digest.hexdigest()}


def inspect_crossing(notes: dict | None = None,
                     docket: dict | None = None,
                     asset: Path | None = None) -> dict:
    if notes is None and docket is None:
        _deny("no carriers supplied")
    if asset is not None and docket is None:
        _deny("asset must have a source docket")
    n = inspect_notes(notes) if notes is not None else None
    d = inspect_evidence(docket, asset) if docket is not None else None
    if n and d and n["trackId"] != d["trackId"]:
        _deny("two jaws refer to different songs")
    return {
        "schema": "workbench.week-crossing-inspection/v0",
        "state": "HOLD",
        "trackId": n["trackId"] if n else d["trackId"],
        "notes": n,
        "evidence": d,
        "effect": "none",
        "law": "SOURCE_CLAIM != RECEIVER_PROOF != HUMAN_ADMISSION",
    }
