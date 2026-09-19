from pathlib import Path
import subprocess

from static_workbench.config import RootConfig
from static_workbench.repos import discover_repositories, inspect_repository


def git(repo: Path, *args: str) -> str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        check=True,
        text=True,
        capture_output=True,
    )
    return result.stdout.strip()


def make_repo(path: Path) -> Path:
    path.mkdir(parents=True)
    git(path, "init", "-b", "main")
    git(path, "config", "user.name", "Test User")
    git(path, "config", "user.email", "test@example.invalid")
    (path / "README.md").write_text("hello\n", encoding="utf-8")
    git(path, "add", "README.md")
    git(path, "commit", "-m", "initial")
    return path


def test_inspect_repository_reports_branch_sha_and_clean_state(tmp_path: Path):
    repo = make_repo(tmp_path / "demo")

    status = inspect_repository(repo)

    assert status.name == "demo"
    assert status.branch == "main"
    assert status.head == git(repo, "rev-parse", "--short", "HEAD")
    assert status.dirty is False
    assert status.ahead is None
    assert status.behind is None


def test_inspect_repository_reports_dirty_worktree(tmp_path: Path):
    repo = make_repo(tmp_path / "demo")
    (repo / "README.md").write_text("changed\n", encoding="utf-8")

    status = inspect_repository(repo)

    assert status.dirty is True


def test_discover_repositories_is_root_qualified_and_depth_bounded(tmp_path: Path):
    root = tmp_path / "root"
    shallow = make_repo(root / "alpha")
    make_repo(root / "nested" / "beta")
    make_repo(root / "too" / "deep" / "gamma")

    results = discover_repositories((RootConfig("static", root),), max_depth=2)

    assert [(item.root_id, item.relative_path) for item in results] == [
        ("static", shallow.relative_to(root).as_posix()),
        ("static", "nested/beta"),
    ]


def test_inspect_repository_detects_local_stack_markers(tmp_path: Path):
    repo = make_repo(tmp_path / "mixed")
    (repo / "package.json").write_text("{}\n", encoding="utf-8")
    (repo / "pyproject.toml").write_text("[project]\nname='mixed'\n", encoding="utf-8")

    status = inspect_repository(repo)

    assert status.stacks == ("node", "python")
    assert status.markers == ("package.json", "pyproject.toml")
