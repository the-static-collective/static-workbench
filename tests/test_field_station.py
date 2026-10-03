from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.field_station import compose_nearby_station_doors
from static_workbench.repos import RepoStatus


def repo(name: str) -> RepoStatus:
    return RepoStatus(
        name=name,
        path=f"/tmp/{name}",
        branch="main",
        detached=False,
        head="abc123",
        dirty=False,
        ahead=0,
        behind=0,
    )


def empty_house():
    return {
        "entered": True,
        "world_version": 0,
        "letters": [],
        "doors": [],
        "receipts": [],
        "external_witnesses": [],
        "laws": [],
    }


def broadcast(connection="unconfigured", present=True):
    return {
        "checkout_present": present,
        "configured": connection != "unconfigured",
        "connection": connection,
        "open_url": "http://127.0.0.1:3008/" if connection == "reachable" else None,
        "event": {"id": "event-1", "title": "Static Radio"} if connection == "reachable" else None,
        "broadcast_state": "ready" if connection == "reachable" else None,
        "recording": False if connection == "reachable" else None,
        "stream": False if connection == "reachable" else None,
        "authority": "static-live",
    }


def witness(kind, snapshot, row=1):
    return {
        "id": f"w{row}",
        "receipt_id": "receipt-1",
        "kind": kind,
        "result_sha256": str(row) * 64,
        "snapshot": snapshot,
        "created_at": f"2026-10-03T0{row}:00:00+00:00",
    }


def mature_house():
    pair_id = "autodisco-audio-look-twice-pair-v0:" + "2" * 64
    window_id = "autodisco-audio-window-v0:" + "1" * 64
    episode_id = "first-signal-deadbeefcafe"
    return {
        "entered": True,
        "world_version": 4,
        "letters": [
            {
                "id": "letter-open",
                "opened_at": "2026-10-03T01:00:00+00:00",
                "title": "Earlier possibility",
            }
        ],
        "doors": [
            {
                "id": "door-old",
                "letter_id": "letter-open",
                "label": "Old open door",
                "adapter_hint": "Dogram",
                "crossed_at": None,
            }
        ],
        "receipts": [],
        "external_witnesses": [
            witness(
                "broadcast_episode:" + episode_id,
                {
                    "schema": "workbench.broadcast-episode-materialized/v0",
                    "local_receipt_id": "receipt-1",
                    "episode_id": episode_id,
                    "title": "First Signal · window-001",
                    "episode_digest": "d" * 64,
                    "pair_id": pair_id,
                    "window_id": window_id,
                    "audio_sha256": "a" * 64,
                },
                9,
            ),
            witness(
                "audio_look_twice_dialogue:" + pair_id,
                {
                    "schema": "workbench.audio-look-twice-dialogue/v0",
                    "pair_id": pair_id,
                    "window_id": window_id,
                    "dialogue_id": "dialogue-1",
                    "dialogue": {
                        "lingering_intrigue": True,
                        "door_seed": "Move the window.",
                    },
                },
                8,
            ),
            witness(
                "audio_look_twice_first:" + pair_id + ":juniper",
                {
                    "pair_id": pair_id,
                    "first_response_id": "first-juniper",
                    "listener": {"id": "juniper"},
                },
                7,
            ),
            witness(
                "audio_look_twice_first:" + pair_id + ":static-sam",
                {
                    "pair_id": pair_id,
                    "first_response_id": "first-sam",
                    "listener": {"id": "static-sam"},
                },
                6,
            ),
            witness(
                "audio_look_twice_pair:" + pair_id,
                {
                    "schema": "workbench.audio-look-twice-pair/v0",
                    "pair_id": pair_id,
                    "window_id": window_id,
                    "pair": {
                        "pair_id": pair_id,
                        "window_ref": {"window_id": window_id},
                    },
                },
                5,
            ),
            witness(
                "audio_window:" + window_id,
                {
                    "schema": "workbench.audio-window-materialized/v0",
                    "window_id": window_id,
                    "audio_sha256": "a" * 64,
                },
                4,
            ),
        ],
        "laws": [],
    }


def test_empty_field_surfaces_first_radio_aperture_and_silence_without_scoring():
    state = compose_nearby_station_doors(
        empty_house(),
        broadcast(),
        [],
        [],
    )
    assert state["read_only"] is True
    assert state["nearby_doors"][0]["kind"] == "cut-audio-window"
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"
    assert all(door["effect"] == "none" for door in state["nearby_doors"])
    assert all("score" not in door for door in state["nearby_doors"])
    assert "RECOMMENDATION != SELECTION" in state["laws"]


