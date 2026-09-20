from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.composition_inspection import (
    CompositionInspectionError, inspect_composition,
)
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.repos import RepoStatus


def descriptor(*repositories: str) -> dict:
    return {
        "schema": "static-collective.founder-node.workbench-inspection.v0.1",
        "mode": "descriptor-only",
        "origin": "founder-node",
        "proposedParticipants": [
            {
                "projectId": repo.split("/")[-1],
                "repository": repo,
                "status": "active",
                "role": "declared role, not verified",
                "owns": ["local project state"],
                "nonAuthority": ["another project's actions"],
                "evidence": [],
            }
            for repo in repositories
        ],
        "sourceRegistry": {
            "projects": {"version": 1, "updated": "2026-09-19", "source": "claimed-project-registry"},
            "invariants": {"version": 1, "updated": "2026-09-18", "source": "claimed-invariant-registry"},
        },
        "localReadiness": "unknown",
        "compatibility": "unverified",
        "executionAuthorized": False,
        "destinationAcceptance": "not-requested",
        "requestedNextStep": "Human may inspect locally installed projects.",
        "nonClaims": ["Does not confer project authority"],
    }


def raw(*repos: str) -> str:
    return json.dumps(descriptor(*repos))


def checkout(name: str, *, root_id: str = "static", relative_path: str | None = None) -> RepoStatus:
    return RepoStatus(
        name=name,
        path="/untrusted/not-used/" + name,
        branch="main",
        detached=False,
        head="abc1234",
        dirty=False,
        ahead=None,
        behind=None,
        root_id=root_id,
        relative_path=relative_path or name,
    )


def test_matches_exact_declared_repository_leaf_only_and_preserves_unknown_state():
    result = inspect_composition(
        raw("the-static-collective/founder-node", "the-static-collective/static-workbench"),
        [checkout("static-workbench"), checkout("static-workbench-clone"), checkout("unrelated")],
    )
    assert result["state"] == "inspection-only"
    assert result["execution_authorized"] is False
    assert result["source_authenticated"] is False
    assert [p["local_state"] for p in result["participants"]] == ["missing", "present"]
    match = result["participants"][1]
    assert match["project_identity_verified"] is False
    assert match["runtime_readiness"] == "unknown"
    assert match["compatibility"] == "unverified"
    assert match["admission"] == "not-requested"
    assert match["checkouts"][0]["relative_path"] == "static-workbench"
    assert "path" not in match["checkouts"][0]


def test_ambiguous_checkout_names_never_select_a_default_match():
    result = inspect_composition(
        raw("the-static-collective/static-workbench", "the-static-collective/founder-node"),
        [checkout("static-workbench", root_id="a"), checkout("static-workbench", root_id="b")],
    )
    assert result["participants"][0]["local_state"] == "ambiguous"
    assert result["participants"][0]["checkouts"] == []


@pytest.mark.parametrize("field,value", [
    ("mode", "execute"),
    ("origin", "agent"),
    ("executionAuthorized", True),
    ("executionAuthorized", "false"),
    ("destinationAcceptance", "accepted"),
    ("localReadiness", "ready"),
    ("compatibility", "compatible"),
    ("schema", "another-schema"),
])
def test_rejects_promoted_or_wrong_contract(field: str, value: object):
    value_dict = descriptor("the-static-collective/static-workbench", "the-static-collective/founder-node")
    value_dict[field] = value
    with pytest.raises(CompositionInspectionError):
        inspect_composition(json.dumps(value_dict), [])


@pytest.mark.parametrize("malformation", [
    "duplicate",
    "outside-org",
    "traversal",
    "unknown-extra-command",
    "oversized",
    "historical",
    "missing-witness",
    "single-participant",
])
def test_refuses_unsafe_and_malformed_descriptors(malformation: str):
    obj = descriptor("the-static-collective/static-workbench", "the-static-collective/founder-node")
    if malformation == "duplicate":
        obj["proposedParticipants"][1]["repository"] = "the-static-collective/static-workbench"
    elif malformation == "outside-org":
        obj["proposedParticipants"][0]["repository"] = "another-org/static-workbench"
    elif malformation == "traversal":
        obj["proposedParticipants"][0]["repository"] = "the-static-collective/../secrets"
    elif malformation == "unknown-extra-command":
        obj["command"] = "rm -rf /"
    elif malformation == "oversized":
        obj["requestedNextStep"] = "x" * 70000
    elif malformation == "historical":
        obj["proposedParticipants"][0]["status"] = "monument"
    elif malformation == "missing-witness":
        del obj["sourceRegistry"]
    elif malformation == "single-participant":
        obj["proposedParticipants"] = obj["proposedParticipants"][:1]
    with pytest.raises(CompositionInspectionError):
        inspect_composition(json.dumps(obj), [])


def config(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    repo = root / "static-workbench"
    repo.mkdir()
    subprocess.run(
        ["git", "-C", str(repo), "init", "-b", "main"],
        capture_output=True, check=True,
    )
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
        max_repo_depth=2,
    )


def test_api_previews_local_checkout_without_store_or_effect(tmp_path: Path):
    workbench = create_app(config(tmp_path))
    with TestClient(workbench, base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token, "origin": "http://127.0.0.1"}
        response = client.post("/api/house/composition/inspect", headers=headers, json={
            "raw_json": raw("the-static-collective/static-workbench", "the-static-collective/founder-node"),
        })
        events = client.get("/api/events").json()["events"]
    assert response.status_code == 200
    body = response.json()
    assert [p["local_state"] for p in body["participants"]] == ["present", "missing"]
    assert body["execution_authorized"] is False
    assert not any(event["kind"].startswith("composition.") for event in events)
    assert not list((tmp_path / "state").glob("*composition*"))


def test_api_rejects_missing_session_cross_origin_and_promoted_payload(tmp_path: Path):
    workbench = create_app(config(tmp_path))
    value = raw("the-static-collective/static-workbench", "the-static-collective/founder-node")
    with TestClient(workbench, base_url="http://127.0.0.1") as client:
        no_token = client.post("/api/house/composition/inspect", json={"raw_json": value})
        token = client.get("/api/bootstrap").json()["session_token"]
        wrong_origin = client.post("/api/house/composition/inspect", headers={
            "origin": "http://evil.example", "x-workbench-session": token,
        }, json={"raw_json": value})
        promoted = descriptor("the-static-collective/static-workbench", "the-static-collective/founder-node")
        promoted["executionAuthorized"] = True
        refused = client.post("/api/house/composition/inspect",
            headers={"x-workbench-session": token}, json={"raw_json": json.dumps(promoted)})
    assert no_token.status_code == 403
    assert wrong_origin.status_code == 403
    assert refused.status_code == 400
