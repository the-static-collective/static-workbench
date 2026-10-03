from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict
from static_workbench.doorhouse_relatte import build_relatte_request


def config_for(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )


def crossed_receipt(store: DoorHouse):
    state = store.enter()
    letter = state["letters"][0]
    store.open_letter(letter["id"])
    state = store.state()
    door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
    store.select(door["id"], 0)
    state = store.cross(door["id"], 0)
    return state["receipts"][0]


def fake_result(receipt: dict) -> dict:
    crossing_id = "relatte-crossing-v0:" + "a" * 64
    return {
        "schema": "relatte.opaque-roundtrip-result/v0",
        "request_id": "relatte-opaque-roundtrip-v0:" + "b" * 64,
        "crossing": {
            "crossing_id": crossing_id,
            "extensions": {
                "organ_adapter": {
                    "donor_claims": {
                        "local_receipt_id": receipt["id"],
                        "local_receipt_sha256": receipt["sha256"],
                    }
                }
            },
        },
        "transport_frame": {
            "transport_id": "relatte-transport-v0:" + "c" * 64,
        },
        "receive_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "d" * 64,
            "kind": "RECEIVED",
            "semantic_effect": "none",
            "world_id": "world:doorhouse-relatte-hold",
        },
        "disposition_receipt": {
            "crossing_id": crossing_id,
            "receipt_id": "relatte-receipt-v0:" + "e" * 64,
            "kind": "R3_HOLD",
            "semantic_effect": "none",
        },
        "receiver_snapshot": {
            "state_ref": "relatte-local-state-v0:" + "f" * 64,
        },
        "laws": ["RECEIVED != ADMITTED"],
    }


def test_relatte_request_is_deterministic_and_carries_exact_local_receipt(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)

    first = build_relatte_request(receipt, tmp_path / "state")
    second = build_relatte_request(receipt, tmp_path / "state")

    assert first == second
    assert first["disposition"] == "HOLD"
    assert first["spec"]["donor_claims"]["local_receipt_id"] == receipt["id"]
    assert first["spec"]["donor_claims"]["local_receipt_sha256"] == receipt["sha256"]
    assert first["spec"]["payload_refs"][0]["address"] == (
        "sha256:" + receipt["snapshot"]["artifact_sha256"]
    )
    assert first["spec"]["requested_effect"]["authority"] == "receiver-local"
    for key in ("created_at",):
        assert first["spec"][key].endswith("Z")
        assert len(first["spec"][key].split(".")[1].removesuffix("Z")) == 3
    for key in ("transport_created_at", "received_at", "disposed_at"):
        assert first[key].endswith("Z")


def test_relatte_witness_attaches_only_to_exact_local_receipt(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    result = fake_result(receipt)

    state = store.record_relatte_witness(receipt["id"], result)
    assert len(state["external_witnesses"]) == 1
    witness = state["external_witnesses"][0]
    assert witness["receipt_id"] == receipt["id"]
    assert witness["snapshot"]["status"] == "RECEIVED_THEN_HELD"
    assert witness["snapshot"]["semantic_effect"] == "none"

    same = store.record_relatte_witness(receipt["id"], result)
    assert len(same["external_witnesses"]) == 1

    changed = fake_result(receipt)
    changed["disposition_receipt"]["receipt_id"] = "relatte-receipt-v0:" + "9" * 64
    with pytest.raises(DoorHouseConflict):
        store.record_relatte_witness(receipt["id"], changed)


def test_relatte_api_records_returned_hold_witness(monkeypatch, tmp_path):
    config = config_for(tmp_path)

    def fake_aperture(receipt, state_dir, repos):
        return fake_result(receipt)

    monkeypatch.setattr(app_module, "run_relatte_aperture", fake_aperture)

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        state = client.post("/api/doorhouse/enter", json={}, headers=headers).json()
        letter = state["letters"][0]
        state = client.post(
            f"/api/doorhouse/letters/{letter['id']}/open", json={}, headers=headers
        ).json()
        door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
        client.post(
            f"/api/doorhouse/doors/{door['id']}/select",
            json={"expected_world_version": 0}, headers=headers,
        )
        state = client.post(
            f"/api/doorhouse/doors/{door['id']}/cross",
            json={"expected_world_version": 0}, headers=headers,
        ).json()
        receipt = state["receipts"][0]

        response = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/relatte",
            json={}, headers=headers,
        )
        assert response.status_code == 200
        returned = response.json()
        assert returned["external_witnesses"][0]["snapshot"]["status"] == "RECEIVED_THEN_HELD"
        assert returned["external_witnesses"][0]["snapshot"]["semantic_effect"] == "none"
