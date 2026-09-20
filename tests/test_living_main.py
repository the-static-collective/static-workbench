from pathlib import Path
import subprocess

import pytest
from fastapi.testclient import TestClient

from static_workbench.config import RootConfig
from static_workbench.living_main import CompositionError, preview_composition
from static_workbench.repos import discover_repositories


def git(path: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(path), *args], check=True, capture_output=True, text=True
    ).stdout.strip()


def fixture(tmp_path: Path):
    root = tmp_path / "root"
    repo = root / "sample"
    repo.mkdir(parents=True)
    git(repo, "init", "-b", "main")
    git(repo, "config", "user.email", "test@example.invalid")
    git(repo, "config", "user.name", "Test")
    (repo / "README.md").write_text("initial\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "initial")
    roots = (RootConfig("root", root),)
    repos = discover_repositories(roots)
    sha = git(repo, "rev-parse", "HEAD")
    selection = {"root_id": "root", "relative_path": "sample", "expected_sha": sha}
    return roots, repos, repo, selection


def test_preview_is_pinned_deterministic_and_nonexecuting(tmp_path: Path):
    roots, repos, _repo, selection = fixture(tmp_path)
    first = preview_composition(roots, repos, [selection])
    second = preview_composition(roots, repos, [selection])
    assert first == second
    assert first["members"][0]["source_sha"] == selection["expected_sha"]
    assert first["members"][0]["body_time_id"].endswith("@" + selection["expected_sha"])
    assert first["execution"] == "NOT_ATTEMPTED"
    assert first["integration"] == "NOT_TESTED"
    assert first["authority"] == "none"


def test_moved_head_is_refused_not_silently_replaced(tmp_path: Path):
    roots, repos, repo, selection = fixture(tmp_path)
    (repo / "README.md").write_text("next\n")
    git(repo, "add", "README.md")
    git(repo, "commit", "-m", "next")
    with pytest.raises(CompositionError, match="HEAD changed"):
        preview_composition(roots, repos, [selection])


def test_dirty_checkout_is_refused(tmp_path: Path):
    roots, repos, repo, selection = fixture(tmp_path)
    (repo / "untracked.txt").write_text("dirty\n")
    with pytest.raises(CompositionError, match="dirty"):
        preview_composition(roots, repos, [selection])


def test_duplicate_unknown_and_spoofed_selections_are_refused(tmp_path: Path):
    roots, repos, _repo, selection = fixture(tmp_path)
    with pytest.raises(CompositionError, match="duplicate"):
        preview_composition(roots, repos, [selection, selection])
    with pytest.raises(CompositionError, match="not found"):
        preview_composition(roots, repos, [{**selection, "relative_path": "unknown"}])
    with pytest.raises(CompositionError, match="only root_id"):
        preview_composition(roots, repos, [{**selection, "authority": "present"}])
    with pytest.raises(CompositionError, match="40-character"):
        preview_composition(roots, repos, [{**selection, "expected_sha": "main"}])


def test_branch_label_is_not_identity(tmp_path: Path):
    roots, repos, repo, selection = fixture(tmp_path)
    original = preview_composition(roots, repos, [selection])
    git(repo, "branch", "-m", "new-name")
    renamed = preview_composition(roots, discover_repositories(roots), [selection])
    assert renamed["configuration_id"] == original["configuration_id"]
    assert renamed["members"][0]["branch_hint"] == "new-name"
