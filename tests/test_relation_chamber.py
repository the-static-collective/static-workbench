from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.living_main import preview_composition
from static_workbench.relation_chamber import RelationError, preview_relation
from static_workbench.repos import discover_repositories


def git(path: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(path), *args], check=True, text=True, capture_output=True).stdout.strip()


def prepared(tmp_path: Path):
    root = tmp_path / "root"
    selections = []
    for name in ("alpha", "beta"):
        repo = root / name
        repo.mkdir(parents=True)
        git(repo, "init", "-b", "main")
        git(repo, "config", "user.name", "Fixture")
        git(repo, "config", "user.email", "fixture@example.invalid")
        (repo / "README.md").write_text(name + "\n", encoding="utf-8")
        git(repo, "add", "README.md")
        git(repo, "commit", "-m", "initial")
        selections.append({"root_id": "static", "relative_path": name, "expected_sha": git(repo, "rev-parse", "HEAD")})
    roots = (RootConfig("static", root),)
    composition = preview_composition(roots, discover_repositories(roots), selections)
    members = composition["members"]
    declaration = {
        "left": members[0]["body_time_id"],
        "right": members[1]["body_time_id"],
        "kind": "equivalent_for_this_experiment",
        "statement": "For one synthetic example, treat the two interfaces as substitutable.",
        "scope": "One proposal-only GRAFT comparison; no execution.",
    }
    return root, roots, selections, composition, declaration


def test_relation_identity_is_scoped_and_distinct_from_source_identity(tmp_path: Path):
    _root, _roots, _selections, composition, declaration = prepared(tmp_path)
    first = preview_relation(composition, declaration)
    assert first == preview_relation(composition, declaration)
    assert first["configuration_id"] == composition["configuration_id"]
    assert first["relation_id"] != composition["configuration_id"]
    assert first["participants"][0]["source_sha"] != first["participants"][1]["source_sha"]
    assert first["relation_proof"] == "NOT_CLAIMED"
    assert first["execution"] == "NOT_ATTEMPTED"
    assert first["authority"] == "none"
    assert preview_relation(composition, {**declaration, "scope": "Different experiment"})["relation_id"] != first["relation_id"]
    assert preview_relation(composition, {**declaration, "kind": "contrast_pair"})["relation_id"] != first["relation_id"]
    assert "declared_relation" not in composition


def test_relation_does_not_accept_aliasing_or_absent_body(tmp_path: Path):
    _root, _roots, _selections, composition, declaration = prepared(tmp_path)
    with pytest.raises(RelationError, match="distinct"):
        preview_relation(composition, {**declaration, "right": declaration["left"]})
    with pytest.raises(RelationError, match="belong"):
        preview_relation(composition, {**declaration, "right": "unknown@sha"})
    with pytest.raises(RelationError, match="supported"):
        preview_relation(composition, {**declaration, "kind": "same_source_identity"})
    with pytest.raises(RelationError, match="statement"):
        preview_relation(composition, {**declaration, "statement": " "})
    with pytest.raises(RelationError, match="control"):
        preview_relation(composition, {**declaration, "scope": "x\x00"})
    with pytest.raises(RelationError, match="exactly"):
        preview_relation(composition, {**declaration, "promote": True})


def test_relation_api_revalidates_checkout_and_local_session(tmp_path: Path):
    root, roots, selections, composition, declaration = prepared(tmp_path)
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=roots, max_repo_depth=2,
    )
    payload = {
        "selections": selections, "expected_configuration_id": composition["configuration_id"],
        "declaration": declaration,
    }
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.post("/api/living-main/relations/preview", json=payload).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token, "origin": "http://127.0.0.1"}
        success = client.post("/api/living-main/relations/preview", json=payload, headers=headers)
        assert success.status_code == 200, success.text
        assert success.json()["status"] == "PROPOSED_UNRUN"
        assert client.post("/api/living-main/relations/preview", json={
            **payload, "expected_configuration_id": "living-main@sha256:" + "0" * 64,
        }, headers=headers).status_code == 409
        (root / "alpha" / "untracked.txt").write_text("changed\n")
        refused = client.post("/api/living-main/relations/preview", json=payload, headers=headers)
        assert refused.status_code == 409
        assert not (root / "alpha" / "untracked.txt").read_text() == ""
