"""STATIC-ARG-001: opt-in, immutable local compositions and fixed doors."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.first_door import FirstDoor, ArgConflict, ArgMissing


def config_for(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )


def test_first_door_store_is_opt_in_append_only_and_restartable(tmp_path):
    path = tmp_path / "state" / "arg.sqlite3"
    store = FirstDoor(path)
    assert store.state()["enrolled"] is False
    try:
        store.seed("No consent", "Do not create")
        assert False, "enrollment must be explicit"
    except ArgConflict:
        pass
    assert store.state()["artifacts"] == []
    store.enter()
    a = store.seed("A", "The house is open.")
    b = store.seed("B", "A card can be a game.")
    c = store.seed("C", "The third seed is for the world.")
    machine = store.machine("House machine", a["id"], b["id"])
    assert [x["id"] for x in machine["snapshot"]["inputs"]] == [a["id"], b["id"]]
    assert machine["snapshot"]["inputs"][0]["sha256"] == a["sha256"]
    assert machine["snapshot"]["prompt"] == "The house is open.\n--- COMPOSE WITH ---\nA card can be a game."
    world = store.world("Doorway Orchard", machine["id"], c["id"], "On a turn, choose a door or rest.")
    assert world["snapshot"]["inputs"][0]["sha256"] == machine["sha256"]
    assert world["snapshot"]["play_rule"] == "On a turn, choose a door or rest."
    assert {door["id"] for door in world["snapshot"]["doors"]} == {"house", "maddloop", "machines"}
    event = store.cross(world["id"], "machines")
    assert event["destination"] == "/machines"
    assert event["source_sha256"] == world["sha256"]
    restarted = FirstDoor(path).state()
    assert restarted["enrolled"] is True
    assert [x["id"] for x in restarted["artifacts"]] == [
        world["id"], machine["id"], c["id"], b["id"], a["id"],
    ]
    assert restarted["artifacts"][-1]["sha256"] == a["sha256"]
    assert restarted["encounters"][0]["id"] == event["id"]
    assert "not project execution" in restarted["nonclaims"][0]


def test_first_door_refuses_reused_sources_nonworld_crossing_and_invented_door(tmp_path):
    store = FirstDoor(tmp_path / "arg.sqlite3")
    store.enter()
    a = store.seed("A", "A")
    b = store.seed("B", "B")
    m = store.machine("M", a["id"], b["id"])
    for fn in (
        lambda: store.machine("Duplicate", a["id"], a["id"]),
        lambda: store.world("Reused", m["id"], a["id"], "A rule"),
        lambda: store.world("Wrong", a["id"], b["id"], "A rule"),
        lambda: store.cross(m["id"], "house"),
        lambda: store.cross(m["id"], "https://outside.invalid"),
    ):
        try:
            fn()
            assert False, "invalid composition or crossing must refuse"
        except ArgConflict:
            pass
    try:
        store.cross("0" * 32, "house")
        assert False, "unknown artifact must refuse"
    except ArgMissing:
        pass
    assert len(store.state()["artifacts"]) == 3
    assert store.state()["encounters"] == []


def test_arg_ui_is_linked_and_local_api_requires_explicit_session(tmp_path):
    config = config_for(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        index = client.get("/")
        page = client.get("/arg")
        script = client.get("/assets/arg.js")
        assert 'href="/arg"' in index.text
        assert page.status_code == 200 and "THE FIRST DOOR" in page.text
        assert "optional, openly fictional" in page.text
        assert script.status_code == 200 and "/api/arg/cross" in script.text
        theme = client.get("/assets/arg-theme.css")
        assert theme.status_code == 200
        assert "@media (max-width:650px)" in theme.text
        assert "prefers-reduced-motion" in theme.text
        assert 'href="/assets/arg-theme.css"' in page.text
        assert 'aria-label="Your creative journey"' in page.text
        assert 'id="arg-next-button"' in page.text
        assert 'id="arg-collection"' in page.text
        assert 'aria-label="Filter artifacts"' in page.text
        assert "updateJourney" in script.text and "renderArtifacts" in script.text
        assert "focusStage" in script.text

        assert "textContent" in script.text and "innerHTML" not in script.text
        assert client.get("/api/arg/state").json()["enrolled"] is False
        seed_data = {"title": "First", "text": "One small actual sketch"}
        assert client.post("/api/arg/seeds", json=seed_data).status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        header = {"x-workbench-session": token}
        assert client.post("/api/arg/seeds", json=seed_data, headers=header).status_code == 409
        assert client.post("/api/arg/enter", json={}, headers={
            **header, "origin": "http://outside.invalid",
        }).status_code == 403
        assert client.post("/api/arg/enter", json={}, headers=header).status_code == 200
        a = client.post("/api/arg/seeds", json=seed_data, headers=header).json()
        b = client.post("/api/arg/seeds", json={"title": "Second", "text": "Second source"}, headers=header).json()
        c = client.post("/api/arg/seeds", json={"title": "Third", "text": "A world rule source"}, headers=header).json()
        assert a["kind"] == "seed"
        assert client.post("/api/arg/machines", json={
            "title": "Cannot reuse", "first_id": a["id"], "second_id": a["id"],
        }, headers=header).status_code == 409
        m = client.post("/api/arg/machines", json={
            "title": "Composed", "first_id": a["id"], "second_id": b["id"],
        }, headers=header)
        assert m.status_code == 200
        world = client.post("/api/arg/worlds", json={
            "title": "Orchard", "machine_id": m.json()["id"],
            "seed_id": c["id"], "rule": "Choose a door or stop.",
        }, headers=header).json()
        assert client.post("/api/arg/cross", json={
            "world_id": a["id"], "door": "house",
        }, headers=header).status_code == 409
        crossed = client.post("/api/arg/cross", json={
            "world_id": world["id"], "door": "maddloop",
        }, headers=header)
        assert crossed.status_code == 200
        assert crossed.json()["destination"] == "/maddloop"
        assert client.get("/api/arg/state").json()["encounters"][0]["source_sha256"] == world["sha256"]

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        again = client.get("/api/arg/state").json()
        assert again["enrolled"] and len(again["artifacts"]) == 5
        assert len(again["encounters"]) == 1
        assert client.get("/machines").status_code == 200
