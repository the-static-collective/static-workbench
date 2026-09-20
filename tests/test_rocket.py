from __future__ import annotations

import hashlib
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.rocket import (
    RocketAdvanceInput, RocketConflict, RocketDesk, RocketMissionInput,
    RocketSelection, RocketSeparateInput,
)


def git(path: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(path), *args], text=True, capture_output=True, check=True
    )
    return result.stdout.strip()


def make_repo(parent: Path, name: str, *, body: bool = False, emit: bool = False) -> Path:
    repo = parent / name
    repo.mkdir()
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Rocket Test")
    git(repo, "config", "user.email", "rocket@example.test")
    (repo / "README.md").write_text("a specific sentence\n", encoding="utf-8")
    if body:
        directory = repo / ".body"
        directory.mkdir()
        import json
        manifest = {
            "schema": "body.surface/v0",
            "authority": "none",
            "owner": "specimen/" + name,
            "interfaces": [
                {"direction": "emit" if emit else "accept", "kind": "packet",
                 "protocol": "specimen.packet", "version": "v0"},
            ],
        }
        (directory / "surface-v0.json").write_text(json.dumps(manifest), encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "fixture")
    return repo


def config_for(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),)
    )


def selection(repo: Path) -> RocketSelection:
    return RocketSelection(root_id="static", repo_path=repo.name,
                           expected_sha=git(repo, "rev-parse", "HEAD"))


def source_input(repo: Path, **extras) -> RocketMissionInput:
    return RocketMissionInput(
        title="Inspect an original", purpose="Inspect one exact source",
        mode="source-preview", selections=[selection(repo)],
        source_path="README.md", **extras,
    )


def make_session(desk: RocketDesk, repo: Path) -> tuple[dict, dict, dict, dict]:
    mission = desk.create(source_input(repo))
    prepared = desk.prepare(mission["id"])
    executed = desk.execute(mission["id"], prepared["sha256"])
    separated = desk.separate(mission["id"], RocketSeparateInput(
        expected_stage_sha256=executed["sha256"],
        next_action="Inspect a distinct source in the next rocket",
        residual_fog="No execution outside the desk has been witnessed",
    ))
    return mission, prepared, executed, separated


def test_source_rocket_restarts_and_requires_explicit_descendant(tmp_path: Path):
    config = config_for(tmp_path)
    repo = make_repo(config.roots[0].path, "alpha")
    desk = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    catalog = desk.catalog()
    observed = next(x for x in catalog["repos"] if x["repo_path"] == "alpha")
    assert observed["selectable"] and observed["expected_sha"] == git(repo, "rev-parse", "HEAD")
    before = (repo / "README.md").read_bytes()

    mission, prepared, executed, separated = make_session(desk, repo)
    assert prepared["output"]["tool"] == "repo.snapshot/v0"
    assert prepared["output"]["sources"][0]["sha"] == git(repo, "rev-parse", "HEAD")
    assert executed["output"]["tool"] == "source.preview/v0"
    assert executed["output"]["source"]["file_sha256"] == hashlib.sha256(before).hexdigest()
    assert executed["output"]["excerpt"] == before.decode()
    assert executed["previous_sha256"] == prepared["sha256"]
    assert separated["previous_sha256"] == executed["sha256"]
    assert separated["output"]["status"] == "proposal_only"
    with pytest.raises(RocketConflict, match="already prepared"):
        desk.prepare(mission["id"])
    with pytest.raises(RocketConflict, match="already consumed"):
        desk.execute(mission["id"], prepared["sha256"])
    with pytest.raises(RocketConflict, match="already separated"):
        desk.separate(mission["id"], RocketSeparateInput(
            expected_stage_sha256=executed["sha256"], next_action="repeat"
        ))

    restarted = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    recovered = restarted.get(mission["id"])
    assert recovered and [s["kind"] for s in recovered["stages"]] == [
        "prepare", "execute", "separate"
    ]
    assert recovered["stages"][-1]["sha256"] == separated["sha256"]
    assert restarted.list()[0]["completed_stages"] == 3
    assert (repo / "README.md").read_bytes() == before
    assert git(repo, "status", "--porcelain") == ""

    other = make_repo(config.roots[0].path, "beta")
    child = restarted.create(source_input(
        other, parent_id=mission["id"], expected_parent_sha256=separated["sha256"],
    ))
    assert child["parent_id"] == mission["id"]
    assert child["parent_sha256"] == separated["sha256"]
    assert child["stages"] == []  # No automatic propagation, even after restart.
    with pytest.raises(RocketConflict, match="exact receipt"):
        restarted.create(source_input(
            other, parent_id=mission["id"], expected_parent_sha256="0" * 64,
        ))
    with pytest.raises(RocketConflict, match="exact receipt"):
        restarted.create(source_input(
            other, parent_id=child["id"], expected_parent_sha256=separated["sha256"],
        ))