def test_mature_field_composes_multiple_organs_without_selecting_any():
    moments = [{
        "momentId": "moment-1",
        "eventId": "event-live",
        "span": {"startMs": 100, "endMs": 900},
        "status": "registered_not_currently_reverified",
    }]
    state = compose_nearby_station_doors(
        mature_house(),
        broadcast("reachable"),
        moments,
        [repo("static-live"), repo("the-haunted-toaster")],
    )
    kinds = [door["kind"] for door in state["nearby_doors"]]

    assert kinds == [
        "play-current-episode",
        "offer-episode-to-static-live",
        "inspect-live-moment",
        "revisit-house-door",
        "hold-silence",
    ]
    assert state["present"]["kind"] == "static-live"
    assert state["present"]["authority"] == "static-live"
    assert state["current_episode"]["episode_id"] == "first-signal-deadbeefcafe"
    assert state["counts"] == {
        "audio_windows": 1,
        "broadcast_episodes": 1,
        "phonograph_answers": 0,
        "phonograph_reentries": 0,
        "dogram_generation_deltas": 0,
        "dogram_listener_deltas": 0,
        "unresolved_house_doors": 1,
        "registered_live_moments": 1,
        "ghot_reseed_holds": 0,
        "ghot_reseed_admissions": 0,
        "ghot_assignment_offers": 0,
        "ghot_assignments": 0,
        "ghot_dispatches": 0,
        "ghot_dispatch_unknown": 0,
    }
    assert {
        pressure["kind"] for pressure in state["memory_pressures"]
    } == {"unresolved-house", "present-occurrence"}
    assert all(door["effect"] == "none" for door in state["nearby_doors"])
    assert len(state["nearby_doors"]) <= 6


def test_radio_lane_advances_only_to_currently_earned_aperture():
    base = mature_house()
    pair_id = base["external_witnesses"][4]["snapshot"]["pair_id"]

    # Remove episode: dialogue exists, so assembly is the next radio aperture.
    base["external_witnesses"] = [
        item for item in base["external_witnesses"]
        if not item["kind"].startswith("broadcast_episode:")
    ]
    state = compose_nearby_station_doors(base, broadcast(), [], [])
    assert state["nearby_doors"][0]["kind"] == "assemble-radio-episode"

    # Remove dialogue: exactly two first listens remain, so cross-read is next.
    base["external_witnesses"] = [
        item for item in base["external_witnesses"]
        if not item["kind"].startswith("audio_look_twice_dialogue:")
    ]
    state = compose_nearby_station_doors(base, broadcast(), [], [])
    assert state["nearby_doors"][0]["kind"] == "cross-read-first-listens"

    # Remove one first listen: acquiring first listens is next.
    base["external_witnesses"] = [
        item for item in base["external_witnesses"]
        if item["kind"] != "audio_look_twice_first:" + pair_id + ":juniper"
    ]
    state = compose_nearby_station_doors(base, broadcast(), [], [])
    assert state["nearby_doors"][0]["kind"] == "acquire-first-listens"


def test_phonograph_descendant_requires_fresh_radio_cross_read_before_next_answer():
    house = mature_house()
    parent_window = next(
        item for item in house["external_witnesses"]
        if item["kind"].startswith("audio_window:")
    )
    parent_window_id = parent_window["snapshot"]["window_id"]
    child_window_id = "autodisco-audio-window-v0:" + "c" * 64
    child_pair_id = "autodisco-audio-look-twice-pair-v0:" + "d" * 64
    child = witness(
        "audio_window:" + child_window_id,
        {
            "schema": "workbench.audio-window-materialized/v0",
            "window_id": child_window_id,
            "audio_sha256": "e" * 64,
            "source_lineage": {
                "schema": "workbench.phonograph-reentry-lineage/v0",
                "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
                "human_action": "explicit-admit",
                "parent_window_id": parent_window_id,
                "proposal_receipt_hash": "sha256:" + "f" * 64,
            },
        },
        20,
    )
    house["external_witnesses"].insert(0, child)

    capability = {
        "checkout_present": True,
        "available": True,
        "repo_head": "038b710",
        "repo_branch": "main",
        "capability": "field-answer-001",
    }
    locked = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("the-haunted-phonography")],
        phonograph=capability,
    )
    assert locked["nearby_doors"][0]["kind"] == "prepare-first-listen-booths"
    assert not any(door["lane"] == "phono" for door in locked["nearby_doors"])

    pair_snapshot = {
        "schema": "workbench.audio-look-twice-pair/v0",
        "pair_id": child_pair_id,
        "window_id": child_window_id,
        "audio_sha256": "e" * 64,
        "pair": {
            "schema": "autodisco.audio-look-twice-pair/v0",
            "pair_id": child_pair_id,
            "window_ref": {
                "window_id": child_window_id,
                "audio_sha256": "e" * 64,
            },
            "packets": [],
        },
    }
    house["external_witnesses"].insert(
        0, witness("audio_look_twice_pair:" + child_pair_id, pair_snapshot, 21)
    )
    for row, listener in [(22, "static-sam"), (23, "juniper")]:
        house["external_witnesses"].insert(
            0,
            witness(
                f"audio_look_twice_first:{child_pair_id}:{listener}",
                {
                    "pair_id": child_pair_id,
                    "first_response_id": f"first-{listener}",
                    "listener": {"id": listener},
                },
                row,
            ),
        )
    house["external_witnesses"].insert(
        0,
        witness(
            "audio_look_twice_dialogue:" + child_pair_id,
            {
                "schema": "workbench.audio-look-twice-dialogue/v0",
                "pair_id": child_pair_id,
                "window_id": child_window_id,
                "dialogue_id": "dialogue-child",
                "dialogue": {
                    "lingering_intrigue": True,
                    "door_seed": "answer after fresh witness",
                },
            },
            24,
        ),
    )

    unlocked = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("the-haunted-phonography")],
        phonograph=capability,
    )
    phono = next(door for door in unlocked["nearby_doors"] if door["lane"] == "phono")
    assert phono["kind"] == "ask-phonograph-answer"
    assert "RECURSION REQUIRES FRESH WITNESS" in unlocked["laws"]


