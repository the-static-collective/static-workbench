"""MIRROR-001: exact-source proposal, explicit apply, and negative authority checks."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.mirror import MirrorStore, MirrorConflict, css_for, digest


def make_client(tmp_path: Path):
    root = tmp_path / "sources"
    root.mkdir()
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("test", root),),
    )
    client = TestClient(create_app(config), base_url="http://127.0.0.1")
    return client, root, config


def request_payload(state, width=420, accent="#aabbcc"):
    return {
        "expected_source_sha256": state["source_sha256"],
        "card_width": width, "accent": accent,
    }


def authorized(client):
    token = client.get("/api/bootstrap").json()["session_token"]
    return {"x-workbench-session": token, "origin": "http://127.0.0.1"}


def test_select_preview_apply_reload_round_trip_and_repo_nonmutation(tmp_path):
    client, root, config = make_client(tmp_path)
    external = root / "other-app" / "style.css"
    external.parent.mkdir()
    external.write_text("/* belongs to another project */", encoding="utf-8")
    with client:
        initial = client.get("/api/mirror/state")
        assert initial.status_code == 200
        state = initial.json()
        assert state["source_kind"] == "workbench_owned_demo_css"
        assert state["source_sha256"] == digest(css_for(360, "#6a9dd4"))
        demo = client.get("/api/mirror/demo")
        assert demo.status_code == 200
        assert 'data-mirror-target="demo-card"' in demo.text
        assert css_for(360, "#6a9dd4") in demo.text
        assert "default-src 'none'" in demo.headers["content-security-policy"]
        patch = request_payload(state)
        headers = authorized(client)
        assert not (config.state_dir / "mirror-001" / "demo.css").exists()
        preview = client.post("/api/mirror/preview", headers=headers, json=patch)
        assert preview.status_code == 200, preview.text
        proposal = preview.json()
        assert proposal["changed"] and "--- mirror-001/demo.css" in proposal["diff"]
        assert proposal["after_sha256"] == digest(css_for(420, "#aabbcc"))
        assert not (config.state_dir / "mirror-001" / "demo.css").exists()
        applied = client.post(
            "/api/mirror/apply", headers=headers, json=patch,
            params={"expected_after_sha256": proposal["after_sha256"]},
        )
        assert applied.status_code == 200, applied.text
        assert applied.json()["applied"] is True
        assert (config.state_dir / "mirror-001" / "demo.css").read_text() == css_for(420, "#aabbcc")
        assert external.read_text() == "/* belongs to another project */"
        assert css_for(420, "#aabbcc") in client.get("/api/mirror/demo").text
        assert client.get("/api/mirror/state").json()["source_sha256"] == proposal["after_sha256"]
        assert any(item["kind"] == "mirror.demo_css.applied" for item in client.get("/api/events").json()["events"])


def test_denied_origin_token_and_stale_or_unreviewed_patch(tmp_path):
    client, _, _ = make_client(tmp_path)
    with client:
        state = client.get("/api/mirror/state").json()
        patch = request_payload(state)
        assert client.post("/api/mirror/preview", json=patch).status_code == 403
        headers = authorized(client)
        cross = {**headers, "origin": "https://attacker.example"}
        assert client.post("/api/mirror/preview", headers=cross, json=patch).status_code == 403
        proposal = client.post("/api/mirror/preview", headers=headers, json=patch).json()
        assert client.post("/api/mirror/apply", headers=headers, json=patch,
            params={"expected_after_sha256": "0" * 64}).status_code == 409
        applied = client.post("/api/mirror/apply", headers=headers, json=patch,
            params={"expected_after_sha256": proposal["after_sha256"]})
        assert applied.status_code == 200
        assert client.post("/api/mirror/preview", headers=headers, json=patch).status_code == 409
        assert client.post("/api/mirror/apply", headers=headers, json=patch,
            params={"expected_after_sha256": proposal["after_sha256"]}).status_code == 409
        bad = {**request_payload(client.get("/api/mirror/state").json()), "file_path": "../other"}
        assert client.post("/api/mirror/preview", headers=headers, json=bad).status_code == 422
        assert client.post("/api/mirror/preview", headers=headers, json={
            **request_payload(client.get("/api/mirror/state").json()), "card_width": 999,
        }).status_code == 422


def test_refuse_symlink_or_tampered_css_without_overwriting(tmp_path):
    store = MirrorStore(tmp_path / "state")
    store.directory.mkdir(parents=True)
    target = tmp_path / "outside.css"
    target.write_text("outside", encoding="utf-8")
    store.source_path.symlink_to(target)
    try:
        store.state()
        assert False, "symlink should be rejected"
    except MirrorConflict:
        pass
    assert target.read_text() == "outside"
    store.source_path.unlink()
    store.source_path.write_text("body {display:none}", encoding="utf-8")
    try:
        store.state()
        assert False, "tampered CSS must be refused"
    except MirrorConflict:
        pass


def test_ui_surface_wired_to_house(tmp_path):
    client, _, _ = make_client(tmp_path)
    with client:
        html = client.get("/").text
        js = client.get("/assets/app.js").text
        mirror_js = client.get("/assets/mirror.js")
        assert 'data-view="mirror"' in html
        assert '/assets/mirror.js' in html
        assert 'renderMirror().catch(showError)' in js
        assert mirror_js.status_code == 200
        assert '/api/mirror/preview' in mirror_js.text
        assert '/api/mirror/apply' in mirror_js.text
