"""Attention Crossing: context, revision, consent and persistence."""
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import WorkbenchConfig, RootConfig


def make_config(tmp_path: Path):
    root = tmp_path / "root"
    root.mkdir(exist_ok=True)
    return WorkbenchConfig("127.0.0.1", 13700, tmp_path / "state", (RootConfig("static", root),))


def test_attention_none_some_all_and_restart(tmp_path):
    config = make_config(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session":token, "origin":"http://127.0.0.1"}
        target = {"kind":"artifact", "target_id":"static:workbench/song#1"}
        assert client.get("/api/attention", params=target).json()["current"] is None

        def declare(selected, none, revision):
            return client.post("/api/attention", headers=headers, json={
                **target, "dimensions":selected, "explicit_none":none,
                "expected_previous_id":revision})

        a = declare([], True, None)
        assert a.status_code == 200
        first = a.json()["current"]
        assert first["explicit_none"] is True and first["dimensions"] == []
        b = declare(["useful","joyful"], False, first["id"])
        assert b.status_code == 200
        second = b.json()["current"]
        assert second["dimensions"] == ["joyful","useful"]
        c = declare(["curiouser","useful","joyful"], False, second["id"])
        assert c.status_code == 200
        third = c.json()["current"]
        assert third["dimensions"] == ["joyful","useful","curiouser"]
        assert [v["id"] for v in c.json()["history"]] == [third["id"],second["id"],first["id"]]
        same = declare(["joyful","useful","curiouser"], False, third["id"])
        assert same.json()["current"]["id"] == third["id"]
        assert declare([], True, first["id"]).status_code == 409
        assert client.get("/api/attention", params={"kind":"artifact","target_id":"other"}).json()["current"] is None
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        reopened = client.get("/api/attention", params=target).json()
        assert [v["id"] for v in reopened["history"]] == [third["id"],second["id"],first["id"]]


def test_attention_security_and_nonmutation(tmp_path):
    config = make_config(tmp_path)
    source = config.roots[0].path / "source.txt"
    source.write_text("untouched", encoding="utf-8")
    payload = {"kind":"artifact","target_id":"static:source.txt",
               "dimensions":["joyful"],"expected_previous_id":None}
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        token = client.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session":token,"origin":"http://127.0.0.1"}
        assert client.post("/api/attention", json=payload).status_code == 403
        assert client.post("/api/attention", json=payload, headers={
            **headers, "origin":"http://evil.example"}).status_code == 403
        invalid = [
            {**payload,"dimensions":["joyful","joyful"]},
            {**payload,"dimensions":["unworthy"]},
            {**payload,"dimensions":["useful"],"explicit_none":True},
            {**payload,"target_id":"bad\nid"},
            {**payload,"unexpected":"no"},
        ]
        for item in invalid:
            assert client.post("/api/attention", json=item, headers=headers).status_code == 422
        assert client.get("/api/attention", params={
            "kind":"artifact","target_id":"static:source.txt"}).json()["history"] == []
        assert client.post("/api/attention", json=payload, headers=headers).status_code == 200
        assert client.get("/api/attention", params={
            "kind":"artifact","target_id":"static:source.txt"}, headers={
            "host":"evil.example"}).status_code == 400
    assert source.read_text(encoding="utf-8") == "untouched"


def test_attention_ui_wired(tmp_path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        script = client.get("/assets/attention.js")
        styles = client.get("/assets/attention.css")
        app = client.get("/assets/app.js").text
    assert 'src="/assets/attention.js"' in html
    assert script.status_code == styles.status_code == 200
    assert "HumanValueBar" in script.text
    assert "dataset.attentionId" in app and "dataset.attentionKind" in app


def test_attention_shelf_latest_and_dimension_filter(tmp_path):
    config = make_config(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        headers = {"x-workbench-session":client.get("/api/bootstrap").json()["session_token"]}
        def mark(target, dimensions, previous=None):
            return client.post("/api/attention", headers=headers, json={
                "kind":"artifact","target_id":target, "dimensions":dimensions,
                "expected_previous_id":previous})
        first = mark("song",["joyful"]).json()["current"]
        mark("song",["useful"],first["id"])
        mark("note",["curiouser"])
        feed = client.get("/api/attention/feed").json()
        assert [v["target_id"] for v in feed["entries"]] == ["note","song"]
        assert feed["order"] == "latest-declaration-first/not-a-ranking"
        assert [v["target_id"] for v in client.get(
            "/api/attention/feed?dimension=useful").json()["entries"]] == ["song"]
        assert client.get("/api/attention/feed?dimension=joyful").json()["entries"] == []
        assert client.get("/api/attention/feed?dimension=bogus").status_code == 422
        assert client.get("/api/attention/feed?limit=0").status_code == 422
        assert client.get("/api/attention/feed?limit=1").json()["entries"][0]["target_id"] == "note"


def test_attention_shelf_ui_wired(tmp_path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        assert 'data-view="attention"' in client.get("/").text
        assert "/api/attention/feed" in client.get("/assets/attention.js").text
        assert "window.HumanValueBar.openShelf()" in client.get("/assets/app.js").text


def test_attention_selected_passage_context_and_additive_migration(tmp_path):
    import sqlite3
    config = make_config(tmp_path)
    config.state_dir.mkdir(parents=True)
    path = config.state_dir / "attention.sqlite3"
    with sqlite3.connect(path) as db:
        db.execute("""CREATE TABLE attention(
            id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL,
            kind TEXT NOT NULL, target_id TEXT NOT NULL, dimensions_json TEXT NOT NULL,
            explicit_none INTEGER NOT NULL, previous_id INTEGER)""")
        db.execute("""INSERT INTO attention(created_at,kind,target_id,dimensions_json,explicit_none,previous_id)
            VALUES('2026-09-20T00:00:00+00:00','artifact','old','["joyful"]',0,NULL)""")
    context = {"scope":"selected-passage","source_kind":"source-hit",
               "source_id":"root:doc#L10","excerpt":"The house takes attendance.",
               "quote_sha256":"a"*64}
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        old = client.get("/api/attention",params={"kind":"artifact","target_id":"old"}).json()["current"]
        assert old["context"] is None
        headers = {"x-workbench-session":client.get("/api/bootstrap").json()["session_token"]}
        def mark(previous=None, ctxt=context, kind="selection", dimensions=None):
            return client.post("/api/attention", headers=headers, json={
                "kind":kind,"target_id":"b"*64,"dimensions":dimensions or ["curiouser"],
                "expected_previous_id":previous, "context":ctxt})
        assert mark(kind="artifact").status_code == 422
        first = mark()
        assert first.status_code == 200
        a = first.json()["current"]
        assert a["context"] == context
        second = mark(previous=a["id"],ctxt=None,dimensions=["joyful"])
        assert second.status_code == 200
        b = second.json()["current"]
        assert b["context"] == context
        assert mark(previous=b["id"],ctxt={**context,"excerpt":"other"}).status_code == 409
        feed = client.get("/api/attention/feed").json()
        assert feed["entries"][0]["context"] == context
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get("/api/attention",params={
            "kind":"selection","target_id":"b"*64}).json()["current"]["context"] == context


def test_attention_selected_passage_ui_is_deliberate(tmp_path):
    with TestClient(create_app(make_config(tmp_path)),base_url="http://127.0.0.1") as client:
        js = client.get("/assets/attention.js").text
        assert "Mark selected passage" in js
        assert "crypto.subtle.digest" in js
        assert "source_kind" in js