def test_state_identity_is_deterministic_and_changes_with_witnessed_field():
    a = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [repo("static-live")]
    )
    b = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [repo("static-live")]
    )
    assert a["field_state_id"] == b["field_state_id"]

    changed_house = empty_house()
    changed_house["world_version"] = 1
    changed = compose_nearby_station_doors(
        changed_house, broadcast(), [], [repo("static-live")]
    )
    assert changed["field_state_id"] != a["field_state_id"]


def test_static_live_checkout_is_not_confused_with_reachable_broadcast_body():
    house = mature_house()
    state = compose_nearby_station_doors(
        house,
        broadcast("offline_or_incompatible"),
        [],
        [repo("static-live")],
    )
    live = next(
        door for door in state["nearby_doors"]
        if door["kind"] == "offer-episode-to-static-live"
    )
    body = next(
        item for item in live["evidence"]
        if item["kind"] == "broadcast-body"
    )
    assert body["connection"] == "offline_or_incompatible"
    assert state["present"] is None


def test_newer_window_does_not_advance_older_pair():
    house = mature_house()
    new_window_id = "autodisco-audio-window-v0:" + "f" * 64
    house["external_witnesses"].insert(
        0,
        witness(
            "audio_window:" + new_window_id,
            {
                "schema": "workbench.audio-window-materialized/v0",
                "window_id": new_window_id,
                "audio_sha256": "e" * 64,
            },
            10,
        ),
    )
    state = compose_nearby_station_doors(house, broadcast(), [], [])
    assert state["nearby_doors"][0]["kind"] == "prepare-first-listen-booths"
    assert state["nearby_doors"][0]["target"]["window_id"] == new_window_id


def test_field_station_api_is_read_only(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        entered = client.post("/api/doorhouse/enter", json={}, headers=headers)
        assert entered.status_code == 200

        before = client.get("/api/doorhouse/state").json()
        field = client.get("/api/doorhouse/field-station")
        after = client.get("/api/doorhouse/state").json()

        assert field.status_code == 200
        payload = field.json()
        assert payload["read_only"] is True
        assert payload["nearby_doors"]
        assert payload["nearby_doors"][-1]["kind"] == "hold-silence"
        assert before["world_version"] == after["world_version"]
        assert len(before["letters"]) == len(after["letters"])
        assert len(before["doors"]) == len(after["doors"])
        assert len(before["external_witnesses"]) == len(after["external_witnesses"])


def test_phonograph_door_requires_actual_capability_not_repo_presence():
    house = mature_house()
    unavailable = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("the-haunted-phonography")],
        phonograph={
            "checkout_present": True,
            "available": False,
            "repo_head": "old",
            "repo_branch": "main",
            "capability": None,
        },
    )
    assert not any(
        door["lane"] == "phono" for door in unavailable["nearby_doors"]
    )

    available = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("the-haunted-phonography")],
        phonograph={
            "checkout_present": True,
            "available": True,
            "repo_head": "038b710",
            "repo_branch": "main",
            "capability": "field-answer-001",
        },
    )
    phono = next(
        door for door in available["nearby_doors"]
        if door["lane"] == "phono"
    )
    assert phono["kind"] == "ask-phonograph-answer"
    assert phono["effect"] == "none"
    assert phono["evidence"][1]["kind"] == "capability"


