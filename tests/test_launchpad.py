from pathlib import Path
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.launchpad import first_run_map


def test_read_only_launchpad_exposes_no_inferred_boot_or_privilege(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    config = WorkbenchConfig("127.0.0.1", 13700, tmp_path / "state",
                            (RootConfig("static", root),))
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        result = client.get("/api/launchpad")
        assert result.status_code == 200
        body = result.json()
        assert body == client.get("/api/launchpad").json()
        assert client.post("/api/launchpad", json={"command":"sudo mkfs"}).status_code == 405
        html = client.get("/").text
        js = client.get("/assets/app.js").text
        view = client.get("/assets/launchpad.js").text
    assert body["authority"] == "none" and body["automatic_actions"] == []
    assert [gate["state"] for gate in body["gates"]] == [
        "observed_in_this_process", "not_observed", "not_observed",
        "not_observed", "not_observed"]
    assert "data-view=\"launchpad\"" in html
    assert "renderLaunchpad" in js and "/api/launchpad" in view
    assert "textContent" not in view or "el('pre', 'code-preview', gate.command)" in view
    assert not list((tmp_path / "state").glob("*launchpad*"))


def test_manifest_source_not_inferred_from_running_page():
    map_ = first_run_map()
    assert map_["gates"][0]["state"] == "observed_in_this_process"
    assert "not independently attested" in map_["gates"][0]["details"]
    assert map_["gates"][-1]["command"] is None
