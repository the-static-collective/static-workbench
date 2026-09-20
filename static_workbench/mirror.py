"""MIRROR-001: a deliberately closed, Workbench-owned visual editing proof.

This is NOT a general source editor, dev-server launcher, or repository writer.
The only editable source is a CSS token fixture in Workbench's local state.
"""
from __future__ import annotations

import difflib
import hashlib
import re
import secrets
import tempfile
import threading
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, ConfigDict, Field

DEFAULT_WIDTH = 360
DEFAULT_ACCENT = "#6a9dd4"
CSS_PATTERN = re.compile(
    r"\A:root \{ --mirror-card-width: ([0-9]{3})px; --mirror-accent: (#[0-9a-f]{6}); \}\n\Z"
)
DEMO_HTML = """<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>MIRROR demo surface</title><style>
*,*::before,*::after { box-sizing:border-box }
body { font:16px/1.5 system-ui,sans-serif; margin:0; padding:32px; color:#edf2ed; background:#141c19 }
main { display:flex; min-height:260px; justify-content:center; align-items:center }
.mirror-card { width:min(100%,var(--mirror-card-width)); border:2px solid var(--mirror-accent);
 border-radius:18px; padding:24px; background:#21312b; box-shadow:0 12px 35px #0005 }
.mirror-chip { font-size:12px; color:#111; background:var(--mirror-accent);
 border-radius:20px; padding:4px 9px; display:inline-block }
h1 {font-size:24px;margin:16px 0 8px} p {margin:0}
</style><style id="mirror-owned-css">__OWNED_CSS__</style></head>
<body><main><article class="mirror-card" data-mirror-target="demo-card">
<span class="mirror-chip">Workbench-owned demo</span>
<h1>Change the shape. Keep the receipt.</h1>
<p>This example is the only surface MIRROR-001 can write.</p>
</article></main></body></html>"""


def css_for(width: int, accent: str) -> str:
    return f":root {{ --mirror-card-width: {width}px; --mirror-accent: {accent}; }}\n"


def digest(source: str) -> str:
    return hashlib.sha256(source.encode("utf-8")).hexdigest()


def validate_css(source: str) -> tuple[int, str]:
    match = CSS_PATTERN.fullmatch(source)
    if not match:
        raise MirrorConflict("MIRROR source is outside the declared fixture format")
    width, accent = int(match.group(1)), match.group(2)
    if not 220 <= width <= 600:
        raise MirrorConflict("MIRROR source width is outside the allowed range")
    return width, accent


class MirrorConflict(ValueError):
    pass


