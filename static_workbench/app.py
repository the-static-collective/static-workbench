from __future__ import annotations

import secrets
from contextlib import asynccontextmanager
from dataclasses import asdict
from pathlib import Path

import uvicorn
from fastapi import FastAPI, HTTPException, Query, Request
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from . import __version__
from .aperture import analyze_aperture
from .config import RootConfig, WorkbenchConfig, load_config
from .journal import Journal, SenseFieldRecord
from .house import build_house_status
from .machine import sample_machine
from .paths import PathOutsideRoot, resolve_under_root
from .repos import discover_repositories
from .schemas import (
    ApertureAnalyzeRequest,
    ApertureHistoryResponse,
    ApertureRecordResponse,
    BootstrapResponse,
    ObjectResponse,
    RootInfo,
)


def _host_name(value: str) -> str:
    value = value.strip().lower()
    if value.startswith("["):
        end = value.find("]")
        return value[1:end] if end != -1 else value
    if value.count(":") == 1:
        return value.rsplit(":", 1)[0]
    return value


def _find_root(config: WorkbenchConfig, root_id: str) -> RootConfig:
    for root in config.roots:
        if root.id == root_id:
            return root
    raise HTTPException(status_code=404, detail=f"unknown root: {root_id}")


def _inspect_object(config: WorkbenchConfig, root_id: str, relative_path: str) -> ObjectResponse:
    root = _find_root(config, root_id)
    try:
        resolved = resolve_under_root(root.path, relative_path)
    except (PathOutsideRoot, FileNotFoundError) as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    if not resolved.exists():
        raise HTTPException(status_code=404, detail="object does not exist")

    stat = resolved.stat()
    relative = resolved.relative_to(root.path.resolve(strict=True)).as_posix()
    if resolved.is_dir():
        entries = sorted(item.name for item in resolved.iterdir())[:200]
        return ObjectResponse(
            root_id=root_id,
            path=relative,
            kind="directory",
            size=None,
            mtime_ns=stat.st_mtime_ns,
            entries=entries,
        )

    preview: str | None = None
    truncated = False
    if resolved.is_file():
        with resolved.open("rb") as handle:
            data = handle.read(config.preview_bytes + 1)
        truncated = len(data) > config.preview_bytes
        data = data[: config.preview_bytes]
        if b"\x00" not in data:
            try:
                preview = data.decode("utf-8")
            except UnicodeDecodeError:
                preview = None

    return ObjectResponse(
        root_id=root_id,
        path=relative,
        kind="file" if resolved.is_file() else "other",
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
        preview=preview,
        preview_truncated=truncated,
    )



def _sense_field_response(record: SenseFieldRecord) -> ApertureRecordResponse:
    return ApertureRecordResponse(
        id=record.id,
        created_at=record.created_at,
        raw_text=record.raw_text,
        parent_id=record.parent_id,
        analysis=record.payload,
    )

def create_app(config: WorkbenchConfig | None = None) -> FastAPI:
    config = config or load_config()
    journal = Journal(config.state_dir / "workbench.sqlite3")
    session_token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        journal.append("workbench.started", {"version": __version__})
        yield

    app = FastAPI(title="Static Workbench", version=__version__, lifespan=lifespan)
    app.state.config = config
    app.state.journal = journal
    app.state.session_token = session_token

    web_dir = Path(__file__).resolve().parent / "web"
    app.mount("/assets", StaticFiles(directory=web_dir), name="assets")

    allowed_hosts = {"127.0.0.1", "localhost", "::1", config.bind_host.lower()}

    @app.middleware("http")
    async def loopback_host_guard(request: Request, call_next):
        host = _host_name(request.headers.get("host", ""))
        if host not in allowed_hosts:
            return JSONResponse(status_code=400, content={"detail": "unapproved Host header"})
        return await call_next(request)

    @app.get("/", include_in_schema=False)
    def index():
        return FileResponse(web_dir / "index.html")

    @app.get("/api/bootstrap", response_model=BootstrapResponse)
    def bootstrap() -> BootstrapResponse:
        return BootstrapResponse(
            version=__version__,
            roots=[RootInfo(id=root.id, path=str(root.path)) for root in config.roots],
            session_token=session_token,
        )

    @app.get("/api/events")
    def events(limit: int = Query(default=100, ge=1, le=1000)):
        return {"events": [asdict(event) for event in journal.latest(limit)]}

    @app.get("/api/repos")
    def repos():
        result = discover_repositories(config.roots, config.max_repo_depth)
        journal.append("repos.scanned", {"count": len(result)})
        return {"repos": [asdict(item) for item in result]}

    @app.get("/api/house")
    def house():
        result = discover_repositories(config.roots, config.max_repo_depth)
        status = build_house_status(result)
        journal.append("house.scanned", status["summary"])
        return status

    @app.get("/api/machine")
    def machine():
        snapshot = sample_machine(config.roots)
        journal.append(
            "machine.sampled",
            {"cpu_percent": snapshot.cpu_percent, "memory_percent": snapshot.memory.percent},
        )
        return asdict(snapshot)


    @app.post("/api/aperture/analyze", response_model=ApertureRecordResponse)
    def aperture_analyze(request: ApertureAnalyzeRequest) -> ApertureRecordResponse:
        if request.parent_id is not None:
            parent = journal.get_sense_field(request.parent_id)
            if parent is None:
                raise HTTPException(status_code=400, detail=f"unknown parent sense field: {request.parent_id}")
            if parent.raw_text != request.raw_text:
                raise HTTPException(
                    status_code=400,
                    detail="child sense field must preserve the same raw carrier as its parent",
                )

        result = analyze_aperture(request.raw_text, request.context_text)
        payload = asdict(result)
        record = journal.append_sense_field(
            raw_text=request.raw_text,
            parent_id=request.parent_id,
            payload=payload,
        )
        journal.append(
            "aperture.analyzed",
            {
                "sense_field_id": record.id,
                "parent_id": record.parent_id,
                "status": result.status,
                "reading_count": len(result.readings),
            },
        )
        return _sense_field_response(record)

    @app.get("/api/aperture/history", response_model=ApertureHistoryResponse)
    def aperture_history(limit: int = Query(default=50, ge=1, le=200)) -> ApertureHistoryResponse:
        return ApertureHistoryResponse(
            sense_fields=[_sense_field_response(record) for record in journal.latest_sense_fields(limit)]
        )

    @app.get("/api/objects/inspect", response_model=ObjectResponse)
    def inspect_object(root_id: str, path: str = "") -> ObjectResponse:
        obj = _inspect_object(config, root_id, path)
        journal.append(
            "object.inspected",
            {"root_id": obj.root_id, "path": obj.path, "kind": obj.kind},
        )
        return obj

    return app


def main() -> None:
    config = load_config()
    uvicorn.run(
        create_app(config),
        host=config.bind_host,
        port=config.port,
        access_log=False,
    )


if __name__ == "__main__":
    main()
