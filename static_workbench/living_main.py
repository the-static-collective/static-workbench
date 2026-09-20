"""Read-only Chronobody-inspired composition preview.

Branch labels navigate; exact commit IDs identify code. This module does not
fetch, checkout, merge, execute, or assert compatibility or project authority.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import RootConfig
from .repos import RepoStatus, _git, _text

_SHA = re.compile(r"^[0-9a-f]{40}$")
_SCHEMA = "static-workbench.living-main-preview/v0"


class CompositionError(ValueError):
    pass


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")


def _resolve_repo(roots: tuple[RootConfig, ...], repo: RepoStatus) -> Path:
    """Reject missing, escaped and moved working trees even for stale inventory."""
    root = next((r for r in roots if r.id == repo.root_id), None)
    if root is None or not repo.relative_path:
        raise CompositionError("unrecognized configured root or relative path")
    root_path = root.path.expanduser().resolve(strict=True)
    path = (root_path / repo.relative_path).resolve(strict=True)
    if not path.is_relative_to(root_path) or str(path) != str(Path(repo.path).resolve(strict=True)):
        raise CompositionError("checkout no longer matches configured-root inventory")
    if _text(_git(path, "rev-parse", "--show-toplevel")) != str(path):
        raise CompositionError("candidate is not the root of its Git worktree")
    return path


def preview_composition(
    roots: tuple[RootConfig, ...],
    repos: list[RepoStatus],
    selections: object,
) -> dict[str, Any]:
    """Produce a deterministic manifest for explicitly selected *clean* checkouts.

    A selection is {root_id, relative_path, expected_sha}. The expected SHA
    binds human intent to a prior observation and prevents a moving branch
    from silently substituting a different body-time.
    """
    if not isinstance(selections, list) or not 1 <= len(selections) <= 24:
        raise CompositionError("select between 1 and 24 checkouts")
    inventory = {(r.root_id, r.relative_path): r for r in repos}
    members: list[dict[str, Any]] = []
    selected: set[tuple[str, str]] = set()
    for item in selections:
        if not isinstance(item, dict) or set(item) != {"root_id", "relative_path", "expected_sha"}:
            raise CompositionError("selection requires only root_id, relative_path and expected_sha")
        root_id, rel, expected = (item[k] for k in ("root_id", "relative_path", "expected_sha"))
        if not isinstance(root_id, str) or not isinstance(rel, str) or not isinstance(expected, str):
            raise CompositionError("selection values must be strings")
        if not _SHA.fullmatch(expected):
            raise CompositionError("expected_sha must be a full lowercase 40-character commit SHA")
        key = (root_id, rel)
        if key in selected:
            raise CompositionError("duplicate checkout selection")
        selected.add(key)
        repo = inventory.get(key)
        if repo is None:
            raise CompositionError("checkout not found in current inventory")
        try:
            path = _resolve_repo(roots, repo)
            actual = _text(_git(path, "rev-parse", "--verify", "HEAD^{commit}"))
            status = _git(path, "status", "--porcelain=v1", "--untracked-files=normal")
            branch = _text(_git(path, "symbolic-ref", "--quiet", "--short", "HEAD"))
        except (OSError, ValueError) as exc:
            raise CompositionError("checkout unavailable or changed") from exc
        if actual != expected:
            raise CompositionError("checkout HEAD changed since selection; inspect again")
        if status.returncode != 0 or status.stdout.strip():
            raise CompositionError("checkout is dirty or Git status is unavailable")
        members.append({
            "root_id": root_id,
            "relative_path": rel,
            "source_sha": actual,
            "branch_hint": branch,  # navigation, not identity
            "body_time_id": f"{root_id}/{rel}@{actual}",
            "observation": "CLEAN_CHECKOUT",
            "compatibility": "UNVERIFIED",
            "authority": "none",
        })
    members.sort(key=lambda m: (m["root_id"], m["relative_path"]))
    identity = {
        "schema": _SCHEMA,
        "members": [{k: v for k, v in member.items() if k != "branch_hint"} for member in members],
    }
    digest = hashlib.sha256(_canonical(identity)).hexdigest()
    return {
        "schema": _SCHEMA,
        "configuration_id": f"living-main@sha256:{digest}",
        "members": members,
        "execution": "NOT_ATTEMPTED",
        "integration": "NOT_TESTED",
        "authority": "none",
        "nonclaims": [
            "checkout presence is not readiness",
            "branch name is not executable identity",
            "component checks do not prove composition compatibility",
            "this preview does not execute, merge, install, promote or save a configuration",
        ],
    }
