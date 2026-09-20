from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorConflict, CreatorShelf
from static_workbench.maxhinal_dock import parse_ride


def ride_fixture():
    # Synthetic portable Maxhinal v0 shape, never claimed to be executed here.
    return {
        "format": "maxhinal/v0", "ride_id": "ride-test", "created_at": None,
        "corpus": {"format": "daily-slice-corpus/v0-legacy-bridge", "digest": "legacy:27"},
        "replay": {"status": "EXACT", "local_digest": "legacy:27"}, "seed": "test",
        "gas": [{"kind": "slice", "slice_id": "slice-1", "status": "AVAILABLE"}],
        "operations": [{"operation_id": "op-0001", "mode": "discontinuity",
                        "output_refs": ["out-0001"], "receipt": {"authority": "none", "promotion": "NONE"}}],
        "outputs": [{"output_id": "out-0001", "kind": "derived", "mode": "discontinuity",
                     "source_operation_id": "op-0001", "value": {"test": "projection"}}],
        "residuals": [{"residual_id": "res-0001", "source_operation_id": "op-0001",
                       "code": "UNRESOLVED", "message": "Nothing proven."}],
        "bad_spins": [{"bad_id": "bad-0001", "output_ref": "out-0001",
                       "kind": "rejected", "reason": "Counterfeit similarity."}],
        "authority": "none", "promotion": "NONE",
    }


def fixture(tmp_path):
    root = tmp_path / "repos"
    repo = root / "the-daily-slice"
    repo.mkdir(parents=True)
    subprocess.run(["git", "-C", str(repo), "init", "-b", "main"], check=True, capture_output=True)
    source = repo / "README.md"
    source.write_text("Hugh Jackman keeps coming back.\n", encoding="utf-8")
    config = WorkbenchConfig(
        bind_host="127.0.0.1", port=13700, state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),), max_repo_depth=2,
    )
    return config, source


def headers(client):
    return {"X-Workbench-Session": client.get("/api/bootstrap").json()["session_token"]}


def seed_pack(shelf):
    return shelf.save_pack({"pack_sha256": "a" * 64, "source_count": 1, "sources": []})["id"]


def test_untrusted_ride_preview_preserves_gas_bad_spins_and_no_promotion():
    raw = json.dumps(ride_fixture(), ensure_ascii=False)
    original, summary = parse_ride(raw)
    assert summary["ride_sha256"] == hashlib.sha256(raw.encode("utf-8")).hexdigest()
    assert summary["source_slice_ids"] == ["slice-1"]
    assert summary["residuals"][0]["code"] == "UNRESOLVED"
    assert summary["bad_spins"][0]["reason"] == "Counterfeit similarity."
    assert summary["operations"][0]["mode"] == "discontinuity"
    assert summary["projections"][0]["id"] == "out-0001"
    assert '"test": "projection"' in summary["projections"][0]["excerpt"]
    assert summary["reported_replay"] == "EXACT"
    assert summary["import_posture"] == "untrusted_local_copy_not_reexecuted"
    assert summary["authority"] == "none" and summary["promotion"] == "NONE"
    assert original == ride_fixture()


@pytest.mark.parametrize("change", [
    lambda x: x.update(authority="canonical"),
    lambda x: x.update(promotion="YES"),
    lambda x: x.update(format="different"),
    lambda x: x.update(operations=[{**x["operations"][0], "mode": []}]),
    lambda x: x.update(operations=[{**x["operations"][0], "output_refs": "fake"}]),
    lambda x: x.update(operations=[{**x["operations"][0], "receipt": {"authority": "admin", "promotion": "NONE"}}]),
    lambda x: x.update(outputs=[{**x["outputs"][0], "source_operation_id": "op-missing"}]),
    lambda x: x.update(gas=[{"kind": "derived", "output_id": "out-0001"}]),
])
def test_invalid_ride_refused(change):
    source = ride_fixture()
    change(source)
    with pytest.raises(ValueError):
        parse_ride(json.dumps(source))


def test_oversized_ride_is_refused():
    with pytest.raises(ValueError, match="128 KiB"):
        parse_ride(json.dumps({**ride_fixture(), "notes": "X" * 132000}))


