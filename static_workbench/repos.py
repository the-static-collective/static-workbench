from __future__ import annotations

import os
import subprocess
from dataclasses import dataclass, replace
from pathlib import Path

from .config import RootConfig


@dataclass(frozen=True)
class RepoStatus:
    name: str
    path: str
    branch: str | None
    detached: bool
    head: str | None
    dirty: bool
    ahead: int | None
    behind: int | None
    full_head: str | None = None
    root_id: str | None = None
    relative_path: str | None = None
    stacks: tuple[str, ...] = ()
    markers: tuple[str, ...] = ()


def _git(path: Path, *args: str, timeout: float = 3.0) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["git", "-C", str(path), *args],
        text=True,
        capture_output=True,
        check=False,
        timeout=timeout,
        env={**os.environ, "LC_ALL": "C", "GIT_OPTIONAL_LOCKS": "0"},
    )


def _text(result: subprocess.CompletedProcess[str]) -> str | None:
    if result.returncode != 0:
        return None
    value = result.stdout.strip()
    return value or None


def inspect_repository(path: Path) -> RepoStatus:
    repo = path.expanduser().resolve(strict=True)
    inside = _git(repo, "rev-parse", "--is-inside-work-tree")
    if _text(inside) != "true":
        raise ValueError(f"not a Git worktree: {repo}")

    branch = _text(_git(repo, "symbolic-ref", "--quiet", "--short", "HEAD"))
    head = _text(_git(repo, "rev-parse", "--short", "HEAD"))
    full_head = _text(_git(repo, "rev-parse", "--verify", "HEAD^{commit}"))
    status = _git(repo, "status", "--porcelain=v1", "--untracked-files=normal")
    if status.returncode != 0:
        raise ValueError(f"unable to inspect Git status: {repo}")
    dirty = bool(status.stdout.strip())

    upstream = _text(_git(repo, "rev-parse", "--abbrev-ref", "@{upstream}"))
    ahead: int | None = None
    behind: int | None = None
    if upstream:
        counts = _text(_git(repo, "rev-list", "--left-right", "--count", "HEAD...@{upstream}"))
        if counts:
            parts = counts.replace("\t", " ").split()
            if len(parts) == 2:
                ahead, behind = int(parts[0]), int(parts[1])

    marker_map = (
        ("package.json", "node"),
        ("pyproject.toml", "python"),
        ("requirements.txt", "python"),
        ("Cargo.toml", "rust"),
        ("go.mod", "go"),
        ("Gemfile", "ruby"),
        ("pom.xml", "java"),
        ("build.gradle", "java"),
        ("docker-compose.yml", "docker"),
        ("compose.yml", "docker"),
    )
    markers = tuple(name for name, _stack in marker_map if (repo / name).is_file())
    stacks = tuple(dict.fromkeys(stack for name, stack in marker_map if (repo / name).is_file()))

    return RepoStatus(
        name=repo.name,
        path=str(repo),
        branch=branch,
        detached=branch is None,
        head=head,
        dirty=dirty,
        full_head=full_head,
        ahead=ahead,
        behind=behind,
        stacks=stacks,
        markers=markers,
    )


def _candidate_repos(root: Path, max_depth: int):
    root = root.expanduser().resolve(strict=False)
    if not root.is_dir():
        return

    for current, dirnames, _filenames in os.walk(root, followlinks=False):
        current_path = Path(current)
        relative = current_path.relative_to(root)
        depth = len(relative.parts)

        dirnames[:] = [d for d in dirnames if d not in {".git", ".worktrees", "node_modules", ".venv"}]
        if depth > max_depth:
            dirnames[:] = []
            continue

        if (current_path / ".git").exists():
            yield current_path
            dirnames[:] = []
            continue

        if depth >= max_depth:
            dirnames[:] = []


def discover_repositories(roots: tuple[RootConfig, ...], max_depth: int = 4) -> list[RepoStatus]:
    discovered: list[RepoStatus] = []
    for root in roots:
        root_real = root.path.expanduser().resolve(strict=False)
        for repo_path in _candidate_repos(root_real, max_depth):
            try:
                status = inspect_repository(repo_path)
            except (OSError, subprocess.SubprocessError, ValueError):
                continue
            discovered.append(
                replace(
                    status,
                    root_id=root.id,
                    relative_path=repo_path.resolve().relative_to(root_real).as_posix(),
                )
            )
    return sorted(discovered, key=lambda item: (item.root_id or "", item.relative_path or item.name))
