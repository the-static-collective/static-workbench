"""BRANCH-DECK-003: explicit exact-SHA isolated local worktree preparation.

Creates no remote branch, installs nothing, and never executes project test code.
The only effect is a detached Git worktree under Workbench-owned state and
the corresponding Git administrative worktree registration.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from pathlib import Path

from .config import WorkbenchConfig
from .repos import RepoStatus, _git

_SHA = re.compile(r"^[0-9a-f]{40}$")


class WorktreeError(ValueError):
    pass


def _git_checked(path: Path, *arguments: str, timeout: int = 6) -> str:
    try:
        result = subprocess.run(
            ["git", "-C", str(path), *arguments],
            capture_output=True, text=True, timeout=timeout, check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorktreeError("git_inspection_unavailable") from exc
    if result.returncode:
        raise WorktreeError("git_inspection_failed")
    return result.stdout.strip()


def _destination(config: WorkbenchConfig, repo: RepoStatus, sha: str) -> Path:
    stem = hashlib.sha256(json.dumps(
        [repo.root_id, repo.relative_path, sha], separators=(",", ":")
    ).encode("utf-8")).hexdigest()[:24]
    return config.state_dir / "branch-deck-worktrees" / ("candidate-" + stem)


def preview_worktree(
    config: WorkbenchConfig, repo: RepoStatus, ref: str, expected_commit: str,
) -> dict:
    if not config.branch_worktrees_enabled:
        raise WorktreeError("isolated_worktrees_disabled")
    if not isinstance(ref, str) or not ref.startswith("refs/heads/"):
        raise WorktreeError("only_preexisting_local_branches_supported")
    if not _SHA.fullmatch(expected_commit):
        raise WorktreeError("invalid_expected_commit")
    # Explicit local ref; not a user-supplied Git option or remote-tracking ref.
    if _git_checked(Path(repo.path), "check-ref-format", ref) != "":
        raise WorktreeError("invalid_ref")
    current = _git_checked(Path(repo.path), "rev-parse", "--verify", ref + "^{commit}")
    if current != expected_commit:
        raise WorktreeError("branch_moved_review_current_commit")
    # Refuse configured external checkout filters; hooks are disabled for this
    # operation. This may refuse repos using Git LFS until separately reviewed.
    configured = _git(Path(repo.path), "config", "--get-regexp",
                      r"^filter\..*\.(process|smudge)$")
    if configured.returncode == 0 and configured.stdout.strip():
        raise WorktreeError("checkout_filters_configured_manual_review_required")
    if configured.returncode not in (0, 1):
        raise WorktreeError("cannot_verify_checkout_filters")
    destination = _destination(config, repo, expected_commit)
    home = config.state_dir.expanduser().resolve(strict=False)
    if destination.is_symlink() or destination.exists():
        raise WorktreeError("isolated_destination_already_exists_inspect_before_retry")
    parent = destination.parent
    if parent.is_symlink():
        raise WorktreeError("worktree_parent_symlink_refused")
    if parent.exists() and not parent.is_dir():
        raise WorktreeError("worktree_parent_not_directory")
    if not destination.resolve(strict=False).is_relative_to(home):
        raise WorktreeError("destination_outside_workbench_state")
    receipt = {
        "root_id": repo.root_id, "repo_path": repo.relative_path,
        "ref": ref, "commit": expected_commit, "destination": str(destination),
        "effect": "create_detached_local_worktree", "tests": "not_run",
    }
    digest = hashlib.sha256(json.dumps(receipt, sort_keys=True,
        separators=(",", ":")).encode("utf-8")).hexdigest()
    return {**receipt, "preview_digest": digest}


def create_worktree(
    config: WorkbenchConfig, repo: RepoStatus, ref: str,
    expected_commit: str, expected_preview_digest: str,
) -> dict:
    preview = preview_worktree(config, repo, ref, expected_commit)
    if preview["preview_digest"] != expected_preview_digest:
        raise WorktreeError("preview_changed_review_again")
    destination = Path(preview["destination"])
    # No destructive cleanup on partial failure: inspect Git worktree list and
    # destination; retry may be unsafe if Git registered a new worktree.
    try:
        destination.parent.mkdir(parents=True, exist_ok=True)
        result = subprocess.run(
            ["git", "-c", "core.hooksPath=/dev/null", "-c", "core.fsmonitor=false",
             "-C", str(Path(repo.path)), "worktree", "add", "--detach",
             str(destination), expected_commit],
            text=True, capture_output=True, timeout=90, check=False,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise WorktreeError("worktree_outcome_uncertain_inspect_destination_and_git_list") from exc
    if result.returncode:
        raise WorktreeError("worktree_creation_failed_inspect_destination_and_git_list")
    actual = _git_checked(destination, "rev-parse", "--verify", "HEAD")
    if actual != expected_commit:
        raise WorktreeError("worktree_commit_mismatch_outcome_uncertain")
    return {
        **preview, "actual_commit": actual, "created": True,
        "tests": "not_run", "project_code_executed": False,
    }