def test_ride_preview_save_and_explicit_draft_link_survive_restart(tmp_path):
    config, source = fixture(tmp_path)
    source_before = source.read_bytes()
    shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    pack1, pack2 = seed_pack(shelf), seed_pack(shelf)
    raw = json.dumps(ride_fixture(), ensure_ascii=False)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        assert client.post("/api/creator/maxhinal/preview", json={"pack_id": pack1, "raw_json": raw}).status_code == 403
        h = headers(client)
        assert client.post("/api/creator/maxhinal/preview",
            headers={**h, "Origin": "http://evil.invalid"}, json={"pack_id": pack1, "raw_json": raw}).status_code == 403
        preview = client.post("/api/creator/maxhinal/preview", headers=h, json={"pack_id": pack1, "raw_json": raw})
        assert preview.status_code == 200
        digest = preview.json()["ride_sha256"]
        assert client.post("/api/creator/maxhinal/rides", headers=h, json={
            "pack_id": pack1, "raw_json": raw, "expected_ride_sha256": "0" * 64,
        }).status_code == 409
        saved = client.post("/api/creator/maxhinal/rides", headers=h, json={
            "pack_id": pack1, "raw_json": raw, "expected_ride_sha256": digest,
        })
        assert saved.status_code == 200
        ride_id = saved.json()["id"]
        assert saved.json()["pack_id"] == pack1
        assert client.get("/api/creator/maxhinal/rides/" + str(ride_id)).json()["ride_sha256"] == digest
        assert client.get("/api/creator/maxhinal/rides").json()["rides"][0]["id"] == ride_id
        payload = {
            "pack_id": pack1, "expected_revision": 0, "title": "The Return",
            "kind": "lyric", "body": "The original lyric.", "assumptions": "It's metaphor.",
            "gaps": "Other performer?", "maxhinal_ride_id": ride_id,
        }
        draft = client.post("/api/creator/drafts", headers=h, json=payload)
        assert draft.status_code == 200
        draft_id = draft.json()["id"]
        assert client.get("/api/creator/drafts/" + str(draft_id)).json()["maxhinal_ride_id"] == ride_id
        assert client.post("/api/creator/drafts", headers=h, json={
            **payload, "pack_id": pack2, "expected_revision": 0,
        }).status_code == 409
        assert client.post("/api/creator/drafts/" + str(draft_id) + "/revisions",
            headers=h, json={**payload, "expected_revision": 1, "maxhinal_ride_id": 999}).status_code == 409
        second = client.post("/api/creator/drafts/" + str(draft_id) + "/revisions",
            headers=h, json={**payload, "expected_revision": 1, "body": "A second take"})
        assert second.status_code == 200 and second.json()["revision"] == 2

    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        restored = client.get("/api/creator/drafts/" + str(draft_id)).json()
        assert restored["maxhinal_ride_id"] == ride_id and restored["body"] == "A second take"
        assert client.get("/api/creator/maxhinal/rides/" + str(ride_id)).json()["ride_id"] == "ride-test"
        assert client.get("/api/creator/drafts/" + str(draft_id) + "/revisions").json()["revisions"][0]["revision"] == 2
        events = client.get("/api/events").json()["events"]
        assert any(event["kind"] == "creator.maxhinal.ride_docked" for event in events)
    assert source.read_bytes() == source_before


def test_ride_shelf_rejects_cross_pack_association_without_harming_previous_revision(tmp_path):
    shelf = CreatorShelf(tmp_path / "state" / "creator.sqlite3")
    pack_a, pack_b = seed_pack(shelf), seed_pack(shelf)
    raw = json.dumps(ride_fixture())
    _ride, summary = parse_ride(raw)
    linked = shelf.save_maxhinal_ride(pack_a, raw, summary)
    assert shelf.get_maxhinal_ride(linked["id"], include_raw=True)["raw_json"] == raw
    assert "raw_json" not in shelf.get_maxhinal_ride(linked["id"])
    payload = {"pack_id": pack_a, "title": "One", "kind": "brief", "body": "Original",
               "assumptions": "", "gaps": "", "maxhinal_ride_id": linked["id"]}
    first = shelf.save_revision(None, 0, payload)
    with pytest.raises(CreatorConflict):
        shelf.save_revision(first["id"], 1, {**payload, "maxhinal_ride_id": 999})
    with pytest.raises(CreatorConflict):
        shelf.save_revision(None, 0, {**payload, "pack_id": pack_b})
    assert shelf.get_draft(first["id"])["body"] == "Original"
    assert len(shelf.revisions(first["id"])) == 1


def test_dock_ui_references_native_machine_not_a_fake_reimplementation(tmp_path):
    config, _ = fixture(tmp_path)
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        js = client.get("/assets/maxhinal-dock.js")
        html = client.get("/").text
        creator = client.get("/assets/creator-v02.js").text
    assert js.status_code == 200
    assert "/assets/maxhinal-dock.js" in html
    assert "hugh-jackman-discontinuity-machine.html" in js.text
    assert "Preview this Maxhinal ride" in js.text
    assert "Dock this reviewed ride locally" in js.text
    assert "maxhinal_ride_id" in creator
    assert "maxhinalRenderDock" in creator
    assert "Copy reviewed ride projections + residuals" in js.text
    assert "maxhinalSourceDoor" in creator
