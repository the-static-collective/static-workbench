"""BRANCH-DECK-001: bounded, read-only inventory of *locally known* Git refs.

This is a navigation surface, not a remote sync, test runner or merge verdict.
"""
from __future__ import annotations

from pathlib import Path

from .repos import RepoStatus, _git

MAX_REFS_PER_REPO = 400


def _worktree_branches(repo: Path) -> dict[str, list[str]]:
    result = _git(repo, "worktree", "list", "--porcelain")
    if result.returncode != 0:
        raise ValueError("unable to inspect local worktrees")
    found: dict[str, list[str]] = {}
    worktree: str | None = None
    for line in result.stdout.splitlines():
        if line.startswith("worktree "):
            worktree = line[len("worktree "):]
        elif line.startswith("branch refs/heads/") and worktree is not None:
            ref = line[len("branch "):]
            found.setdefault(ref, []).append(worktree)
    return found


def inspect_branches(repo: RepoStatus, limit: int = MAX_REFS_PER_REPO) -> tuple[list[dict], bool]:
    """Return branch cards and an explicit truncation signal. No fetch or checkout."""
    if not 1 <= limit <= MAX_REFS_PER_REPO:
        raise ValueError("invalid branch scan limit")
    path = Path(repo.path)
    # The scanner accepts only paths already discovered by the configured-root
    # repository inventory. Never take a path or a Git argument from a request.
    worktrees = _worktree_branches(path)
    result = _git(
        path, "for-each-ref", f"--count={limit + 1}", "--sort=-committerdate",
        "--format=%(refname)%09%(objectname)%09%(committerdate:iso8601-strict)%09%(symref)",
        "refs/heads", "refs/remotes",
    )
    if result.returncode != 0:
        raise ValueError("unable to inspect local refs")
    lines = result.stdout.splitlines()
    truncated = len(lines) > limit
    cards: list[dict] = []
    home = path.resolve(strict=False)
    for line in lines[:limit]:
        fields = line.split("\t")
        if len(fields) != 4:
            raise ValueError("malformed local Git ref")
        ref, sha, committed_at, symref = fields
        if symref or len(sha) != 40:
            continue
        if ref.startswith("refs/heads/"):
            kind = "local"
            name = ref[len("refs/heads/"):]
            elsewhere = [p for p in worktrees.get(ref, []) if Path(p).resolve(strict=False) != home]
            location = "here" if any(Path(p).resolve(strict=False) == home for p in worktrees.get(ref, [])) else ("other_worktree" if elsewhere else "not_checked_out")
        elif ref.startswith("refs/remotes/"):
            kind = "cached_remote"
            name = ref[len("refs/remotes/"):]
            location = "not_checked_out"
        else:
            continue
        cards.append({
            "root_id": repo.root_id, "repo_path": repo.relative_path, "repo_name": repo.name,
            "name": name, "ref": ref, "kind": kind, "commit": sha,
            "committed_at": committed_at or None, "checkout": location,
            "feature_like": name.lower().startswith(("feat/", "feature/", "fix/", "experiment/", "exp/")),
            "readiness": "not_tested",
        })
    return cards, truncated


def build_branch_deck(repos: list[RepoStatus]) -> dict:
    branches: list[dict] = []
    gaps: list[dict] = []
    for repo in repos:
        try:
            cards, truncated = inspect_branches(repo)
            branches.extend(cards)
            if truncated:
                gaps.append({"root_id": repo.root_id, "repo_path": repo.relative_path, "reason": "ref_limit_reached"})
        except (OSError, ValueError) as exc:
            gaps.append({"root_id": repo.root_id, "repo_path": repo.relative_path, "reason": str(exc)})
    return {
        "scope": "local_refs_and_cached_remote_tracking_refs_only",
        "remote_fetched": False,
        "all_branches_discovered": not gaps,
        "repos_scanned": len(repos),
        "branches": branches,
        "gaps": gaps,
    }
