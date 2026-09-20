from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorShelf
from static_workbench.native_maxhinal import preview_fuels, spin, FuelConflict


def setup(tmp_path):
    root = tmp_path / "root"
    root.mkdir()
    (root / "notes").mkdir()
    (root / "notes" / "first.txt").write_text("The house takes attendance.\nFire and storm.\n", encoding="utf-8")
    (root / "notes" / "second.txt").write_text("The storm passed through the house.\n", encoding="utf-8")
    (root / "notes" / "photo.png").write_bytes(b"\x89PNG\x00\x02\x03\xff")
    config = WorkbenchConfig(bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),))
    return config, root


def file_fuel(name):
    return {"kind": "file", "root_id": "static", "path": "notes/" + name}


def session(client):
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def test_explicit_multifile_text_fuel_discontinuity_and_deterministic_shuffle(tmp_path):
    config, _ = setup(tmp_path)
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    selectors = [file_fuel("first.txt"), file_fuel("second.txt")]
    preview = preview_fuels(config.roots, shelf, selectors)
    assert preview["fuels"][0]["reading"] == "bounded_utf8_excerpt"
    assert preview["fuels"][0]["sha256"] == hashlib.sha256(
        b"The house takes attendance.\nFire and storm.\n").hexdigest()
    assert preview["fuel_sha256"] and preview["authority"] == "none"
    ride = spin(preview, "discontinuity", "foo", "")
    assert {"house", "storm"}.issubset(set(ride["outputs"][0]["surviving_literal_tokens"]))
    assert ride["bad_spins"] and ride["authority"] == "none" and ride["promotion"] == "NONE"
    assert spin(preview, "shuffle", "seed", "how?") == spin(preview, "shuffle", "seed", "how?")
    assert spin(preview, "braid", "seed", "")["outputs"][0]["kind"] == "ordered_braid"
    assert spin(preview, "pressure", "seed", "")["outputs"][0]["kind"] == "pressure_questions"
    assert spin(preview, "compose", "seed", "")["outputs"][0]["kind"] == "composition_prompt"


def test_binary_file_is_metadata_only_and_not_hallucinated(tmp_path):
    config, _ = setup(tmp_path)
    packet = preview_fuels(config.roots, CreatorShelf(config.state_dir / "creator.sqlite3"), [file_fuel("photo.png")])
    fuel = packet["fuels"][0]
    assert fuel["excerpt"] is None
    assert fuel["reading"] == "metadata_only"
    assert fuel["byte_size"] == 8
    assert fuel["sha256"] == hashlib.sha256(b"\x89PNG\x00\x02\x03\xff").hexdigest()
    ride = spin(packet, "braid", "0", "")
    assert any("metadata" in reason for reason in ride["residuals"])
    assert "a beautiful sunset" not in json.dumps(ride)


def test_source_pack_and_unrelated_local_file_can_share_one_native_ride(tmp_path):
    config, _ = setup(tmp_path)
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    pack = shelf.save_pack({
        "pack_sha256": "a" * 64, "source_count": 1,
        "sources": [{"excerpt": "The house is a doorway.", "root_id": "static", "repo_path": "example"}],
    })
    preview = preview_fuels(config.roots, shelf, [
        {"kind": "source_pack", "pack_id": pack["id"]}, file_fuel("first.txt"),
    ])
    assert preview["fuels"][0]["reading"] == "saved_human_selected_excerpts"
    ride = spin(preview, "compose", "0", "Can these make a chorus?")
    assert ride["source_refs"][0]["pack_id"] == pack["id"]
    assert ride["source_refs"][1]["path"] == "notes/first.txt"
    assert ride["question"] == "Can these make a chorus?"
    assert ride["outputs"][0]["instruction"] == ride["question"]


