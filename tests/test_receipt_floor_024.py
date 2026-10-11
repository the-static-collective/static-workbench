from pathlib import Path
from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig


def config(tmp_path: Path):
    root = tmp_path / "source"
    root.mkdir()
    return WorkbenchConfig(
        bind_host="127.0.0.1",
        port=13700,
        state_dir=tmp_path / "state",
        roots=(RootConfig("source", root),),
    )


def test_receipt_floor_mounts_in_native_workbench_shell_without_an_executor(tmp_path):
    with TestClient(create_app(config(tmp_path)), base_url="http://127.0.0.1") as client:
        page = client.get("/receipt-floor")
        index = client.get("/")
        ghot = client.get("/assets/app.js")
        prior = client.get("/stack-floor")
        core = client.get("/assets/receipt-floor-core.mjs")
        ui = client.get("/assets/receipt-floor-ui.mjs")
        css = client.get("/assets/receipt-floor.css")
        for response in (page, index, ghot, prior, core, ui, css):
            assert response.status_code == 200
        assert 'href="/receipt-floor"' in index.text
        assert "receiptDoor.href = '/receipt-floor'" in ghot.text
        assert 'href="/receipt-floor"' in prior.text
        assert 'id="receipt-file"' in page.text
        assert 'id="chain"' in page.text
        assert 'id="consent"' in page.text
        assert 'id="export-packet"' in page.text
        assert "connect-src 'none'" in page.text
        assert "NO PRIVATE PAYLOAD" in page.text
        assert "FOREIGN_NATIVE_CI_CLAIM_NOT_BROWSER_VERIFIED" in core.text
        assert "inspectPublicWitness" in ui.text
        assert client.post("/receipt-floor", json={"execute": True}).status_code == 405
        assert client.post("/api/receipt-floor", json={"execute": True}).status_code == 404
        assert client.get("/receipt-floor", headers={"host":"evil.example"}).status_code == 400
