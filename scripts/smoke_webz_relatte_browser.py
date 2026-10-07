#!/usr/bin/env python3
"""Real Chromium witness for WEBZ-RELATTE-002, with actual pinned LocalReceiver."""
from __future__ import annotations

import argparse
import multiprocessing
import socket
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parents[1]
RELATTE = ROOT / ".compat" / "reLATTE"


def serve(state: str, port: int) -> None:
    import uvicorn
    from static_workbench.app import create_app
    from static_workbench.config import RootConfig, WorkbenchConfig
    cfg = WorkbenchConfig(
        bind_host="127.0.0.1", port=port,
        state_dir=Path(state),
        roots=(RootConfig("relatte", RELATTE),),
    )
    uvicorn.run(create_app(cfg), host="127.0.0.1", port=port, log_level="error")


def port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_ready(base: str) -> None:
    for _ in range(150):
        try:
            with urlopen(base + "/webz", timeout=1) as response:
                if response.status == 200:
                    return
        except Exception:
            pass
        time.sleep(.1)
    raise AssertionError("webZ test Workbench never became ready")


def send(page, base: str, kind: str, expected_status: str) -> None:
    page.goto(base + "/webz/world/sanctuary", wait_until="networkidle")
    page.wait_for_function("!document.querySelector('#webz-parcel-inspect').disabled")
    page.locator("#webz-parcel-kind").select_option(kind)
    assert page.locator("#webz-parcel-send").is_disabled()
    page.locator("#webz-parcel-inspect").click()
    page.wait_for_function("!document.querySelector('#webz-parcel-confirm').disabled")
    assert "SHA-256" in page.locator("#webz-parcel-preview").inner_text()
    assert page.locator("#webz-parcel-send").is_disabled()
    page.locator("#webz-parcel-confirm").check()
    assert page.locator("#webz-parcel-send").is_enabled()
    page.locator("#webz-parcel-send").click()
    page.wait_for_function(
        "(expect) => document.querySelector('#webz-parcel-status').textContent.includes(expect)",
        expected_status,
        timeout=65000,
    )
    assert "ADMITTED: NO" in page.locator("#webz-parcel-status").inner_text()


def main() -> int:
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("browser-artifacts"))
    args = parser.parse_args()
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    assert (RELATTE / "scripts" / "opaque-roundtrip.ts").is_file(), "pinned reLATTE missing"

    with tempfile.TemporaryDirectory(prefix="webz-relatte-browser-") as td:
        state = Path(td) / "state"
        p = port()
        base = f"http://127.0.0.1:{p}"
        server = multiprocessing.Process(target=serve, args=(str(state), p), daemon=True)
        server.start()
        try:
            wait_ready(base)
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
                try:
                    for label, viewport in [
                        ("desktop", {"width": 1366, "height": 880}),
                        ("mobile", {"width": 390, "height": 844}),
                    ]:
                        context = browser.new_context(viewport=viewport, reduced_motion="reduce")
                        try:
                            page = context.new_page()
                            page.goto(base + "/webz/world/sanctuary", wait_until="networkidle")
                            assert page.locator("#webz-cross").is_disabled()
                            assert page.locator("#webz-parcel-send").is_disabled()
                            # Merely opening a scene does not launch reLATTE or stage bytes.
                            if label == "desktop":
                                assert not (state / "webz-relatte").exists()
                            page.screenshot(path=str(out / f"webz-relatte-{label}-preflight.png"), full_page=True)
                            for kind, expected in (
                                ("fruit", "RECEIVED_THEN_HELD"),
                                ("spore", "RECEIVED_THEN_REFUSED"),
                            ):
                                send(page, base, kind, expected)
                                page.screenshot(path=str(out / f"webz-relatte-{label}-{kind}-sent.png"), full_page=True)
                            page.goto(base + "/webz/world/orchard", wait_until="networkidle")
                            page.wait_for_function("document.querySelectorAll('.webz-parcel-receipt').length === 2")
                            displayed = page.locator("#webz-parcel-inbox").inner_text()
                            assert "RECEIVED_THEN_HELD" in displayed
                            assert "RECEIVED_THEN_REFUSED" in displayed
                            assert "NOT ADMITTED" in displayed
                            assert "webz:the-static-collective/orchard-022100" in page.locator(".webz-identity").inner_text()
                            assert not page.evaluate("document.documentElement.scrollWidth > window.innerWidth + 3")
                            page.locator(".webz-parcel-receipt button").first.click()
                            page.wait_for_function("document.querySelector('#webz-parcel-proof').textContent.includes('relatte.crossing-envelope/v0')")
                            proof = page.locator("#webz-parcel-proof").inner_text()
                            assert "relatte.receipt/v0" in proof
                            assert "PRIVATE" not in proof
                            page.screenshot(path=str(out / f"webz-relatte-{label}-orchard-receiver.png"), full_page=True)
                            page.reload(wait_until="networkidle")
                            page.wait_for_function("document.querySelectorAll('.webz-parcel-receipt').length === 2")
                        finally:
                            context.close()
                finally:
                    browser.close()
        finally:
            server.terminate()
            server.join(timeout=10)
            if server.is_alive():
                server.kill()
                server.join(timeout=5)
    print("WEBZ-RELATTE-002 BROWSER PASS: desktop/mobile gated inspect/consent/SEND, actual signed HOLD and REFUSE, Orchard evidence, reload.")
    print("Artifacts:", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
