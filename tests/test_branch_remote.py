"""No external network is used by the BRANCH-DECK-002 fixture suite."""
from pathlib import Path
import subprocess

from fastapi.testclient import TestClient
import pytest

from static_workbench.app import create_app
from static_workbench.branch_remote import RemoteDiscoveryError, _origin_slug, inspect_github_repo
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.repos import discover_repositories


def git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], text=True, capture_output=True, check=True
    ).stdout.strip()


def local(tmp_path: Path) -> tuple[Path, WorkbenchConfig]:
    root = tmp_path / "sources"
    repo = root / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "README.md").write_text("demo\n", encoding="utf-8")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "first")
    git(repo, "branch", "feat/local")
    git(repo, "remote", "add", "origin", "https://github.com/the-static-collective/demo.git")
    return repo, WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
        github_remote_discovery=True)


def fixture_pages(repo: Path):
    head = git(repo, "rev-parse", "HEAD")
    def read(path: str):
        if "/branches?" in path:
            return [
                {"name": "main", "commit": {"sha": head}, "protected": True},
                {"name": "feat/local", "commit": {"sha": head}, "protected": False},
                {"name": "feat/remote-only", "commit": {"sha": "a" * 40}, "protected": False},
            ]
        if "/pulls?" in path:
            return [{
                "number": 34, "title": "Proposed feature", "draft": True,
                "head": {"ref": "feat/remote-only", "sha": "a" * 40,
                         "repo": {"full_name": "the-static-collective/demo"}},
            }, {
                "number": 35, "title": "Fork collides with a local name", "draft": False,
                "head": {"ref": "feat/local", "sha": head,
                         "repo": {"full_name": "somebody-else/demo"}},
            }]
        raise AssertionError(path)
    return read


def test_github_origin_is_whitelisted_without_credentials_or_attacker_host(tmp_path: Path):
    repo, config = local(tmp_path)
    status = discover_repositories(config.roots)[0]
    assert _origin_slug(status) == "the-static-collective/demo"
    for bad in (
        "https://github.com.evil.example/the-static-collective/demo",
        "https://evil.example/the-static-collective/demo",
        "https://github.com/other/demo", "file:///tmp/anywhere",
        "https://user:secret@github.com/the-static-collective/demo",
    ):
        git(repo, "remote", "set-url", "origin", bad)
        with pytest.raises(RemoteDiscoveryError):
            _origin_slug(status)


def test_explicit_lookup_detects_remote_only_and_same_repo_pr(monkeypatch, tmp_path: Path):
    repo, config = local(tmp_path)
    monkeypatch.setattr("static_workbench.branch_remote._github_json", fixture_pages(repo))
    head = git(repo, "rev-parse", "HEAD")
    before = git(repo, "status", "--porcelain")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        result = client.get("/api/branches/remote",
            params={"root_id": "static", "repo_path": "demo"})
        events = client.get("/api/events").json()["events"]
    assert result.status_code == 200, result.text
    body = result.json()
    cards = {item["name"]: item for item in body["branches"]}
    assert body["github_repo"] == "the-static-collective/demo"
    assert body["branch_scan_complete"] is True
    assert cards["feat/remote-only"]["relation"] == "remote_only"
    assert cards["feat/remote-only"]["open_prs"][0]["number"] == 34
    assert cards["feat/remote-only"]["open_prs"][0]["draft"] is True
    assert cards["feat/local"]["relation"] == "same_local_commit"
    assert cards["feat/local"]["open_prs"] == []  # Fork cannot impersonate origin ref.
    assert cards["main"]["commit"] == head
    assert any(e["kind"] == "branches.github_observed" for e in events)
    assert git(repo, "symbolic-ref", "--short", "HEAD") == "main"
    assert git(repo, "status", "--porcelain") == before


def test_remote_lookup_is_disabled_by_default_and_does_not_call_network(monkeypatch, tmp_path: Path):
    repo, config = local(tmp_path)
    config = WorkbenchConfig(bind_host=config.bind_host, port=config.port,
        state_dir=config.state_dir, roots=config.roots)
    monkeypatch.setattr("static_workbench.branch_remote._github_json",
        lambda path: pytest.fail("network call despite disabled remote discovery"))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.get("/api/branches/remote",
            params={"root_id": "static", "repo_path": "demo"})
    assert response.status_code == 403


def test_remote_missing_checkout_refuses_instead_of_guessing(monkeypatch, tmp_path: Path):
    repo, config = local(tmp_path)
    monkeypatch.setattr("static_workbench.branch_remote._github_json",
        lambda path: pytest.fail("unknown local repo must not initiate network"))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        response = client.get("/api/branches/remote",
            params={"root_id": "static", "repo_path": "../other"})
    assert response.status_code == 404


def test_pr_failure_preserves_branch_data_with_explicit_gap(monkeypatch, tmp_path: Path):
    repo, config = local(tmp_path)
    fixture = fixture_pages(repo)
    def request(path: str):
        if "/pulls?" in path:
            raise RemoteDiscoveryError("github_http_403")
        return fixture(path)
    monkeypatch.setattr("static_workbench.branch_remote._github_json", request)
    status = discover_repositories(config.roots)[0]
    observed = inspect_github_repo(status, [])
    assert len(observed["branches"]) == 3
    assert observed["pr_scan_complete"] is False
    assert observed["gaps"] == ["github_http_403"]
    assert observed["branches"][0]["open_prs"] == []
    assert observed["branches"][0]["pr_scan_complete"] is False


def test_full_page_sets_uncertainty_not_complete(monkeypatch, tmp_path: Path):
    repo, config = local(tmp_path)
    branch_items = [{"name": f"feat/n-{i}", "commit": {"sha": "c" * 40}}
                    for i in range(100)]
    def request(path: str):
        if "/branches?" in path:
            return branch_items
        return []
    monkeypatch.setattr("static_workbench.branch_remote._github_json", request)
    status = discover_repositories(config.roots)[0]
    observed = inspect_github_repo(status, [])
    assert observed["branch_scan_complete"] is False
    assert "branch_page_limit_reached" in observed["gaps"]
