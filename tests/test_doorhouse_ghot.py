from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench import app as app_module
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.doorhouse import DoorHouse, DoorHouseConflict


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


def fake_relatte(receipt: dict) -> dict:
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
        "transport_frame": {"transport_id": "relatte-transport-v0:" + "c" * 64},
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
        "receiver_snapshot": {"state_ref": "relatte-local-state-v0:" + "f" * 64},
        "laws": ["RECEIVED != ADMITTED"],
    }


def fake_offer() -> dict:
    return {
        "kind": "ghot.body-choice.offer",
        "version": "0",
        "offer_id": "ghot-body-offer-v0:" + "1" * 64,
        "capability": "system.hash",
        "observed_at": "2026-10-03T03:00:00+00:00",
        "requester_node_id": "node-requester",
        "candidates": [
            {
                "node_id": "node-alpha",
                "location": "local",
                "hostname": "alpha",
                "eligible": True,
                "matching_offer": {
                    "kind": "ghot.offer",
                    "version": "0",
                    "capability": "system.hash",
                    "available": True,
                },
                "rejected": [],
            },
            {
                "node_id": "node-sleeping",
                "location": "remote",
                "hostname": "sleeping",
                "eligible": False,
                "matching_offer": None,
                "rejected": ["liveness is asleep, not awake"],
            },
        ],
        "laws": ["OFFER != ASSIGNMENT"],
    }


def fake_execution(offer: dict, selected: str) -> dict:
    return {
        "kind": "ghot.body-choice.result",
        "version": "0",
        "assignment": {
            "kind": "ghot.assignment",
            "version": "0",
            "assignment_id": "assignment-001",
            "offer_id": offer["offer_id"],
            "selected_node_id": selected,
            "capability": "system.hash",
            "selection_source": "doorhouse-user-explicit",
            "created_at": "2026-10-03T03:01:00+00:00",
        },
        "execution": {
            "task": {
                "kind": "ghot.task",
                "version": "0",
                "task_id": "task-001",
                "capability": "system.hash",
            },
            "receipt": {
                "kind": "ghot.receipt",
                "version": "0",
                "receipt_id": "receipt-ghot-001",
                "task_id": "task-001",
                "executor_node_id": selected,
                "capability": "system.hash",
                "status": "ok",
                "output": {"sha256": "9" * 64},
                "output_sha256": "8" * 64,
            },
        },
        "status": "ok",
        "laws": ["ASSIGNMENT != EXECUTION"],
    }


def test_ghot_requires_relatte_hold_then_preserves_offer_before_assignment(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    offer = fake_offer()

    with pytest.raises(DoorHouseConflict):
        store.record_ghot_offer(receipt["id"], offer)

    store.record_relatte_witness(receipt["id"], fake_relatte(receipt))
    state = store.record_ghot_offer(receipt["id"], offer)
    ghot_offer = next(
        w for w in state["external_witnesses"]
        if w["kind"].startswith("ghot_offer:")
    )
    assert ghot_offer["snapshot"]["offer_id"] == offer["offer_id"]
    assert "selected" not in ghot_offer["snapshot"]
    assert not any(w["kind"] == "ghot_execution" for w in state["external_witnesses"])


def test_ghot_execution_must_match_latest_offer_and_explicit_selected_body(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    receipt = crossed_receipt(store)
    store.record_relatte_witness(receipt["id"], fake_relatte(receipt))
    offer = fake_offer()
    store.record_ghot_offer(receipt["id"], offer)

    result = fake_execution(offer, "node-alpha")
    state = store.record_ghot_execution(
        receipt["id"], offer["offer_id"], "node-alpha", result
    )
    witness = next(
        w for w in state["external_witnesses"] if w["kind"] == "ghot_execution"
    )
    assert witness["snapshot"]["selected_node_id"] == "node-alpha"
    assert witness["snapshot"]["executor_node_id"] == "node-alpha"
    assert witness["snapshot"]["selection_source"] == "doorhouse-user-explicit"
    assert witness["snapshot"]["status"] == "ok"

    wrong = fake_execution(offer, "node-sleeping")
    with pytest.raises(DoorHouseConflict):
        store.record_ghot_execution(
            receipt["id"], offer["offer_id"], "node-sleeping", wrong
        )


def test_ghot_api_separates_discovery_from_assignment(monkeypatch, tmp_path):
    config = config_for(tmp_path)

    monkeypatch.setattr(
        app_module,
        "run_relatte_aperture",
        lambda receipt, state_dir, repos: fake_relatte(receipt),
    )
    monkeypatch.setattr(
        app_module,
        "discover_ghot_bodies",
        lambda receipt, relatte, repos: fake_offer(),
    )
    monkeypatch.setattr(
        app_module,
        "assign_ghot_body",
        lambda receipt, relatte, offer, selected, repos: fake_execution(offer, selected),
    )

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        state = client.post("/api/doorhouse/enter", json={}, headers=headers).json()
        letter = state["letters"][0]
        state = client.post(
            f"/api/doorhouse/letters/{letter['id']}/open",
            json={}, headers=headers,
        ).json()
        door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
        client.post(
            f"/api/doorhouse/doors/{door['id']}/select",
            json={"expected_world_version": 0},
            headers=headers,
        )
        state = client.post(
            f"/api/doorhouse/doors/{door['id']}/cross",
            json={"expected_world_version": 0},
            headers=headers,
        ).json()
        receipt = state["receipts"][0]

        before_relatte = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/offers",
            json={}, headers=headers,
        )
        assert before_relatte.status_code == 409

        assert client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/relatte",
            json={}, headers=headers,
        ).status_code == 200

        offered = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/offers",
            json={}, headers=headers,
        )
        assert offered.status_code == 200
        offered_state = offered.json()
        assert not any(
            w["kind"] == "ghot_execution"
            for w in offered_state["external_witnesses"]
        )

        assigned = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/assign",
            json={
                "expected_offer_id": fake_offer()["offer_id"],
                "selected_node_id": "node-alpha",
            },
            headers=headers,
        )
        assert assigned.status_code == 200
        execution = next(
            w for w in assigned.json()["external_witnesses"]
            if w["kind"] == "ghot_execution"
        )
        assert execution["snapshot"]["executor_node_id"] == "node-alpha"

        stale = client.post(
            f"/api/doorhouse/receipts/{receipt['id']}/ghot/assign",
            json={
                "expected_offer_id": "ghot-body-offer-v0:" + "0" * 64,
                "selected_node_id": "node-alpha",
            },
            headers=headers,
        )
        assert stale.status_code == 409