def test_phonograph_answer_changes_field_door_to_audition_without_admission():
    house = mature_house()
    window_id = next(
        item["snapshot"]["window_id"]
        for item in house["external_witnesses"]
        if item["kind"].startswith("audio_window:")
    )
    house["external_witnesses"].insert(
        0,
        witness(
            "phonograph_field_answer:" + window_id,
            {
                "schema": "workbench.phonograph-field-answer/v0",
                "status": "proposal-ready",
                "window_id": window_id,
                "audio_sha256": "a" * 64,
                "proposal_receipt_hash": "sha256:" + "f" * 64,
                "proposal_hash": "sha256:" + "e" * 64,
                "audition": {"sha256": "sha256:" + "d" * 64},
            },
            10,
        ),
    )
    state = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("the-haunted-phonography")],
        phonograph={
            "checkout_present": True,
            "available": True,
            "repo_head": "038b710",
            "repo_branch": "main",
            "capability": "field-answer-001",
        },
    )
    phono = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "phono"
    )
    assert phono["kind"] == "audition-phonograph-answer"
    assert phono["effect"] == "none"
    assert phono["target"]["artifact"] == "audition.wav"
    assert state["counts"]["phonograph_answers"] == 1



def _generation_house_with_both_cross_reads():
    house = mature_house()
    parent_window = next(
        item for item in house["external_witnesses"]
        if item["kind"].startswith("audio_window:")
    )
    parent_window_id = parent_window["snapshot"]["window_id"]
    child_window_id = "autodisco-audio-window-v0:" + "c" * 64
    child_pair_id = "autodisco-audio-look-twice-pair-v0:" + "d" * 64
    proposal_receipt_hash = "sha256:" + "f" * 64

    house["external_witnesses"].insert(
        0,
        witness(
            "audio_window:" + child_window_id,
            {
                "schema": "workbench.audio-window-materialized/v0",
                "window_id": child_window_id,
                "audio_sha256": "e" * 64,
                "source_lineage": {
                    "schema": "workbench.phonograph-reentry-lineage/v0",
                    "relation": "ADMITTED_PROPOSAL_AS_NEW_AUDIO_SPECIMEN",
                    "human_action": "explicit-admit",
                    "parent_window_id": parent_window_id,
                    "proposal_receipt_hash": proposal_receipt_hash,
                },
            },
            30,
        ),
    )
    house["external_witnesses"].insert(
        0,
        witness(
            "phonograph_reentry:" + child_window_id,
            {
                "schema": "workbench.phonograph-reentry/v0",
                "status": "admitted-as-audio-specimen",
                "parent_window_id": parent_window_id,
                "proposal_receipt_hash": proposal_receipt_hash,
                "child_window_id": child_window_id,
            },
            31,
        ),
    )
    house["external_witnesses"].insert(
        0,
        witness(
            "audio_look_twice_pair:" + child_pair_id,
            {
                "schema": "workbench.audio-look-twice-pair/v0",
                "pair_id": child_pair_id,
                "window_id": child_window_id,
                "pair": {
                    "pair_id": child_pair_id,
                    "window_ref": {"window_id": child_window_id},
                },
            },
            32,
        ),
    )
    for row, listener in [(33, "static-sam"), (34, "juniper")]:
        house["external_witnesses"].insert(
            0,
            witness(
                f"audio_look_twice_first:{child_pair_id}:{listener}",
                {
                    "pair_id": child_pair_id,
                    "first_response_id": f"child-first-{listener}",
                    "listener": {"id": listener},
                },
                row,
            ),
        )
    house["external_witnesses"].insert(
        0,
        witness(
            "audio_look_twice_dialogue:" + child_pair_id,
            {
                "schema": "workbench.audio-look-twice-dialogue/v0",
                "pair_id": child_pair_id,
                "window_id": child_window_id,
                "dialogue_id": "dialogue-child",
                "dialogue": {
                    "lingering_intrigue": True,
                    "door_seed": "measure what changed",
                },
            },
            35,
        ),
    )
    return house, parent_window_id, child_window_id


