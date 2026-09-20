"""Local, untrusted Maxhinal ride snapshot for the Creator Desk.

The Maxhinal owns semantics. HOUSE never interprets operation outcomes as
truth, runs Daily Slice code, mutates the original ride, or silently rebases
a ride's corpus to the local checkout.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

MAX_RIDE_BYTES = 131072
MAX_OPERATIONS = 64
MAX_OUTPUTS = 64
MAX_RESIDUALS = 128
MAX_BAD_SPINS = 128
MODES = frozenset({
    "discontinuity", "walk-braid", "fiber", "compose",
    "pressure", "moving-origin", "quantumslinky", "maddclown",
})


def parse_ride(raw: str) -> tuple[dict[str, Any], dict[str, Any]]:
    data = raw.encode("utf-8")
    if not data or len(data) > MAX_RIDE_BYTES:
        raise ValueError("ride must be nonblank UTF-8 JSON of at most 128 KiB")
    try:
        ride = json.loads(raw)
    except (ValueError, RecursionError) as exc:
        raise ValueError("ride is not valid bounded JSON") from exc
    if not isinstance(ride, dict) or ride.get("format") != "maxhinal/v0":
        raise ValueError("ride is not a Maxhinal v0 object")
    if ride.get("authority") != "none" or ride.get("promotion") != "NONE":
        raise ValueError("ride must retain authority:none and promotion:NONE")
    if not isinstance(ride.get("ride_id"), str) or not 1 <= len(ride["ride_id"]) <= 128:
        raise ValueError("ride identity is missing or invalid")
    corpus = ride.get("corpus")
    if not isinstance(corpus, dict) or not isinstance(corpus.get("digest"), str) or not 1 <= len(corpus["digest"]) <= 256:
        raise ValueError("corpus digest is missing")
    if not isinstance(ride.get("seed"), str) or len(ride["seed"]) > 256:
        raise ValueError("ride seed is not declared")
    limits = {
        "gas": 64,
        "operations": MAX_OPERATIONS,
        "outputs": MAX_OUTPUTS,
        "residuals": MAX_RESIDUALS,
        "bad_spins": MAX_BAD_SPINS,
    }
    for field, cap in limits.items():
        if not isinstance(ride.get(field), list) or len(ride[field]) > cap:
            raise ValueError(f"ride {field} must be a bounded list")
    ids: set[str] = set()
    for op in ride["operations"]:
        if (not isinstance(op, dict) or not isinstance(op.get("mode"), str)
            or op["mode"] not in MODES or not isinstance(op.get("operation_id"), str)
            or not isinstance(op.get("output_refs"), list)
            or len(op["output_refs"]) > MAX_OUTPUTS
            or any(not isinstance(ref, str) or len(ref) > 128 for ref in op["output_refs"])):
            raise ValueError("ride contains an invalid operation")
        if op["operation_id"] in ids:
            raise ValueError("ride operation identity was reused")
        ids.add(op["operation_id"])
        receipt = op.get("receipt")
        if not isinstance(receipt, dict) or receipt.get("authority") != "none" or receipt.get("promotion") != "NONE":
            raise ValueError("ride operation has inconsistent authority boundary")
    for field, identifier in (("outputs", "output_id"), ("residuals", "residual_id"), ("bad_spins", "bad_id")):
        seen: set[str] = set()
        for item in ride[field]:
            if not isinstance(item, dict) or not isinstance(item.get(identifier), str) or not item[identifier]:
                raise ValueError(f"ride contains an invalid {field} record")
            if item[identifier] in seen:
                raise ValueError(f"ride contains duplicate {field} identity")
            seen.add(item[identifier])
            if field == "outputs" and item.get("source_operation_id") not in ids:
                raise ValueError("derived output refers to an unknown operation")
    for entry in ride["gas"]:
        if not isinstance(entry, dict) or entry.get("kind") != "slice" or not isinstance(entry.get("slice_id"), str) or not entry["slice_id"]:
            raise ValueError("ride has unsupported gas reference")
    if (not isinstance(ride.get("replay"), dict)
        or not isinstance(ride["replay"].get("status"), str)
        or len(ride["replay"]["status"]) > 64):
        raise ValueError("ride replay status is missing")

    summary = {
        "format": "house.maxhinal-ride-snapshot/v0.1",
        "ride_id": ride["ride_id"],
        "corpus_digest": corpus["digest"],
        "reported_replay": ride["replay"].get("status"),
        "source_slice_ids": [entry["slice_id"] for entry in ride["gas"]],
        "operations": [{"id": op["operation_id"], "mode": op["mode"], "outputs": op.get("output_refs", [])}
                       for op in ride["operations"]],
        "output_count": len(ride["outputs"]),
        "residuals": [{"id": x["residual_id"], "code": str(x.get("code", ""))[:100],
                       "message": str(x.get("message", ""))[:400]} for x in ride["residuals"]],
        "bad_spins": [{"id": x["bad_id"], "kind": str(x.get("kind", ""))[:100],
                       "reason": str(x.get("reason", ""))[:400]} for x in ride["bad_spins"]],
        "ride_sha256": hashlib.sha256(data).hexdigest(),
        "import_posture": "untrusted_local_copy_not_reexecuted",
        "authority": "none",
        "promotion": "NONE",
    }
    return ride, summary
