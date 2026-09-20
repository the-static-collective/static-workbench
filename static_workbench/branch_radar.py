"""BRANCH-DECK-004: opt-in, bounded public Collective branch radar.

The radar is a *rolling observation*, never a claim of complete coverage.
Its SQLite state belongs to Workbench, not any source repository.
"""
from __future__ import annotations

import json
import re
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from .branch_remote import ORG, RemoteDiscoveryError, _github_json, _SHA

_REPO_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,99}$")
BATCH_REPOS = 5
MAX_REPOS = 100
MAX_BRANCHES = 100


def _utc() -> str:
    return datetime.now(timezone.utc).isoformat()


class CollectiveRadar:
    def __init__(self, state_dir: Path):
        self.path = state_dir / "branch-radar.sqlite3"
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS observations (
                  repo TEXT NOT NULL, branch TEXT NOT NULL,
                  sha TEXT NOT NULL, first_seen TEXT NOT NULL,
                  last_seen TEXT NOT NULL, baseline INTEGER NOT NULL,
                  PRIMARY KEY (repo, branch)
                );
                CREATE TABLE IF NOT EXISTS repository_scans (
                  repo TEXT PRIMARY KEY, observed_at TEXT NOT NULL,
                  branch_count INTEGER NOT NULL, complete INTEGER NOT NULL
                );
                CREATE TABLE IF NOT EXISTS meta (
                  key TEXT PRIMARY KEY, value TEXT NOT NULL
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        return db

    def snapshot(self) -> dict:
        with self._connect() as db:
            rows = db.execute("""
                SELECT o.repo, o.branch, o.sha, o.first_seen, o.last_seen,
                       o.baseline, s.observed_at AS repo_scanned_at, s.complete
                FROM observations AS o JOIN repository_scans AS s ON s.repo=o.repo
                ORDER BY o.last_seen DESC, o.repo, o.branch LIMIT 2000
            """).fetchall()
            scans = db.execute("SELECT * FROM repository_scans ORDER BY repo").fetchall()
            meta = dict(db.execute("SELECT key, value FROM meta").fetchall())
            total = db.execute("SELECT count(*) FROM observations").fetchone()[0]
        return {
            "source": "public_github_rolling_snapshot",
            "scope": "public_Collective_owner_first_100_repos_five_per_cycle",
            "updated_at": meta.get("updated_at"),
            "last_error": meta.get("last_error"),
            "last_success_at": meta.get("last_success_at"),
            "repos_observed": len(scans), "repo_limit": MAX_REPOS,
            "repo_count_last_listing": int(meta.get("repo_count", "0")),
            "cursor": int(meta.get("cursor", "0")),
            "all_repositories_observed": bool(scans) and len(scans) >= int(meta.get("repo_count", "0")) and meta.get("repository_list_truncated") != "1",
            "repository_list_truncated": meta.get("repository_list_truncated") == "1",
            "rows_truncated": total > len(rows),
            "branches": [{
                "github_repo": r["repo"], "name": r["branch"], "commit": r["sha"],
                "kind": "github_remote", "feature_like": r["branch"].lower().startswith(
                    ("feat/", "feature/", "fix/", "experiment/", "exp/")),
                "first_seen": r["first_seen"], "last_seen": r["last_seen"],
                "repo_scanned_at": r["repo_scanned_at"], "baseline": bool(r["baseline"]),
                "scan_complete": bool(r["complete"]), "readiness": "not_tested",
                "url": f"https://github.com/{r['repo']}/tree/{r['sha']}",
            } for r in rows],
        }

    def record_error(self, message: str) -> None:
        with self._connect() as db:
            db.execute("INSERT OR REPLACE INTO meta VALUES ('last_error', ?)",
                       (message[:160],))

    def scan_once(self) -> dict:
        """One bounded cycle: one repo-list GET plus at most five branch GETs."""
        try:
            repositories = _github_json(
                f"/users/{ORG}/repos?per_page={MAX_REPOS}&page=1&type=owner&sort=full_name"
            )
            if len(repositories) > MAX_REPOS:
                raise RemoteDiscoveryError("repository_page_over_limit")
            names: list[str] = []
            for item in repositories:
                if not isinstance(item, dict):
                    raise RemoteDiscoveryError("invalid_repository_listing")
                name = item.get("name")
                full_name = item.get("full_name")
                owner = item.get("owner")
                if not isinstance(name, str) or not _REPO_NAME.fullmatch(name):
                    raise RemoteDiscoveryError("invalid_repository_name")
                if not isinstance(full_name, str) or full_name.lower() != f"{ORG}/{name}".lower():
                    raise RemoteDiscoveryError("owner_identity_mismatch")
                if not isinstance(owner, dict) or str(owner.get("login", "")).lower() != ORG:
                    raise RemoteDiscoveryError("owner_identity_mismatch")
                if item.get("fork") is True or item.get("archived") is True:
                    continue
                names.append(f"{ORG}/{name}")
            names = sorted(set(names), key=str.casefold)
            now = _utc()
            with self._connect() as db:
                value = db.execute("SELECT value FROM meta WHERE key='cursor'").fetchone()
                cursor = int(value[0]) if value else 0
            chosen = [names[(cursor + i) % len(names)] for i in range(min(BATCH_REPOS, len(names)))] if names else []
            successes, errors = [], []
            for slug in chosen:
                try:
                    branches = _github_json(
                        f"/repos/{slug}/branches?per_page={MAX_BRANCHES}&page=1"
                    )
                    if len(branches) > MAX_BRANCHES:
                        raise RemoteDiscoveryError("branch_page_over_limit")
                    parsed: list[tuple[str, str]] = []
                    seen: set[str] = set()
                    for item in branches:
                        name = item.get("name") if isinstance(item, dict) else None
                        commit = item.get("commit") if isinstance(item, dict) else None
                        sha = commit.get("sha") if isinstance(commit, dict) else None
                        if not isinstance(name, str) or not name or len(name) > 255 or "\x00" in name or name in seen or not isinstance(sha, str) or not _SHA.fullmatch(sha):
                            raise RemoteDiscoveryError("invalid_branch_payload")
                        seen.add(name)
                        parsed.append((name, sha))
                    # One transaction per repository: failed pages never replace a
                    # previously observed snapshot or mark missing refs as deleted.
                    with self._connect() as db:
                        had_baseline = db.execute(
                            "SELECT 1 FROM repository_scans WHERE repo=?", (slug,)
                        ).fetchone() is not None
                        for name, sha in parsed:
                            existing = db.execute(
                                "SELECT sha, first_seen, baseline FROM observations WHERE repo=? AND branch=?",
                                (slug, name),
                            ).fetchone()
                            if existing is None:
                                db.execute(
                                    "INSERT INTO observations VALUES (?,?,?,?,?,?)",
                                    (slug, name, sha, now, now, int(not had_baseline)),
                                )
                            else:
                                db.execute(
                                    "UPDATE observations SET sha=?, last_seen=? WHERE repo=? AND branch=?",
                                    (sha, now, slug, name),
                                )
                        db.execute("INSERT OR REPLACE INTO repository_scans VALUES (?,?,?,?)",
                                   (slug, now, len(parsed), int(len(parsed) < MAX_BRANCHES)))
                    successes.append(slug)
                except (RemoteDiscoveryError, OSError, ValueError) as exc:
                    errors.append(f"{slug}:{str(exc)[:80]}")
            with self._connect() as db:
                metadata = {
                    "cursor": str((cursor + len(chosen)) % len(names)) if names else "0",
                    "updated_at": now,
                    "repo_count": str(len(names)),
                    "repository_list_truncated": str(int(len(repositories) == MAX_REPOS)),
                    "last_error": "; ".join(errors)[:160],
                    **({"last_success_at": now} if successes else {}),
                }
                for key, value in metadata.items():
                    db.execute("INSERT OR REPLACE INTO meta VALUES (?,?)", (key, value))
            return {"repos_scanned": successes, "errors": errors,
                    "candidate_repos": len(names), "cursor": metadata["cursor"],
                    "repository_list_truncated": len(repositories) == MAX_REPOS}
        except (RemoteDiscoveryError, OSError, ValueError) as exc:
            self.record_error(str(exc))
            return {"repos_scanned": [], "errors": [str(exc)],
                    "candidate_repos": None, "repository_list_truncated": None}
