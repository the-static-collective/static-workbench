"""BRANCH HARBOR 003 — read-only Freeport 006 manifest shelf + Free Graph seed.

Import is deliberately an ephemeral *preview*, never project state. Manifest
hashes and reported local HOLD are not authenticated by reading JSON.
Free Graph v0 projection is source-compatible and independently validated
against the original pinned Free Graph core in CI.
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any

MAX_MANIFEST_BYTES = 16384
FG_PIN = "ec0ad8743c5faac3f3675760bbafcbcb1df846c1"
SOURCE_PINS = (
    ("the-static-collective/CANNON", "experiment/stack-squared-017",
     "3aa5b0d0e9403e90affe05ec4056825e8d166fe4",
     "src/stack-squared-017.mjs"),
    ("the-static-collective/static-workbench",
     "feature/old-growth-002-pinned-graft-import",
     "16b0d5a2eb9c4c9b7da27f9ee1d8d8ba422a35a2",
     "static_workbench/old_growth_import.py"),
)
GHOT_PIN = ("the-static-collective/GHoT", "external-adapter-manifest-001",
            "e12ce3e62486feb1e5cd2324d1ae5a6a2be8b19b")
MANIFEST_KEYS = frozenset({
    "schema", "version", "pins", "sources", "source_cells", "joined_cell",
    "candidate_cell", "candidate_packet_sha256", "candidate_receipt_sha256",
    "ghot_capability", "review_offer_address", "destination",
    "disposition", "candidate_branch_name", "branch_created", "git_mutations",
    "donor_branch_modules_executed", "exact_selected_source_bytes_preserved",
    "host_admitted", "receiver_admitted", "selected_for_canon",
    "permission_to_publish", "remote_transmission", "deployment_count",
})
PIN_FIELDS = frozenset({"repository", "ref", "sha", "path"})
SOURCE_FIELDS = frozenset({
    "repository", "branch_hint", "commit", "path",
    "git_blob_sha1", "sha256", "byte_length",
})
HEX40 = re.compile(r"^[0-9a-f]{40}$")
HEX64 = re.compile(r"^[0-9a-f]{64}$")
DIGEST = re.compile(r"^sha256:[0-9a-f]{64}$")
BRANCH = re.compile(r"^experiment/branch-harbor-review-[0-9a-f]{12}$")


class HarborError(ValueError):
    """Malformed, ambiguous, or authority-promoting foreign manifest."""


def _pairs(parts: list[tuple[str, Any]]) -> dict[str, Any]:
    value: dict[str, Any] = {}
    for key, part in parts:
        if key in value:
            raise HarborError("duplicate JSON key is refused")
        value[key] = part
    return value


def _check(value: Any, keys: frozenset[str], code: str) -> dict[str, Any]:
    if type(value) is not dict or value.keys() != keys:
        raise HarborError(code)
    return value


def _need(cond: bool, code: str) -> None:
    if not cond:
        raise HarborError(code)


def _canonical(value: Any) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"),
        ensure_ascii=False, allow_nan=False,
    ).encode("utf-8")


def _digest(value: Any) -> str:
    return "sha256:" + hashlib.sha256(_canonical(value)).hexdigest()


def _id(kind: str, record: dict[str, Any]) -> str:
    return kind + ":sha256:" + hashlib.sha256(_canonical(record)).hexdigest()


def _entry(kind: str, body: dict[str, Any]) -> dict[str, Any]:
    return {"id": _id(kind, body), **body}


def parse_freeport006(raw: str) -> dict[str, Any]:
    if type(raw) is not str:
        raise HarborError("a single UTF-8 JSON manifest is required")
    data = raw.encode("utf-8")
    _need(0 < len(data) <= MAX_MANIFEST_BYTES, "manifest exceeds the 16 KiB review boundary")
    try:
        manifest = json.loads(raw, object_pairs_hook=_pairs,
                              parse_constant=lambda value: (_ for _ in ()).throw(HarborError("nonfinite JSON")))
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise HarborError("manifest is not bounded, unambiguous JSON: " + str(exc)[:90]) from exc
    m = _check(manifest, MANIFEST_KEYS, "unexpected or missing manifest fields")
    _need(m["schema"] == "freeport.branch-graft/v0" and m["version"] == "006",
          "only the FREEPORT 006 specimen contract is accepted")
    pins = _check(m["pins"], frozenset({"cannon", "workbench", "ghot"}), "donor pin fields")
    for i, (label, expected) in enumerate(zip(("cannon", "workbench"), SOURCE_PINS)):
        p = _check(pins[label], PIN_FIELDS, "donor pin shape")
        _need(tuple(p[k] for k in ("repository", "ref", "sha", "path")) == expected,
              "donor pin drift: " + label)
    g = _check(pins["ghot"], frozenset({"repository", "ref", "sha"}), "GHoT pin fields")
    _need(tuple(g[k] for k in ("repository", "ref", "sha")) == GHOT_PIN, "GHoT original donor drift")
    _need(type(m["sources"]) is list and len(m["sources"]) == 2, "exactly two source selectors")
    _need(type(m["source_cells"]) is list and len(m["source_cells"]) == 2
          and all(type(x) is str and HEX64.fullmatch(x) for x in m["source_cells"]),
          "untrusted source cell references")
    for index, original in enumerate(m["sources"]):
        row = _check(original, SOURCE_FIELDS, "unexpected source selector fields")
        p = pins[("cannon", "workbench")[index]]
        _need(tuple(row[k] for k in ("repository", "branch_hint", "commit", "path")) ==
              (p["repository"], p["ref"], p["sha"], p["path"]),
              "source entry not bound to pinned donor " + str(index))
        _need(type(row["git_blob_sha1"]) is str and HEX40.fullmatch(row["git_blob_sha1"]),
              "invalid exact Git blob ID")
        _need(type(row["sha256"]) is str and DIGEST.fullmatch(row["sha256"]),
              "invalid source SHA-256")
        _need(type(row["byte_length"]) is int and 512 < row["byte_length"] <= 65536,
              "invalid source byte length")
    for key in ("joined_cell", "candidate_cell"):
        _need(type(m[key]) is str and HEX64.fullmatch(m[key]), "invalid " + key)
    _need(len(set(m["source_cells"] + [m["joined_cell"], m["candidate_cell"]])) == 4,
          "ambiguous cargo identity")
    for key in ("candidate_packet_sha256", "candidate_receipt_sha256", "review_offer_address"):
        _need(type(m[key]) is str and DIGEST.fullmatch(m[key]), "invalid " + key)
    _need(m["ghot_capability"] == "freeport.synthetic.branch_graft_probe_v0",
          "GHoT synthetic capability mismatch")
    _need(m["destination"] == "Review-World" and m["disposition"] == "HOLD",
          "unsupported or promoted destination decision")
    _need(type(m["candidate_branch_name"]) is str and BRANCH.fullmatch(m["candidate_branch_name"])
          and m["candidate_branch_name"] ==
              "experiment/branch-harbor-review-" + m["candidate_packet_sha256"][7:19],
          "candidate branch proposal not source-bound")
    for field in ("branch_created", "host_admitted", "receiver_admitted",
                  "selected_for_canon", "permission_to_publish", "remote_transmission"):
        _need(m[field] is False, "forbidden authority promotion: " + field)
    _need(m["exact_selected_source_bytes_preserved"] is True,
          "original custody declaration absent")
    for field in ("git_mutations", "donor_branch_modules_executed", "deployment_count"):
        _need(type(m[field]) is int and m[field] == 0, "side-effect promotion: " + field)
    return m


def _graph(m: dict[str, Any]) -> dict[str, Any]:
    """Seed-only, pointer-only graph. Original Free Graph validates it in CI.

    No 'constitutes' relation: neither an unsigned manifest nor a reported
    HOLD qualifies as independently verified owner-local gate evidence.
    """
    manifest_digest = _digest(m)
    source = _entry("fgs", {
        "source_class": "unresolved-receipt",
        "locator": {
            "system": "manual Workbench import", "coordinate": "FREEPORT 006 manifest",
            "revision": manifest_digest, "resolution": "unverified user-supplied pointer",
        },
        "observed_at": "unverified-manifest",
        "acquisition": "explicit local browser paste",
        "digest": manifest_digest, "access": "unknown", "export": "unknown",
        "authority": "none", "resolvable_pointer": "session-only:freeport-006-manifest",
    })
    sid = source["id"]
    cards: list[dict[str, Any]] = []
    for row in m["sources"]:
        cards.append(_entry("fgn", {
            "kind": "artifact", "label": row["repository"].split("/")[1] + " @ " + row["commit"][:12],
            "status": "unresolved", "source_ids": [sid],
            "extensions": {"claimed_git_commit": row["commit"],
                           "claimed_git_blob": row["git_blob_sha1"],
                           "claimed_source_digest": row["sha256"], "path": row["path"],
                           "source_verification": "not independently performed by Workbench"},
        }))
    candidate = _entry("fgn", {
        "kind": "artifact", "label": "Proposed graft " + m["candidate_packet_sha256"][7:19],
        "status": "proposed", "source_ids": [sid],
        "extensions": {"proposed_branch_not_created": m["candidate_branch_name"],
                       "native_freeport_proof": "not supplied or verified",
                       "candidate_digest_claim": m["candidate_packet_sha256"]},
    })
    claim = _entry("fgn", {
        "kind": "claim", "label": "Actual CANNON × Workbench runtime compatibility",
        "status": "unresolved", "source_ids": [sid], "claim_class": "design",
        "witness_requirement": "machine",
    })
    test = _entry("fgn", {
        "kind": "test", "label": "Reported GHoT digest-only synthetic probe",
        "status": "proposed", "source_ids": [sid],
        "extensions": {"only_manifest_attests_run": True,
                       "does_not_test_donor_interoperability": True},
    })
    hold = _entry("fgn", {
        "kind": "receipt", "label": "Review-World HOLD — manifest-reported",
        "status": "unresolved", "source_ids": [sid],
        "extensions": {"disposition_claim": "HOLD", "signature_verified": False,
                       "authority": "none", "owner_admission": False},
    })
    links = [
        _entry("fgl", {"from": candidate["id"], "to": parent["id"], "verb": "descends-from",
                       "qualifier": "source-named parent; source bytes not independently checked",
                       "status": "proposed", "source_ids": [sid], "authority": "none"})
        for parent in cards
    ]
    links.append(_entry("fgl", {
        "from": test["id"], "to": claim["id"], "verb": "tests",
        "qualifier": "reported digest-only probe does not establish runtime compatibility",
        "status": "proposed", "source_ids": [sid], "authority": "none",
    }))
    links.append(_entry("fgl", {
        "from": hold["id"], "to": candidate["id"], "verb": "connects",
        "qualifier": "claimed destination-local HOLD, not verified constitution or admission",
        "status": "unresolved", "source_ids": [sid], "authority": "none",
    }))
    packet = {
        "schema": "free-graph.packet/v0",
        "purpose": "Review an explicitly supplied FREEPORT 006 branch graft without promoting claims",
        "modes": ["seed"],
        "scope": {"task": "Branch Deck Freeport 006 proposal desk",
                  "worlds": ["CANNON", "Static Workbench", "Freeport", "Review-World"],
                  "resolution": "manifest fields only; no independently checked donor Git bytes"},
        "task_world_cut": {
            "status": "unresolved", "selected_ids": [sid, candidate["id"]],
            "owner_head_source_ids": [],
            "omitted": [
                {"door": "Original Freeport 006 cold verifier",
                 "reason": "Manifest alone does not prove source bytes, receipts, GHoT execution or HOLD"},
                {"door": "Source owners, licenses, target runtime tests and local admission",
                 "reason": "No independent owner gate or donor compatibility proof was supplied"},
            ],
            "rationale": "Only the bounded manifest claim has entered this seed-only projection.",
        },
        "sources": [source],
        "nodes": [*cards, candidate, claim, test, hold],
        "links": links,
        "residual_fog": [
            "Branch names are hints; exact commits are source claims until Git is independently verified.",
            "Reported signed HOLD is not verified by this projection.",
            "Synthetic GHoT digest probe does not test native donor runtime compatibility.",
        ],
        "non_imports": [
            "No branch execution, checkout, Git fetch, merge or canon selection.",
            "No foreign payload, private archive, credentials or executable adapter imported.",
            "No constituted destination decision or public publication permission.",
        ],
    }
    packet["packet_id"] = "fgp:" + _digest(packet)
    return packet


def preview_branch_harbor(raw: str) -> dict[str, Any]:
    m = parse_freeport006(raw)
    packet = _graph(m)
    return {
        "schema": "house.branch-harbor-preview/v0.1",
        "manifest_digest": _digest(m),
        "manifest_authenticated": False,
        "freeport_cold_verified": False,
        "remote_github_checked": False,
        "source_blobs_checked": False,
        "reported_destination": m["destination"],
        "reported_disposition": "HOLD",
        "proposal_branch": m["candidate_branch_name"],
        "proposal_branch_created": False,
        "sources": [
            {"repository": row["repository"], "branch_hint": row["branch_hint"],
             "commit": row["commit"], "path": row["path"], "source_sha256": row["sha256"],
             "verified": False}
            for row in m["sources"]
        ],
        "graph": packet,
        "graph_validation": "Free Graph v0 projection; independent original-code validation required",
        "authority": "none", "promotion": "NONE",
    }
