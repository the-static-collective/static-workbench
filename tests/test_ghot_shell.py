from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.ghot_shell import build_ghot_status


def make_config(tmp_path: Path) -> WorkbenchConfig:
    root = tmp_path / "root"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )


def test_ghot_projection_uses_observed_counts_without_claiming_authority():
    house = {
        "summary": {
            "repos": 7,
            "dirty": 2,
            "diverged": 1,
            "detached": 0,
            "core_organs_present": 4,
            "core_organs_total": 10,
        }
    }
    road = {
        "configured": True,
        "present": True,
        "verification": "identity_content_address_checked; receipt_signatures_not_reverified",
        "summary": {"inbox": 3, "outbox": 1, "foreign_holds": 2, "admits": 1},
    }
    status = build_ghot_status(house, road, [object(), object(), object()])

    assert status["schema"] == "static-workbench.ghot-shell/v0"
    assert status["resources"]["visible_repos"] == 7
    assert status["resources"]["witness_xp"] == 3
    assert status["resources"]["local_admits"] == 1
    assert "XP == WITNESS COUNT, NOT CAPABILITY" in status["laws"]

    quests = {item["id"]: item for item in status["quests"]}
    assert quests["road-threshold"]["status"] == "ready"
    assert quests["public-door"]["status"] == "human_gate"
    assert quests["staticjack-polsia"]["status"] == "held"
    assert quests["staticjack-polsia"]["target_view"] is None


def test_ghot_api_is_available_without_external_authority(tmp_path: Path):
    with TestClient(create_app(make_config(tmp_path)), base_url="http://127.0.0.1") as client:
        response = client.get("/api/ghot")

    assert response.status_code == 200
    body = response.json()
    assert body["mode"] == "idle-operator-projection"
    assert body["idle_tick"]["effect"] == "observation-only"
    polsia = next(item for item in body["quests"] if item["id"] == "staticjack-polsia")
    assert polsia["authority"] == "none"
