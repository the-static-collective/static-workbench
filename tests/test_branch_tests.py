"""BRANCH-DECK-005 tests run only in disposable fixture repositories."""
from pathlib import Path
import sqlite3
import subprocess
import sys

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.branch_worktree import create_worktree, preview_worktree
from static_workbench.branch_tests import available_suites, preview_test
from static_workbench.config import BranchTestSuite, RootConfig, WorkbenchConfig
from static_workbench.repos import discover_repositories


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          capture_output=True, text=True).stdout.strip()


def fixture(tmp_path: Path, test_body: str = "print('HELLO_FROM_ISOLATED_BRANCH')\n",
            configured: bool = True):
    root = tmp_path / "sources"
    repo = root / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Fixture")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "specimen.py").write_text(test_body, encoding="utf-8")
    git(repo, "add", "specimen.py")
    git(repo, "commit", "-m", "fixture")
    git(repo, "branch", "feat/specimen")
    git(repo, "remote", "add", "origin",
        "https://github.com/the-static-collective/demo.git")
    suite = BranchTestSuite(
        repo="the-static-collective/demo", id="fixture",
        argv=(sys.executable, "-I", "specimen.py"), timeout_seconds=15,
    )
    cfg = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),), branch_worktrees_enabled=True,
        branch_test_suites=(suite,) if configured else (),
    )
    return repo, cfg, git(repo, "rev-parse", "HEAD")


def prepare(repo: Path, config: WorkbenchConfig, sha: str):
    status = discover_repositories(config.roots)[0]
    plan = preview_worktree(config, status, "refs/heads/feat/specimen", sha)
    return create_worktree(config, status, "refs/heads/feat/specimen", sha,
                           plan["preview_digest"])


def request_body(sha: str):
    return {"root_id": "static", "repo_path": "demo",
            "ref": "refs/heads/feat/specimen",
            "expected_commit": sha, "suite_id": "fixture"}


def test_declared_suite_runs_only_after_separate_confirm_and_preserves_original(tmp_path: Path):
    repo, config, sha = fixture(tmp_path)
    prepared = prepare(repo, config, sha)
    original_status = git(repo, "status", "--porcelain")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"X-Workbench-Session": token}
        suites = client.get("/api/branches/tests/suites",
             params={"root_id": "static", "repo_path": "demo"}).json()["suites"]
        assert len(suites) == 1
        assert suites[0]["id"] == "fixture"
        plan_response = client.post("/api/branches/tests/preview",
            json=request_body(sha), headers=headers)
        assert plan_response.status_code == 200, plan_response.text
        plan = plan_response.json()
        assert plan["commit"] == sha
        assert plan["runtime_isolation"] == "none_process_runs_as_workbench_user"
        refused = client.post("/api/branches/tests/run", headers=headers,
            json={**request_body(sha), "expected_preview_digest": plan["preview_digest"],
                  "acknowledge_code_execution": False})
        assert refused.status_code == 422
        ran = client.post("/api/branches/tests/run", headers=headers,
            json={**request_body(sha), "expected_preview_digest": plan["preview_digest"],
                  "acknowledge_code_execution": True})
        assert ran.status_code == 200, ran.text
        result = ran.json()
        assert result["status"] == "passed"
        assert result["exit_code"] == 0
        assert "HELLO_FROM_ISOLATED_BRANCH" in result["output_excerpt"]
        assert result["commit"] == sha
        assert result["receipt_sha256"] and result["output_sha256"]
        events = client.get("/api/events").json()["events"]
        assert any(item["kind"] == "branches.test_run_finished" for item in events)
    assert git(repo, "symbolic-ref", "--short", "HEAD") == "main"
    assert git(repo, "status", "--porcelain") == original_status
    assert git(Path(prepared["destination"]), "rev-parse", "HEAD") == sha
    with sqlite3.connect(config.state_dir / "branch-test-receipts.sqlite3") as db:
        assert db.execute("SELECT count(*) FROM runs").fetchone()[0] == 1


def test_branch_owned_program_failure_is_recorded_not_renamed_success(tmp_path: Path):
    repo, cfg, sha = fixture(tmp_path, test_body="raise SystemExit(3)\n")
    prepare(repo, cfg, sha)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as client:
        headers = {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}
        plan = client.post("/api/branches/tests/preview",
                           json=request_body(sha), headers=headers).json()
        result = client.post("/api/branches/tests/run", headers=headers,
            json={**request_body(sha), "expected_preview_digest": plan["preview_digest"],
                  "acknowledge_code_execution": True})
    assert result.status_code == 200
    assert result.json()["status"] == "failed"
    assert result.json()["exit_code"] == 3


def test_test_preview_refuses_dirty_or_missing_worktree(tmp_path: Path):
    repo, config, sha = fixture(tmp_path)
    status = discover_repositories(config.roots)[0]
    try:
        preview_test(config, status, "refs/heads/feat/specimen", sha, "fixture")
    except ValueError as exc:
        assert "missing" in str(exc)
    else:
        raise AssertionError("test preview should refuse missing worktree")
    prepared = prepare(repo, config, sha)
    (Path(prepared["destination"]) / "specimen.py").write_text("dirty", encoding="utf-8")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        headers = {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}
        response = client.post("/api/branches/tests/preview",
                               json=request_body(sha), headers=headers)
    assert response.status_code == 409
    assert "not_clean" in response.json()["detail"]


def test_no_declared_suite_means_no_program_execution(tmp_path: Path):
    repo, config, sha = fixture(tmp_path, configured=False)
    prepare(repo, config, sha)
    assert available_suites(config, discover_repositories(config.roots)[0]) == ()
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        headers = {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}
        response = client.post("/api/branches/tests/preview",
                               json=request_body(sha), headers=headers)
    assert response.status_code == 409
    assert "not_declared" in response.json()["detail"]