def test_stale_and_dirty_sources_refuse_before_executing(tmp_path: Path):
    config = config_for(tmp_path)
    repo = make_repo(config.roots[0].path, "alpha")
    desk = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    mission = desk.create(source_input(repo))
    prepared = desk.prepare(mission["id"])
    (repo / "README.md").write_text("changed by someone else\n", encoding="utf-8")
    with pytest.raises(RocketConflict, match="dirty"):
        desk.execute(mission["id"], prepared["sha256"])
    assert len(desk.get(mission["id"])["stages"]) == 1

    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "different head")
    with pytest.raises(RocketConflict, match="moved"):
        desk.execute(mission["id"], prepared["sha256"])
    assert len(desk.get(mission["id"])["stages"]) == 1


def test_source_rejects_escape_untracked_and_secret_named_inputs(tmp_path: Path):
    config = config_for(tmp_path)
    repo = make_repo(config.roots[0].path, "alpha")
    desk = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    for name in ("../outside.txt", ".env", "private-token.txt", "missing.md"):
        mission = desk.create(RocketMissionInput(
            title="Negative", purpose="Reject an unsafe file", mode="source-preview",
            selections=[selection(repo)], source_path=name,
        ))
        prepared = desk.prepare(mission["id"])
        with pytest.raises((RocketConflict, ValueError)):
            desk.execute(mission["id"], prepared["sha256"])
        assert len(desk.get(mission["id"])["stages"]) == 1

    (repo / "untracked.md").write_text("private text", encoding="utf-8")
    # The new untracked file makes the checkout dirty: admission refuses earlier.
    mission = desk.create(RocketMissionInput(
        title="Negative", purpose="Do not admit an untracked file",
        mode="source-preview", selections=[selection(repo)],
        source_path="untracked.md",
    ))
    with pytest.raises(RocketConflict, match="dirty"):
        desk.prepare(mission["id"])


def test_body_overlap_executes_exact_typed_comparison_without_project_execution(tmp_path: Path):
    config = config_for(tmp_path)
    left = make_repo(config.roots[0].path, "left", body=True, emit=True)
    right = make_repo(config.roots[0].path, "right", body=True, emit=False)
    desk = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    mission = desk.create(RocketMissionInput(
        title="Compare interfaces", purpose="Check an exact emit and accept interface",
        mode="body-overlap", selections=[selection(left), selection(right)],
    ))
    prepared = desk.prepare(mission["id"])
    result = desk.execute(mission["id"], prepared["sha256"])
    assert result["output"]["tool"] == "body.overlap/v0"
    assert result["output"]["exact_interface_overlaps"] == [
        {"kind": "packet", "protocol": "specimen.packet", "version": "v0"}
    ]
    assert "Free Graph and Dogram were not executed" in result["output"]["notice"]
    assert git(left, "status", "--porcelain") == ""
    assert git(right, "status", "--porcelain") == ""

    # The same direction is not a compatible handoff.
    other = make_repo(config.roots[0].path, "other", body=True, emit=True)
    mission2 = desk.create(RocketMissionInput(
        title="Compare incompatible", purpose="Preserve missing compatibility",
        mode="body-overlap", selections=[selection(left), selection(other)],
    ))
    prepared2 = desk.prepare(mission2["id"])
    result2 = desk.execute(mission2["id"], prepared2["sha256"])
    assert result2["output"]["exact_interface_overlaps"] == []
    assert result2["output"]["unresolved"]


