import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.field_return import FieldReturnStore, compose_field_return
from static_workbench.field_station import compose_nearby_station_doors


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


def empty_broadcast():
    return {
        "checkout_present": False,
        "configured": False,
        "connection": "unconfigured",
        "open_url": None,
        "event": None,
        "broadcast_state": None,
        "recording": None,
        "stream": None,
        "authority": "static-live",
    }


def field():
    return compose_nearby_station_doors(
        empty_house(),
        empty_broadcast(),
        [],
        [],
    )


def test_take_binds_exact_field_and_emits_proposal_only_reseed():
    state = field()
    door = state["nearby_doors"][0]

    result = compose_field_return(
        state,
        door["door_id"],
        "take",
        "Carry this exact aperture into the next composition.",
    )

    assert result["schema"] == "workbench.field-return/v0"
    assert result["field_state_id"] == state["field_state_id"]
    assert result["selected_door"] == door
    assert result["effect"] == "none"
    assert result["reseed"]["schema"] == "workbench.field-reseed/v0"
    assert result["reseed"]["door"] == door
    assert result["reseed"]["status"] == "proposal-only"
    assert result["reseed"]["effect"] == "none"
    assert "SELECTION != EXECUTION" in result["laws"]
    assert "RESEED != ADMISSION" in result["reseed"]["laws"]


def test_same_exact_return_is_deterministic():
    state = field()
    door_id = state["nearby_doors"][0]["door_id"]

    a = compose_field_return(state, door_id, "take", "same note")
    b = compose_field_return(state, door_id, "take", "same note")

    assert a["receipt_id"] == b["receipt_id"]
    assert a["reseed"]["reseed_id"] == b["reseed"]["reseed_id"]


@pytest.mark.parametrize("disposition", ["hold", "pass"])
def test_hold_and_pass_record_disposition_without_reseed(disposition):
    state = field()
    door_id = state["nearby_doors"][-1]["door_id"]

    result = compose_field_return(state, door_id, disposition)

    assert result["disposition"] == disposition
    assert result["effect"] == "none"
    assert result["reseed"] is None


def test_unknown_door_is_refused():
    state = field()

    with pytest.raises(ValueError, match="not present"):
        compose_field_return(state, "field-door-v0:not-real", "take")


def test_invalid_disposition_is_refused():
    state = field()
    door_id = state["nearby_doors"][0]["door_id"]

    with pytest.raises(ValueError, match="unsupported field disposition"):
        compose_field_return(state, door_id, "execute")


def test_tampered_field_state_is_refused_even_when_door_id_still_matches():
    state = field()
    door_id = state["nearby_doors"][0]["door_id"]
    state["nearby_doors"][0]["label"] = "silently rewritten label"

    with pytest.raises(ValueError, match="identity mismatch"):
        compose_field_return(state, door_id, "take")


def test_return_snapshot_is_detached_from_later_caller_mutation():
    state = field()
    door = state["nearby_doors"][0]
    result = compose_field_return(state, door["door_id"], "take")

    door["label"] = "later mutation"

    assert result["selected_door"]["label"] != "later mutation"
    assert result["reseed"]["door"]["label"] != "later mutation"