def test_dogram_generation_door_requires_both_cross_reads_and_real_capability():
    house, parent_window_id, child_window_id = _generation_house_with_both_cross_reads()
    dogram_capability = {
        "checkout_present": True,
        "available": True,
        "repo_head": "f352fe5",
        "repo_branch": "main",
        "capability": "generation-delta-001",
    }

    measured_ready = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram=dogram_capability,
    )
    dogram_door = next(
        door for door in measured_ready["nearby_doors"]
        if door["lane"] == "dogram"
    )
    assert dogram_door["kind"] == "measure-generation-delta"
    assert dogram_door["target"]["parent_window_id"] == parent_window_id
    assert dogram_door["target"]["child_window_id"] == child_window_id
    assert dogram_door["effect"] == "none"

    no_parent_dialogue = {
        **house,
        "external_witnesses": [
            item for item in house["external_witnesses"]
            if not (
                item["kind"].startswith("audio_look_twice_dialogue:")
                and item["snapshot"].get("window_id") == parent_window_id
            )
        ],
    }
    blocked = compose_nearby_station_doors(
        no_parent_dialogue,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram=dogram_capability,
    )
    assert not any(
        door["lane"] == "dogram" for door in blocked["nearby_doors"]
    )

    unavailable = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram={
            "checkout_present": True,
            "available": False,
            "repo_head": "old",
            "repo_branch": "main",
            "capability": None,
        },
    )
    assert not any(
        door["lane"] == "dogram" for door in unavailable["nearby_doors"]
    )


def test_dogram_receipt_changes_field_to_inspection_and_silence_survives_cap():
    house, parent_window_id, child_window_id = _generation_house_with_both_cross_reads()
    house["external_witnesses"].insert(
        0,
        witness(
            "dogram_generation_delta:" + child_window_id,
            {
                "schema": "workbench.dogram-generation-delta/v0",
                "status": "measured",
                "parent_window_id": parent_window_id,
                "child_window_id": child_window_id,
                "dogram_receipt_hash": "sha256:" + "9" * 64,
                "classification": "MEASURED_CHANGE",
                "changed_axes": ["rms_quartiles_q15", "peak_q15"],
            },
            40,
        ),
    )
    moments = [{
        "momentId": "moment-field",
        "eventId": "event-field",
        "span": {"startMs": 0, "endMs": 100},
        "status": "registered_not_currently_reverified",
    }]
    state = compose_nearby_station_doors(
        house,
        broadcast("reachable"),
        moments,
        [repo("Dogram"), repo("the-haunted-phonography"), repo("static-live")],
        phonograph={
            "checkout_present": True,
            "available": True,
            "repo_head": "038b710",
            "repo_branch": "main",
            "capability": "field-answer-001",
        },
        dogram={
            "checkout_present": True,
            "available": True,
            "repo_head": "f352fe5",
            "repo_branch": "main",
            "capability": "generation-delta-001",
        },
    )
    dogram_door = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "dogram"
    )
    assert dogram_door["kind"] == "inspect-generation-delta"
    assert dogram_door["evidence"][0]["classification"] == "MEASURED_CHANGE"
    assert state["counts"]["dogram_generation_deltas"] == 1
    assert len(state["nearby_doors"]) == 6
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"
    assert "DELTA != VALUE" in state["laws"]



def test_receiver_hold_changes_field_to_explicit_admission_without_execution():
    base = compose_nearby_station_doors(
        empty_house(), broadcast(), [], []
    )
    receiver = [{
        "stored_at": "2026-10-03T16:30:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "RECEIVED_THEN_HELD",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": None,
        "intent_id": None,
    }]

    held = compose_nearby_station_doors(
        empty_house(),
        broadcast(),
        [],
        [],
        field_receivers=receiver,
    )

    carried = next(
        door for door in held["nearby_doors"]
        if door["lane"] == "carried"
    )
    assert carried["kind"] == "admit-ghot-field-reseed"
    assert carried["effect"] == "none"
    assert carried["target"]["control"] == "ghot-field-reseed-admit"
    assert held["counts"]["ghot_reseed_holds"] == 1
    assert held["counts"]["ghot_reseed_admissions"] == 0
    assert any(
        pressure["kind"] == "receiver-hold"
        for pressure in held["memory_pressures"]
    )
    assert held["nearby_doors"][-1]["kind"] == "hold-silence"
    assert held["field_state_id"] != base["field_state_id"]


def test_receiver_admission_changes_field_to_assignment_offer_aperture():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "ADMITTED_NOT_ASSIGNED",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
    }]

    admitted = compose_nearby_station_doors(
        empty_house(),
        broadcast(),
        [],
        [],
        field_receivers=receiver,
    )

    carried = next(
        door for door in admitted["nearby_doors"]
        if door["lane"] == "carried"
    )
    assert carried["kind"] == "offer-ghot-carried-intent-assignment"
    assert carried["effect"] == "none"
    assert carried["target"]["control"] == "ghot-field-intent-offer"
    assert carried["evidence"][0]["status"] == "ADMITTED_NOT_ASSIGNED"
    assert admitted["counts"]["ghot_reseed_holds"] == 0
    assert admitted["counts"]["ghot_reseed_admissions"] == 1
    assert admitted["counts"]["ghot_assignment_offers"] == 0
    assert admitted["counts"]["ghot_assignments"] == 0
    assert "ADMISSION != ASSIGNMENT" in admitted["laws"]
    assert "ASSIGNMENT != EXECUTION" in admitted["laws"]
    assert admitted["nearby_doors"][-1]["kind"] == "hold-silence"



