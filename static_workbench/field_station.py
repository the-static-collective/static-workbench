"""FIELD-STATION-001: read-only composition of nearby, attributable station doors.

The field station does not select, execute, score, or persist proposals. It composes
a small set of currently reachable possibilities from already-witnessed House,
radio, live-moment, repository, and Static Live state.
"""
from __future__ import annotations

import hashlib
import json
from typing import Any

from .repos import RepoStatus


def _canonical(value: Any) -> str:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    )


def _digest(value: Any) -> str:
    return hashlib.sha256(_canonical(value).encode("utf-8")).hexdigest()


def _latest(witnesses: list[dict], prefix: str) -> dict | None:
    for witness in witnesses:
        if str(witness.get("kind", "")).startswith(prefix):
            return witness
    return None


def _latest_for_pair(
    witnesses: list[dict],
    prefix: str,
    pair_id: str | None,
) -> dict | None:
    if pair_id is None:
        return None
    for witness in witnesses:
        if (
            str(witness.get("kind", "")).startswith(prefix)
            and witness.get("snapshot", {}).get("pair_id") == pair_id
        ):
            return witness
    return None


def _door(
    kind: str,
    label: str,
    why: str,
    *,
    lane: str,
    adapter: str,
    evidence: list[dict],
    target: dict | None = None,
) -> dict:
    body = {
        "schema": "workbench.field-station-door/v0",
        "kind": kind,
        "label": label,
        "why": why,
        "lane": lane,
        "adapter": adapter,
        "evidence": evidence,
        "target": target,
        "effect": "none",
        "laws": [
            "RECOMMENDATION != SELECTION",
            "DOOR != CROSSING",
            "AVAILABILITY != OBLIGATION",
        ],
    }
    return {
        **body,
        "door_id": "field-door-v0:" + _digest(body),
    }


def _repo_names(repos: list[RepoStatus]) -> set[str]:
    return {repo.name.casefold() for repo in repos}


