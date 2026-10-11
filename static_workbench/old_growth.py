"""OLD-GROWTH-001: explicit historical-source composition, proposal only.

Adaptation of seedFORK's human-selected Nearby Growth source packets and
mundaneWORMHOLE's non-overwriting parent graft.  This does not replace HOUSE
GRAFT, retrieve GitHub files, authenticate repository origins, or write state.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

LANES = ("semantic", "lineage", "active_tension", "human_link", "rejected_parallel")
MOVES = ("fuse", "invert", "continue", "wildcard")
_SOURCE_FIELDS = {
    "repository", "commit", "path", "content", "content_sha256",
    "start_byte", "end_byte",
}
_REPO = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
MAX_SOURCE_BYTES = 131_072
MAX_EXCERPT_BYTES = 4096


class OldGrowthError(ValueError):
    """Refuse malformed, ambiguous, unpinned or unverified supplied bytes."""


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False,
        allow_nan=False,
    ).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def _statement(name: str, value: Any, limit: int = 400) -> str:
    if (
        type(value) is not str or not value.strip() or len(value) > limit
        or any(ord(ch) < 32 and ch not in "\n\t" for ch in value)
    ):
        raise OldGrowthError(f"{name} must be nonblank bounded human-declared text")
    return value.strip()


def _selection(raw: Any) -> dict[str, Any]:
    if type(raw) is not dict or set(raw) != _SOURCE_FIELDS:
        raise OldGrowthError("Source needs exactly repository, commit, path, content, "
                             "content_sha256, start_byte and end_byte")
    repository, commit, path = raw["repository"], raw["commit"], raw["path"]
    digest, content = raw["content_sha256"], raw["content"]
    if (
        type(repository) is not str or not _REPO.fullmatch(repository)
        or any(part in (".", "..") for part in repository.split("/"))
        or type(commit) is not str or not _HEX40.fullmatch(commit)
        or type(path) is not str or not 1 <= len(path) <= 256
        or path.startswith("/") or "\\" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
        or any(ord(ch) < 32 or ord(ch) == 127 for ch in path)
    ):
        raise OldGrowthError("Choose a repository, exact lowercase 40-hex commit and safe relative path")
    if type(digest) is not str or not _HEX64.fullmatch(digest):
        raise OldGrowthError("content_sha256 must be lowercase 64-hex")
    if type(content) is not str or "\x00" in content:
        raise OldGrowthError("Source content must be UTF-8 text")
    try:
        source_bytes = content.encode("utf-8")
    except UnicodeEncodeError as exc:
        raise OldGrowthError("Source content must encode as UTF-8") from exc
    if not 1 <= len(source_bytes) <= MAX_SOURCE_BYTES:
        raise OldGrowthError("Source must contain 1 to 131072 UTF-8 bytes")
    if _sha(source_bytes) != digest:
        raise OldGrowthError("Supplied source bytes do not match content_sha256")
    start, end = raw["start_byte"], raw["end_byte"]
    if (
        type(start) is not int or type(end) is not int
        or not 0 <= start < end <= len(source_bytes)
        or end - start > MAX_EXCERPT_BYTES
    ):
        raise OldGrowthError("Choose a nonempty, bounded byte span in the supplied source")
    excerpt_bytes = source_bytes[start:end]
    try:
        excerpt = excerpt_bytes.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OldGrowthError("Source byte span splits a UTF-8 character") from exc
    return {
        "repository": repository, "commit": commit, "path": path,
        "content_sha256": digest, "source_byte_length": len(source_bytes),
        "start_byte": start, "end_byte": end,
        "excerpt": excerpt, "excerpt_sha256": _sha(excerpt_bytes),
        "origin_status": "caller_declared_not_remotely_authenticated",
    }


def compose(
    source_a: Any, source_b: Any, *, keep: Any, bend: Any,
    question: Any, relation_lane: Any, move: Any = "fuse",
) -> dict[str, Any]:
    """Return a content-addressed *calculation*, not a durable event receipt.

    The caller selects both pinned sources and exact excerpt byte ranges.
    Full supplied source text is neither included in output nor written.
    """
    a, b = _selection(source_a), _selection(source_b)
    if (
        a["repository"], a["commit"], a["path"], a["start_byte"], a["end_byte"]
    ) == (
        b["repository"], b["commit"], b["path"], b["start_byte"], b["end_byte"]
    ):
        raise OldGrowthError("Choose two distinct source selections")
    if type(relation_lane) is not str or relation_lane not in LANES:
        raise OldGrowthError("Relation lane must be explicitly declared")
    if type(move) is not str or move not in MOVES:
        raise OldGrowthError("Choose a supported proposed transformation")
    declared = {
        "keep": _statement("keep", keep), "bend": _statement("bend", bend),
        "question": _statement("question", question),
        "relation_lane": relation_lane, "move": move,
        "relation_status": "human_declared_not_inferred",
    }
    packet = {
        "schema": "house.old-growth-source-composition/v0.1",
        "sources": [a, b],
        "declarations": declared,
        "candidate": {
            "status": "PROPOSED_UNRUN",
            "question": declared["question"],
            "preservation_constraint": declared["keep"],
            "transformation": declared["move"],
            "next_step": "Human reviews source excerpts and designs one reversible synthetic test.",
        },
        "parallel_alternative": {
            "status": "LEFT_OPEN",
            "question": "What could be learned by keeping both parent artifacts separate?",
        },
        "authority": "none", "promotion": "NONE", "effects": [],
        "non_claims": [
            "No repository ref, remote origin, history or authorship was authenticated.",
            "Matching supplied bytes and digests do not prove the claimed GitHub commit contains them.",
            "Relation lane, KEEP, BEND and question are human declarations, not inferred facts.",
            "No source was changed, no compatibility established and no candidate executed or accepted.",
            "The returned calculation receipt is not a durable Workbench or project-native event.",
        ],
    }
    packet_sha = _sha(_canonical(packet))
    receipt = {
        "schema": "house.old-growth-calculation-receipt/v0.1",
        "packet_sha256": packet_sha,
        "source_excerpt_sha256": [a["excerpt_sha256"], b["excerpt_sha256"]],
        "status": "calculated_not_persisted",
        "authority": "none",
    }
    return {
        "packet": packet, "packet_sha256": packet_sha,
        "receipt": receipt, "receipt_sha256": _sha(_canonical(receipt)),
    }
