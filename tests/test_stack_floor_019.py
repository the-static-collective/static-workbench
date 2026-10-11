from pathlib import Path
from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def config(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def test_living_lego_floor_is_linked_locally_but_does_not_create_an_execution_api(tmp_path):
    with TestClient(create_app(config(tmp_path)), base_url="http://127.0.0.1") as client:
        index = client.get("/")
        home_js = client.get("/assets/app.js")
        page = client.get("/stack-floor")
        css = client.get("/assets/stack-floor.css")
        core = client.get("/assets/stack-floor-core.mjs")
        ui = client.get("/assets/stack-floor-ui.mjs")
        for response in (index, home_js, page, css, core, ui):
            assert response.status_code == 200
        assert 'href="/stack-floor"' in index.text
        assert "stackDoor.href = '/stack-floor'" in home_js.text
        assert 'id="sockets"' in page.text
        assert 'id="tray"' in page.text
        assert 'id="summary"' in page.text
        assert 'id="native"' in page.text
        assert 'id="consent"' in page.text
        assert 'id="trial"' in page.text
        assert 'id="export"' in page.text
        assert "connect-src 'self'" in page.text
        assert "runLocalTrial" in ui.text
        assert "signature_verification:'NOT_REVERIFIED_IN_BROWSER'" in core.text
        assert "WEBCRYPTO_SHA256_ONLY" in core.text
        assert client.post("/stack-floor", json={"run": True}).status_code == 405
        assert client.post("/api/stack-floor", json={"execute": True}).status_code == 404
        assert client.get("/stack-floor", headers={"host": "evil.example"}).status_code == 400
