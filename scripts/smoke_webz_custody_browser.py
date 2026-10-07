#!/usr/bin/env python3
"""Actual Chromium browser verification for WEBZ-003's second explicit byte gate.

Requires two clean, exact reLATTE worktrees in .compat/reLATTE and
.compat/custody/reLATTE, with npm dependencies installed in each.
"""
from __future__ import annotations
import argparse
import multiprocessing
import socket
import tempfile
import time
from pathlib import Path
from urllib.request import urlopen

ROOT=Path(__file__).resolve().parents[1]
OLD=ROOT/".compat"/"reLATTE"
NEW=ROOT/".compat"/"custody"/"reLATTE"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        return int(sock.getsockname()[1])


def serve(state: str, port: int) -> None:
    import uvicorn
    from static_workbench.app import create_app
    from static_workbench.config import RootConfig,WorkbenchConfig
    cfg=WorkbenchConfig(
        bind_host="127.0.0.1",port=port,
        state_dir=Path(state),
        roots=(RootConfig("old-relatte",OLD),RootConfig("new-relatte",NEW)),
    )
    uvicorn.run(create_app(cfg),host="127.0.0.1",port=port,log_level="error")


def wait_ready(url: str) -> None:
    for _ in range(150):
        try:
            with urlopen(url+"/webz",timeout=1) as response:
                if response.status==200:return
        except Exception:
            pass
        time.sleep(.1)
    raise AssertionError("Workbench did not become available")


def first_signed_offer(page,kind: str, expected: str) -> None:
    page.locator("#webz-parcel-kind").select_option(kind)
    assert page.locator("#webz-parcel-send").is_disabled()
    page.locator("#webz-parcel-inspect").click()
    page.wait_for_function("!document.querySelector('#webz-parcel-confirm').disabled")
    page.locator("#webz-parcel-confirm").check()
    assert page.locator("#webz-parcel-send").is_enabled()
    page.locator("#webz-parcel-send").click()
    page.wait_for_function(
        "(status) => document.querySelector('#webz-parcel-status').textContent.includes(status)",
        arg=expected,timeout=65000,
    )


def independent_delivery(page,kind: str, expected: str) -> None:
    page.locator("#webz-custody-kind").select_option(kind)
    assert page.locator("#webz-custody-deliver").is_disabled()
    page.locator("#webz-custody-inspect").click()
    page.wait_for_function("!document.querySelector('#webz-custody-confirm').disabled",timeout=30000)
    inspect=page.locator("#webz-custody-preview").inner_text()
    assert "SIGNED CROSSING" in inspect
    assert "ACTUAL BYTES · SHA-256" in inspect
    assert page.locator("#webz-custody-deliver").is_disabled()
    page.locator("#webz-custody-confirm").check()
    assert page.locator("#webz-custody-deliver").is_enabled()
    page.locator("#webz-custody-deliver").click()
    page.wait_for_function(
        "(status) => document.querySelector('#webz-custody-status').textContent.includes(status)",
        arg=expected,timeout=65000,
    )
    text=page.locator("#webz-custody-status").inner_text()
    assert "ADMITTED: NO" in text
    assert "CUSTODY SIGNED RECEIPT" in text


def walkthrough(browser,url: str,label: str,viewport: dict,out:Path,state:Path) -> None:
    context=browser.new_context(viewport=viewport,reduced_motion="reduce")
    try:
        page=context.new_page()
        page.goto(url+"/webz/world/sanctuary",wait_until="networkidle")
        page.wait_for_function("!document.querySelector('#webz-parcel-inspect').disabled")
        assert page.locator("#webz-cross").is_disabled()
        assert page.locator("#webz-parcel-send").is_disabled()
        assert page.locator("#webz-custody-deliver").is_disabled()
        assert not (state/"webz-relatte").exists()
        page.locator("#webz-custody-inspect").click()
        page.wait_for_function("document.querySelector('#webz-custody-status').textContent.includes('NOT READY')")
        assert page.locator("#webz-custody-deliver").is_disabled()
        page.screenshot(path=str(out/f"webz-003-{label}-before.png"),full_page=True)

        for kind,policy in (("fruit","HOLD"),("spore","REFUSE")):
            first_signed_offer(page,kind,"RECEIVED_THEN_HELD" if kind=="fruit" else "RECEIVED_THEN_REFUSED")
            independent_delivery(
                page,kind,"BYTES_VERIFIED_AND_HELD" if kind=="fruit" else "BYTES_VERIFIED_AND_REFUSED",
            )
            page.screenshot(path=str(out/f"webz-003-{label}-{kind}-verified.png"),full_page=True)
            assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3")
        page.goto(url+"/webz/world/orchard",wait_until="networkidle")
        page.wait_for_function("document.querySelectorAll('.webz-custody-receipt').length===2",timeout=25000)
        view=page.locator("#webz-custody-inbox").inner_text()
        assert "BYTES_VERIFIED_AND_HELD" in view
        assert "BYTES_VERIFIED_AND_REFUSED" in view
        assert "ADMITTED · NO" in view
        page.locator(".webz-custody-receipt button").first.click()
        page.wait_for_function(
            "document.querySelector('#webz-custody-proof').textContent.includes('PAYLOAD_BYTES_VERIFIED')",
            timeout=30000,
        )
        proof=page.locator("#webz-custody-proof").inner_text()
        assert "sha256" in proof
        assert "relatte.receipt/v0" in proof
        page.screenshot(path=str(out/f"webz-003-{label}-orchard-custody.png"),full_page=True)
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 3")
        page.reload(wait_until="networkidle")
        page.wait_for_function("document.querySelectorAll('.webz-custody-receipt').length===2")
    finally:
        context.close()


def main() -> int:
    from playwright.sync_api import sync_playwright
    parser=argparse.ArgumentParser()
    parser.add_argument("--out",type=Path,default=Path("browser-artifacts"))
    args=parser.parse_args()
    out=args.out.resolve()
    out.mkdir(parents=True,exist_ok=True)
    assert (NEW/"scripts"/"opaque-roundtrip.ts").is_file(),"R14 signing unavailable in custody-compatible owner"
    assert (NEW/"scripts"/"material-delivery.ts").is_file(),"custody reLATTE owner unavailable"
    with tempfile.TemporaryDirectory(prefix="webz-003-chromium-") as td:
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
            try:
                for label,viewport in (
                    ("desktop",{"width":1366,"height":880}),
                    ("mobile",{"width":390,"height":844}),
                ):
                    state=Path(td)/label/"state"
                    number=free_port()
                    url=f"http://127.0.0.1:{number}"
                    server=multiprocessing.Process(target=serve,args=(str(state),number),daemon=True)
                    server.start()
                    try:
                        wait_ready(url)
                        walkthrough(browser,url,label,viewport,out,state)
                    finally:
                        server.terminate()
                        server.join(timeout=10)
                        if server.is_alive():
                            server.kill()
                            server.join(timeout=5)
            finally:
                browser.close()
    print("WEBZ-003 BROWSER PASS: desktop/mobile no automatic send; explicit earlier envelope; independently verified signed actual-byte custody HOLD and REFUSE; Orchard read-only proof; reload.")
    print("Artifacts:",out)
    return 0


if __name__=="__main__":
    raise SystemExit(main())
