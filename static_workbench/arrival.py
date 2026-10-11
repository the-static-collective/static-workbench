"""ARK/ARRIVAL-001: bounded, read-only local inventory and Creator re-entry.

Presence, installed dependencies, verified readiness, and effect authorization are
distinct. This module never runs repository code, installs software, starts a
service, invokes a plugin, or writes a project/source file.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from importlib import resources
from pathlib import Path
from typing import Any

from .config import WorkbenchConfig, load_config
from .creator import creator_desk_status
from .house import build_house_status
from .repos import RepoStatus, discover_repositories

_SCHEMA = "house.arrival/v0.1"
_REENTRY_SCHEMA = "house.creator-reentry/v0.1"


def _canonical(value: Any) -> bytes:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def _sha(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def load_manifest() -> dict[str, Any]:
    """Versioned static inventory; never executable instructions or admission."""
    raw = resources.files("static_workbench").joinpath("ark_manifest.json").read_bytes()
    if len(raw) > 32 * 1024:
        raise ValueError("ARK manifest exceeds 32 KiB")
    manifest = json.loads(raw)
    if (type(manifest) is not dict or manifest.get("version") != "house.ark-manifest/v0.1"
        or type(manifest.get("organs")) is not list):
        raise ValueError("unsupported ARK manifest")
    ids: set[str] = set()
    for organ in manifest["organs"]:
        if (type(organ) is not dict or set(organ) != {"id", "role", "aliases", "optional"}
            or type(organ["id"]) is not str or not organ["id"]
            or organ["id"] in ids or type(organ["role"]) is not str
            or type(organ["aliases"]) is not list or not organ["aliases"]
            or any(type(alias) is not str or not alias for alias in organ["aliases"])
            or type(organ["optional"]) is not bool):
            raise ValueError("invalid or duplicate ARK organ")
        ids.add(organ["id"])
    return manifest


def diagnose(config: WorkbenchConfig, repos: list[RepoStatus] | None = None,
             manifest: dict[str, Any] | None = None) -> dict[str, Any]:
    """Observed local checkouts, not readiness or authorization.

    'repos' injection permits tests without scanning the host. Actual discovery
    reuses the Workbench's bounded root/depth inspection.
    """
    manifest = manifest if manifest is not None else load_manifest()
    repos = repos if repos is not None else discover_repositories(config.roots, config.max_repo_depth)
    by_alias: dict[str, list[RepoStatus]] = {}
    for repo in repos:
        by_alias.setdefault(repo.name.casefold(), []).append(repo)
    organs: list[dict[str, Any]] = []
    for spec in manifest["organs"]:
        matches = [repo for alias in spec["aliases"] for repo in by_alias.get(alias.casefold(), [])]
        # Multiple local checkouts of one organ must not be silently chosen.
        distinct = {(repo.root_id, repo.relative_path): repo for repo in matches}
        locations = [
            {"root_id": repo.root_id, "relative_path": repo.relative_path,
             "head": repo.head, "branch": repo.branch, "dirty": repo.dirty,
             "detached": repo.detached}
            for _, repo in sorted(distinct.items(), key=lambda item: str(item[0]))
        ]
        organs.append({
            "id": spec["id"], "role": spec["role"], "optional": spec["optional"],
            "observed": "not_discovered" if not locations else "checkout_observed",
            "selection": "ambiguous" if len(locations) > 1 else "not_selected",
            "checkouts": locations,
            "installed": "not_evaluated", "compatible": "not_evaluated",
            "ready": "not_evaluated", "authorized": False,
        })
    roots = [
        {"id": root.id, "exists": root.path.is_dir(), "is_symlink": root.path.is_symlink()}
        for root in config.roots
    ]
    return {
        "version": _SCHEMA,
        "manifest_sha256": _sha(_canonical(manifest)),
        "roots": roots,
        "repo_count": len(repos),
        "organs": organs,
        "creator_workflows": creator_desk_status(repos)["workflows"],
        "workbench_house_summary": build_house_status(repos)["summary"],
        "next_step": "Select a source in Creator Desk; no external project action was run.",
        "laws": ["present != ready", "compatible != admitted",
                 "local digest != remote authorship", "read-only diagnosis != permission"],
    }


def creator_reentry(state_dir: Path, draft_id: int) -> dict[str, Any]:
    """Verify a saved Creator pack/draft identity without mutating its SQLite shelf.

    This supplies a pointer into the existing Creator Desk, not a new memory
    authority. Stored local-worktree excerpts are not freshly authenticated.
    """
    if type(draft_id) is not int or draft_id <= 0:
        raise ValueError("draft_id must be a positive integer")
    db_path = Path(state_dir) / "creator.sqlite3"
    if db_path.is_symlink() or not db_path.is_file():
        raise ValueError("Creator shelf is missing or symlinked")
    # SQLite read-only URI prevents accidental creation and migration.
    with sqlite3.connect(db_path.resolve(strict=True).as_uri() + "?mode=ro", uri=True) as db:
        db.row_factory = sqlite3.Row
        row = db.execute(
            """SELECT d.id,d.pack_id,r.revision,r.payload_json,r.content_sha256,
                      p.digest AS pack_digest,p.payload_json AS pack_json
               FROM creator_drafts d JOIN creator_revisions r ON r.draft_id=d.id
               JOIN creator_packs p ON p.id=d.pack_id
               WHERE d.id=? ORDER BY r.revision DESC LIMIT 1""", (draft_id,)
        ).fetchone()
    if row is None:
        raise ValueError("saved Creator draft or source pack is missing")
    pack = json.loads(row["pack_json"])
    draft = json.loads(row["payload_json"])
    if (pack.get("pack_sha256") != row["pack_digest"]
        or type(pack.get("sources")) is not list
        or _sha(_canonical(pack["sources"])) != row["pack_digest"]
        or draft.get("pack_id") != row["pack_id"]
        or type(draft.get("body")) is not str
        or _sha(draft["body"].encode("utf-8")) != row["content_sha256"]):
        raise ValueError("saved Creator draft/source identity mismatch")
    return {
        "version": _REENTRY_SCHEMA, "status": "local_saved_state_verified",
        "draft_id": row["id"], "revision": row["revision"],
        "pack_id": row["pack_id"], "pack_sha256": row["pack_digest"],
        "body_sha256": row["content_sha256"], "title": draft.get("title", ""),
        "kind": draft.get("kind", ""), "selected_source_count": len(pack["sources"]),
        "resume_in": "Creator Desk", "source_current": "not_checked",
        "external_handoff": "not_attempted", "execution_authority": "none",
        "notice": "Only saved local shelf bytes were checked; source trees may have changed.",
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Read-only ARK/ARRIVAL check")
    parser.add_argument("--config", type=Path, help="Workbench TOML config")
    parser.add_argument("--draft-id", type=int, help="inspect one existing Creator Desk draft")
    args = parser.parse_args(argv)
    config = load_config(args.config)
    report = diagnose(config)
    if args.draft_id is not None:
        report["reentry"] = creator_reentry(config.state_dir, args.draft_id)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
