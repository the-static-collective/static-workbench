"""BRANCH-HARBOR-003: foreign Freeport manifest remains a read-only seed."""
from __future__ import annotations

import copy
import importlib.util
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.branch_harbor import (
    FG_PIN, GHOT_PIN, MAX_MANIFEST_BYTES, SOURCE_PINS,
    HarborError, parse_freeport006, preview_branch_harbor,
)
from static_workbench.config import WorkbenchConfig


def fixture() -> dict:
    packet = "sha256:" + "1" * 64
    return {
        "schema": "freeport.branch-graft/v0", "version": "006",
        "pins": {
            "cannon": dict(zip(("repository", "ref", "sha", "path"), SOURCE_PINS[0])),
            "workbench": dict(zip(("repository", "ref", "sha", "path"), SOURCE_PINS[1])),
            "ghot": dict(zip(("repository", "ref", "sha"), GHOT_PIN)),
        },
        "sources": [
            {"repository": p[0], "branch_hint": p[1], "commit": p[2], "path": p[3],
             "git_blob_sha1": str(i + 1) * 40, "sha256": "sha256:" + str(i + 2) * 64,
             "byte_length": 2048}
            for i, p in enumerate(SOURCE_PINS)
        ],
        "source_cells": ["a" * 64, "b" * 64],
        "joined_cell": "c" * 64, "candidate_cell": "d" * 64,
        "candidate_packet_sha256": packet,
        "candidate_receipt_sha256": "sha256:" + "4" * 64,
        "ghot_capability": "freeport.synthetic.branch_graft_probe_v0",
        "review_offer_address": "sha256:" + "5" * 64,
        "destination": "Review-World", "disposition": "HOLD",
        "candidate_branch_name": "experiment/branch-harbor-review-" + "1" * 12,
        "branch_created": False, "git_mutations": 0, "donor_branch_modules_executed": 0,
        "exact_selected_source_bytes_preserved": True,
        "host_admitted": False, "receiver_admitted": False,
        "selected_for_canon": False, "permission_to_publish": False,
        "remote_transmission": False, "deployment_count": 0,
    }


def encode(value: dict) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_manifest_shelf_returns_two_source_claims_and_explicit_unverified_hold():
    preview = preview_branch_harbor(encode(fixture()))
    assert preview["schema"] == "house.branch-harbor-preview/v0.1"
    assert preview["reported_disposition"] == "HOLD"
    assert preview["proposal_branch_created"] is False
    assert preview["source_blobs_checked"] is False
    assert preview["freeport_cold_verified"] is False
    assert preview["manifest_authenticated"] is False
    assert preview["remote_github_checked"] is False
    assert preview["authority"] == "none"
    assert [s["repository"] for s in preview["sources"]] == [s[0] for s in SOURCE_PINS]
    graph = preview["graph"]
    assert graph["schema"] == "free-graph.packet/v0"
    assert graph["modes"] == ["seed"]
    assert graph["task_world_cut"]["status"] == "unresolved"
    assert [edge["verb"] for edge in graph["links"]].count("descends-from") == 2
    assert [edge["verb"] for edge in graph["links"]].count("tests") == 1
    assert [edge["verb"] for edge in graph["links"]].count("connects") == 1
    assert not any(edge["verb"] == "constitutes" for edge in graph["links"])
    assert all(edge["authority"] == "none" for edge in graph["links"])
    assert "private" not in encode(graph)
    assert "payload_base64" not in encode(graph)


def test_bytewise_graph_seed_determinism_and_single_source_digest():
    one = preview_branch_harbor(encode(fixture()))
    two = preview_branch_harbor(json.dumps(fixture(), indent=2))
    assert one == two
    assert len(one["graph"]["sources"]) == 1
    assert one["graph"]["sources"][0]["authority"] == "none"
    assert one["graph"]["sources"][0]["access"] == "unknown"
    assert one["graph"]["sources"][0]["source_class"] == "unresolved-receipt"
    assert one["graph"]["sources"][0]["digest"] == one["manifest_digest"]