def workbench_config(tmp_path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def test_store_is_durable_and_idempotent(tmp_path):
    state = field()
    door_id = state["nearby_doors"][0]["door_id"]
    receipt = compose_field_return(state, door_id, "take", "carry me")
    db_path = tmp_path / "field_returns.sqlite3"

    first_store = FieldReturnStore(db_path)
    first = first_store.save(receipt)
    duplicate = first_store.save(receipt)

    assert first["receipt_id"] == receipt["receipt_id"]
    assert duplicate["stored_at"] == first["stored_at"]
    assert len(first_store.latest()) == 1

    reopened = FieldReturnStore(db_path)
    latest = reopened.latest()
    assert len(latest) == 1
    assert latest[0]["receipt_id"] == receipt["receipt_id"]
    assert latest[0]["reseed"]["reseed_id"] == receipt["reseed"]["reseed_id"]


def test_field_return_api_persists_choice_without_mutating_house_world(tmp_path):
    config = workbench_config(tmp_path)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        boot = client.get("/api/bootstrap").json()
        headers = {"x-workbench-session": boot["session_token"]}
        before_house = client.get("/api/doorhouse/state").json()
        observed = client.get("/api/doorhouse/field-station").json()
        door = observed["nearby_doors"][0]

        response = client.post(
            "/api/doorhouse/field-station/returns",
            headers=headers,
            json={
                "expected_field_state_id": observed["field_state_id"],
                "door_id": door["door_id"],
                "disposition": "take",
                "note": "carry this exact aperture",
            },
        )
        assert response.status_code == 200
        saved = response.json()
        assert saved["selected_door"] == door
        assert saved["reseed"]["status"] == "proposal-only"

        after_house = client.get("/api/doorhouse/state").json()
        assert after_house["world_version"] == before_house["world_version"]
        assert after_house["receipts"] == before_house["receipts"]

        shelf = client.get("/api/doorhouse/field-station/returns").json()["returns"]
        assert [item["receipt_id"] for item in shelf] == [saved["receipt_id"]]

    with TestClient(create_app(config), base_url="http://127.0.0.1") as reopened:
        shelf = reopened.get("/api/doorhouse/field-station/returns").json()["returns"]
        assert [item["receipt_id"] for item in shelf] == [saved["receipt_id"]]
        assert shelf[0]["human_note"] == "carry this exact aperture"


def test_field_return_api_refuses_stale_observation(tmp_path):
    config = workbench_config(tmp_path)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        boot = client.get("/api/bootstrap").json()
        headers = {"x-workbench-session": boot["session_token"]}
        observed = client.get("/api/doorhouse/field-station").json()
        door = observed["nearby_doors"][0]

        response = client.post(
            "/api/doorhouse/field-station/returns",
            headers=headers,
            json={
                "expected_field_state_id": "field-station-v0:" + "0" * 64,
                "door_id": door["door_id"],
                "disposition": "take",
                "note": "",
            },
        )

        assert response.status_code == 409
        assert "field changed" in response.json()["detail"]
        assert client.get(
            "/api/doorhouse/field-station/returns"
        ).json()["returns"] == []



def test_store_persists_receiver_hold_then_admission_across_restart(tmp_path):
    state = field()
    receipt = compose_field_return(
        state,
        state["nearby_doors"][0]["door_id"],
        "take",
        "cross this exact possibility",
    )
    db_path = tmp_path / "field_returns.sqlite3"
    store = FieldReturnStore(db_path)
    stored = store.save(receipt)

    crossing = {
        "schema": "workbench.field-reseed-crossing/v0",
        "field_return_id": stored["receipt_id"],
        "reseed_id": stored["reseed"]["reseed_id"],
        "status": "RECEIVED_THEN_HELD",
        "semantic_effect": "none",
        "pins": {"relatte": "r14", "ghot": "receiver-001"},
        "relatte": {"schema": "relatte.opaque-roundtrip-result/v0"},
        "ghot_hold": {
            "schema": "ghot.field-reseed-hold/v0",
            "hold_id": "ghot-field-reseed-hold-v0:" + "3" * 64,
            "status": "HOLD",
            "semantic_effect": "none",
        },
    }
    held = store.save_crossing(stored["receipt_id"], crossing)
    assert held["status"] == "RECEIVED_THEN_HELD"

    reopened = FieldReturnStore(db_path)
    shelf = reopened.latest()
    assert shelf[0]["receiver"]["status"] == "RECEIVED_THEN_HELD"
    summary = reopened.receiver_field_state()[0]
    assert summary["hold_id"] == crossing["ghot_hold"]["hold_id"]
    assert summary["admission_id"] is None

    admission = {
        "schema": "workbench.field-reseed-admission/v0",
        "field_return_id": stored["receipt_id"],
        "reseed_id": stored["reseed"]["reseed_id"],
        "status": "ADMITTED_NOT_ASSIGNED",
        "semantic_effect": "local-inbox-only",
        "pins": {"ghot": "receiver-001"},
        "ghot_admission": {
            "schema": "ghot.field-reseed-admission/v0",
            "admission_id": "ghot-field-reseed-admission-v0:" + "4" * 64,
            "status": "ADMITTED",
            "intent": {
                "schema": "ghot.carried-intent/v0",
                "intent_id": "ghot-carried-intent-v0:" + "5" * 64,
                "status": "admitted-not-assigned",
            },
        },
    }
    admitted = reopened.save_admission(stored["receipt_id"], admission)
    assert admitted["status"] == "ADMITTED_NOT_ASSIGNED"

    again = FieldReturnStore(db_path)
    summary = again.receiver_field_state()[0]
    assert summary["status"] == "ADMITTED_NOT_ASSIGNED"
    assert summary["admission_id"] == admission["ghot_admission"]["admission_id"]
    assert summary["intent_id"] == admission["ghot_admission"]["intent"]["intent_id"]


def test_store_refuses_receiver_consequence_for_non_take_return(tmp_path):
    state = field()
    receipt = compose_field_return(
        state,
        state["nearby_doors"][-1]["door_id"],
        "hold",
    )
    store = FieldReturnStore(tmp_path / "field_returns.sqlite3")
    stored = store.save(receipt)

    with pytest.raises(ValueError, match="only TAKE"):
        store.save_crossing(
            stored["receipt_id"],
            {
                "schema": "workbench.field-reseed-crossing/v0",
                "field_return_id": stored["receipt_id"],
                "reseed_id": "field-reseed-v0:" + "0" * 64,
            },
        )
