from __future__ import annotations

from dataclasses import asdict
from typing import Any

from .repos import RepoStatus


CORE_ORGANS: tuple[dict[str, Any], ...] = (
    {
        "id": "toaster",
        "label": "Haunted Toaster",
        "aliases": ("the-haunted-toaster", "haunted-toaster"),
        "role": "media renderer / artifact witness",
    },
    {
        "id": "dogram",
        "label": "Dogram",
        "aliases": ("dogram",),
        "role": "mathematical comparison / delta",
    },
    {
        "id": "alex",
        "label": "ALEX",
        "aliases": ("alex.2", "alex"),
        "role": "provenance-first research substrate",
    },
    {
        "id": "3rdi",
        "label": "3rdi",
        "aliases": ("3rdi",),
        "role": "observer-local projection",
    },
    {
        "id": "loadout",
        "label": "LOADOUT",
        "aliases": ("loadout",),
        "role": "bounded capability / handoff compilation",
    },
    {
        "id": "static-live",
        "label": "Static Live",
        "aliases": ("static-live",),
        "role": "performance + local broadcast surface",
    },
    {
        "id": "band-runtime",
        "label": "Band Runtime",
        "aliases": ("band-runtime",),
        "role": "shared event / hold / replay runtime",
    },
    {
        "id": "garden",
        "label": "Garden / NanaSpork",
        "aliases": ("bananaspork", "nanaspork", "garden"),
        "role": "human-facing help / campfire desk",
    },
    {
        "id": "jubilee",
        "label": "Jubilee Engine / Book of Acts",
        "aliases": ("jubilee-engine-vm", "jubilee-engine"),
        "role": "act-first durable memory / receipts",
    },
    {
        "id": "full-measure",
        "label": "Full Measure",
        "aliases": ("full-measure-world-layer", "full-measure"),
        "role": "inhabitable participation / world layer",
    },
)


def _find_repo(repos: list[RepoStatus], aliases: tuple[str, ...]) -> RepoStatus | None:
    normalized = {alias.lower() for alias in aliases}
    for repo in repos:
        if repo.name.lower() in normalized:
            return repo
    return None


def build_house_status(repos: list[RepoStatus]) -> dict[str, Any]:
    organs: list[dict[str, Any]] = []
    for spec in CORE_ORGANS:
        repo = _find_repo(repos, spec["aliases"])
        organ = {
            "id": spec["id"],
            "label": spec["label"],
            "role": spec["role"],
            "present": repo is not None,
            "repo": None if repo is None else asdict(repo),
        }
        organs.append(organ)

    dirty = sum(1 for repo in repos if repo.dirty)
    diverged = sum(1 for repo in repos if (repo.ahead or 0) > 0 or (repo.behind or 0) > 0)
    detached = sum(1 for repo in repos if repo.detached)
    present_organs = sum(1 for organ in organs if organ["present"])

    return {
        "summary": {
            "repos": len(repos),
            "dirty": dirty,
            "diverged": diverged,
            "detached": detached,
            "core_organs_present": present_organs,
            "core_organs_total": len(organs),
        },
        "organs": organs,
        "laws": [
            "present != ready",
            "ready != authorized",
            "compatible != admitted",
            "workbench receipt != project receipt",
        ],
    }