@pytest.mark.parametrize("mutate", [
    lambda m: m.update({"branch_created": True}),
    lambda m: m.update({"selected_for_canon": True}),
    lambda m: m.update({"receiver_admitted": True}),
    lambda m: m.update({"host_admitted": True}),
    lambda m: m.update({"disposition": "ADMIT"}),
    lambda m: m.update({"permission_to_publish": True}),
    lambda m: m.update({"git_mutations": 1}),
    lambda m: m.update({"git_mutations": False}),
    lambda m: m.update({"deployment_count": True}),
    lambda m: m.update({"remote_transmission": True}),
    lambda m: m.update({"ghot_capability": "freeport.execute_anything"}),
    lambda m: m.update({"candidate_branch_name": "main"}),
    lambda m: m.update({"extra_powers": ["grant"]}),
    lambda m: m["sources"][0].update({"path": "../../secrets"}),
    lambda m: m["sources"][1].update({"commit": "0" * 40}),
    lambda m: m["sources"][0].update({"exec": True}),
    lambda m: m["pins"]["ghot"].update({"sha": "0" * 40}),
    lambda m: m["pins"]["cannon"].update({"ref": "main"}),
    lambda m: m["source_cells"].append("f" * 64),
    lambda m: m.update({"candidate_cell": "a" * 64}),
    lambda m: m.update({"review_offer_address": "https://attacker.invalid/exfil"}),
    lambda m: m["sources"][0].update({"byte_length": 10**10}),
])
def test_forbidden_authority_and_provenance_smuggling_fails_closed(mutate):
    item = fixture()
    mutate(item)
    with pytest.raises(HarborError):
        preview_branch_harbor(encode(item))


@pytest.mark.parametrize("raw", [
    "",
    "{}",
    "[]",
    "null",
    '{"schema":"freeport.branch-graft/v0","schema":"freeport.branch-graft/v0"}',
    "{" + '"a":1,' * 10000 + '"z":1}',
    "not JSON",
    '{"unsafe":NaN}',
])
def test_ambiguous_oversized_and_invalid_carriers_refused(raw):
    with pytest.raises(HarborError):
        parse_freeport006(raw)


def test_session_guarded_endpoint_returns_projection_without_persisting_foreign_carrier(tmp_path):
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
                             state_dir=tmp_path / "state", roots=())
    app = create_app(config)
    with TestClient(app, base_url="http://127.0.0.1") as client:
        before = client.get("/api/events").json()
        html = client.get("/").text
        asset = client.get("/assets/branch-harbor.js")
        assert asset.status_code == 200
        assert "branchHarborCard" in asset.text
        assert 'src="/assets/branch-harbor.js"' in html
        assert "branchHarborCard(workspaceBody)" in client.get("/assets/branch-deck.js").text
        assert client.post("/api/branches/freeport/preview", data=encode(fixture()),
                           headers={"Content-Type": "application/json"}).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"Content-Type": "application/json", "x-workbench-session": token}
        response = client.post("/api/branches/freeport/preview", data=encode(fixture()),
                               headers=headers)
        assert response.status_code == 200, response.text
        assert response.json()["graph"]["task_world_cut"]["status"] == "unresolved"
        assert client.post("/api/branches/freeport/preview",
                           data=encode(fixture()), headers={**headers, "Origin": "https://evil.invalid"}).status_code == 403
        assert client.post("/api/branches/freeport/preview", data="X" * (MAX_MANIFEST_BYTES + 1),
                           headers=headers).status_code == 413
        assert client.post("/api/branches/freeport/preview", data="{}",
                           headers={**headers, "Content-Type": "text/plain"}).status_code == 415
        assert client.get("/api/events").json() == before
    assert not (tmp_path / "state" / "branch-harbor").exists()


def test_projection_validates_with_original_pinned_free_graph_core_when_available():
    root = os.environ.get("FREE_GRAPH_ORIGINAL_ROOT")
    if not root:
        pytest.skip("native Free Graph original checkout not supplied")
    origin = Path(root)
    import subprocess
    sha = subprocess.check_output(
        ["git", "-C", str(origin), "rev-parse", "HEAD"], timeout=10, text=True
    ).strip()
    assert sha == FG_PIN
    spec = importlib.util.spec_from_file_location("free_graph_v0_original", origin / "scripts" / "fg_core.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    packet = preview_branch_harbor(encode(fixture()))["graph"]
    assert module.validate_packet(packet) == []
    assert module.packet_id(packet) == packet["packet_id"]
    assert len(packet["nodes"]) == 6
    assert len(packet["links"]) == 4
