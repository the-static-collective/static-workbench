"""BRANCH-DECK-002: opt-in public GitHub observation for one selected local repo.

No credentials, git fetch, checkout, project writes, or automatic polling.
Network requests use a fixed HTTPS host and bounded pages/response size.
"""
from __future__ import annotations

import http.client
import json
import re
import ssl
from datetime import datetime, timezone
from pathlib import Path

from .repos import RepoStatus, _git

ORG = "the-static-collective"
_REPO = r"[A-Za-z0-9][A-Za-z0-9._-]{0,99}"
_SHA = re.compile(r"^[0-9a-f]{40}$")
_REMOTE = (
    re.compile(rf"^https://github\.com/({ORG})/({_REPO})(?:\.git)?/?$", re.I),
    re.compile(rf"^git@github\.com:({ORG})/({_REPO})(?:\.git)?$", re.I),
    re.compile(rf"^ssh://git@github\.com/({ORG})/({_REPO})(?:\.git)?/?$", re.I),
)
_MAX_BYTES = 2_000_000
_MAX_PAGES = 2
_PAGE_SIZE = 100


class RemoteDiscoveryError(ValueError):
    pass


def _origin_slug(repo: RepoStatus) -> str:
    result = _git(Path(repo.path), "config", "--get", "remote.origin.url")
    if result.returncode != 0:
        raise RemoteDiscoveryError("origin_unconfigured")
    origin = result.stdout.strip()
    for pattern in _REMOTE:
        match = pattern.fullmatch(origin)
        if match:
            name = match.group(2)
            if name.endswith(".git"):
                name = name[:-4]
            if name not in {".", ".."}:
                return f"{ORG}/{name}"
    raise RemoteDiscoveryError("origin_not_supported_public_collective_github_url")


def _github_json(path: str) -> list:
    """Fixed api.github.com GET with no redirects or authentication."""
    if not (path.startswith(f"/repos/{ORG}/") or path == f"/users/{ORG}/repos?per_page=100&page=1&type=owner&sort=full_name"):
        raise RemoteDiscoveryError("invalid_github_api_path")
    connection = http.client.HTTPSConnection(
        "api.github.com", timeout=6, context=ssl.create_default_context()
    )
    try:
        connection.request("GET", path, headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "static-workbench-branch-deck/002",
            "X-GitHub-Api-Version": "2022-11-28",
        })
        response = connection.getresponse()
        if response.status != 200:
            raise RemoteDiscoveryError(f"github_http_{response.status}")
        data = response.read(_MAX_BYTES + 1)
        if len(data) > _MAX_BYTES:
            raise RemoteDiscoveryError("github_response_too_large")
        try:
            decoded = json.loads(data)
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise RemoteDiscoveryError("invalid_github_response") from exc
        if not isinstance(decoded, list):
            raise RemoteDiscoveryError("unexpected_github_response_shape")
        return decoded
    except (OSError, TimeoutError, http.client.HTTPException) as exc:
        raise RemoteDiscoveryError("github_network_unavailable") from exc
    finally:
        connection.close()


def _paged(path: str) -> tuple[list, bool]:
    all_items: list = []
    for page in range(1, _MAX_PAGES + 1):
        items = _github_json(f"{path}&page={page}")
        if len(items) > _PAGE_SIZE:
            raise RemoteDiscoveryError("github_page_over_limit")
        all_items.extend(items)
        if len(items) < _PAGE_SIZE:
            return all_items, False
    return all_items, True  # A full last page does not prove completeness.


def _pr_index(slug: str) -> tuple[dict[str, list[dict]], bool]:
    items, capped = _paged(f"/repos/{slug}/pulls?state=open&per_page={_PAGE_SIZE}")
    by_name: dict[str, list[dict]] = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        head = item.get("head")
        number = item.get("number")
        if not isinstance(head, dict) or type(number) is not int or number < 1:
            continue
        head_repo = head.get("repo")
        if not isinstance(head_repo, dict) or not isinstance(head_repo.get("full_name"), str) or head_repo["full_name"].lower() != slug.lower():
            continue  # Fork PRs are not origin-branch identity.
        name = head.get("ref")
        sha = head.get("sha")
        if not isinstance(name, str) or not isinstance(sha, str) or not _SHA.fullmatch(sha):
            continue
        by_name.setdefault(name, []).append({
            "number": number, "title": str(item.get("title", ""))[:240],
            "draft": item.get("draft") is True, "head_commit": sha,
            "url": f"https://github.com/{slug}/pull/{number}",
        })
    return by_name, capped


def inspect_github_repo(repo: RepoStatus, local_cards: list[dict]) -> dict:
    slug = _origin_slug(repo)
    branches, capped = _paged(f"/repos/{slug}/branches?per_page={_PAGE_SIZE}")
    pr_gaps: list[str] = []
    prs: dict[str, list[dict]] = {}
    pr_capped = False
    try:
        prs, pr_capped = _pr_index(slug)
    except RemoteDiscoveryError as exc:
        pr_gaps.append(str(exc))
    local = {card["name"]: card for card in local_cards if card["kind"] == "local"}
    cached = {
        card["name"][len("origin/"):]: card
        for card in local_cards
        if card["kind"] == "cached_remote" and card["name"].startswith("origin/")
    }
    seen: set[str] = set()
    cards: list[dict] = []
    for item in branches:
        if not isinstance(item, dict):
            raise RemoteDiscoveryError("invalid_github_branch")
        name, commit = item.get("name"), item.get("commit")
        sha = commit.get("sha") if isinstance(commit, dict) else None
        if not isinstance(name, str) or not name or not isinstance(sha, str) or not _SHA.fullmatch(sha) or name in seen:
            raise RemoteDiscoveryError("invalid_github_branch")
        seen.add(name)
        tracked = local.get(name)
        cache = cached.get(name)
        relation = ("same_local_commit" if tracked and tracked["commit"] == sha else
                    "different_local_commit" if tracked else
                    "same_cached_commit" if cache and cache["commit"] == sha else
                    "different_cached_commit" if cache else "remote_only")
        cards.append({
            "root_id": repo.root_id, "repo_path": repo.relative_path, "repo_name": repo.name,
            "github_repo": slug, "name": name, "ref": f"refs/heads/{name}",
            "kind": "github_remote", "commit": sha, "committed_at": None,
            "checkout": "not_observed_on_remote", "relation": relation,
            "feature_like": name.lower().startswith(("feat/", "feature/", "fix/", "experiment/", "exp/")),
            "readiness": "not_tested", "protected": item.get("protected") is True,
            "open_prs": prs.get(name, []), "pr_scan_complete": not (pr_capped or pr_gaps),
            "url": f"https://github.com/{slug}/tree/{sha}",
        })
    return {
        "source": "github_public_api", "github_repo": slug,
        "observed_at": datetime.now(timezone.utc).isoformat(),
        "branches": cards, "branch_scan_complete": not capped,
        "pr_scan_complete": not (pr_capped or pr_gaps),
        "gaps": (["branch_page_limit_reached"] if capped else []) +
                (["pr_page_limit_reached"] if pr_capped else []) + pr_gaps,
        "read_only": True,
    }
