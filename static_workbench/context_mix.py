"""Experimental read-only L BRANCH context routing.

A proposal describes what *may* influence a destination. It neither reads source
bytes nor supplies permission, project authority, an execution plan, or a tool
adapter. Source identities and target affordances are caller declarations, not
independently authenticated facts. See docs/L-BRANCH-CONTEXT-001.md.
"""
from __future__ import annotations

from dataclasses import dataclass
from hashlib import sha256
import json
import re
from typing import Sequence

_ID = re.compile(r"^[a-z0-9][a-z0-9._:-]{0,127}$")
_SHA256 = re.compile(r"^[0-9a-f]{64}$")
_EVIDENCE = frozenset({"human-supplied", "observed", "inferred", "influence-only"})
_WEIGHT = frozenset({"light", "medium", "strong"})
_RESPONSE = frozenset({"follow", "contrast", "accent"})
_DETAIL = frozenset({"reference", "summary", "excerpt"})
POLICY = "workbench.lbranch.context-proposal.v0"


class ContextMixError(ValueError):
    """A declared context or routing proposal cannot be accepted."""


@dataclass(frozen=True)
class ContextLane:
    lane_id: str
    source_ref: str
    source_sha256: str
    evidence_class: str
    declared_targets: tuple[str, ...]
    declared_scopes: tuple[str, ...] = ("whole",)
    available: bool = True


@dataclass(frozen=True)
class Send:
    lane_id: str
    target: str
    scope: str = "whole"
    weight: str = "medium"
    detail: str = "reference"
    response: str = "follow"


@dataclass(frozen=True)
class MixProposal:
    policy: str
    context_sha256: str
    plan_sha256: str
    sends: tuple[Send, ...]
    available: tuple[str, ...]
    used: tuple[str, ...]
    ignored: tuple[str, ...]
    unavailable: tuple[str, ...]
    influence_only: tuple[str, ...]
    status: str = "unrun_proposal_no_authority"


def _id(value: str, field: str) -> None:
    if not isinstance(value, str) or not _ID.fullmatch(value):
        raise ContextMixError(f"{field}: expected a bounded declared identifier")


def _digest(obj: object) -> str:
    return sha256(json.dumps(obj, ensure_ascii=False, sort_keys=True,
                             separators=(",", ":"), allow_nan=False).encode("utf-8")).hexdigest()


def _check_lane(lane: ContextLane) -> None:
    _id(lane.lane_id, "lane_id")
    if not isinstance(lane.source_ref, str) or not (1 <= len(lane.source_ref) <= 1024):
        raise ContextMixError("source_ref: expected a bounded source reference")
    if not isinstance(lane.source_sha256, str) or not _SHA256.fullmatch(lane.source_sha256):
        raise ContextMixError("source_sha256: expected a lowercase SHA-256 declaration")
    if lane.evidence_class not in _EVIDENCE:
        raise ContextMixError("evidence_class: unsupported")
    if type(lane.available) is not bool:
        raise ContextMixError("available: expected boolean")
    if not isinstance(lane.declared_targets, tuple) or not lane.declared_targets:
        raise ContextMixError("declared_targets: expected a nonempty tuple")
    if not isinstance(lane.declared_scopes, tuple) or not lane.declared_scopes:
        raise ContextMixError("declared_scopes: expected a nonempty tuple")
    for target in lane.declared_targets:
        _id(target, "declared target")
    for scope in lane.declared_scopes:
        _id(scope, "declared scope")
    if len(set(lane.declared_targets)) != len(lane.declared_targets):
        raise ContextMixError("duplicate declared target")
    if len(set(lane.declared_scopes)) != len(lane.declared_scopes):
        raise ContextMixError("duplicate declared scope")


def _check_send(send: Send, lanes: dict[str, ContextLane]) -> None:
    _id(send.lane_id, "send lane_id")
    _id(send.target, "send target")
    _id(send.scope, "send scope")
    if send.weight not in _WEIGHT or send.response not in _RESPONSE or send.detail not in _DETAIL:
        raise ContextMixError("unsupported send control")
    lane = lanes.get(send.lane_id)
    if lane is None:
        raise ContextMixError("send references an unknown lane")
    if not lane.available:
        raise ContextMixError("send references unavailable evidence")
    if send.target not in lane.declared_targets:
        raise ContextMixError("destination not declared for this lane")
    if send.scope not in lane.declared_scopes:
        raise ContextMixError("scope not declared for this lane")


def propose_mix(lanes: Sequence[ContextLane], sends: Sequence[Send]) -> MixProposal:
    """Return an inert, replayable reference-only proposal and context diet.

    Input declarations must originate from an independently validated source
    selection. Never treat this calculation as authorization to read, execute,
    export, or publish anything.
    """
    if len(lanes) > 32 or len(sends) > 64:
        raise ContextMixError("bounded context limit exceeded")
    if not lanes:
        raise ContextMixError("no context lanes supplied")
    lane_by_id: dict[str, ContextLane] = {}
    for lane in lanes:
        _check_lane(lane)
        if lane.lane_id in lane_by_id:
            raise ContextMixError("duplicate lane identity")
        lane_by_id[lane.lane_id] = lane

    send_keys: set[tuple[str, str, str]] = set()
    for send in sends:
        _check_send(send, lane_by_id)
        key = (send.lane_id, send.target, send.scope)
        if key in send_keys:
            raise ContextMixError("duplicate lane/target/scope route")
        send_keys.add(key)

    sorted_lanes = sorted(lanes, key=lambda lane: lane.lane_id)
    sorted_sends = tuple(sorted(sends, key=lambda send:
                               (send.lane_id, send.target, send.scope)))
    context = [
        {"id": lane.lane_id, "source": lane.source_ref, "hash": lane.source_sha256,
         "class": lane.evidence_class, "targets": sorted(lane.declared_targets),
         "scopes": sorted(lane.declared_scopes), "available": lane.available}
        for lane in sorted_lanes
    ]
    context_sha256 = _digest({"policy": POLICY, "context": context})
    plan_sha256 = _digest({
        "policy": POLICY, "context_sha256": context_sha256,
        "sends": [
            {"lane": send.lane_id, "target": send.target, "scope": send.scope,
             "weight": send.weight, "detail": send.detail, "response": send.response}
            for send in sorted_sends
        ],
    })
    used = frozenset(send.lane_id for send in sorted_sends)
    return MixProposal(
        policy=POLICY, context_sha256=context_sha256, plan_sha256=plan_sha256,
        sends=sorted_sends,
        available=tuple(lane.lane_id for lane in sorted_lanes if lane.available),
        used=tuple(lane.lane_id for lane in sorted_lanes if lane.lane_id in used),
        ignored=tuple(lane.lane_id for lane in sorted_lanes
                      if lane.available and lane.lane_id not in used),
        unavailable=tuple(lane.lane_id for lane in sorted_lanes if not lane.available),
        influence_only=tuple(lane.lane_id for lane in sorted_lanes
                             if lane.lane_id in used and
                             lane.evidence_class in {"inferred", "influence-only"}),
    )
