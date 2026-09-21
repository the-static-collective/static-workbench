"""Book of Machines: frozen source pages, exact domino joins, local-only API."""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.maddloop import MaddloopStore
from static_workbench.machine_book import MachineBook, BookConflict, inspect_board


def config_for(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1", port=13700,
        state_dir=tmp_path / "state", roots=(RootConfig("static", root),),
    )


def layer(name, input_class="note", input_port="note", output_class="note", output_port="note"):
    return {
        "kind": "text", "label": name, "body": "Human sketch: " + name,
        "input_class": input_class, "input_port": input_port,
        "output_class": output_class, "output_port": output_port,
    }


def stores(tmp_path):
    loops = MaddloopStore(tmp_path / "maddloop.sqlite3")
    book = MachineBook(tmp_path / "machine_book.sqlite3", tmp_path / "maddloop.sqlite3")
    return loops, book


def inscribe(book, loop, title):
    return book.record_folio(title, "Human purpose for " + title, loop["id"], loop["head_revision_id"])


def test_folios_freeze_source_revision_without_overwriting_parent(tmp_path):
    loops, book = stores(tmp_path)
    loop = loops.create("idea", layer("first"))
    first = inscribe(book, loop, "Idea domino")
    edited = loops.overdub(loop["id"], loop["head_revision_id"], layer("second"))
    frozen = MachineBook(tmp_path / "machine_book.sqlite3", tmp_path / "maddloop.sqlite3").folio(first["id"])
    assert len(frozen["layers"]) == 1
    assert frozen["revision_id"] == loop["head_revision_id"]
    assert frozen["snapshot_sha256"] == loop["snapshot_sha256"]
    assert frozen["layers"][0]["source_id"] == loop["layers"][0]["source_id"]
    assert len(loops.get(loop["id"])["layers"]) == 2
    try:
        book.record_folio("stale", "Do not save", loop["id"], loop["head_revision_id"])
        assert False, "stale revision must refuse"
    except Exception as error:
        assert "changed since review" in str(error)
    newer = inscribe(book, edited, "Another page")
    assert newer["revision_id"] == edited["head_revision_id"]
    assert newer["id"] != first["id"]


def test_abstract_domino_legs_do_not_imply_executable_route(tmp_path):
    loops, book = stores(tmp_path)
    p = inscribe(book, loops.create("p", layer("P to Q_in", "P", "p", "Q", "q_in")), "P to Q")
    q = inscribe(book, loops.create("q", layer("Q_out to R", "Q", "q_out", "R", "r")), "Q to R")
    blocked = book.compose("Missing bridge", [p["id"], q["id"]])
    assert blocked["result"]["status"] == "candidate_with_gaps"
    gap = blocked["result"]["gaps"][0]
    assert gap["reason"] == "concrete_lift_gap"
    assert gap["available"] == {"class": "Q", "port": "q_in"}
    assert gap["required"] == {"class": "Q", "port": "q_out"}
    assert blocked["kind"] == "frozen_domino_arrangement"
    compatible = inscribe(book, loops.create(
        "repair", layer("Q_in to R", "Q", "q_in", "R", "r"),
    ), "Exact repair")
    repaired = book.compose("Alternate route", [p["id"], compatible["id"]])
    assert repaired["result"]["status"] == "synthetic_route_matched"
    assert not repaired["result"]["gaps"]
    assert book.board(blocked["id"])["result"]["status"] == "candidate_with_gaps"
    assert "no project action" in repaired["result"]["nonclaim"]


def test_internal_folio_obstruction_blocks_board_even_when_outer_ports_meet(tmp_path):
    loops, book = stores(tmp_path)
    first = loops.create("a", layer("a to Q_in", "A", "a", "Q", "q_in"))
    internal = loops.overdub(first["id"], first["head_revision_id"], layer(
        "Q_out to R", "Q", "q_out", "R", "r",
    ))
    bad = inscribe(book, internal, "Broken interior")
    ending = inscribe(book, loops.create("end", layer("R to Z", "R", "r", "Z", "z")), "Ending")
    result = book.compose("Cannot silently skip internal gap", [bad["id"], ending["id"]])
    assert result["result"]["status"] == "candidate_with_gaps"
    assert result["result"]["gaps"][0]["kind"] == "within_folio"
    assert result["result"]["gaps"][0]["reason"] == "concrete_lift_gap"


def test_folio_order_and_repetition_are_preserved_by_board_receipt(tmp_path):
    loops, book = stores(tmp_path)
    a = inscribe(book, loops.create("a", layer("self join")), "Reusable page")
    arranged = book.compose("Repetition", [a["id"], a["id"], a["id"]])
    assert [item["id"] for item in arranged["folios"]] == [a["id"]] * 3
    assert arranged["result"]["status"] == "synthetic_route_matched"
    assert len(book.boards()) == 1


def test_protected_api_and_book_page_are_live_and_persist(tmp_path):
    cfg = config_for(tmp_path)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as c:
        assert 'href="/machines"' in c.get("/").text
        assert "THE BOOK OF MACHINES" in c.get("/machines").text
        assert c.get("/assets/machines.js").status_code == 200
        assert "Lay this domino" in c.get("/assets/machines.js").text
        token = c.get("/api/bootstrap").json()["session_token"]
        headers = {"x-workbench-session": token}
        created_loop = c.post("/api/maddloop/loops", headers=headers, json={
            "title": "Origin", "layer": layer("One"),
        }).json()
        request = {
            "title": "First folio", "purpose": "Something human-authored",
            "loop_id": created_loop["id"],
            "expected_revision_id": created_loop["head_revision_id"],
        }
        assert c.post("/api/machines/folios", json=request).status_code == 403
        assert c.post("/api/machines/folios", json=request, headers={
            **headers, "origin": "http://other.example",
        }).status_code == 403
        folio_response = c.post("/api/machines/folios", json=request, headers=headers)
        assert folio_response.status_code == 200
        fid = folio_response.json()["id"]
        board_response = c.post("/api/machines/boards", json={
            "title": "Two copies", "folio_ids": [fid, fid],
        }, headers=headers)
        assert board_response.status_code == 200
        board_id = board_response.json()["id"]
        assert c.post("/api/machines/boards", json={
            "title": "Only one", "folio_ids": [fid],
        }, headers=headers).status_code == 422
        assert c.post("/api/machines/boards", json={
            "title": "Missing folio", "folio_ids": ["0" * 32, fid],
        }, headers=headers).status_code == 404
        events = c.get("/api/events").json()["events"]
        assert any(row["kind"] == "machines.folio_recorded" for row in events)
        assert any(row["kind"] == "machines.board_recorded" for row in events)
    with TestClient(create_app(cfg), base_url="http://127.0.0.1") as c:
        assert c.get("/api/machines/folios/" + fid).status_code == 200
        saved = c.get("/api/machines/boards/" + board_id).json()
        assert saved["kind"] == "frozen_domino_arrangement"
        assert saved["result"]["status"] == "synthetic_route_matched"
