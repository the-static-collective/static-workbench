from pathlib import Path
import subprocess

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.branch_deck import build_branch_deck, inspect_branches
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.repos import discover_repositories


def git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", "-C", str(repo), *args], check=True,
                          text=True, capture_output=True).stdout.strip()


def make_repo(tmp_path: Path) -> tuple[Path, tuple[RootConfig, ...]]:
    root = tmp_path / "sources"
    repo = root / "demo"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    (repo / "README.md").write_text("hello\n", encoding="utf-8")
    git(repo, "add", ".")
    git(repo, "commit", "-m", "initial")
    git(repo, "branch", "feat/visible")
    git(repo, "branch", "fix/also-visible")
    git(repo, "update-ref", "refs/remotes/origin/feat/cached-only", "HEAD")
    return repo, (RootConfig("static", root),)


def test_deck_finds_non_checked_out_local_and_cached_remote_refs(tmp_path: Path):
    repo, roots = make_repo(tmp_path)
    before = git(repo, "status", "--porcelain")
    head = git(repo, "rev-parse", "HEAD")
    result = build_branch_deck(discover_repositories(roots))
    refs = {card["ref"]: card for card in result["branches"]}
    feature = refs["refs/heads/feat/visible"]
    cached = refs["refs/remotes/origin/feat/cached-only"]

    assert result["remote_fetched"] is False
    assert result["all_branches_discovered"] is True
    assert feature["checkout"] == "not_checked_out"
    assert feature["commit"] == head
    assert feature["feature_like"] is True
    assert feature["readiness"] == "not_tested"
    assert cached["kind"] == "cached_remote"
    assert cached["checkout"] == "not_checked_out"
    assert refs["refs/heads/main"]["checkout"] == "here"
    assert git(repo, "status", "--porcelain") == before
    assert git(repo, "symbolic-ref", "--short", "HEAD") == "main"


def test_deck_detects_branch_in_another_worktree(tmp_path: Path):
    repo, roots = make_repo(tmp_path)
    other = tmp_path / "separate"
    git(repo, "worktree", "add", str(other), "feat/visible")
    found = build_branch_deck(discover_repositories(roots))
    card = next(card for card in found["branches"] if card["ref"] == "refs/heads/feat/visible")
    assert card["checkout"] == "other_worktree"
    assert card["repo_path"] == "demo"


def test_deck_reports_ref_ceiling_instead_of_claiming_completeness(tmp_path: Path):
    repo, roots = make_repo(tmp_path)
    status = discover_repositories(roots)[0]
    cards, truncated = inspect_branches(status, limit=1)
    assert len(cards) <= 1
    assert truncated is True
    assert build_branch_deck([status])["gaps"] == []


def test_deck_endpoint_and_asset_are_read_only(tmp_path: Path):
    repo, roots = make_repo(tmp_path)
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
                             state_dir=tmp_path / "state", roots=roots)
    before = git(repo, "status", "--porcelain")
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        result = client.get("/api/branches")
        html = client.get("/").text
        script = client.get("/assets/branch-deck.js")
        events = client.get("/api/events").json()["events"]
    assert result.status_code == 200
    assert result.json()["scope"] == "local_refs_and_cached_remote_tracking_refs_only"
    assert any(card["name"] == "feat/visible" for card in result.json()["branches"])
    assert 'data-view="branches"' in html
    assert script.status_code == 200
    assert "/api/branches" in script.text
    assert any(e["kind"] == "branches.scanned" for e in events)
    assert git(repo, "status", "--porcelain") == before
