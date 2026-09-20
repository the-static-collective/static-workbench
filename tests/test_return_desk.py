from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.return_desk import (
    CheckpointInput, NoteInput, ReturnConflict, ReturnDesk, SessionInput,
)


def make_config(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "roots"
    root.mkdir(exist_ok=True)
    (root / "original.txt").write_text("original stays original\n", encoding="utf-8")
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def test_return_shelf_survives_restart_preserves_original_and_chains_checkpoints(tmp_path):
    db = tmp_path / "state" / "return.sqlite3"
    shelf = ReturnDesk(db)
    note = shelf.save_note(NoteInput(
        title="Beginning", raw_text="Unedited RAW", margin="Possibly connected",
        carry="Remember what I said, not what the project claims",
    ))
    session = shelf.create_session(SessionInput(
        note_id=note["id"], expected_note_sha256=note["sha256"],
        project="some local project", intention="Make one change",
        next_step="Open a file", unresolved="Not verified",
    ))
    second = shelf.save_checkpoint(session["id"], CheckpointInput(
        expected_revision=1, changed="I opened the file",
        next_step="Run a bounded test", unresolved="Still not verified",
    ))
    reopened = ReturnDesk(db)
    found = reopened.get_session(session["id"])
    assert found is not None
    assert found["note"]["raw_text"] == "Unedited RAW"
    assert found["note"]["margin"] == "Possibly connected"
    assert found["note"]["carry"] == "Remember what I said, not what the project claims"
    assert found["note"]["sha256"] == note["sha256"]
    assert len(found["checkpoints"]) == 2
    assert found["checkpoints"][0]["next_step"] == "Open a file"
    assert found["checkpoints"][1]["changed"] == "I opened the file"
    assert found["checkpoints"][1]["previous_sha256"] == session["checkpoint"]["sha256"]
    assert found["checkpoints"][1]["sha256"] == second["sha256"]
    assert reopened.list_sessions()[0]["next_step"] == "Run a bounded test"


def test_return_shelf_rejects_unknown_note_stale_digest_and_stale_checkpoint(tmp_path):
    shelf = ReturnDesk(tmp_path / "return.sqlite3")
    note = shelf.save_note(NoteInput(title="Note", raw_text="RAW"))
    args = dict(project="", intention="Work", next_step="Open", unresolved="")
    try:
        shelf.create_session(SessionInput(
            note_id=999, expected_note_sha256=note["sha256"], **args,
        ))
        assert False, "unknown note accepted"
    except ReturnConflict:
        pass
    try:
        shelf.create_session(SessionInput(
            note_id=note["id"], expected_note_sha256="0" * 64, **args,
        ))
        assert False, "stale note accepted"
    except ReturnConflict:
        pass
    session = shelf.create_session(SessionInput(
        note_id=note["id"], expected_note_sha256=note["sha256"], **args,
    ))
    shelf.save_checkpoint(session["id"], CheckpointInput(
        expected_revision=1, next_step="New step",
    ))
    try:
        shelf.save_checkpoint(session["id"], CheckpointInput(
            expected_revision=1, next_step="Overwrite stale revision",
        ))
        assert False, "stale checkpoint accepted"
    except ReturnConflict:
        pass
    assert len(shelf.get_session(session["id"])["checkpoints"]) == 2


def test_return_api_guard_recovery_and_no_project_write(tmp_path):
    config = make_config(tmp_path)
    original = (config.roots[0].path / "original.txt").read_bytes()
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        denied = client.post("/api/return/notes", json={
            "title": "A", "raw_text": "B",
        })
        assert denied.status_code == 403
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"X-Workbench-Session": token}
        cross_origin = client.post("/api/return/notes", headers={
            **headers, "Origin": "http://elsewhere.local",
        }, json={"title": "A", "raw_text": "B"})
        assert cross_origin.status_code == 403
        note = client.post("/api/return/notes", headers=headers, json={
            "title": "First note", "raw_text": "Untouched",
            "margin": "Maybe", "carry": "Preserve this",
        })
        assert note.status_code == 200
        saved = note.json()
        assert client.get("/api/return/notes").json()["notes"][0]["sha256"] == saved["sha256"]
        bad_digest = client.post("/api/return/sessions", headers=headers, json={
            "note_id": saved["id"], "expected_note_sha256": "0" * 64,
            "intention": "Work", "next_step": "Begin",
        })
        assert bad_digest.status_code == 409
        opened = client.post("/api/return/sessions", headers=headers, json={
            "note_id": saved["id"], "expected_note_sha256": saved["sha256"],
            "project": "Only a label", "intention": "Test a return",
            "next_step": "Do the thing", "unresolved": "No project outcome yet",
        })
        assert opened.status_code == 200
        session_id = opened.json()["id"]
        update = client.post(
            f"/api/return/sessions/{session_id}/checkpoints", headers=headers,
            json={"expected_revision": 1, "changed": "Did one thing",
                  "next_step": "Check it", "unresolved": "Unverified"},
        )
        assert update.status_code == 200
        stale = client.post(
            f"/api/return/sessions/{session_id}/checkpoints", headers=headers,
            json={"expected_revision": 1, "next_step": "Stale"},
        )
        assert stale.status_code == 409
        assert client.get("/api/return/sessions/99999").status_code == 404
        assert client.get("/api/return/notes/99999").status_code == 404
        assert any(event["kind"] == "return.session.checkpointed"
                   for event in client.get("/api/events").json()["events"])
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        recovered = client.get(f"/api/return/sessions/{session_id}")
        assert recovered.status_code == 200
        body = recovered.json()
        assert body["note"]["raw_text"] == "Untouched"
        assert body["latest"]["next_step"] == "Check it"
        assert len(body["checkpoints"]) == 2
        assert client.get("/api/return/sessions").json()["sessions"][0]["revision"] == 2
        html = client.get("/").text
        js = client.get("/assets/return-desk.js").text
        assert 'data-view="return"' in html
        assert "/api/return/sessions/" in js
        assert "returnDeskLoad()" in client.get("/assets/app.js").text
    assert (config.roots[0].path / "original.txt").read_bytes() == original
