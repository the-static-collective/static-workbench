from __future__ import annotations

from typing import Any


LAWS = [
    "GAME STATE != CLAIMED REALITY",
    "QUEST READY != AUTHORIZED",
    "XP == WITNESS COUNT, NOT CAPABILITY",
    "OBSERVATION != EXECUTION",
    "HUMAN GATE != AGENT DECISION",
]


def _quest(
    quest_id: str,
    title: str,
    *,
    status: str,
    target_view: str | None,
    description: str,
    evidence: list[str],
    authority: str = "local-observation",
) -> dict[str, Any]:
    return {
        "id": quest_id,
        "title": title,
        "status": status,
        "target_view": target_view,
        "description": description,
        "evidence": evidence,
        "authority": authority,
    }


def build_ghot_status(
    house: dict[str, Any],
    roadkit: dict[str, Any],
    witness_events: list[Any],
) -> dict[str, Any]:
    summary = house["summary"]
    road_summary = roadkit.get("summary") or {}
    repos = int(summary.get("repos", 0))
    organs = int(summary.get("core_organs_present", 0))
    organs_total = int(summary.get("core_organs_total", 0))
    foreign_holds = int(road_summary.get("foreign_holds", 0))
    local_admits = int(road_summary.get("admits", 0))

    road_configured = bool(roadkit.get("configured"))
    road_present = bool(roadkit.get("present"))
    road_status = "ready" if road_present else ("held" if road_configured else "locked")

    quests = [
        _quest(
            "inspect-house",
            "Inventory the Body",
            status="ready" if repos else "locked",
            target_view="house",
            description="Inspect discovered organs, repositories and local worktree state.",
            evidence=[f"{repos} repositories visible", f"{organs}/{organs_total} core organs present"],
        ),
        _quest(
            "branch-deck",
            "Survey the Branch Wilds",
            status="ready" if repos else "locked",
            target_view="branches",
            description="Inspect branch topology without treating branch age as authority.",
            evidence=[f"{repos} repositories available for bounded local inspection"],
        ),
        _quest(
            "creator-craft",
            "Craft from Attributable Sources",
            status="ready" if repos else "locked",
            target_view="creator",
            description="Carry exact local provenance into a bounded creative draft.",
            evidence=[f"{repos} repositories visible as possible source carriers"],
        ),
        _quest(
            "road-threshold",
            "Crossings at the Threshold",
            status=road_status,
            target_view="roadkit",
            description="Observe foreign HOLDs and local ADMIT receipts without silently accepting anything.",
            evidence=[
                f"{foreign_holds} foreign HOLD receipts",
                f"{local_admits} local ADMIT receipts",
                str(roadkit.get("verification", "not_evaluated")),
            ],
        ),
        _quest(
            "return-desk",
            "Leave a Checkpoint",
            status="ready",
            target_view="return",
            description="Write a Workbench-owned local note or resumable checkpoint.",
            evidence=["Return Desk is a local explicit-write surface"],
            authority="human-session",
        ),
        _quest(
            "public-door",
            "The Public Door",
            status="human_gate",
            target_view="rocket",
            description="Stage consequential work, but keep irreversible/public movement behind an explicit human gate.",
            evidence=["Staged Rocket requires deliberate local-session actions"],
            authority="human-decision",
        ),
        _quest(
            "staticjack-polsia",
            "STATICJACK-001 · Polsia in a Jar",
            status="held",
            target_view=None,
            description="Foreign-system specimen quest. No Polsia credentials or authority are wired into Workbench.",
            evidence=["experiment conceived", "external authority intentionally absent"],
            authority="none",
        ),
    ]

    party = [
        {"id": "scout", "label": "Scout", "state": "ready" if repos else "waiting"},
        {"id": "builder", "label": "Builder", "state": "ready" if organs else "waiting"},
        {"id": "composer", "label": "Composer", "state": "ready" if repos else "waiting"},
        {"id": "witness", "label": "Witness", "state": "recording"},
        {
            "id": "roadkeeper",
            "label": "Roadkeeper",
            "state": "ready" if road_present else ("held" if road_configured else "unconfigured"),
        },
    ]

    return {
        "schema": "static-workbench.ghot-shell/v0",
        "title": "GHoT · Giant Heap of Things",
        "mode": "idle-operator-projection",
        "resources": {
            "visible_repos": repos,
            "core_organs_present": organs,
            "core_organs_total": organs_total,
            "dirty_trees": int(summary.get("dirty", 0)),
            "diverged_trees": int(summary.get("diverged", 0)),
            "detached_trees": int(summary.get("detached", 0)),
            "foreign_holds": foreign_holds,
            "local_admits": local_admits,
            "witness_xp": len(witness_events),
        },
        "party": party,
        "quests": quests,
        "laws": LAWS,
        "idle_tick": {
            "effect": "observation-only",
            "description": "Refresh local House, repository, road and witness projections. No project command is executed.",
        },
    }
