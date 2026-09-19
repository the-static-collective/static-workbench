"""Read-only local source handoffs inspired by Creator Workspace routing.

This module does not call ChatGPT plugins, run repository code, or promote source text
to project authority. A person explicitly chooses a local checkout and a search term.
"""
from __future__ import annotations

import os
import hashlib
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .config import RootConfig
from .repos import RepoStatus

_SKIP_DIRS = frozenset({
    ".git", ".venv", "node_modules", "dist", "build", "vendor",
    "private", "secrets", "credentials", "__pycache__", ".next",
})
_SKIP_NAME_PARTS = ("secret", "credential", "password", "token", ".env", "private")
_SOURCE_EXTENSIONS = frozenset({".md", ".markdown", ".txt"})
_MAX_FILES = 200
_MAX_BYTES = 131072
_MAX_HITS = 20
_MAX_DEPTH = 4

_WORKFLOWS: tuple[dict[str, Any], ...] = (
    {
        "id": "recall", "label": "Recall / research brief",
        "route": "workspace-recall -> brain-briefs",
        "job": "Find a small, attributable context set before synthesizing a brief.",
        "aliases": ("the-autodisco", "alex.2", "dogram", "national-treasure", "the-daily-slice"),
    },
    {
        "id": "create", "label": "Create from the brain",
        "route": "workspace-recall -> create-from-brain",
        "job": "Bring specific notes into a lyric, post, script or other draft; mark interpretation.",
        "aliases": ("the-autodisco", "the-haunted-toaster", "static-live", "the-haunted-phonography"),
    },
    {
        "id": "live", "label": "Live / podcast",
        "route": "project-owned Static Live / Broadcast console",
        "job": "Inspect the local media organs; no stream or recording is started here.",
        "aliases": ("static-live", "the-haunted-phonography", "iron-lung"),
    },
    {
        "id": "community", "label": "Community / whole return",
        "route": "project-owned Garden -> Band Runtime -> Nourish",
        "job": "Inspect the help-slip organs; source needs and confirmations remain project-owned.",
        "aliases": ("bananaspork", "band-runtime", "nourish-kids"),
    },
    {
        "id": "build", "label": "Research -> executable",
        "route": "local source -> bounded experiment -> project-native receipt",
        "job": "Inspect the relevant repo before proposing a change; this desk cannot execute it.",
        "aliases": ("loadout", "3rdi", "alex.2", "dogram", "static-workbench"),
    },
)


def creator_desk_status(repos: list[RepoStatus]) -> dict[str, Any]:
    by_name = {repo.name.casefold(): repo for repo in repos}
    workflows = []
    for spec in _WORKFLOWS:
        matches = [asdict(by_name[name]) for name in spec["aliases"] if name in by_name]
        workflows.append({
            "id": spec["id"], "label": spec["label"], "route": spec["route"],
            "job": spec["job"], "local_sources": matches,
            "status": "inspectable" if matches else "not_discovered",
        })
    return {
        "workflows": workflows,
        "laws": [
            "source != interpretation",
            "working tree != frozen commit",
            "plugin route != local plugin execution",
            "inspection != project authority",
        ],
        "limits": {"max_files": _MAX_FILES, "max_file_bytes": _MAX_BYTES, "max_hits": _MAX_HITS},
    }


def search_sources(
    roots: tuple[RootConfig, ...],
    repos: list[RepoStatus],
    root_id: str,
    repo_path: str,
    query: str,
) -> dict[str, Any]:
    """Search bounded Markdown/plain-text sources in one explicitly chosen checkout."""
    needle = query.strip().casefold()
    if len(needle) < 2 or len(needle) > 100:
        raise ValueError("query must have between 2 and 100 nonblank characters")
    root = next((item for item in roots if item.id == root_id), None)
    repo = next(
        (item for item in repos if item.root_id == root_id and item.relative_path == repo_path),
        None,
    )
    if root is None or repo is None:
        raise ValueError("choose a discovered repository under a configured root")

    root_real = root.path.resolve(strict=True)
    repo_real = Path(repo.path).resolve(strict=True)
    try:
        repo_real.relative_to(root_real)
    except ValueError as exc:
        raise ValueError("repository is outside its configured root") from exc

    hits: list[dict[str, Any]] = []
    examined = 0
    for current, directories, filenames in os.walk(repo_real, followlinks=False):
        folder = Path(current)
        depth = len(folder.relative_to(repo_real).parts)
        directories[:] = sorted(
            d for d in directories
            if depth < _MAX_DEPTH
            and not d.startswith(".")
            and d.casefold() not in _SKIP_DIRS
            and not (folder / d).is_symlink()
        )
        for name in sorted(filenames):
            if examined >= _MAX_FILES or len(hits) >= _MAX_HITS:
                break
            lower = name.casefold()
            if name.startswith(".") or any(part in lower for part in _SKIP_NAME_PARTS):
                continue
            path = folder / name
            if path.suffix.casefold() not in _SOURCE_EXTENSIONS or path.is_symlink():
                continue
            try:
                resolved = path.resolve(strict=True)
                resolved.relative_to(repo_real)
                if not resolved.is_file() or resolved.stat().st_size > _MAX_BYTES:
                    continue
                examined += 1
                raw = resolved.read_bytes()
                body = raw.decode("utf-8")
            except (OSError, UnicodeError, ValueError):
                continue
            for line_number, line in enumerate(body.splitlines(), start=1):
                if needle not in line.casefold():
                    continue
                hits.append({
                    "file_sha256": hashlib.sha256(raw).hexdigest(),
                    "root_id": root_id,
                    "repo_path": repo_path,
                    "source_path": resolved.relative_to(repo_real).as_posix(),
                    "line": line_number,
                    "snippet": line.strip()[:240],
                    "head": repo.head,
                    "dirty": repo.dirty,
                })
                if len(hits) >= _MAX_HITS:
                    break
        if examined >= _MAX_FILES or len(hits) >= _MAX_HITS:
            break

    return {
        "root_id": root_id, "repo_path": repo_path, "query": query.strip(),
        "hits": hits, "files_examined": examined,
        "truncated": examined >= _MAX_FILES or len(hits) >= _MAX_HITS,
        "source_kind": "local_worktree",
        "authority": "none",
    }
