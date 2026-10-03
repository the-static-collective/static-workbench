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
    phonograph: dict | None = None,
    dogram: dict | None = None,
    listener_dogram: dict | None = None,
) -> dict:
    """Return a deterministic, read-only station field.

    The order is lane coverage, not ranking:
    current radio work -> live body -> present moment -> House -> silence.
    """
    witnesses = list(house_state.get("external_witnesses") or [])
    repo_names = _repo_names(repos)

    audio_window = _latest(witnesses, "audio_window:")
    current_window_id = (
        audio_window.get("snapshot", {}).get("window_id")
        if audio_window is not None
        else None
    )
    audio_pair = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith("audio_look_twice_pair:")
            and witness.get("snapshot", {}).get("window_id") == current_window_id
        ),
        None,
    )
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
    phonograph = phonograph or {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }
    dogram = dogram or {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }
    listener_dogram = listener_dogram or {
        "checkout_present": False,
        "available": False,
        "repo_head": None,
        "repo_branch": None,
        "capability": None,
    }
    phono_answer = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith("phonograph_field_answer:")
            and witness.get("snapshot", {}).get("window_id") == current_window_id
        ),
        None,
    )
    current_snapshot = (
        audio_window.get("snapshot", {})
        if audio_window is not None
        else {}
    )
    current_lineage = current_snapshot.get("source_lineage")
    current_is_phono_descendant = (
        isinstance(current_lineage, dict)
        and current_lineage.get("schema")
            == "workbench.phonograph-reentry-lineage/v0"
    )
    parent_window_id = (
        current_lineage.get("parent_window_id")
        if current_is_phono_descendant
        else None
    )
    parent_dialogue = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith(
                "audio_look_twice_dialogue:"
            )
            and witness.get("snapshot", {}).get("window_id")
                == parent_window_id
        ),
        None,
    )
    parent_pair = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith(
                "audio_look_twice_pair:"
            )
            and witness.get("snapshot", {}).get("window_id")
                == parent_window_id
        ),
        None,
    )
    parent_pair_id = (
        parent_pair.get("snapshot", {}).get("pair_id")
        if parent_pair is not None
        else None
    )
    parent_firsts = [
        witness
        for witness in witnesses
        if str(witness.get("kind", "")).startswith(
            "audio_look_twice_first:"
        )
        and witness.get("snapshot", {}).get("pair_id") == parent_pair_id
    ]
    dogram_delta = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith(
                "dogram_generation_delta:"
            )
            and witness.get("snapshot", {}).get("child_window_id")
                == current_window_id
        ),
        None,
    )
    dogram_listener_delta = next(
        (
            witness
            for witness in witnesses
            if str(witness.get("kind", "")).startswith(
                "dogram_listener_delta:"
            )
            and witness.get("snapshot", {}).get("child_window_id")
                == current_window_id
        ),
        None,
    )

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

    # PHONOGRAPH LANE — only a proven local FIELD ANSWER executable earns a door.
    if audio_window is not None and phonograph.get("available") is True:
        window_snapshot = audio_window.get("snapshot", {})
        source_lineage = window_snapshot.get("source_lineage")
        phono_descendant = (
            isinstance(source_lineage, dict)
            and source_lineage.get("schema")
                == "workbench.phonograph-reentry-lineage/v0"
        )
        recursion_unlocked = (not phono_descendant) or audio_dialogue is not None
        if phono_answer is None and recursion_unlocked:
            doors.append(_door(
                "ask-phonograph-answer",
                "Ask Haunted Phonograph to answer this window",
                "FIELD ANSWER 001 is present locally and can turn bounded PCM facts into one receipted musical proposal.",
                lane="phono",
                adapter="Haunted Phonograph / FIELD ANSWER 001",
                evidence=[
                    {
                        "kind": "audio-window",
                        "ref": window_snapshot.get("window_id"),
                        "audio_sha256": window_snapshot.get("audio_sha256"),
                    },
                    {
                        "kind": "capability",
                        "ref": "field-answer-001",
                        "repo_head": phonograph.get("repo_head"),
                        "repo_branch": phonograph.get("repo_branch"),
                    },
                ],
                target={
                    "receipt_id": audio_window.get("receipt_id"),
                    "window_id": window_snapshot.get("window_id"),
                    "control": "phonograph-field-answer",
                },
            ))
        elif phono_answer is not None:
            answer = phono_answer.get("snapshot", {})
            doors.append(_door(
                "audition-phonograph-answer",
                "Audition Haunted Phonograph's musical proposal",
                "A receipted proposal already answers the current exact audio window. Playback remains audition, not admission.",
                lane="phono",
                adapter="Haunted Phonograph / FIELD ANSWER 001",
                evidence=[
                    {
                        "kind": "phonograph-field-answer",
                        "ref": answer.get("proposal_receipt_hash"),
                        "window_id": answer.get("window_id"),
                        "proposal_hash": answer.get("proposal_hash"),
                        "audition_sha256": answer.get("audition", {}).get("sha256"),
                    }
                ],
                target={
                    "receipt_id": phono_answer.get("receipt_id"),
                    "window_id": answer.get("window_id"),
                    "artifact": "audition.wav",
                },
            ))

        elif phono_descendant and not recursion_unlocked:
            # Deliberately no Phonograph door. A Phonograph-derived descendant
            # must acquire a fresh sealed radio cross-read before another
            # musical answer may be requested.
            pass

    # DOGRAM LANE — signal first, then sealed response transform.
    if (
        current_is_phono_descendant
        and parent_dialogue is not None
        and audio_dialogue is not None
    ):
        reentry = next(
            (
                witness
                for witness in witnesses
                if str(witness.get("kind", "")).startswith(
                    "phonograph_reentry:"
                )
                and witness.get("snapshot", {}).get("child_window_id")
                    == current_window_id
            ),
            None,
        )
        if (
            reentry is not None
            and dogram_delta is None
            and dogram.get("available") is True
        ):
            rw = reentry.get("snapshot", {})
            doors.append(_door(
                "measure-generation-delta",
                "Measure what changed from parent to descendant",
                "Both generations have sealed radio cross-reads, and Dogram GENERATION-DELTA-001 can measure the admitted PCM transform without grading it.",
                lane="dogram",
                adapter="Dogram / GENERATION-DELTA-001",
                evidence=[
                    {
                        "kind": "phonograph-reentry",
                        "ref": current_window_id,
                        "parent_window_id": parent_window_id,
                        "proposal_receipt_hash": rw.get(
                            "proposal_receipt_hash"
                        ),
                    },
                    {
                        "kind": "parent-dialogue",
                        "ref": parent_dialogue.get(
                            "snapshot", {}
                        ).get("dialogue_id"),
                    },
                    {
                        "kind": "child-dialogue",
                        "ref": audio_dialogue.get(
                            "snapshot", {}
                        ).get("dialogue_id"),
                    },
                    {
                        "kind": "capability",
                        "ref": "generation-delta-001",
                        "repo_head": dogram.get("repo_head"),
                        "repo_branch": dogram.get("repo_branch"),
                    },
                ],
                target={
                    "receipt_id": audio_window.get("receipt_id"),
                    "parent_window_id": parent_window_id,
                    "child_window_id": current_window_id,
                    "control": "dogram-generation-delta",
                },
            ))
        elif (
            reentry is not None
            and dogram_delta is not None
            and dogram_listener_delta is None
            and listener_dogram.get("available") is True
            and len(parent_firsts) == 2
            and len(audio_firsts) == 2
        ):
            gd = dogram_delta.get("snapshot", {})
            doors.append(_door(
                "measure-listener-delta",
                "Measure how the sealed first responses changed",
                "The signal transform is receipted and both generations retain exactly two sealed first listens. Dogram LISTENER-DELTA-001 can measure response structure without scoring listeners or claiming causation.",
                lane="dogram",
                adapter="Dogram / LISTENER-DELTA-001",
                evidence=[
                    {
                        "kind": "dogram-generation-delta",
                        "ref": gd.get("dogram_receipt_hash"),
                        "classification": gd.get("classification"),
                    },
                    {
                        "kind": "parent-first-listens",
                        "refs": sorted(
                            item.get("snapshot", {}).get("first_response_id")
                            for item in parent_firsts
                        ),
                    },
                    {
                        "kind": "child-first-listens",
                        "refs": sorted(
                            item.get("snapshot", {}).get("first_response_id")
                            for item in audio_firsts
                        ),
                    },
                    {
                        "kind": "capability",
                        "ref": "listener-delta-001",
                        "repo_head": listener_dogram.get("repo_head"),
                        "repo_branch": listener_dogram.get("repo_branch"),
                    },
                ],
                target={
                    "receipt_id": audio_window.get("receipt_id"),
                    "parent_window_id": parent_window_id,
                    "child_window_id": current_window_id,
                    "generation_delta_receipt_hash": gd.get(
                        "dogram_receipt_hash"
                    ),
                    "control": "dogram-listener-delta",
                },
            ))
        elif dogram_listener_delta is not None:
            ld = dogram_listener_delta.get("snapshot", {})
            doors.append(_door(
                "inspect-listener-delta",
                "Inspect the measured listener-response delta",
                "Dogram has receipted the sealed first-response transform. The receipt measures response structure, not people, preference, or causal effect.",
                lane="dogram",
                adapter="Dogram / LISTENER-DELTA-001",
                evidence=[
                    {
                        "kind": "dogram-listener-delta",
                        "ref": ld.get("dogram_receipt_hash"),
                        "classification": ld.get("classification"),
                        "changed_listener_count": ld.get(
                            "changed_listener_count"
                        ),
                        "listener_count": ld.get("listener_count"),
                        "shared_changed_axes": ld.get(
                            "shared_changed_axes"
                        ),
                    }
                ],
                target={
                    "receipt_id": dogram_listener_delta.get("receipt_id"),
                    "child_window_id": current_window_id,
                    "artifact": "listener-delta.json",
                },
            ))
        elif dogram_delta is not None:
            dw = dogram_delta.get("snapshot", {})
            doors.append(_door(
                "inspect-generation-delta",
                "Inspect the measured generation delta",
                "The signal transform is receipted. LISTENER-DELTA-001 is not currently available, so the Field retains the existing signal measurement door.",
                lane="dogram",
                adapter="Dogram / GENERATION-DELTA-001",
                evidence=[
                    {
                        "kind": "dogram-generation-delta",
                        "ref": dw.get("dogram_receipt_hash"),
                        "classification": dw.get("classification"),
                        "changed_axes": dw.get("changed_axes"),
                    }
                ],
                target={
                    "receipt_id": dogram_delta.get("receipt_id"),
                    "child_window_id": current_window_id,
                    "artifact": "generation-delta.json",
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

    # Keep at most six doors while preserving constitutional silence.
    # This is deterministic lane coverage, not a relevance score.
    silence = next(
        (door for door in doors if door.get("lane") == "silence"),
        None,
    )
    non_silence = [
        door for door in doors if door.get("lane") != "silence"
    ][:5]
    doors = non_silence + ([silence] if silence is not None else [])

    counts = {
        "audio_windows": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("audio_window:")
        ),
        "broadcast_episodes": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("broadcast_episode:")
        ),
        "phonograph_answers": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("phonograph_field_answer:")
        ),
        "phonograph_reentries": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith("phonograph_reentry:")
        ),
        "dogram_generation_deltas": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith(
                "dogram_generation_delta:"
            )
        ),
        "dogram_listener_deltas": sum(
            1 for item in witnesses
            if str(item.get("kind", "")).startswith(
                "dogram_listener_delta:"
            )
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
        "phonograph_capability": {
            "checkout_present": phonograph.get("checkout_present"),
            "available": phonograph.get("available"),
            "repo_head": phonograph.get("repo_head"),
            "repo_branch": phonograph.get("repo_branch"),
            "capability": phonograph.get("capability"),
        },
        "dogram_capability": {
            "checkout_present": dogram.get("checkout_present"),
            "available": dogram.get("available"),
            "repo_head": dogram.get("repo_head"),
            "repo_branch": dogram.get("repo_branch"),
            "capability": dogram.get("capability"),
        },
        "listener_dogram_capability": {
            "checkout_present": listener_dogram.get("checkout_present"),
            "available": listener_dogram.get("available"),
            "repo_head": listener_dogram.get("repo_head"),
            "repo_branch": listener_dogram.get("repo_branch"),
            "capability": listener_dogram.get("capability"),
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
            "REPOSITORY PRESENT != CAPABILITY AVAILABLE",
            "MUSICAL POSSIBILITY != RECOMMENDATION",
            "RECURSION REQUIRES FRESH WITNESS",
            "DESCENDANT != PARENT",
            "DOGRAM MEASURES TRANSFORMS, NOT PEOPLE",
            "DELTA != VALUE",
            "SIGNAL DELTA != LISTENER DELTA",
            "RESPONSE DELTA != PERSON DELTA",
            "RESPONSE DELTA != CAUSAL EFFECT",
            "LEXICAL OVERLAP != SEMANTIC AGREEMENT",
            "RESIDUAL != FAILURE",
        ],
    }
    return {
        **state_body,
        "field_state_id": "field-station-v0:" + _digest(state_body),
    }