def test_mission_rejects_bad_composition_and_unfinished_parent(tmp_path: Path):
    config = config_for(tmp_path)
    repo = make_repo(config.roots[0].path, "alpha")
    desk = RocketDesk(config.state_dir / "rockets.sqlite3", config)
    with pytest.raises(RocketConflict, match="duplicate"):
        desk.create(RocketMissionInput(
            title="Bad", purpose="Duplicate", mode="body-overlap",
            selections=[selection(repo), selection(repo)],
        ))
    root = desk.create(source_input(repo))
    with pytest.raises(RocketConflict, match="exact receipt"):
        desk.create(source_input(
            repo, parent_id=root["id"], expected_parent_sha256="0" * 64,
        ))
    with pytest.raises(RocketConflict, match="together"):
        desk.create(source_input(repo, parent_id=root["id"]))


def test_rocket_api_guards_stage_sequence_restart_and_browser_door(tmp_path: Path):
    config = config_for(tmp_path)
    repo = make_repo(config.roots[0].path, "alpha")
    payload = source_input(repo).model_dump()
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        denied = client.post("/api/rockets/missions", json=payload)
        assert denied.status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"X-Workbench-Session": token}
        denied_origin = client.post("/api/rockets/missions", headers={
            **headers, "Origin": "http://foreign.example",
        }, json=payload)
        assert denied_origin.status_code == 403
        assert any(r["repo_path"] == "alpha" for r in client.get("/api/rockets/catalog").json()["repos"])
        created = client.post("/api/rockets/missions", headers=headers, json=payload)
        assert created.status_code == 200
        mission = created.json()
        assert client.get("/api/rockets/missions/999").status_code == 404
        skip = client.post(f"/api/rockets/missions/{mission['id']}/execute",
                           headers=headers, json={"expected_stage_sha256": "0" * 64})
        assert skip.status_code == 409
        prepared = client.post(f"/api/rockets/missions/{mission['id']}/prepare",
                               headers=headers)
        assert prepared.status_code == 200
        stale = client.post(f"/api/rockets/missions/{mission['id']}/execute",
                            headers=headers, json={"expected_stage_sha256": "0" * 64})
        assert stale.status_code == 409
        result = client.post(f"/api/rockets/missions/{mission['id']}/execute",
                             headers=headers, json={
                                 "expected_stage_sha256": prepared.json()["sha256"],
                             })
        assert result.status_code == 200
        separated = client.post(f"/api/rockets/missions/{mission['id']}/separate",
                                headers=headers, json={
                                    "expected_stage_sha256": result.json()["sha256"],
                                    "next_action": "Inspect a neighboring project",
                                    "residual_fog": "Not yet checked",
                                })
        assert separated.status_code == 200
        events = client.get("/api/events").json()["events"]
        assert any(e["kind"] == "rocket.stage.executed" for e in events)
        assert 'data-view="rocket"' in client.get("/").text
        assert "/api/rockets/missions/" in client.get("/assets/rocket.js").text
        assert "rocketLoad()" in client.get("/assets/app.js").text
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        recovered = client.get(f"/api/rockets/missions/{mission['id']}")
        assert recovered.status_code == 200
        assert len(recovered.json()["stages"]) == 3
        assert recovered.json()["stages"][-1]["sha256"] == separated.json()["sha256"]
