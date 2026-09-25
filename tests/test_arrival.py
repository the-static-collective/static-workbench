from __future__ import annotations

import hashlib
import json
import sqlite3
from pathlib import Path

import pytest

from static_workbench.arrival import creator_reentry, diagnose, load_manifest
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.repos import RepoStatus


def _config(tmp_path: Path) -> WorkbenchConfig:
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path,
        roots=(RootConfig("static", tmp_path / "repos"),),
    )


def _repo(name: str, relative: str = "one", dirty: bool = False) -> RepoStatus:
    return RepoStatus(
        name=name, path=f"/tmp/{relative}/{name}", branch="main", detached=False,
        head="0123456", dirty=dirty, ahead=None, behind=None,
        root_id="static", relative_path=f"{relative}/{name}",
    )


def _canonical(value: object) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()


def _fixture_shelf(tmp_path: Path, body: str = "Song begins") -> int:
    """Small standalone SQLite fixture; production owner remains CreatorShelf."""
    db_path = tmp_path / "creator.sqlite3"
    sources = [{"root_id": "static", "repo_path": "one/GOATnote", "source_path": "song.md",
                "line_start": 1, "excerpt": "hello"}]
    pack_sha = hashlib.sha256(_canonical(sources)).hexdigest()
    pack = {"sources": sources, "pack_sha256": pack_sha}
    draft = {"pack_id": 1, "body": body, "title": "First flight", "kind": "lyric"}
    with sqlite3.connect(db_path) as db:
        db.executescript("""
            CREATE TABLE creator_packs(id INTEGER PRIMARY KEY,digest TEXT,payload_json TEXT);
            CREATE TABLE creator_drafts(id INTEGER PRIMARY KEY,pack_id INTEGER);
            CREATE TABLE creator_revisions(draft_id INTEGER,revision INTEGER,
                                           payload_json TEXT,content_sha256 TEXT);
        """)
        db.execute("INSERT INTO creator_packs VALUES(1,?,?)", (pack_sha, json.dumps(pack)))
        db.execute("INSERT INTO creator_drafts VALUES(1,1)")
        db.execute("INSERT INTO creator_revisions VALUES(1,1,?,?)",
                   (json.dumps(draft), hashlib.sha256(body.encode()).hexdigest()))
    return 1


def test_manifest_is_versioned_nonexecuting_data():
    manifest = load_manifest()
    assert manifest["version"] == "house.ark-manifest/v0.1"
    assert all(item["optional"] for item in manifest["organs"])
    assert len({item["id"] for item in manifest["organs"]}) == len(manifest["organs"])


def test_arrival_reports_presence_not_readiness(tmp_path):
    report = diagnose(_config(tmp_path), repos=[_repo("Dogram", dirty=True)])
    dogram = next(item for item in report["organs"] if item["id"] == "dogram")
    assert dogram["observed"] == "checkout_observed"
    assert dogram["checkouts"][0]["dirty"] is True
    assert dogram["ready"] == "not_evaluated"
    assert dogram["authorized"] is False
    assert report["repo_count"] == 1
    assert next(item for item in report["organs"] if item["id"] == "static-live")["observed"] == "not_discovered"


def test_duplicate_checkouts_do_not_select_a_winner(tmp_path):
    report = diagnose(_config(tmp_path), repos=[_repo("Dogram", "one"), _repo("Dogram", "two")])
    dogram = next(item for item in report["organs"] if item["id"] == "dogram")
    assert dogram["selection"] == "ambiguous"
    assert len(dogram["checkouts"]) == 2
    assert dogram["authorized"] is False


def test_reentry_of_saved_draft_is_stable_after_reopen(tmp_path):
    _fixture_shelf(tmp_path)
    before = creator_reentry(tmp_path, 1)
    after = creator_reentry(tmp_path, 1)  # A new read-only DB connection.
    assert before == after
    assert before["status"] == "local_saved_state_verified"
    assert before["source_current"] == "not_checked"
    assert before["selected_source_count"] == 1
    assert before["title"] == "First flight"
    assert "Song begins" not in json.dumps(before)


def test_reentry_rejects_changed_draft_or_pack(tmp_path):
    _fixture_shelf(tmp_path)
    with sqlite3.connect(tmp_path / "creator.sqlite3") as db:
        db.execute("UPDATE creator_revisions SET payload_json=? WHERE draft_id=1",
                   (json.dumps({"pack_id": 1, "body": "changed"}),))
    with pytest.raises(ValueError, match="identity mismatch"):
        creator_reentry(tmp_path, 1)

    (tmp_path / "creator.sqlite3").unlink()
    _fixture_shelf(tmp_path)
    with sqlite3.connect(tmp_path / "creator.sqlite3") as db:
        db.execute("UPDATE creator_packs SET digest=? WHERE id=1", ("0" * 64,))
    with pytest.raises(ValueError, match="identity mismatch"):
        creator_reentry(tmp_path, 1)


def test_reentry_refuses_missing_db_symlink_and_invalid_id(tmp_path):
    with pytest.raises(ValueError, match="missing or symlinked"):
        creator_reentry(tmp_path, 1)
    with pytest.raises(ValueError, match="positive integer"):
        creator_reentry(tmp_path, True)
    other = tmp_path / "other.db"
    other.write_bytes(b"not a database")
    (tmp_path / "creator.sqlite3").symlink_to(other)
    with pytest.raises(ValueError, match="missing or symlinked"):
        creator_reentry(tmp_path, 1)
