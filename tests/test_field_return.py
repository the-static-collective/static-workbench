import pytest

from static_workbench.field_return import compose_field_return
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
