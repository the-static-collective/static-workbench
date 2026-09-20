"""MIRROR/ATTENTION: selected fixture identity, local storage, and authority split."""
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def make_config(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),))


def test_selected_mirror_demo_declares_without_mutating_source(tmp_path):
    config=make_config(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html=client.get("/").text
        mirror=client.get("/assets/mirror.js").text
        attention=client.get("/assets/attention.js").text
        assert '/assets/attention.js' in html
        assert '/assets/attention.css' in html
        assert "window.HumanValueBar.mount(inspector" in mirror
        assert "mirror-001:demo-card" in mirror
        assert "window.HumanValueBar" in attention
        source_before=client.get("/api/mirror/state").json()["source_sha256"]
        token=client.get("/api/bootstrap").json()["session_token"]
        payload={"kind":"mirror-fixture","target_id":"mirror-001:demo-card",
            "dimensions":["curiouser","joyful"],"explicit_none":False,
            "expected_previous_id":None}
        denied=client.post("/api/attention",json=payload)
        assert denied.status_code==403
        result=client.post("/api/attention",json=payload,
            headers={"x-workbench-session":token,"origin":"http://127.0.0.1"})
        assert result.status_code==200
        first=result.json()["current"]
        assert first["dimensions"]==["joyful","curiouser"]
        assert first["authority"]=="human-declared/local-only"
        assert client.get("/api/mirror/state").json()["source_sha256"]==source_before
        assert client.get("/api/events").json()["events"]
    with TestClient(create_app(config),base_url="http://127.0.0.1") as client:
        current=client.get("/api/attention",params={
            "kind":"mirror-fixture","target_id":"mirror-001:demo-card"}).json()["current"]
        assert current["id"]==first["id"]
        assert client.get("/api/mirror/state").json()["source_sha256"]==source_before