def test_active_receiver_boundary_survives_dense_field_cap():
    receiver = [{
        "stored_at": "2026-10-03T16:20:00+00:00",
        "receiver_at": "2026-10-03T16:40:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "RECEIVED_THEN_HELD",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": None,
        "intent_id": None,
    }]
    moments = [{
        "momentId": "moment-dense",
        "eventId": "event-dense",
        "span": {"startMs": 0, "endMs": 100},
        "status": "registered_not_currently_reverified",
    }]
    state = compose_nearby_station_doors(
        mature_house(),
        broadcast("reachable"),
        moments,
        [repo("static-live"), repo("the-haunted-phonography")],
        phonograph={
            "checkout_present": True,
            "available": True,
            "repo_head": "038b710",
            "repo_branch": "main",
            "capability": "field-answer-001",
        },
        field_receivers=receiver,
    )

    assert len(state["nearby_doors"]) == 6
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"
    assert any(
        door["kind"] == "admit-ghot-field-reseed"
        for door in state["nearby_doors"]
    )
    assert sum(
        1 for door in state["nearby_doors"]
        if door["lane"] == "carried"
    ) == 1


def test_dogram_lane_advances_from_signal_delta_to_listener_delta():
    house, parent_window_id, child_window_id = _generation_house_with_both_cross_reads()
    generation_hash = "sha256:" + "9" * 64
    house["external_witnesses"].insert(
        0,
        witness(
            "dogram_generation_delta:" + child_window_id,
            {
                "schema": "workbench.dogram-generation-delta/v0",
                "status": "measured",
                "parent_window_id": parent_window_id,
                "child_window_id": child_window_id,
                "proposal_receipt_hash": "sha256:" + "f" * 64,
                "dogram_receipt_hash": generation_hash,
                "classification": "MEASURED_CHANGE",
                "changed_axes": ["peak_q15"],
            },
            41,
        ),
    )
    listener_capability = {
        "checkout_present": True,
        "available": True,
        "repo_head": "551b5f9",
        "repo_branch": "main",
        "capability": "listener-delta-001",
    }

    state = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram={
            "checkout_present": True,
            "available": True,
            "repo_head": "551b5f9",
            "repo_branch": "main",
            "capability": "generation-delta-001",
        },
        listener_dogram=listener_capability,
    )
    dogram_door = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "dogram"
    )
    assert dogram_door["kind"] == "measure-listener-delta"
    assert dogram_door["target"]["parent_window_id"] == parent_window_id
    assert dogram_door["target"]["child_window_id"] == child_window_id
    assert (
        dogram_door["target"]["generation_delta_receipt_hash"]
        == generation_hash
    )
    assert dogram_door["effect"] == "none"
    assert state["listener_dogram_capability"]["capability"] == "listener-delta-001"

    house["external_witnesses"].insert(
        0,
        witness(
            "dogram_listener_delta:" + child_window_id,
            {
                "schema": "workbench.dogram-listener-delta/v0",
                "status": "measured",
                "parent_window_id": parent_window_id,
                "child_window_id": child_window_id,
                "generation_delta_receipt_hash": generation_hash,
                "dogram_receipt_hash": "sha256:" + "8" * 64,
                "classification": "MEASURED_RESPONSE_CHANGE",
                "listener_count": 2,
                "changed_listener_count": 2,
                "shared_changed_axes": ["closing_line"],
            },
            42,
        ),
    )
    inspected = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram={
            "checkout_present": True,
            "available": True,
            "repo_head": "551b5f9",
            "repo_branch": "main",
            "capability": "generation-delta-001",
        },
        listener_dogram=listener_capability,
    )
    inspect_door = next(
        door for door in inspected["nearby_doors"]
        if door["lane"] == "dogram"
    )
    assert inspect_door["kind"] == "inspect-listener-delta"
    assert (
        inspect_door["evidence"][0]["classification"]
        == "MEASURED_RESPONSE_CHANGE"
    )
    assert inspect_door["evidence"][0]["changed_listener_count"] == 2
    assert inspected["counts"]["dogram_generation_deltas"] == 1
    assert inspected["counts"]["dogram_listener_deltas"] == 1
    assert "RESPONSE DELTA != PERSON DELTA" in inspected["laws"]
    assert "RESPONSE DELTA != CAUSAL EFFECT" in inspected["laws"]


