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


def test_workbench_links_to_native_webz_cockpit(tmp_path):
    with make_client(tmp_path) as client:
        assert 'href="/webz"' in client.get("/").text


def test_webz_cockpit_resolve_and_enter_are_separate(tmp_path):
    with make_client(tmp_path) as client:
        html = client.get("/webz").text
        script = client.get("/assets/webz.js")
        style = client.get("/assets/webz.css")
        assert 'id="webz-address"' in html
        assert 'id="webz-resolve"' in html
        assert 'id="webz-enter"' in html
        assert 'id="webz-result"' in html
        assert 'type="module" src="/assets/webz.js"' in html
        assert script.status_code == 200
        assert style.status_code == 200
        assert "prefers-reduced-motion" in style.text
        assert "textContent" in script.text
        assert "innerHTML" not in script.text
        assert "eval(" not in script.text
        assert "/api/webz/resolve" in script.text
        assert "webz::" in html


def test_native_webz_cockpit_never_executes_on_resolve(tmp_path):
    with make_client(tmp_path) as client:
        script = client.get("/assets/webz.js").text
        assert "addEventListener" in script
        assert "webz-enter" in script
        assert "/webz/world/sanctuary" in script
        assert "/webz/world/orchard" in script
        assert "window.location" in script
        assert "new Function(" not in script


def test_two_worlds_expose_independent_portal_controls(tmp_path):
    with make_client(tmp_path) as client:
        sanctuary = client.get("/webz/world/sanctuary").text
        orchard = client.get("/webz/world/orchard").text
        assert 'data-webz-world="sanctuary"' in sanctuary
        assert 'data-webz-world="orchard"' in orchard
        assert 'id="webz-inspect"' in sanctuary
        assert 'id="webz-cross"' in sanctuary
        assert 'id="webz-remain"' in sanctuary
        assert 'id="webz-return"' in orchard
        assert 'id="webz-world-status"' in sanctuary
        assert 'type="module" src="/assets/webz-world.js"' in sanctuary
        assert 'type="module" src="/assets/webz-world.js"' in orchard
        assert "carry: NONE" in sanctuary and "carry: NONE" in orchard
        assert "Psychedelic Punk Sanctuary" in sanctuary
        assert "The Orchard / 022100" in orchard


def test_world_portal_script_requires_inspection_then_explicit_cross(tmp_path):
    with make_client(tmp_path) as client:
        script = client.get("/assets/webz-world.js")
        assert script.status_code == 200
        assert "webz-inspect" in script.text
        assert "webz-cross" in script.text
        assert "webz-remain" in script.text
        assert "webz-return" in script.text
        assert "/api/webz/worlds/" in script.text
        assert "/api/webz/resolve" in script.text
        assert "window.location.assign" in script.text
        assert "textContent" in script.text
        assert "innerHTML" not in script.text
        assert "eval(" not in script.text


def test_webz_worlds_expose_explicit_opt_in_and_export_erase(tmp_path):
    with make_client(tmp_path) as client:
        for route in ("/webz/world/sanctuary", "/webz/world/orchard"):
            html = client.get(route).text
            assert 'id="webz-begin-recording"' in html
            assert 'id="webz-pause-recording"' in html
            assert 'id="webz-export-voyage"' in html
            assert 'id="webz-erase-voyage"' in html
            assert 'id="webz-recording-status"' in html
            assert "recording is off" in html.lower()


def test_world_portal_wires_optional_storage_after_trusted_resolution(tmp_path):
    with make_client(tmp_path) as client:
        world_script = client.get("/assets/webz-world.js").text
        assert './webz-storage.mjs' in world_script
        assert "confirmArrival(" in world_script
        assert "recordDeparture(" in world_script
        assert "beginRecording(" in world_script
        assert "exportVoyage(" in world_script
        assert "eraseVoyage(" in world_script
        assert "window.location.assign" in world_script
        assert "innerHTML" not in world_script
        cockpit = client.get("/webz").text
        assert 'id="webz-export-voyage"' in cockpit
        assert 'id="webz-erase-voyage"' in cockpit
        assert 'id="webz-recording-status"' in cockpit
