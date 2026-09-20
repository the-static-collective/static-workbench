"""OLD-GROWTH-002: pinned local Git source preview -> explicit HOUSE GRAFT ride.

No remote fetch, code execution, source checkout write or auto-GRAFT round.
A local Git object is verified against the selected commit tree; a configured
origin URL is only a local declaration, not authenticated remote history.
"""
from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path
from typing import Any

from .config import WorkbenchConfig
from .creator_shelf import CreatorShelf
from .old_growth import (
    MAX_SOURCE_BYTES, OldGrowthError, _canonical, _sha, compose,
)

_HEX40 = re.compile(r"^[0-9a-f]{40}$")
_RELATIVE = re.compile(r"^[A-Za-z0-9_.-]+(?:/[A-Za-z0-9_.-]+)*$")
_ALLOWED_ORIGINS = (
    "https://github.com/{repo}.git",
    "https://github.com/{repo}",
    "git@github.com:{repo}.git",
    "git@github.com:{repo}",
    "ssh://git@github.com/{repo}.git",
)


def _git(repo_dir: Path, *arguments: str, max_output: int = 2048) -> bytes:
    env = {**os.environ, "GIT_NO_REPLACE_OBJECTS": "1", "GIT_NO_LAZY_FETCH": "1",
           "GIT_NO_PROMISOR_FETCH": "1", "GIT_TERMINAL_PROMPT": "0"}
    # Avoid local "git" aliases, optional locks, hooks, checkout and filters.
    try:
        proc = subprocess.run(
            ["git", "--no-optional-locks", "-C", str(repo_dir), *arguments],
            env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            timeout=5, check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise OldGrowthError("Local Git source could not be inspected") from exc
    if proc.returncode != 0 or len(proc.stdout) > max_output:
        raise OldGrowthError("Local Git object absent, unreadable or beyond inspection limit")
    return proc.stdout


def _path(text: Any, name: str) -> str:
    if (type(text) is not str or len(text) > 256 or not _RELATIVE.fullmatch(text)
        or any(part in (".", "..") for part in text.split("/"))
        or any(part.casefold() in (".git", ".env", "secrets", "private", "credentials")
               for part in text.split("/"))):
        raise OldGrowthError(f"{name} must be a safe relative path")
    return text


def _source(config: WorkbenchConfig, selected: Any) -> dict[str, Any]:
    required = {
        "root_id", "repo_path", "repository", "commit", "path",
        "start_byte", "end_byte",
    }
    if type(selected) is not dict or set(selected) != required:
        raise OldGrowthError("Select exactly root_id, repo_path, repository, commit, path, start_byte, end_byte")
    root_id, repo_path = selected["root_id"], _path(selected["repo_path"], "repo_path")
    root = next((r for r in config.roots if r.id == root_id), None)
    if root is None:
        raise OldGrowthError("Select a configured Workbench root")
    root_real = root.path.resolve(strict=True)
    chosen = root_real
    for part in repo_path.split("/"):
        chosen = chosen / part
        if chosen.is_symlink():
            raise OldGrowthError("Symlinked repository location refused")
    repo_dir = chosen.resolve(strict=True)
    if not repo_dir.is_dir() or repo_dir == root_real:
        raise OldGrowthError("Select an actual repository directory")
    try:
        repo_dir.relative_to(root_real)
    except ValueError as exc:
        raise OldGrowthError("Repository outside configured root") from exc
    top = _git(repo_dir, "rev-parse", "--show-toplevel").decode("utf-8").strip()
    if Path(top).resolve(strict=True) != repo_dir:
        raise OldGrowthError("Selected path is not the checkout root")
    repository, commit, path = selected["repository"], selected["commit"], _path(selected["path"], "path")
    if (type(repository) is not str or not repository.startswith("the-static-collective/")
        or len(repository.split("/")) != 2 or
        not re.fullmatch(r"the-static-collective/[A-Za-z0-9_.-]+", repository)
        or type(commit) is not str or not _HEX40.fullmatch(commit)):
        raise OldGrowthError("Select a declared Collective repository and exact SHA-1 commit")
    origin = _git(repo_dir, "remote", "get-url", "origin").decode("utf-8").strip()
    if origin not in tuple(form.format(repo=repository) for form in _ALLOWED_ORIGINS):
        raise OldGrowthError("Local origin URL does not match the declared Collective repository")
    actual = _git(repo_dir, "rev-parse", "--verify", f"{commit}^{{commit}}").decode().strip()
    if actual != commit:
        raise OldGrowthError("Selected commit is not an exact local Git commit")
    listing = _git(repo_dir, "ls-tree", "-z", commit, "--", path, max_output=32768)
    lines = listing.split(b"\x00")
    matches = []
    for line in lines:
        if not line:
            continue
        try:
            meta, item_path = line.split(b"\t", 1)
            mode, kind, oid = meta.decode("ascii").split(" ")
            if item_path.decode("utf-8") == path:
                matches.append((mode, kind, oid))
        except (ValueError, UnicodeDecodeError) as exc:
            raise OldGrowthError("Malformed tree entry") from exc
    if len(matches) != 1 or matches[0][0] not in ("100644", "100755") or matches[0][1] != "blob":
        raise OldGrowthError("Selected commit path must be exactly one regular Git blob, not a symlink, tree or submodule")
    blob = matches[0][2]
    size_str = _git(repo_dir, "cat-file", "-s", blob).decode().strip()
    if not size_str.isdigit() or not 1 <= int(size_str) <= MAX_SOURCE_BYTES:
        raise OldGrowthError("Git blob is missing or exceeds bounded text-source size")
    raw = _git(repo_dir, "cat-file", "blob", blob, max_output=MAX_SOURCE_BYTES)
    if len(raw) != int(size_str) or b"\x00" in raw:
        raise OldGrowthError("Git object size/format mismatch or binary source")
    try:
        content = raw.decode("utf-8")
    except UnicodeDecodeError as exc:
        raise OldGrowthError("Pinned Git blob is not UTF-8") from exc
    # Explicitly re-use OLD-GROWTH-001's byte-span and digest validation.
    source = {
        "repository": repository, "commit": commit, "path": path,
        "content": content, "content_sha256": _sha(raw),
        "start_byte": selected["start_byte"], "end_byte": selected["end_byte"],
    }
    return {"source": source, "git_blob_sha": blob, "root_id": root_id, "repo_path": repo_path}


def preview(config: WorkbenchConfig, *, source_a: Any, source_b: Any,
            keep: Any, bend: Any, question: Any, relation_lane: Any,
            move: Any = "fuse") -> dict[str, Any]:
    a, b = _source(config, source_a), _source(config, source_b)
    result = compose(a["source"], b["source"], keep=keep, bend=bend,
                     question=question, relation_lane=relation_lane, move=move)
    for record, checked in zip(result["packet"]["sources"], (a, b)):
        record["origin_status"] = "verified_against_local_pinned_git_blob_only"
        record["git_blob_sha"] = checked["git_blob_sha"]
        record["root_id"] = checked["root_id"]
        record["repo_path"] = checked["repo_path"]
    # The proof scope changed: bind the verified-local metadata into both digests.
    result["packet"]["non_claims"] = [
        "Selected bytes, blob object, path and commit tree were checked in the local Git checkout.",
        "A locally declared origin URL does not authenticate GitHub history, authorship, remote custody or permission.",
        *result["packet"]["non_claims"][2:],
    ]
    result["packet_sha256"] = _sha(_canonical(result["packet"]))
    result["receipt"]["packet_sha256"] = result["packet_sha256"]
    result["receipt_sha256"] = _sha(_canonical(result["receipt"]))
    result["review"] = {
        "source_excerpt_sha256": result["receipt"]["source_excerpt_sha256"],
        "packet_sha256": result["packet_sha256"],
        "status": "review_required_before_import",
        "instruction": "Inspect both exact excerpts and source refs before separately saving one HOUSE-native ride.",
    }
    return result


def import_reviewed(config: WorkbenchConfig, shelf: CreatorShelf, *,
                    expected_packet_sha256: Any, reviewed_excerpt_sha256: Any,
                    human_confirmed: Any, **request: Any) -> dict[str, Any]:
    if human_confirmed is not True:
        raise OldGrowthError("Explicit human confirmation is required")
    fresh = preview(config, **request)
    if type(expected_packet_sha256) is not str or fresh["packet_sha256"] != expected_packet_sha256:
        raise OldGrowthError("Source or declarations changed since preview; review again")
    if (type(reviewed_excerpt_sha256) is not list or
        reviewed_excerpt_sha256 != fresh["receipt"]["source_excerpt_sha256"]):
        raise OldGrowthError("Both exact excerpt digests require separate review")
    packet = fresh["packet"]
    ride = {
        "format": "house.native-maxhinal-ride/v0.1",
        "engine": "house.old-growth-pinned-import/v0.2",
        "mode": "compose", "fuel_sha256": fresh["packet_sha256"],
        "seed": "0", "question": packet["declarations"]["question"],
        "residuals": ["Historical parallel remains available; no automatic GRAFT round was created."],
        "bad_spins": [],
        "source_refs": packet["sources"],
        "outputs": [
            {"kind": "old_growth_proposal", "candidate": packet["candidate"]},
            {"kind": "old_growth_parallel", "candidate": packet["parallel_alternative"]},
        ],
        "old_growth_packet_sha256": fresh["packet_sha256"],
        "declarations": packet["declarations"],
        "authority": "none", "promotion": "NONE",
        "notice": "Human-reviewed local Git source import; GRAFT round and candidate selection still require separate actions.",
        "non_claims": packet["non_claims"],
    }
    saved = shelf.save_old_growth_ride(ride, fresh["packet_sha256"])
    return {
        "receipt": saved, "ride": shelf.get_native_ride(saved["id"]),
        "next": f"/api/house-maxhinal/graft/rides/{saved['id']}/rounds",
        "status": "local_ride_saved_not_grafted",
    }
