"""WEBZ-NATIVE-001: Workbench routes must not enlarge project authority."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def make_client(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )
    return TestClient(create_app(config), base_url="http://127.0.0.1")


def test_webz_pages_are_separate_and_old_routes_remain(tmp_path):
    with make_client(tmp_path) as client:
        for route in ("/", "/arg", "/arg/world", "/doorhouse", "/webz"):
            assert client.get(route).status_code == 200
        sanctuary = client.get("/webz/world/sanctuary")
        orchard = client.get("/webz/world/orchard")
        assert sanctuary.status_code == 200
        assert orchard.status_code == 200
        assert "Psychedelic Punk Sanctuary" in sanctuary.text
        assert "The Orchard / 022100" in orchard.text
        assert sanctuary.text != orchard.text


def test_resolve_api_is_read_only_and_tagged(tmp_path):
    with make_client(tmp_path) as client:
        before = client.get("/api/events").json()
        home = client.get("/api/webz/resolve", params={
            "address": "webz::static/sanctuary",
        })
        assert home.status_code == 200
        assert home.json()["world_id"] == "webz:the-static-collective/sanctuary"
        assert home.json()["status"] == "resolved"
        assert home.json()["entry_route"] == "/webz/world/sanctuary"
        assert "location" not in home.headers
        assert client.get("/api/webz/resolve", params={"address": "webz::static/unknown"}).json() == {
            "status": "unresolved", "typed_address": "webz::static/unknown",
        }
        invalid = client.get("/api/webz/resolve", params={"address": "webz::http://evil.test"})
        assert invalid.status_code == 200
        assert invalid.json()["status"] == "invalid"
        assert "entry_route" not in invalid.json()
        assert client.get("/api/events").json() == before


def test_world_api_uses_own_manifest_and_refuses_unknown_slug(tmp_path):
    with make_client(tmp_path) as client:
        a = client.get("/api/webz/worlds/sanctuary")
        b = client.get("/api/webz/worlds/orchard")
        assert a.status_code == 200 and b.status_code == 200
        assert a.json()["world_id"] != b.json()["world_id"]
        assert a.json()["doors"][0]["to_address"] == "webz::static/orchard/022100"
        assert b.json()["doors"][0]["to_address"] == "webz::static/sanctuary"
        assert client.get("/api/webz/worlds/elsewhere").status_code == 404
        assert client.get("/webz/world/elsewhere").status_code == 404


def test_corrupt_webz_registry_does_not_break_workbench(tmp_path, monkeypatch):
    from static_workbench.webz_native import WebzRegistryError

    def broken(*args, **kwargs):
        raise WebzRegistryError("corrupt fixture")
    monkeypatch.setattr("static_workbench.app.load_registry", broken, raising=False)
    with make_client(tmp_path) as client:
        response = client.get("/api/webz/resolve", params={"address": "webz::static/sanctuary"})
        assert response.status_code == 503
        assert "unavailable" in response.json()["detail"].lower()
        assert client.get("/").status_code == 200


def test_webz_uses_only_local_read_routes_and_preserves_host_guard(tmp_path):
    with make_client(tmp_path) as client:
        assert client.get("/api/webz/resolve", params={
            "address": "webz::static/sanctuary",
        }, headers={"host": "example.test"}).status_code == 400
        assert client.post("/api/webz/resolve", json={"address": "webz::static/sanctuary"}).status_code == 405
        assert client.post("/api/webz/worlds/sanctuary", json={}).status_code == 405
