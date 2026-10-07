"""WEBZ-NATIVE-001: actual desktop/mobile Chromium door + local replay witness.

Run after: pip install playwright && python -m playwright install chromium
This is an integration check against the real FastAPI app, not a mocked scene.
"""
from __future__ import annotations

import argparse
import json
import multiprocessing
import socket
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen


def serve(root: str, state: str, port: int) -> None:
    import uvicorn
    from static_workbench.app import create_app
    from static_workbench.config import RootConfig, WorkbenchConfig

    cfg = WorkbenchConfig(
        bind_host="127.0.0.1", port=port, state_dir=Path(state),
        roots=(RootConfig("static", Path(root)),),
    )
    uvicorn.run(create_app(cfg), host="127.0.0.1", port=port, log_level="error")


def choose_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def wait_ready(base: str) -> None:
    last = None
    for _ in range(120):
        try:
            with urlopen(base + "/webz", timeout=1) as reply:
                if reply.status == 200:
                    return
        except Exception as exc:
            last = exc
        time.sleep(0.1)
    raise RuntimeError(f"Workbench test service failed to start: {last}")


def walk(browser, base: str, label: str, viewport: dict, out: Path) -> None:
    context = browser.new_context(viewport=viewport, accept_downloads=True, reduced_motion="reduce")
    try:
        page = context.new_page()
        page.goto(base + "/", wait_until="networkidle")
        assert page.locator('a[href="/webz"]').count() == 1
        page.locator('a[href="/webz"]').click()
        page.wait_for_url("**/webz")
        page.locator("#webz-address").fill("webz::static/sanctuary")
        assert page.locator("#webz-enter").is_disabled()
        page.locator("#webz-resolve").click()
        page.wait_for_function("!document.querySelector('#webz-enter').disabled")
        assert "webz:the-static-collective/sanctuary" in page.locator("#webz-result").inner_text()
        page.locator("#webz-enter").click()
        page.wait_for_url("**/webz/world/sanctuary")
        page.wait_for_function("!document.querySelector('#webz-inspect').disabled")
        assert "Psychedelic Punk Sanctuary" in page.locator("#world-heading").inner_text()
        assert not page.locator("#webz-cross").is_enabled()
        page.screenshot(path=str(out / f"webz-{label}-sanctuary.png"), full_page=True)

        # Local history begins ONLY on an explicit human choice.
        assert "Recording is off" in page.locator("#webz-recording-status").inner_text()
        page.locator("#webz-begin-recording").click()
        page.wait_for_function("document.querySelector('#webz-recording-status').textContent.includes('Recording 0')")
        page.locator("#webz-inspect").click()
        assert page.locator("#webz-cross").is_enabled()
        assert page.url.endswith("/webz/world/sanctuary")  # Inspect is never Cross
        page.locator("#webz-remain").click()
        assert page.locator("#webz-cross").is_disabled()
        page.locator("#webz-inspect").click()
        page.locator("#webz-cross").click()
        page.wait_for_url("**/webz/world/orchard")
        page.wait_for_function("document.querySelector('#webz-recording-status').textContent.includes('2 navigation events')")
        assert "022100" in page.locator("#world-heading").inner_text()
        page.screenshot(path=str(out / f"webz-{label}-orchard.png"), full_page=True)

        page.wait_for_function("!document.querySelector('#webz-return').disabled")
        page.locator("#webz-return").click()
        assert page.locator("#webz-cross").is_enabled()
        page.locator("#webz-cross").click()
        page.wait_for_url("**/webz/world/sanctuary")
        page.wait_for_function("document.querySelector('#webz-recording-status').textContent.includes('4 navigation events')")
        page.reload(wait_until="networkidle")
        page.wait_for_function("document.querySelector('#webz-recording-status').textContent.includes('4 navigation events')")
        page.screenshot(path=str(out / f"webz-{label}-return.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3")

        with page.expect_download() as info:
            page.locator("#webz-export-voyage").click()
        download = info.value
        path = out / f"webz-{label}-voyage.json"
        download.save_as(str(path))
        packet = json.loads(path.read_text())
        assert packet["schema"] == "webz/voyage-local/v0"
        assert len(packet["events"]) == 4
        assert [x["kind"] for x in packet["events"]] == [
            "departed", "arrived", "departed", "arrived",
        ]
        page.once("dialog", lambda dialog: dialog.accept())
        page.locator("#webz-erase-voyage").click()
        assert "Recording is off" in page.locator("#webz-recording-status").inner_text()

        page.goto(base + "/webz", wait_until="networkidle")
        page.locator("#webz-address").fill("webz::static/unbuilt")
        page.locator("#webz-resolve").click()
        page.wait_for_function("document.querySelector('#webz-result').textContent.includes('UNRESOLVED')")
        assert page.locator("#webz-enter").is_disabled()
        page.screenshot(path=str(out / f"webz-{label}-unresolved.png"), full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3")
    finally:
        context.close()


def main() -> None:
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("browser-artifacts"))
    args = parser.parse_args()
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="webz-native-") as tmp:
        folder = Path(tmp)
        root = folder / "root"
        root.mkdir()
        port = choose_port()
        base = f"http://127.0.0.1:{port}"
        process = multiprocessing.Process(
            target=serve, args=(str(root), str(folder / "state"), port), daemon=True,
        )
        process.start()
        try:
            wait_ready(base)
            with sync_playwright() as p:
                browser = p.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    walk(browser, base, "desktop", {"width": 1366, "height": 880}, output)
                    walk(browser, base, "mobile", {"width": 390, "height": 844}, output)
                finally:
                    browser.close()
        finally:
            process.terminate()
            process.join(timeout=10)
            if process.is_alive():
                process.kill()
                process.join(timeout=5)
    print("WEBZ-NATIVE-001 BROWSER WITNESS: desktop/mobile entered, crossed, returned, replayed, exported, erased, and refused unknown address.")
    print("Screenshots/exports:", output)


if __name__ == "__main__":
    main()