def compose_nearby_station_doors(
    house_state: dict,
    broadcast: dict,
    moments: list[dict],
    repos: list[RepoStatus],
) -> dict:
    """Return a deterministic, read-only station field.

    The order is lane coverage, not ranking:
    current radio work -> live body -> present moment -> House -> silence.
    """
    witnesses = list(house_state.get("external_witnesses") or [])
    repo_names = _repo_names(repos)

    audio_window = _latest(witnesses, "audio_window:")
    audio_pair = _latest(witnesses, "audio_look_twice_pair:")
    pair_id = (
        audio_pair.get("snapshot", {}).get("pair_id")
        if audio_pair is not None
        else None
    )
    audio_firsts = [
        witness
        for witness in witnesses
        if str(witness.get("kind", "")).startswith("audio_look_twice_first:")
        and witness.get("snapshot", {}).get("pair_id") == pair_id
    ]
    audio_dialogue = _latest_for_pair(
        witnesses,
        "audio_look_twice_dialogue:",
        pair_id,
    )
    episode = _latest(witnesses, "broadcast_episode:")

    doors: list[dict] = []

    # RADIO WORKFLOW LANE — one currently earned next aperture only.
    if audio_window is None:
        doors.append(_door(
            "cut-audio-window",
            "Cut one bounded audio window",
            "No AUDIO WINDOW witness exists yet, so first-listen radio has no current specimen.",
            lane="radio",
            adapter="Autodisco / AUDIO WINDOW",
            evidence=[{
                "kind": "absence",
                "ref": "audio_window",
                "claim": "no audio_window witness in current House state",
            }],
            target={"surface": "doorhouse", "control": "audio-window"},
        ))
    elif audio_pair is None:
        snapshot = audio_window.get("snapshot", {})
        doors.append(_door(
            "prepare-first-listen-booths",
            "Prepare two isolated first-listen booths",
            "A bounded audio specimen exists, but no audio LOOK TWICE pair has been prepared.",
            lane="radio",
            adapter="Autodisco / Audio LOOK TWICE",
            evidence=[{
                "kind": "audio-window",
                "ref": snapshot.get("window_id"),
                "audio_sha256": snapshot.get("audio_sha256"),
            }],
            target={"window_id": snapshot.get("window_id")},
        ))
    elif len(audio_firsts) < 2:
        pair = audio_pair.get("snapshot", {})
        doors.append(_door(
            "acquire-first-listens",
            "Invite both fresh listeners independently",
            f"The current audio pair has {len(audio_firsts)}/2 sealed first listens.",
            lane="radio",
            adapter="Autodisco / Audio LOOK TWICE",
            evidence=[{
                "kind": "audio-pair",
                "ref": pair_id,
                "sealed_first_listens": len(audio_firsts),
            }],
            target={"pair_id": pair_id},
        ))
    elif audio_dialogue is None:
        doors.append(_door(
            "cross-read-first-listens",
            "Let the two sealed first listens compare notes",
            "Exactly two first listens exist for the current pair, and no sealed cross-read exists yet.",
            lane="radio",
            adapter="Autodisco / Audio LOOK TWICE",
            evidence=[
                {
                    "kind": "audio-pair",
                    "ref": pair_id,
                },
                {
                    "kind": "first-listens",
                    "refs": sorted(
                        item.get("snapshot", {}).get("first_response_id")
                        for item in audio_firsts
                    ),
                },
            ],
            target={"pair_id": pair_id},
        ))
    elif episode is None or episode.get("snapshot", {}).get("pair_id") != pair_id:
        dialogue = audio_dialogue.get("snapshot", {})
        doors.append(_door(
            "assemble-radio-episode",
            "Assemble the current evidence into a playable radio episode",
            "The current pair has two sealed first listens and a sealed dialogue, but no episode witness for this pair.",
            lane="radio",
            adapter="Autodisco / BROADCAST ASSEMBLY",
            evidence=[{
                "kind": "audio-dialogue",
                "ref": dialogue.get("dialogue_id"),
                "pair_id": pair_id,
            }],
            target={"pair_id": pair_id},
        ))
    else:
        ep = episode.get("snapshot", {})
        doors.append(_door(
            "play-current-episode",
            "Play the assembled episode",
            "A verified portable episode exists for the current audio pair.",
            lane="radio",
            adapter="Autodisco / local episode player",
            evidence=[{
                "kind": "broadcast-episode",
                "ref": ep.get("episode_id"),
                "episode_digest": ep.get("episode_digest"),
            }],
            target={
                "receipt_id": ep.get("local_receipt_id"),
                "episode_id": ep.get("episode_id"),
            },
        ))

    # STATIC LIVE LANE — presence/reachability is factual, never inferred.
    static_live_present = "static-live" in repo_names
    if episode is not None and static_live_present:
        ep = episode.get("snapshot", {})
        connection = broadcast.get("connection")
        why = (
            "Static Live is reachable and a verified episode artifact is available."
            if connection == "reachable"
            else "A Static Live checkout and verified episode artifact exist; the broadcast service is not currently reachable."
        )
        doors.append(_door(
            "offer-episode-to-static-live",
            "Offer the episode to Static Live",
            why,
            lane="live",
            adapter="Static Live / Broadcast",
            evidence=[
                {
                    "kind": "broadcast-episode",
                    "ref": ep.get("episode_id"),
                    "episode_digest": ep.get("episode_digest"),
                },
                {
                    "kind": "broadcast-body",
                    "connection": connection,
                    "state": broadcast.get("broadcast_state"),
                    "recording": broadcast.get("recording"),
                    "stream": broadcast.get("stream"),
                },
            ],
            target={
                "episode_id": ep.get("episode_id"),
                "static_live_connection": connection,
            },
        ))
    elif broadcast.get("connection") == "reachable":
        doors.append(_door(
            "inspect-static-live",
            "Look into the live room",
            "Static Live reports a reachable local broadcast body even though no current assembled episode is available to offer it.",
            lane="live",
            adapter="Static Live / Broadcast",
            evidence=[{
                "kind": "broadcast-body",
                "event": broadcast.get("event"),
                "state": broadcast.get("broadcast_state"),
                "recording": broadcast.get("recording"),
                "stream": broadcast.get("stream"),
            }],
            target={"surface": "static-live"},
        ))

    # PRESENT OCCURRENCE LANE.
    if moments:
        moment = moments[0]
        doors.append(_door(
            "inspect-live-moment",
            "Open the newest preserved live moment",
            "Lifestream has a registered moment available as present-tense source material.",
            lane="present",
            adapter="Lifestream / Moment Inbox",
            evidence=[{
                "kind": "lifestream-moment",
                "ref": moment.get("momentId"),
                "event_id": moment.get("eventId"),
                "span": moment.get("span"),
                "status": moment.get("status"),
            }],
            target={"moment_id": moment.get("momentId")},
        ))

    # HOUSE LANE — only already-open, uncrossed proposals are considered nearby.
    letters_by_id = {
        item.get("id"): item
        for item in house_state.get("letters", [])
    }
    unresolved = []
    for door in house_state.get("doors", []):
        if door.get("crossed_at") is not None:
            continue
        letter = letters_by_id.get(door.get("letter_id"))
        if not letter or letter.get("opened_at") is None:
            continue
        unresolved.append(door)
    if unresolved:
        door = unresolved[0]
        doors.append(_door(
            "revisit-house-door",
            "Revisit an already-open House door",
            "An earlier opened letter still has an uncrossed proposal. The Field Station may surface it but cannot select it.",
            lane="house",
            adapter=door.get("adapter_hint") or "House",
            evidence=[{
                "kind": "house-door",
                "ref": door.get("id"),
                "label": door.get("label"),
                "letter_id": door.get("letter_id"),
            }],
            target={"door_id": door.get("id")},
        ))

    # SILENCE LANE is always lawful and intentionally carries no execution target.
    doors.append(_door(
        "hold-silence",
        "Hold silence",
        "Nothing in the field is obligated to cross merely because it is available.",
        lane="silence",
        adapter="House / HOLD",
        evidence=[{
            "kind": "constitutional-law",
            "claim": "AVAILABILITY != OBLIGATION",
        }],
        target=None,
    ))

    # Keep one door per lane in deterministic construction order, max six.
    doors = doors[:6]

    counts = {
        "audio_windows": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("audio_window:")
        ),
        "broadcast_episodes": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("broadcast_episode:")
        ),
        "unresolved_house_doors": len(unresolved),
        "registered_live_moments": len(moments),
    }
    pressures = []
    if counts["unresolved_house_doors"]:
        pressures.append({
            "kind": "unresolved-house",
            "value": counts["unresolved_house_doors"],
            "effect": "surface-one-nearby-door",
        })
    if counts["registered_live_moments"]:
        pressures.append({
            "kind": "present-occurrence",
            "value": counts["registered_live_moments"],
            "effect": "surface-newest-moment",
        })
    if counts["broadcast_episodes"] == 0:
        pressures.append({
            "kind": "first-episode-absence",
            "value": 1,
            "effect": "keep-radio-workflow-visible",
        })

    current_episode = (
        episode.get("snapshot")
        if episode is not None
        else None
    )
    present = None
    if broadcast.get("connection") == "reachable":
        present = {
            "kind": "static-live",
            "event": broadcast.get("event"),
            "state": broadcast.get("broadcast_state"),
            "recording": broadcast.get("recording"),
            "stream": broadcast.get("stream"),
            "authority": "static-live",
        }
    elif moments:
        present = {
            "kind": "lifestream-moment",
            "moment_id": moments[0].get("momentId"),
            "event_id": moments[0].get("eventId"),
            "span": moments[0].get("span"),
            "status": moments[0].get("status"),
            "authority": "lifestream",
        }

    state_body = {
        "schema": "workbench.field-station-state/v0",
        "read_only": True,
        "world_version": house_state.get("world_version"),
        "present": present,
        "current_episode": (
            {
                "episode_id": current_episode.get("episode_id"),
                "title": current_episode.get("title"),
                "episode_digest": current_episode.get("episode_digest"),
                "pair_id": current_episode.get("pair_id"),
                "window_id": current_episode.get("window_id"),
            }
            if isinstance(current_episode, dict)
            else None
        ),
        "broadcast_body": {
            "checkout_present": broadcast.get("checkout_present"),
            "configured": broadcast.get("configured"),
            "connection": broadcast.get("connection"),
            "event": broadcast.get("event"),
            "state": broadcast.get("broadcast_state"),
            "recording": broadcast.get("recording"),
            "stream": broadcast.get("stream"),
            "authority": broadcast.get("authority"),
        },
        "counts": counts,
        "memory_pressures": pressures,
        "nearby_doors": doors,
        "laws": [
            "RECOMMENDATION != SELECTION",
            "DOOR != CROSSING",
            "AVAILABILITY != OBLIGATION",
            "MEMORY PRESSURE != AUTHORITY",
            "FIELD STATE != WORLD STATE",
            "READ != OCCURRENCE",
        ],
    }
    return {
        **state_body,
        "field_state_id": "field-station-v0:" + _digest(state_body),
    }
