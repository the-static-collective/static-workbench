from pathlib import Path

from fastapi.testclient import TestClient

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


def test_complete_loop_keeps_selection_crossing_and_adapter_truth_separate(tmp_path):
    store = DoorHouse(tmp_path / "doorhouse.sqlite3")
    assert store.state()["entered"] is False
    state = store.enter()
    assert state["world_version"] == 0
    letter = state["letters"][0]
    assert letter["body"] is None
    door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])

    try:
        store.select(door["id"], 0)
        assert False, "sealed letters cannot select doors"
    except DoorHouseConflict:
        pass

    state = store.open_letter(letter["id"])
    state = store.select(door["id"], 0)
    selected = next(d for d in state["doors"] if d["id"] == door["id"])
    assert selected["selected_at"] and selected["crossed_at"] is None
    assert state["receipts"] == []

    state = store.cross(door["id"], 0)
    assert state["world_version"] == 1
    receipt = state["receipts"][0]
    assert receipt["snapshot"]["execution"]["mode"] == "REAL_LOCAL_TRANSFORM"
    assert receipt["snapshot"]["adapters"]["relatte"] == "AVAILABLE_AFTER_LOCAL_CROSSING"
    assert len(receipt["snapshot"]["artifact_sha256"]) == 64
    assert receipt["snapshot"]["adapters"]["ghot"] == "LOCAL_BODY_ONLY_NOT_GHOT_ASSIGNMENT"
    assert receipt["world_before"] == 0 and receipt["world_after"] == 1
    assert any(letter["parent_crossing_id"] == receipt["id"] for letter in state["letters"])
    sibling = next(
        d for d in state["doors"]
        if d["letter_id"] == letter["id"] and d["id"] != door["id"]
    )
    try:
        store.select(sibling["id"], 1)
        assert False, "unchosen sibling doors must become historical proposals"
    except DoorHouseConflict:
        pass


def test_doorhouse_route_and_writes_are_session_guarded(tmp_path):
    with TestClient(create_app(config_for(tmp_path)), base_url="http://127.0.0.1") as client:
        assert client.get("/doorhouse").status_code == 200
        assert client.get("/api/doorhouse/state").json()["entered"] is False
        assert client.post("/api/doorhouse/enter", json={}).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        state = client.post("/api/doorhouse/enter", json={}, headers=headers).json()
        letter = state["letters"][0]
        state = client.post(
            f"/api/doorhouse/letters/{letter['id']}/open", json={}, headers=headers
        ).json()
        door = next(d for d in state["doors"] if d["letter_id"] == letter["id"])
        selected = client.post(
            f"/api/doorhouse/doors/{door['id']}/select",
            json={"expected_world_version": 0}, headers=headers,
        )
        assert selected.status_code == 200
        crossed = client.post(
            f"/api/doorhouse/doors/{door['id']}/cross",
            json={"expected_world_version": 0}, headers=headers,
        )
        assert crossed.status_code == 200
        assert crossed.json()["world_version"] == 1