def test_path_escape_hidden_secrets_symlink_missing_and_large_files_fail_closed(tmp_path):
    config, root = setup(tmp_path)
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    outside = tmp_path / "outside.txt"
    outside.write_text("outside", encoding="utf-8")
    (root / "notes" / "link.txt").symlink_to(outside)
    (root / "notes" / ".hidden.txt").write_text("secret", encoding="utf-8")
    (root / "notes" / "passwords.txt").write_text("secret", encoding="utf-8")
    (root / "notes" / "massive.mp4").write_bytes(b"x" * (16 * 1024 * 1024 + 1))
    for item in [
        {"kind": "file", "root_id": "static", "path": "../outside.txt"},
        {"kind": "file", "root_id": "static", "path": str(outside)},
        {"kind": "file", "root_id": "static", "path": "notes/link.txt"},
        {"kind": "file", "root_id": "static", "path": "notes/.hidden.txt"},
        {"kind": "file", "root_id": "static", "path": "notes/passwords.txt"},
        {"kind": "file", "root_id": "static", "path": "notes/massive.mp4"},
        {"kind": "file", "root_id": "static", "path": "notes/missing.txt"},
        {"kind": "file", "root_id": "missing", "path": "notes/first.txt"},
        {"kind": "file", "root_id": "static"},
        {"kind": "source_pack"},
    ]:
        with pytest.raises((ValueError, OSError)):
            preview_fuels(config.roots, shelf, [item])
    with pytest.raises(ValueError, match="repeated"):
        preview_fuels(config.roots, shelf, [file_fuel("first.txt"), file_fuel("first.txt")])
    with pytest.raises(ValueError):
        preview_fuels(config.roots, shelf, [file_fuel("first.txt")] * 5)


def test_reviewed_fuel_change_refuses_spin_without_changing_file_or_prior_receipts(tmp_path):
    config, root = setup(tmp_path)
    target = root / "notes" / "first.txt"
    original = target.read_bytes()
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        h = session(client)
        bad = client.post("/api/house-maxhinal/fuel/preview", json={"fuels": [file_fuel("first.txt")]})
        assert bad.status_code == 403
        assert client.post("/api/house-maxhinal/fuel/preview", headers={
            **h, "Origin": "http://evil.invalid",
        }, json={"fuels": [file_fuel("first.txt")]}).status_code == 403
        preview_response = client.post("/api/house-maxhinal/fuel/preview", headers=h,
            json={"fuels": [file_fuel("first.txt")]})
        assert preview_response.status_code == 200
        checksum = preview_response.json()["fuel_sha256"]
        mismatch = client.post("/api/house-maxhinal/spin", headers=h, json={
            "fuels": [file_fuel("first.txt")], "expected_fuel_sha256": "0" * 64, "mode": "pressure",
        })
        assert mismatch.status_code == 409
        assert client.get("/api/house-maxhinal/rides").json()["rides"] == []
        good = client.post("/api/house-maxhinal/spin", headers=h, json={
            "fuels": [file_fuel("first.txt")], "expected_fuel_sha256": checksum, "mode": "pressure",
        })
        assert good.status_code == 200
        saved = good.json()["receipt"]
        assert saved["id"] == 1
        assert saved["ride_sha256"]
        assert client.get("/api/house-maxhinal/rides/1").json()["outputs"] == good.json()["ride"]["outputs"]
        target.write_bytes(original + b"Changed!\n")
        stale = client.post("/api/house-maxhinal/spin", headers=h, json={
            "fuels": [file_fuel("first.txt")], "expected_fuel_sha256": checksum, "mode": "pressure",
        })
        assert stale.status_code == 409
        assert len(client.get("/api/house-maxhinal/rides").json()["rides"]) == 1
        assert client.get("/api/house-maxhinal/rides/1").json()["fuels"][0]["sha256"] == hashlib.sha256(original).hexdigest()
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.get("/api/house-maxhinal/rides/1").json()["id"] == 1
        assert client.get("/api/house-maxhinal/rides/1").json()["mode"] == "pressure"


def test_browser_surface_and_local_boundaries(tmp_path):
    config, _ = setup(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        native = client.get("/assets/native-maxhinal.js")
        main = client.get("/assets/app.js").text
        status = client.get("/api/house-maxhinal")
    assert native.status_code == 200 and status.status_code == 200
    assert 'data-view="maxhinal"' in html
    assert "Review this fuel before spinning" in native.text
    assert "Spin reviewed fuel and save local ride" in native.text
    assert "navigator.clipboard" in native.text
    assert "renderNativeMaxhinal" in main
    assert status.json()["authority"] == "none"
    assert status.json()["max_file_bytes"] == 16777216