def test_listener_delta_capability_is_not_inferred_from_generation_delta():
    house, parent_window_id, child_window_id = _generation_house_with_both_cross_reads()
    house["external_witnesses"].insert(
        0,
        witness(
            "dogram_generation_delta:" + child_window_id,
            {
                "schema": "workbench.dogram-generation-delta/v0",
                "status": "measured",
                "parent_window_id": parent_window_id,
                "child_window_id": child_window_id,
                "dogram_receipt_hash": "sha256:" + "9" * 64,
                "classification": "MEASURED_CHANGE",
                "changed_axes": ["peak_q15"],
            },
            43,
        ),
    )
    state = compose_nearby_station_doors(
        house,
        broadcast(),
        [],
        [repo("Dogram")],
        dogram={
            "checkout_present": True,
            "available": True,
            "repo_head": "551b5f9",
            "repo_branch": "main",
            "capability": "generation-delta-001",
        },
    )
    dogram_door = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "dogram"
    )
    assert dogram_door["kind"] == "inspect-generation-delta"
    assert not any(
        door["kind"] == "measure-listener-delta"
        for door in state["nearby_doors"]
    )



def test_assignment_offer_changes_field_to_explicit_pair_choice():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:32:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "OFFER_READY",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_offer_id": "ghot-carried-intent-offer-v0:" + "6" * 64,
        "assignment_id": None,
        "selected_node_id": None,
        "capability": None,
    }]
    state = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [], field_receivers=receiver
    )
    carried = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "carried"
    )
    assert carried["kind"] == "choose-ghot-carried-intent-assignment"
    assert carried["target"]["control"] == "ghot-field-intent-assign"
    assert carried["target"]["offer_id"] == receiver[0]["assignment_offer_id"]
    assert carried["effect"] == "none"
    assert state["counts"]["ghot_assignment_offers"] == 1
    assert state["counts"]["ghot_assignments"] == 0
    assert any(
        pressure["kind"] == "receiver-assignment-offer"
        for pressure in state["memory_pressures"]
    )


def test_assignment_receipt_changes_field_to_explicit_dispatch_crossing():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:33:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "ASSIGNED_NOT_EXECUTED",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_offer_id": "ghot-carried-intent-offer-v0:" + "6" * 64,
        "assignment_id": "ghot-carried-intent-assignment-v0:" + "7" * 64,
        "selected_node_id": "node-local",
        "capability": "system.hash",
    }]
    state = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [], field_receivers=receiver
    )
    carried = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "carried"
    )
    assert carried["kind"] == "dispatch-ghot-carried-intent-assignment"
    assert carried["effect"] == "none"
    assert carried["target"]["control"] == "ghot-field-intent-dispatch"
    assert carried["evidence"][0]["selected_node_id"] == "node-local"
    assert carried["evidence"][0]["capability"] == "system.hash"
    assert state["counts"]["ghot_assignment_offers"] == 0
    assert state["counts"]["ghot_assignments"] == 1
    assert state["counts"]["ghot_dispatches"] == 0
    assert state["counts"]["ghot_dispatch_unknown"] == 0
    assert "ASSIGNMENT != TASK" in state["laws"]
    assert "DISPATCH REQUIRES A NEW EXPLICIT CROSSING" in state["laws"]
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"



