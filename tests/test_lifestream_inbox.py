import json
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.lifestream_001 import hash_object, source_bytes


UTC = "2026-09-20T15:00:00.000Z"
CLOCK = {"clockId": "clockwork.abstract-60", "reading": "17",
         "basis": "independent symbolic observation; not UTC or media time",
         "observedAtUtc": UTC, "evidenceRef": "fixture:clock-17"}


def setup(tmp_path: Path):
    root = tmp_path / "selected"
    root.mkdir()
    source = root / "recording.raw"
    source.write_bytes(b"synthetic selected media bytes\n")
    unsigned = {"schema": "static-lifestream.moment/v0.1", "eventId": "session:01",
                "source": source_bytes(source), "span": {"startMs": 100, "endMs": 500},
                "time": {"recordingStartedAtUtc": UTC, "observedAtUtc": UTC},
                "clockWitnesses": [CLOCK]}
    moment = {**unsigned, "momentId": hash_object(unsigned)}
    (root / "moment.json").write_text(json.dumps(moment), encoding="utf-8")
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
                             state_dir=tmp_path / "state", roots=(RootConfig("selected", root),))
    return config, source, moment


def headers(client):
    token = client.get("/api/bootstrap").json()["session_token"]
    return {"x-workbench-session": token, "origin": "http://127.0.0.1"}


def test_browser_import_review_export_and_source_revocation(tmp_path):
    config, source, moment = setup(tmp_path)
    payload = {"root_id": "selected", "manifest_path": "moment.json",
               "source_path": "recording.raw"}
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        page = client.get("/lifestream")
        assert page.status_code == 200 and "Living Moment Inbox" in page.text
        assert "lifestream.js" in page.text
        assert "Living Moment Inbox" in client.get("/").text
        assert client.post("/api/lifestream/moments/import", json=payload).status_code == 403
        imported = client.post("/api/lifestream/moments/import",
                               json=payload, headers=headers(client))
        assert imported.status_code == 200, imported.text
        mid = imported.json()["momentId"]
        assert mid == moment["momentId"]
        listed = client.get("/api/lifestream/moments").json()["moments"]
        assert len(listed) == 1 and listed[0]["clockWitnesses"][0]["reading"] == "17"
        assert listed[0]["status"] == "registered_not_currently_reverified"
        assert client.get("/api/lifestream/moments/" + mid).json()["status"] == "source_verified_no_effect"
        url = "/api/lifestream/moments/" + mid + "/returns"
        draft = {"kind": "lyric", "text": "The road is still becoming.\n",
                 "admitted_by": "human:operator", "reviewed": False}
        assert client.post(url, json=draft, headers=headers(client)).status_code == 409
        assert client.get(url).json()["returns"] == []
        draft["reviewed"] = True
        accepted = client.post(url, json=draft, headers=headers(client))
        assert accepted.status_code == 200, accepted.text
        assert accepted.json()["effects"] == {"broadcast": False, "stage": False, "publish": False}
        rid = accepted.json()["returnId"]
        exported = client.get(url + "/" + rid).json()
        assert exported["returnId"] == rid and exported["momentId"] == mid
        assert exported["artifact"]["text"] == draft["text"]
        source.write_bytes(b"changed after review")
        assert client.get(url + "/" + rid).status_code == 409
        assert client.get("/api/lifestream/moments/" + mid).status_code == 409
        assert client.post(url, json=draft, headers=headers(client)).status_code == 409
        assert len(client.get("/api/lifestream/moments").json()["moments"]) == 1


def test_explicit_configured_root_no_absolute_path_or_parent_escape(tmp_path):
    config, _, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        auth = headers(client)
        for bad in ("../recording.raw", "/etc/passwd"):
            req = {"root_id": "selected", "manifest_path": "moment.json", "source_path": bad}
            assert client.post("/api/lifestream/moments/import",
                               json=req, headers=auth).status_code == 409
        assert client.post("/api/lifestream/moments/import", json={
            "root_id": "unknown", "manifest_path": "moment.json", "source_path": "recording.raw"
        }, headers=auth).status_code == 409


def test_inbox_persists_after_restart_without_promoting_source_freshness(tmp_path):
    config, _, moment = setup(tmp_path)
    payload = {"root_id": "selected", "manifest_path": "moment.json", "source_path": "recording.raw"}
    for iteration in range(2):
        with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
            if iteration == 0:
                assert client.post("/api/lifestream/moments/import", json=payload,
                                   headers=headers(client)).status_code == 200
            else:
                entries = client.get("/api/lifestream/moments").json()["moments"]
                assert len(entries) == 1 and entries[0]["momentId"] == moment["momentId"]
                assert client.get("/api/lifestream/moments/" + moment["momentId"]).status_code == 200
