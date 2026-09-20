"""COMPOSABLE-OCCURRENCE-001: read-only, explicit multi-owner source/projection graph.

This is a *wire demonstration*, not a substitute for ALEX, TranchNode, LOADOUT,
project-owned witness receipts, or the separate CLOCKWORK draft. No transport,
network, persistence, sensor access, shell commands, or project execution.
"""
from __future__ import annotations
import hashlib
import json
from datetime import datetime


def _required(x, name):
    if not isinstance(x, str) or not x.strip() or len(x) > 256:
        raise ValueError(f"{name} requires bounded nonblank identity")
    return x


def _utc(x):
    _required(x,"timestamp")
    if not x.endswith("Z"):
        raise ValueError("explicit UTC required")
    try:
        d=datetime.fromisoformat(x.replace("Z","+00:00"))
        if d.utcoffset().total_seconds() != 0:
            raise ValueError("non-UTC offset")
    except (TypeError,ValueError) as exc:
        raise ValueError("invalid UTC instant") from exc
    return x


def compose_occurrence(*, occurrence_id, source_ref, observed_utc,
                       projections):
    """Return one immutable-by-convention JSON-ready projection, never an event."""
    _required(occurrence_id,"occurrence_id")
    _required(source_ref,"source_ref")
    _utc(observed_utc)
    if not isinstance(projections,list) or len(projections)>64:
        raise ValueError("bounded projection list required")
    seen=set(); output=[]
    for item in projections:
        if not isinstance(item,dict) or set(item)!={"projection_id","owner_ref","method_ref","source_ref","kind","value"}:
            raise ValueError("projection schema mismatch")
        for k in ("projection_id","owner_ref","method_ref","source_ref","kind"):
            _required(item[k],k)
        if item["projection_id"] in seen:
            raise ValueError("duplicate projection identity")
        seen.add(item["projection_id"])
        value=item["value"]
        # avoid infinite / NaN numbers and externally supplied executable objects
        try:
            safe=json.loads(json.dumps(value,sort_keys=True,allow_nan=False))
        except (TypeError,ValueError,OverflowError) as exc:
            raise ValueError("projection value must be finite JSON") from exc
        output.append({**{k:item[k] for k in ("projection_id","owner_ref","method_ref","source_ref","kind")},"value":safe})
    body={"schema":"house.composable-occurrence/0.1",
          "occurrence":{"occurrence_id":occurrence_id,"source_ref":source_ref,"observed_utc":observed_utc},
          "projections":output,"non_claims":["source citation not source verification",
          "projection presence not permission to execute","numeric coincidence not historical or causal evidence",
          "an occurrence cannot be reconstructed merely from matching coordinates"]}
    body["digest"]="sha256:"+hashlib.sha256(json.dumps(body,sort_keys=True,separators=(",",":"),ensure_ascii=False).encode("utf8")).hexdigest()
    return body
