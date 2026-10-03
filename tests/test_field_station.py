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
        "unresolved_house_doors": 1,
        "registered_live_moments": 1,
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
