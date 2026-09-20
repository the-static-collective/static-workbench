"""BRANCH-DECK-003 effects run only in disposable tmp_path repositories."""
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
import pytest

from static_workbench.app import create_app
from static_workbench.branch_worktree import WorktreeError, preview_worktree
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.repos import discover_repositories


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          text=True, capture_output=True).stdout.strip()


def fixture(tmp_path: Path, enabled: bool = True):
    root = tmp_path / "sources"
    repo = root / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    git(repo, "branch", "feat/isolated")
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
        branch_worktrees_enabled=enabled)
    return repo, config, git(repo, "rev-parse", "HEAD")


def payload(commit: str):
    return {"root_id": "static", "repo_path": "demo",
            "ref": "refs/heads/feat/isolated", "expected_commit": commit}


def test_explicit_preview_and_create_preserve_main_and_do_not_run_hook(tmp_path: Path):
    repo, config, sha = fixture(tmp_path)
    hook_marker = tmp_path / "hook-ran"
    hook = repo / ".git" / "hooks" / "post-checkout"
    hook.write_text("#!/bin/sh\necho ran > " + str(hook_marker) + "\n", encoding="utf-8")
    hook.chmod(0o755)
    before_status = git(repo, "status", "--porcelain")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        session = client.get("/api/bootstrap").json()["session_token"]
        headers = {"X-Workbench-Session": session}
        preview = client.post("/api/branches/worktrees/preview",
                              json=payload(sha), headers=headers)
        assert preview.status_code == 200, preview.text
        plan = preview.json()
        assert plan["effect"] == "create_detached_local_worktree"
        assert not Path(plan["destination"]).exists()
        denied = client.post("/api/branches/worktrees/create", json={
            **payload(sha), "expected_preview_digest": plan["preview_digest"],
            "acknowledge_effect": False}, headers=headers)
        assert denied.status_code == 422
        created = client.post("/api/branches/worktrees/create", json={
            **payload(sha), "expected_preview_digest": plan["preview_digest"],
            "acknowledge_effect": True}, headers=headers)
        assert created.status_code == 200, created.text
        outcome = created.json()
        assert outcome["actual_commit"] == sha
        assert outcome["tests"] == "not_run"
        assert git(Path(outcome["destination"]), "rev-parse", "HEAD") == sha
        assert git(Path(outcome["destination"]), "symbolic-ref", "-q", "HEAD") == ""
        assert not hook_marker.exists()
        again = client.post("/api/branches/worktrees/create", json={
            **payload(sha), "expected_preview_digest": plan["preview_digest"],
            "acknowledge_effect": True}, headers=headers)
        assert again.status_code == 409
        events = client.get("/api/events").json()["events"]
        assert sum(e["kind"] == "branches.worktree_created" for e in events) == 1
    assert git(repo, "symbolic-ref", "--short", "HEAD") == "main"
    assert git(repo, "status", "--porcelain") == before_status


def test_guard_refuses_missing_session(tmp_path: Path):
    repo, config, sha = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.post("/api/branches/worktrees/preview", json=payload(sha))
    assert response.status_code == 403


def test_disabled_by_default_and_remote_only_refs_refused(tmp_path: Path):
    repo, config, sha = fixture(tmp_path, enabled=False)
    status = discover_repositories(config.roots)[0]
    with pytest.raises(WorktreeError, match="disabled"):
        preview_worktree(config, status, "refs/heads/feat/isolated", sha)
    enabled = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=config.state_dir, roots=config.roots, branch_worktrees_enabled=True)
    with pytest.raises(WorktreeError, match="local_branches"):
        preview_worktree(enabled, status, "refs/remotes/origin/feat/isolated", sha)


def test_stale_ref_commit_and_external_filter_are_refused(tmp_path: Path):
    repo, config, sha = fixture(tmp_path)
    status = discover_repositories(config.roots)[0]
    with pytest.raises(WorktreeError, match="branch_moved"):
        preview_worktree(config, status, "refs/heads/feat/isolated", "a" * 40)
    git(repo, "config", "filter.danger.smudge", "touch /tmp/should-never-run")
    with pytest.raises(WorktreeError, match="checkout_filters"):
        preview_worktree(config, status, "refs/heads/feat/isolated", sha)