class MirrorPatch(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    expected_source_sha256: str = Field(pattern=r"^[0-9a-f]{64}$")
    card_width: int = Field(ge=220, le=600)
    accent: str = Field(pattern=r"^#[0-9a-f]{6}$")


class MirrorStore:
    """One named fixture; never accepts a user-provided path or command."""

    def __init__(self, state_dir: Path):
        self.directory = state_dir / "mirror-001"
        self.source_path = self.directory / "demo.css"
        self.lock = threading.Lock()

    def read(self) -> str:
        if self.directory.is_symlink() or self.source_path.is_symlink():
            raise MirrorConflict("symlinked MIRROR state is refused")
        if not self.source_path.exists():
            return css_for(DEFAULT_WIDTH, DEFAULT_ACCENT)
        if not self.source_path.is_file() or self.source_path.stat().st_size > 256:
            raise MirrorConflict("MIRROR source is not a bounded regular file")
        try:
            source = self.source_path.read_text(encoding="utf-8")
        except (UnicodeError, OSError) as exc:
            raise MirrorConflict("MIRROR source is unreadable") from exc
        validate_css(source)
        return source

    def state(self) -> dict:
        source = self.read()
        width, accent = validate_css(source)
        return {
            "source_sha256": digest(source), "card_width": width, "accent": accent,
            "source_kind": "workbench_owned_demo_css", "demo_url": "/api/mirror/demo",
        }

    def preview(self, patch: MirrorPatch) -> dict:
        source = self.read()
        if digest(source) != patch.expected_source_sha256:
            raise MirrorConflict("source changed since inspection; reload before proposing a patch")
        changed = css_for(patch.card_width, patch.accent)
        diff = "".join(difflib.unified_diff(
            source.splitlines(keepends=True), changed.splitlines(keepends=True),
            fromfile="mirror-001/demo.css (observed)", tofile="mirror-001/demo.css (proposed)",
        ))
        return {
            "before_sha256": digest(source), "after_sha256": digest(changed),
            "changed": source != changed, "diff": diff,
            "proposed": {"card_width": patch.card_width, "accent": patch.accent},
            "scope": "workbench_owned_demo_css",
        }

    def apply(self, patch: MirrorPatch, expected_after_sha256: str) -> dict:
        with self.lock:
            proposed = self.preview(patch)
            if not proposed["changed"]:
                raise MirrorConflict("no source change to apply")
            if expected_after_sha256 != proposed["after_sha256"]:
                raise MirrorConflict("proposed patch identity does not match reviewed preview")
            if self.directory.is_symlink() or self.source_path.is_symlink():
                raise MirrorConflict("symlinked MIRROR state is refused")
            self.directory.mkdir(parents=True, exist_ok=True)
            if self.directory.is_symlink():
                raise MirrorConflict("symlinked MIRROR state is refused")
            # tempfile + atomic replacement: the original remains intact if writing fails.
            temporary = None
            try:
                with tempfile.NamedTemporaryFile(
                    mode="w", encoding="utf-8", dir=self.directory,
                    prefix=".mirror-", suffix=".tmp", delete=False,
                ) as handle:
                    temporary = Path(handle.name)
                    handle.write(css_for(patch.card_width, patch.accent))
                    handle.flush()
                # Re-read immediately before replacement: refuse an intervening edit.
                if digest(self.read()) != patch.expected_source_sha256:
                    raise MirrorConflict("source changed during apply; no patch written")
                temporary.replace(self.source_path)
                temporary = None
            finally:
                if temporary is not None:
                    temporary.unlink(missing_ok=True)
            return {"applied": True, **self.state(), "before_sha256": proposed["before_sha256"]}


def mirror_router(state_dir: Path, session_token: str, journal=None) -> APIRouter:
    router = APIRouter(prefix="/api/mirror", tags=["MIRROR-001 experimental"])
    store = MirrorStore(state_dir)

    def guard(request: Request) -> None:
        host = request.headers.get("host", "")
        origin = request.headers.get("origin")
        if origin is not None and origin != f"http://{host}":
            raise HTTPException(status_code=403, detail="cross-origin MIRROR writes refused")
        if not secrets.compare_digest(request.headers.get("x-workbench-session", ""), session_token):
            raise HTTPException(status_code=403, detail="local session token required")

    @router.get("/state")
    def state():
        try:
            return store.state()
        except MirrorConflict as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @router.get("/demo", response_class=HTMLResponse)
    def demo():
        try:
            html = DEMO_HTML.replace("__OWNED_CSS__", store.read())
        except MirrorConflict as exc:
            raise HTTPException(409, detail=str(exc)) from exc
        return HTMLResponse(html, headers={
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'; frame-ancestors 'self'",
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
        })

    @router.post("/preview")
    def preview(patch: MirrorPatch, request: Request):
        guard(request)
        try:
            return store.preview(patch)
        except MirrorConflict as exc:
            raise HTTPException(409, detail=str(exc)) from exc

    @router.post("/apply")
    def apply(patch: MirrorPatch, request: Request, expected_after_sha256: str):
        guard(request)
        if not re.fullmatch(r"[0-9a-f]{64}", expected_after_sha256):
            raise HTTPException(422, detail="invalid proposed patch identity")
        try:
            result = store.apply(patch, expected_after_sha256)
        except MirrorConflict as exc:
            raise HTTPException(409, detail=str(exc)) from exc
        if journal is not None:
            journal.append("mirror.demo_css.applied", {
                "before_sha256": result["before_sha256"], "after_sha256": result["source_sha256"],
                "scope": "workbench_owned_demo_css",
            })
        return result

    return router