def test_execution_consequence_sprouts_unranked_banana_elf_co_delight_field():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:45:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "EXECUTED",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_offer_id": "ghot-carried-intent-offer-v0:" + "6" * 64,
        "assignment_id": "ghot-carried-intent-assignment-v0:" + "7" * 64,
        "selected_node_id": "node-local",
        "capability": "system.hash",
        "dispatch_crossing_id": "relatte-crossing-v0:" + "8" * 64,
        "task_id": "task-123",
        "execution_receipt_id": "receipt-123",
        "signed_receipt_id": "relatte-receipt-v0:" + "9" * 64,
        "execution_status": "ok",
        "output_sha256": "a" * 64,
    }]
    state = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [], field_receivers=receiver
    )
    delight = [
        door for door in state["nearby_doors"]
        if door["lane"] == "delight"
    ]
    assert [door["kind"] for door in delight] == [
        "banana-elf-delightfuler",
        "banana-elf-helpfuler",
        "banana-elf-curiouser",
    ]
    assert [door["target"]["facet"] for door in delight] == [
        "delightfuler",
        "helpfuler",
        "curiouser",
    ]
    assert [door["target"]["move"] for door in delight] == [
        "tiny-gift",
        "make-room",
        "keep-weird",
    ]
    assert all(door["effect"] == "none" for door in delight)
    assert all(
        door["evidence"][0]["task_id"] == "task-123"
        and door["evidence"][0]["signed_receipt_id"]
        == receiver[0]["signed_receipt_id"]
        for door in delight
    )
    assert all(door["target"]["orientation"] == "co-delight" for door in delight)
    assert all("DELIGHT != SCORE" in door["laws"] for door in delight)
    assert all("CO-DELIGHT REQUIRES RETURN" in door["laws"] for door in delight)
    assert '"score"' not in __import__("json").dumps(delight)
    assert state["counts"]["ghot_assignments"] == 0
    assert state["counts"]["ghot_dispatches"] == 1
    assert state["counts"]["ghot_dispatch_unknown"] == 0
    pressure = next(
        item for item in state["memory_pressures"]
        if item["kind"] == "receiver-execution-consequence"
    )
    assert pressure["effect"] == "surface-banana-elf-co-delight-field"
    assert "DISPATCH != SUCCESS" in state["laws"]
    assert "EXECUTION != RECEIPT" in state["laws"]
    assert "DELIGHT != SCORE" in state["laws"]
    assert "UNKNOWN UTILITY != ZERO VALUE" in state["laws"]
    assert "NOT EVERYTHING MUST GRADUATE" in state["laws"]
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"


def test_ambiguous_dispatch_changes_field_to_inspection_without_retry_control():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:44:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "DISPATCH_OUTCOME_UNKNOWN",
        "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
        "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_offer_id": "ghot-carried-intent-offer-v0:" + "6" * 64,
        "assignment_id": "ghot-carried-intent-assignment-v0:" + "7" * 64,
        "selected_node_id": "node-local",
        "capability": "system.hash",
        "dispatch_crossing_id": "relatte-crossing-v0:" + "8" * 64,
        "task_id": None,
        "execution_receipt_id": None,
        "signed_receipt_id": None,
        "execution_status": None,
        "output_sha256": None,
    }]
    state = compose_nearby_station_doors(
        empty_house(), broadcast(), [], [], field_receivers=receiver
    )
    carried = next(
        door for door in state["nearby_doors"]
        if door["lane"] == "carried"
    )
    assert carried["kind"] == "inspect-ghot-carried-intent-dispatch-unknown"
    assert carried["effect"] == "none"
    assert carried["target"].get("control") is None
    assert state["counts"]["ghot_dispatches"] == 0
    assert state["counts"]["ghot_dispatch_unknown"] == 1
    assert any(
        pressure["kind"] == "receiver-dispatch-unknown"
        for pressure in state["memory_pressures"]
    )
    assert "AMBIGUOUS OUTCOME != SAFE RETRY" in state["laws"]
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"



def test_banana_elf_field_survives_dense_lane_cap_without_becoming_ranked():
    receiver = [{
        "stored_at": "2026-10-03T16:31:00+00:00",
        "receiver_at": "2026-10-03T16:45:00+00:00",
        "field_return_id": "field-return-v0:" + "1" * 64,
        "reseed_id": "field-reseed-v0:" + "2" * 64,
        "status": "EXECUTION_ERROR",
        "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
        "assignment_id": "ghot-carried-intent-assignment-v0:" + "7" * 64,
        "selected_node_id": "node-local",
        "capability": "system.hash",
        "dispatch_crossing_id": "relatte-crossing-v0:" + "8" * 64,
        "task_id": "task-error",
        "execution_receipt_id": "receipt-error",
        "signed_receipt_id": "relatte-receipt-v0:" + "9" * 64,
        "execution_status": "error",
        "output_sha256": None,
    }]
    moments = [{
        "momentId": "moment-dense-delight",
        "eventId": "event-dense-delight",
        "span": {"startMs": 0, "endMs": 100},
        "status": "registered_not_currently_reverified",
    }]
    state = compose_nearby_station_doors(
        mature_house(),
        broadcast("reachable"),
        moments,
        [repo("static-live"), repo("the-haunted-phonography")],
        phonograph={
            "checkout_present": True,
            "available": True,
            "repo_head": "038b710",
            "repo_branch": "main",
            "capability": "field-answer-001",
        },
        field_receivers=receiver,
    )
    delight = [
        door for door in state["nearby_doors"]
        if door["lane"] == "delight"
    ]
    assert len(delight) == 3
    assert len(state["nearby_doors"]) <= 6
    assert state["nearby_doors"][-1]["kind"] == "hold-silence"
    assert all(
        door["evidence"][0]["status"] == "EXECUTION_ERROR"
        for door in delight
    )
    assert all(
        door["target"]["novelty"] == "proposal-only"
        for door in delight
    )
