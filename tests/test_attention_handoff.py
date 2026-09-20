"""PATH-ALL-HOME-001 — reviewed source-preserving local imports."""
import hashlib
import json
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def settings(tmp_path):
    root = tmp_path / "source"
    root.mkdir(exist_ok=True)
    (root / "artifact.txt").write_text("owner's unmodified original", encoding="utf-8")
    return WorkbenchConfig("127.0.0.1", 13700, tmp_path / "state", (RootConfig("source", root),))


def envelope(app="goatnote", record="rec-001", target="note-01", dims=None, none=False):
    return {
        "schema": "attention-crossing.handoff/v0.1",
        "source_app": app,
        "source_record_id": record,
        "source_target_id": target,
        "source_recorded_at": "2026-09-20T16:25:00.000Z",
        "source_previous_id": None,
        "source_locator": "note/note-01/version/version-01",
        "label": "Human-marked passage",
        "dimensions": ["curiouser"] if dims is None else dims,
        "explicit_none": none,
        "evidence": "source-export/self-reported"
    }


def test_preview_save_dedupe_divergence_and_restart(tmp_path):
    config = settings(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        auth = {"x-workbench-session": token, "origin": "http://127.0.0.1"}
        raw = json.dumps(envelope(), ensure_ascii=False)
        request = {"raw_json": raw}
        assert client.post("/api/attention/import/preview", json=request).status_code == 403
        assert client.post("/api/attention/import/preview", json=request,
            headers={**auth, "origin":"https://evil.example"}).status_code == 403
        preview = client.post("/api/attention/import/preview", json=request, headers=auth)
        assert preview.status_code == 200
        digest = hashlib.sha256(raw.encode()).hexdigest()
        assert preview.json()["raw_sha256"] == digest
        assert preview.json()["notice"].startswith("source-export")
        bad = client.post("/api/attention/import/save", headers=auth,
            json={**request, "expected_sha256":"0"*64})
        assert bad.status_code == 409
        assert client.get("/api/attention/imports").json()["entries"] == []
        first = client.post("/api/attention/import/save", headers=auth,
            json={**request, "expected_sha256":digest})
        assert first.status_code == 200 and first.json()["duplicate"] is False
        receipt = first.json()["import"]
        assert receipt["source_record_id"] == "rec-001"
        assert receipt["authority"] == "imported-self-report/not-independent-witness"
        assert client.post("/api/attention/import/save", headers=auth,
            json={**request,"expected_sha256":digest}).json()["duplicate"] is True
        conflicting = json.dumps({**envelope(),"dimensions":["useful"]})
        conflict_sha = hashlib.sha256(conflicting.encode()).hexdigest()
        assert client.post("/api/attention/import/save", headers=auth,json={
            "raw_json":conflicting,"expected_sha256":conflict_sha}).status_code == 409
        second = json.dumps(envelope(app="static-live",record="rec-002",target="session:mark",
            dims=[],none=True))
        second_sha = hashlib.sha256(second.encode()).hexdigest()
        other = client.post("/api/attention/import/save", headers=auth,json={
            "raw_json":second,"expected_sha256":second_sha})
        assert other.status_code == 200
        feed = client.get("/api/attention/imports").json()["entries"]
        assert [item["source_app"] for item in feed] == ["static-live","goatnote"]
        assert len(client.get("/api/attention/imports?dimension=curiouser").json()["entries"]) == 1
        assert client.get("/api/attention/imports?dimension=joyful").json()["entries"] == []
        assert client.get("/api/attention/imports?dimension=unknown").status_code == 422
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert len(client.get("/api/attention/imports").json()["entries"]) == 2
    assert (config.roots[0].path / "artifact.txt").read_text() == "owner's unmodified original"


def test_handoff_validation_and_ui(tmp_path):
    config = settings(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        auth = {"x-workbench-session":client.get("/api/bootstrap").json()["session_token"]}
        for altered in [
            {**envelope(),"source_app":"invented"},
            {**envelope(),"dimensions":["joyful","joyful"]},
            {**envelope(),"explicit_none":True},
            {**envelope(),"source_recorded_at":"2026-09-20"},
            {**envelope(),"source_target_id":"source\nid"},
            {**envelope(),"source_record_id":" "},
            {**envelope(),"unexpected":"false identity"},
        ]:
            assert client.post("/api/attention/import/preview",headers=auth,json={
                "raw_json":json.dumps(altered)}).status_code == 422
        assert client.post("/api/attention/import/preview",headers=auth,json={
            "raw_json":"x"*8193}).status_code == 422
        assert client.post("/api/attention/import/preview",headers=auth,json={
            "raw_json":"not json"}).status_code == 422
        js=client.get("/assets/attention.js").text
        assert "/api/attention/import/preview" in js
        assert "/api/attention/import/save" in js
        assert "/api/attention/imports?" in js
        assert "Source-owned" not in js or "source-owned" in js
