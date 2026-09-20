"""LIFESTREAM-001 manual HOUSE bridge. Files only; no server route or project effects.

A selected Static Live moment + the exact local source bytes may produce one explicitly
reviewed HOUSE draft return. CLOCKWORK readings are opaque attributed witnesses, never
used to change UTC, media offsets, editorial sequence or broadcast authority.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

MOMENT = "static-lifestream.moment/v0.1"
RETURN = "static-lifestream.return/v0.1"
TOKEN = re.compile(r"^[A-Za-z0-9._:-]{1,120}$")
UTC = re.compile(r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d\.\d{3}Z$")


def refuse(unless: bool, reason: str) -> None:
    if not unless:
        raise ValueError(reason)


def exact(value: object, names: set[str]) -> dict:
    refuse(isinstance(value, dict) and set(value) == names, "missing or unexpected fields")
    return value


def digest(data: bytes) -> str:
    return "sha256:" + hashlib.sha256(data).hexdigest()


def canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"),
                      allow_nan=False).encode("utf-8")


def hash_object(value: object) -> str:
    return digest(canonical(value))


def token(value: object, name: str) -> None:
    refuse(isinstance(value, str) and TOKEN.fullmatch(value) is not None, "invalid " + name)


def utc(value: object) -> None:
    refuse(isinstance(value, str) and UTC.fullmatch(value) is not None,
           "explicit millisecond-precision UTC instant required")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("invalid UTC instant") from exc
    refuse(parsed.isoformat(timespec="milliseconds").replace("+00:00", "Z") == value,
           "invalid UTC instant")


def sha256_field(value: object) -> None:
    refuse(isinstance(value, str) and re.fullmatch(r"sha256:[0-9a-f]{64}", value) is not None,
           "invalid sha256 digest")


def source_bytes(source_file: str | Path) -> dict:
    path = Path(source_file)
    refuse(not path.is_symlink(), "source symlink refused")
    with path.open("rb") as stream:
        stat = os.fstat(stream.fileno())
        refuse(os.path.isfile(path) and stat.st_size > 0, "source must be a nonempty regular file")
        h = hashlib.sha256()
        size = 0
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
            size += len(chunk)
        refuse(size == stat.st_size, "source changed during read")
    return {"sha256": "sha256:" + h.hexdigest(), "byteLength": size}


def check_clocks(witnesses: object) -> None:
    refuse(isinstance(witnesses, list) and len(witnesses) <= 32,
           "up to 32 independent clock witnesses permitted")
    for witness in witnesses:
        exact(witness, {"clockId", "reading", "basis", "observedAtUtc", "evidenceRef"})
        token(witness["clockId"], "clockId")
        refuse(isinstance(witness["reading"], str) and len(witness["reading"]) <= 512,
               "invalid clock reading")
        for field in ("basis", "evidenceRef"):
            refuse(isinstance(witness[field], str) and 0 < len(witness[field]) <= 512,
                   "clock basis and provenance required")
        utc(witness["observedAtUtc"])


def verify_moment(moment: object, source_file: str | Path) -> dict:
    moment = exact(moment, {"schema", "eventId", "source", "span", "time", "clockWitnesses", "momentId"})
    refuse(moment["schema"] == MOMENT, "unsupported moment schema")
    token(moment["eventId"], "eventId")
    source = exact(moment["source"], {"sha256", "byteLength"})
    sha256_field(source["sha256"])
    refuse(type(source["byteLength"]) is int and source["byteLength"] > 0
           and source["byteLength"] <= 2**53 - 1, "invalid source length")
    span = exact(moment["span"], {"startMs", "endMs"})
    refuse(type(span["startMs"]) is int and type(span["endMs"]) is int
           and 0 <= span["startMs"] < span["endMs"] <= 2**53 - 1, "invalid media span")
    times = exact(moment["time"], {"recordingStartedAtUtc", "observedAtUtc"})
    utc(times["recordingStartedAtUtc"])
    utc(times["observedAtUtc"])
    check_clocks(moment["clockWitnesses"])
    sha256_field(moment["momentId"])
    unsigned = {key: value for key, value in moment.items() if key != "momentId"}
    refuse(hash_object(unsigned) == moment["momentId"], "moment manifest digest mismatch")
    refuse(source_bytes(source_file) == source, "source bytes do not match moment")
    return moment


def make_return(moment: object, source_file: str | Path, reviewed_text: bytes,
                kind: str, admitted_by: str, admitted_at_utc: str) -> dict:
    moment = verify_moment(moment, source_file)
    refuse(kind in {"lyric", "journal", "invention"}, "unsupported artifact kind")
    token(admitted_by, "attribution")
    utc(admitted_at_utc)
    refuse(0 < len(reviewed_text) <= 128 * 1024, "draft must be 1..131072 UTF-8 bytes")
    text = reviewed_text.decode("utf-8")
    refuse(bool(text.strip()), "empty draft refused")
    artifact = {"kind": kind, "text": text, "sha256": digest(reviewed_text),
                "sourceMomentId": moment["momentId"]}
    unsigned = {"schema": RETURN, "momentId": moment["momentId"], "artifact": artifact,
                "review": {"admittedBy": admitted_by, "admittedAtUtc": admitted_at_utc,
                           "disposition": "reviewed_local_draft"},
                "effects": {"broadcast": False, "stage": False, "publish": False}}
    return {**unsigned, "returnId": hash_object(unsigned)}


def new_private_json(destination: str | Path, payload: dict) -> None:
    """Exclusive create: no implicit overwrite of a past admission."""
    fd = os.open(destination, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
        json.dump(payload, stream, indent=2, ensure_ascii=False)
        stream.write("\n")


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Manual local LIFESTREAM-001 HOUSE crossing")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "draft"):
        p = sub.add_parser(name)
        p.add_argument("--moment", type=Path, required=True)
        p.add_argument("--source", type=Path, required=True)
        if name == "draft":
            p.add_argument("--draft-file", type=Path, required=True)
            p.add_argument("--kind", choices=["lyric", "journal", "invention"], required=True)
            p.add_argument("--admitted-by", required=True)
            p.add_argument("--reviewed", action="store_true", required=True,
                           help="explicit human review; not identity authentication")
            p.add_argument("--out", type=Path, required=True)
    a = parser.parse_args(argv)
    moment = json.loads(a.moment.read_text(encoding="utf-8"))
    verify_moment(moment, a.source)
    if a.command == "inspect":
        print(json.dumps({"status": "source_verified_no_effect", "momentId": moment["momentId"],
                          "clockWitnesses": len(moment["clockWitnesses"])}))
        return
    refuse(not a.draft_file.is_symlink(), "draft symlink refused")
    now = datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")
    returned = make_return(moment, a.source, a.draft_file.read_bytes(), a.kind, a.admitted_by, now)
    new_private_json(a.out, returned)
    print(json.dumps({"status": "reviewed_local_draft_return", "momentId": moment["momentId"],
                      "returnId": returned["returnId"], "out": str(a.out),
                      "broadcast": False, "stage": False, "publish": False}))


if __name__ == "__main__":
    try:
        main()
    except (OSError, ValueError, UnicodeError, json.JSONDecodeError) as error:
        parser_message = "LIFESTREAM-001 REFUSED: " + str(error)
        raise SystemExit(parser_message) from error
