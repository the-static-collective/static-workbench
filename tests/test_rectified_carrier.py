"""Cross-lane carrier smoke: preserve navigation and independent authority boundaries.

One app instance must expose the separately source-owned surfaces together.
This is an API/HTML fixture, not an actual Linux/browser or real project run.
"""
from pathlib import Path

from fastapi.testclient import TestClient

from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def test_rectified_house_carrier_keeps_distinct_surfaces(tmp_path: Path):
    root = tmp_path / "checkout-root"
    root.mkdir()
    config = WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("static", root),),
    )
    with TestClient(create_app(config), base_url="http://127.0.0.1") as client:
        html = client.get("/").text
        for name in ("branches", "attention", "returns", "return", "rocket",
                     "mirror", "living-main", "groundkeeper"):
            assert html.count(f'data-view="{name}"') == 1, name
        for asset in ("branch-deck.js", "attention.js", "return-shelf.js",
                      "return-desk.js", "rocket.js", "mirror.js",
                      "living-main.js", "groundkeeper.js"):
            assert html.count(f'/assets/{asset}"') == 1, asset
        assert html.count('href="/lifestream"') == 1
        for path in ("/api/branches", "/api/branches/radar", "/api/house/returns",
                     "/api/return/notes", "/api/rockets/catalog", "/api/mirror/state"):
            response = client.get(path)
            assert response.status_code == 200, (path, response.text)
        assert client.get("/api/branches/radar").json()["enabled"] is False
        assert client.get("/api/house/returns").json()["records"] == []

        # A foreign POST cannot borrow HOUSE authority even for inert previews.
        assert client.post("/api/house/loom/preview", json={}).status_code == 403
        original = client.get("/api/mirror/state").json()["source_sha256"]
        assert client.post("/api/attention", json={
            "kind": "mirror-fixture", "target_id": "mirror-001:demo-card",
            "dimensions": ["joyful"], "explicit_none": False,
            "expected_previous_id": None,
        }).status_code == 403
        assert client.get("/api/mirror/state").json()["source_sha256"] == original
        assert client.get("/api/house/returns").json()["records"] == []
