from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def make_config(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def test_root_serves_three_region_workbench_shell(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        response = client.get("/")

    assert response.status_code == 200
    assert "STATIC / WORKBENCH" in response.text
    assert 'data-region="navigator"' in response.text
    assert 'data-region="workspace"' in response.text
    assert 'data-region="witness"' in response.text


def test_static_assets_are_served(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        css = client.get("/assets/styles.css")
        js = client.get("/assets/app.js")

    assert css.status_code == 200
    assert "--bg" in css.text
    assert js.status_code == 200
    assert "/api/bootstrap" in js.text
    assert "/api/events" in js.text


def test_humanterminal_surface_and_aperture_endpoints_are_wired(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        js = client.get("/assets/app.js").text

    assert "HumanTerminal" in html
    assert 'data-view="humanterminal"' in html
    assert 'id="humanterminal-input"' in html
    assert 'id="humanterminal-context"' in html
    assert "/api/aperture/analyze" in js
    assert "/api/aperture/history" in js
    assert "possible meaning != intended meaning" in js


def test_house_is_default_habitat_surface(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        js = client.get("/assets/app.js").text

    assert 'data-view="house"' in html
    assert "local habitat / provenance desk" in html
    assert "/api/house" in js
    assert "house.laws" in js
    assert "The house is awake." in js


def test_living_main_is_navigable_and_serves_its_inspection_ui(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        ui = client.get("/assets/living-main.js")
        styles = client.get("/assets/styles.css").text

    assert 'data-view="living-main"' in html
    assert 'src="/assets/living-main.js"' in html
    assert ui.status_code == 200
    assert "/api/living-main/preview" in ui.text
    assert "expected_sha: repo.full_head" in ui.text
    assert "NOT EXECUTED" in ui.text
    assert "INTEGRATION NOT TESTED" in ui.text
    assert "livingMainDesk.selected" in ui.text
    assert ".lm-layout" in styles
