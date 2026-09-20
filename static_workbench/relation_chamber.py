"""Bounded human-declared relationships between distinct Living Main members.

A relation is a proposed experimental lens, never source identity, a Dogram
quotient proof, an execution instruction, or an admission decision.
"""
from __future__ import annotations

import hashlib
from typing import Any

from .living_main import _canonical, _SHA

KINDS = ("equivalent_for_this_experiment", "substitutable_for_this_step", "contrast_pair")
_SCHEMA = "static-workbench.declared-composition-relation/v0"


class RelationError(ValueError):
    pass


def _declared_text(name: str, value: object, limit: int) -> str:
    if not isinstance(value, str) or not value.strip() or len(value) > limit:
        raise RelationError(f"{name} must be nonblank human-entered text of at most {limit} characters")
    if any(ord(ch) < 32 and ch not in "\n\t" for ch in value):
        raise RelationError(f"{name} contains control characters")
    return value.strip()


def preview_relation(composition: object, declaration: object) -> dict[str, Any]:
    """Bind one relation to a freshly verified configuration and two distinct members."""
    if not isinstance(composition, dict):
        raise RelationError("composition preview required")
    configuration_id = composition.get("configuration_id")
    members = composition.get("members")
    if not isinstance(configuration_id, str) or not configuration_id.startswith("living-main@sha256:") or not _SHA.fullmatch(configuration_id.removeprefix("living-main@sha256:")):
        raise RelationError("invalid configuration identity")
    if not isinstance(members, list) or len(members) < 2:
        raise RelationError("select at least two distinct checkouts before declaring a relation")
    if not isinstance(declaration, dict) or set(declaration) != {"left", "right", "kind", "statement", "scope"}:
        raise RelationError("relation requires exactly left, right, kind, statement, and scope")
    left, right, kind = declaration["left"], declaration["right"], declaration["kind"]
    handles = {member["body_time_id"]: member for member in members}
    if not isinstance(left, str) or not isinstance(right, str) or left == right:
        raise RelationError("relation must connect two distinct selected bodies")
    if left not in handles or right not in handles:
        raise RelationError("relation endpoints must belong to this configuration")
    if kind not in KINDS:
        raise RelationError("choose an explicitly supported relation kind")
    statement = _declared_text("statement", declaration["statement"], 800)
    scope = _declared_text("scope", declaration["scope"], 400)
    identity = {
        "schema": _SCHEMA,
        "configuration_id": configuration_id,
        "left": left,
        "right": right,
        "kind": kind,
        "statement": statement,
        "scope": scope,
        "status": "PROPOSED_UNRUN",
        "authority": "none",
    }
    digest = hashlib.sha256(_canonical(identity)).hexdigest()
    return {
        **identity,
        "relation_id": f"declared-relation@sha256:{digest}",
        "participants": [
            {"body_time_id": left, "source_sha": handles[left]["source_sha"]},
            {"body_time_id": right, "source_sha": handles[right]["source_sha"]},
        ],
        "execution": "NOT_ATTEMPTED",
        "relation_proof": "NOT_CLAIMED",
        "nonclaims": [
            "the declaration does not change or identify either source body",
            "equivalent_for_this_experiment does not establish mathematical congruence",
            "the relation applies only to the named composition and stated experiment scope",
            "a relation preview is not a GRAFT round, Dogram calculation, frozen prediction, or execution receipt",
            "removing this preview leaves the source composition and source identities unchanged",
        ],
    }
