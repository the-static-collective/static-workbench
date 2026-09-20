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
from .dogram_impact import ImpactDeskError, preview_impact, run_impact, read_report
from .graft_witness import GraftWitnessError, preview as preview_graft, measure as measure_graft
from .graft_round import preview_round, save_round
from .graft_draft import candidate_context, open_draft, save_draft
from .creator import creator_desk_status, search_sources
from .creator_shelf import CreatorShelf, CreatorConflict, preview_pack
from .maxhinal_dock import parse_ride
from .native_maxhinal import preview_fuels, spin, FuelConflict
from .broadcast import broadcast_door
from .journal import Journal, SenseFieldRecord
from .house import build_house_status
from .groundkeeper import make_receipt as groundkeeper_first_ignition
from .machine import sample_machine
from .paths import PathOutsideRoot, resolve_under_root
from .repos import discover_repositories
from .branch_deck import build_branch_deck
from .branch_remote import inspect_github_repo, RemoteDiscoveryError
from .branch_worktree import WorktreeError, preview_worktree, create_worktree
from .schemas import (
    ApertureAnalyzeRequest,
    CreatorPackRequest,
    CreatorPackSaveRequest,
    CreatorDraftRequest,
    MaxhinalRideRequest,
    MaxhinalRideSaveRequest,
    NativeFuelRequest,
    NativeSpinRequest,
    DogramImpactRequest,
    DogramImpactRunRequest,
    GraftWitnessPreviewRequest,
    GraftWitnessRunRequest,
    GraftRoundPreviewRequest,
    GraftRoundSaveRequest,
    GraftDraftSaveRequest,
    BranchWorktreeRequest,
    BranchWorktreeCreateRequest,
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
    creator_shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
    session_token = secrets.token_urlsafe(32)

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        journal.append("workbench.started", {"version": __version__})
        yield

    app = FastAPI(title="Static Workbench", version=__version__, lifespan=lifespan)
    app.state.config = config
    app.state.journal = journal
    app.state.creator_shelf = creator_shelf
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

    @app.get("/api/branches")
    def branch_deck():
        # No user-controlled paths, Git arguments, network fetch or checkout.
        result = build_branch_deck(discover_repositories(config.roots, config.max_repo_depth))
        journal.append("branches.scanned", {
            "repos": result["repos_scanned"],
            "refs": len(result["branches"]),
            "gaps": len(result["gaps"]),
        })
        return result

    @app.get("/api/branches/remote")
    def branch_deck_remote(root_id: str, repo_path: str):
        # Explicit browser action only; configured-root checkout and approved
        # Collective GitHub origin are resolved server-side. No user URL accepted.
        if not config.github_remote_discovery:
            raise HTTPException(status_code=403, detail="public GitHub discovery disabled; enable github_remote_discovery in Workbench config")
        repos = discover_repositories(config.roots, config.max_repo_depth)
        selected = next(
            (repo for repo in repos if repo.root_id == root_id and repo.relative_path == repo_path),
            None,
        )
        if selected is None:
            raise HTTPException(status_code=404, detail="repository not discovered under configured roots")
        local_deck = build_branch_deck([selected])
        if local_deck["gaps"]:
            raise HTTPException(status_code=409, detail="local reference scan incomplete; inspect scan gaps before relating to remote")
        try:
            observed = inspect_github_repo(selected, local_deck["branches"])
        except RemoteDiscoveryError as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc
        journal.append("branches.github_observed", {
            "root_id": selected.root_id, "repo_path": selected.relative_path,
            "github_repo": observed["github_repo"], "refs": len(observed["branches"]),
            "gaps": observed["gaps"],
        })
        return observed

    @app.get("/api/house")
    def house():
        result = discover_repositories(config.roots, config.max_repo_depth)
        status = build_house_status(result)
        journal.append("house.scanned", status["summary"])
        return status

    @app.get("/api/creator/desk")
    def creator_desk():
        repos = discover_repositories(config.roots, config.max_repo_depth)
        return creator_desk_status(repos)

    @app.get("/api/creator/sources")
    def creator_sources(
        root_id: str,
        repo_path: str,
        query: str = Query(min_length=2, max_length=100),
    ):
        repos = discover_repositories(config.roots, config.max_repo_depth)
        try:
            return search_sources(config.roots, repos, root_id, repo_path, query)
        except (ValueError, OSError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    def _creator_write_guard(request: Request) -> None:
        origin = request.headers.get("origin")
        host = request.headers.get("host", "")
        if origin is not None and origin != f"http://{host}":
            raise HTTPException(status_code=403, detail="cross-origin creator writes are refused")
        token = request.headers.get("x-workbench-session", "")
        if not secrets.compare_digest(token, session_token):
            raise HTTPException(status_code=403, detail="creator write requires a local session token")

    def _worktree_source(payload: BranchWorktreeRequest):
        repos = discover_repositories(config.roots, config.max_repo_depth)
        selected = next(
            (repo for repo in repos if repo.root_id == payload.root_id and repo.relative_path == payload.repo_path),
            None,
        )
        if selected is None:
            raise HTTPException(status_code=404, detail="local checkout is not under a configured root")
        deck = build_branch_deck([selected])
        if deck["gaps"]:
            raise HTTPException(status_code=409, detail="local branch scan incomplete; inspect before worktree preparation")
        matching = next((
            card for card in deck["branches"]
            if card["kind"] == "local" and card["ref"] == payload.ref
            and card["commit"] == payload.expected_commit
        ), None)
        if matching is None:
            raise HTTPException(status_code=409, detail="local branch/commit not observed or moved; refresh Branch Deck")
        return selected

    @app.post("/api/branches/worktrees/preview")
    def worktree_preview(payload: BranchWorktreeRequest, request: Request):
        _creator_write_guard(request)
        selected = _worktree_source(payload)
        try:
            return preview_worktree(config, selected, payload.ref, payload.expected_commit)
        except WorktreeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/branches/worktrees/create")
    def worktree_create(payload: BranchWorktreeCreateRequest, request: Request):
        _creator_write_guard(request)
        if payload.acknowledge_effect is not True:
            raise HTTPException(status_code=422, detail="explicit worktree effect acknowledgement required")
        selected = _worktree_source(payload)
        try:
            result = create_worktree(config, selected, payload.ref, payload.expected_commit,
                                     payload.expected_preview_digest)
        except WorktreeError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        journal.append("branches.worktree_created", {
            "root_id": selected.root_id, "repo_path": selected.relative_path,
            "commit": result["actual_commit"], "destination": result["destination"],
            "preview_digest": result["preview_digest"], "tests": "not_run",
        })
        return result

    @app.post("/api/dogram/impact/preview")
    def dogram_impact_preview(payload: DogramImpactRequest, request: Request):
        _creator_write_guard(request)
        try:
            return preview_impact(config, payload.root_id, payload.repo_path)
        except ImpactDeskError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/dogram/impact/run")
    def dogram_impact_run(payload: DogramImpactRunRequest, request: Request):
        _creator_write_guard(request)
        try:
            result = run_impact(
                config, payload.root_id, payload.repo_path,
                payload.expected_input_sha256, payload.expected_candidate_commit,
                payload.expected_dogram_commit,
            )
        except ImpactDeskError as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        journal.append(
            "dogram.impact.saved",
            {"report_id": result["report_id"],
             "input_sha256": result["report"]["source"]["input_sha256"]},
        )
        return result

    @app.get("/api/dogram/impact/reports/{report_id}")
    def dogram_impact_report(report_id: str):
        try:
            return {"report_id": report_id, "report": read_report(config, report_id)}
        except ImpactDeskError as exc:
            raise HTTPException(status_code=404, detail=str(exc)) from exc

    def _pack_for_request(payload: CreatorPackRequest):
        try:
            repos = discover_repositories(config.roots, config.max_repo_depth)
            return preview_pack(config.roots, repos, [item.model_dump() for item in payload.selections])
        except (CreatorConflict, ValueError, OSError) as exc:
            raise HTTPException(status_code=409 if isinstance(exc, CreatorConflict) else 400, detail=str(exc)) from exc

    @app.post("/api/creator/packs/preview")
    def creator_pack_preview(payload: CreatorPackRequest, request: Request):
        _creator_write_guard(request)
        return _pack_for_request(payload)

    @app.post("/api/creator/packs")
    def creator_pack_save(payload: CreatorPackSaveRequest, request: Request):
        _creator_write_guard(request)
        pack = _pack_for_request(payload)
        if pack["pack_sha256"] != payload.expected_pack_sha256:
            raise HTTPException(status_code=409, detail="source pack differs from preview; review again")
        saved = creator_shelf.save_pack(pack)
        journal.append("creator.pack.saved", {"pack_id": saved["id"], "source_count": saved["source_count"]})
        return saved

    @app.get("/api/creator/packs")
    def creator_packs():
        return {"packs": creator_shelf.list_packs()}

    @app.get("/api/creator/packs/{pack_id}")
    def creator_pack(pack_id: int):
        result = creator_shelf.get_pack(pack_id)
        if result is None:
            raise HTTPException(status_code=404, detail="source pack not found")
        return result

    def _save_draft(payload: CreatorDraftRequest, draft_id: int | None = None):
        try:
            saved = creator_shelf.save_revision(
                draft_id,
                payload.expected_revision,
                payload.model_dump(exclude={"expected_revision"}),
            )
        except CreatorConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        journal.append("creator.draft.saved", {"draft_id": saved["id"], "revision": saved["revision"]})
        return saved

    @app.post("/api/creator/drafts")
    def creator_draft_create(payload: CreatorDraftRequest, request: Request):
        _creator_write_guard(request)
        return _save_draft(payload)

    @app.post("/api/creator/drafts/{draft_id}/revisions")
    def creator_draft_rev(draft_id: int, payload: CreatorDraftRequest, request: Request):
        _creator_write_guard(request)
        if draft_id < 1:
            raise HTTPException(status_code=404, detail="draft not found")
        return _save_draft(payload, draft_id)

    @app.get("/api/creator/drafts")
    def creator_drafts():
        return {"drafts": creator_shelf.list_drafts()}

    @app.get("/api/creator/drafts/{draft_id}")
    def creator_draft(draft_id: int):
        draft = creator_shelf.get_draft(draft_id)
        if draft is None:
            raise HTTPException(status_code=404, detail="draft not found")
        return draft

    @app.get("/api/creator/drafts/{draft_id}/revisions")
    def creator_draft_revisions(draft_id: int):
        if creator_shelf.get_draft(draft_id) is None:
            raise HTTPException(status_code=404, detail="draft not found")
        return {"revisions": creator_shelf.revisions(draft_id)}

    @app.post("/api/creator/maxhinal/preview")
    def maxhinal_ride_preview(payload: MaxhinalRideRequest, request: Request):
        _creator_write_guard(request)
        if creator_shelf.get_pack(payload.pack_id) is None:
            raise HTTPException(status_code=404, detail="selected source pack not found")
        try:
            _ride, summary = parse_ride(payload.raw_json)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        return {"pack_id": payload.pack_id, **summary}

    @app.post("/api/creator/maxhinal/rides")
    def maxhinal_ride_import(payload: MaxhinalRideSaveRequest, request: Request):
        _creator_write_guard(request)
        try:
            _ride, summary = parse_ride(payload.raw_json)
            if summary["ride_sha256"] != payload.expected_ride_sha256:
                raise HTTPException(status_code=409, detail="ride differs from preview; review again")
            saved = creator_shelf.save_maxhinal_ride(payload.pack_id, payload.raw_json, summary)
        except CreatorConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        journal.append("creator.maxhinal.ride_docked", {
            "ride_id": saved["id"], "pack_id": payload.pack_id,
            "ride_sha256": saved["ride_sha256"],
        })
        return saved

    @app.get("/api/creator/maxhinal/rides")
    def maxhinal_rides():
        return {"rides": creator_shelf.list_maxhinal_rides()}

    @app.get("/api/creator/maxhinal/rides/{ride_id}")
    def maxhinal_ride(ride_id: int):
        saved = creator_shelf.get_maxhinal_ride(ride_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="docked ride not found")
        return saved

    def _house_fuel(payload: NativeFuelRequest):
        try:
            return preview_fuels(
                config.roots, creator_shelf,
                [item.model_dump() for item in payload.fuels],
            )
        except (FuelConflict, ValueError, OSError) as exc:
            raise HTTPException(
                status_code=409 if isinstance(exc, FuelConflict) else 400,
                detail=str(exc),
            ) from exc

    @app.get("/api/house-maxhinal")
    def house_maxhinal_info():
        return {
            "format": "house.native-maxhinal/v0.1",
            "modes": ["discontinuity", "braid", "compose", "pressure", "shuffle"],
            "max_fuels": 4, "max_file_bytes": 16777216,
            "authority": "none", "promotion": "NONE",
            "notice": "Local user-selected fuel only; not the Daily Slice Maxhinal runtime.",
        }

    @app.post("/api/house-maxhinal/fuel/preview")
    def house_maxhinal_preview(payload: NativeFuelRequest, request: Request):
        _creator_write_guard(request)
        return _house_fuel(payload)

    @app.post("/api/house-maxhinal/spin")
    def house_maxhinal_spin(payload: NativeSpinRequest, request: Request):
        _creator_write_guard(request)
        preview = _house_fuel(payload)
        if preview["fuel_sha256"] != payload.expected_fuel_sha256:
            raise HTTPException(status_code=409, detail="fuel changed since preview; review again")
        try:
            ride = spin(preview, payload.mode, payload.seed, payload.question)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        saved = creator_shelf.save_native_ride(ride)
        journal.append("house.maxhinal.spin_saved", {
            "ride_id": saved["id"], "mode": saved["mode"],
            "fuel_sha256": saved["fuel_sha256"],
        })
        return {"receipt": saved, "ride": ride}

    @app.get("/api/house-maxhinal/rides")
    def house_maxhinal_rides():
        return {"rides": creator_shelf.list_native_rides()}

    @app.get("/api/house-maxhinal/rides/{ride_id}")
    def house_maxhinal_ride(ride_id: int):
        saved = creator_shelf.get_native_ride(ride_id)
        if saved is None:
            raise HTTPException(status_code=404, detail="native Maxhinal ride not found")
        return saved

    @app.post("/api/house-maxhinal/graft/rounds/preview")
    def graft_round_preview(payload: GraftRoundPreviewRequest, request: Request):
        _creator_write_guard(request)
        try:
            return preview_round(creator_shelf, **payload.model_dump())
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/house-maxhinal/graft/rounds")
    def graft_round_save(payload: GraftRoundSaveRequest, request: Request):
        _creator_write_guard(request)
        try:
            result = save_round(creator_shelf, **payload.model_dump())
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        journal.append("house.graft.round_saved", {
            "ride_id": payload.ride_id, "round_sha256": result["round_sha256"],
        })
        return result

    @app.get("/api/house-maxhinal/graft/rides/{ride_id}/rounds")
    def graft_rounds(ride_id: int):
        if creator_shelf.get_native_ride(ride_id) is None:
            raise HTTPException(status_code=404, detail="Maxhinal ride not found")
        return {"rounds": creator_shelf.list_graft_rounds(ride_id)}

    @app.get("/api/house-maxhinal/graft/rounds/{round_sha256}")
    def graft_round_read(round_sha256: str):
        try:
            result = creator_shelf.get_graft_round(round_sha256)
        except CreatorConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if result is None:
            raise HTTPException(status_code=404, detail="GRAFT round not found")
        return result

    @app.get("/api/house-maxhinal/graft/candidates/{candidate_sha256}/draft")
    def graft_draft_open(candidate_sha256: str):
        try:
            return open_draft(creator_shelf, candidate_sha256)
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/house-maxhinal/graft/drafts")
    def graft_draft_save(payload: GraftDraftSaveRequest, request: Request):
        _creator_write_guard(request)
        try:
            result = save_draft(creator_shelf, **payload.model_dump())
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        journal.append("house.graft.draft_revision_saved", {
            "candidate_sha256": payload.candidate_sha256, "revision": result["revision"],
            "draft_sha256": result["draft_sha256"],
        })
        return result

    @app.get("/api/house-maxhinal/graft/candidates/{candidate_sha256}/draft/revisions")
    def graft_draft_revisions(candidate_sha256: str):
        try:
            candidate_context(creator_shelf, candidate_sha256)
            return {"revisions": creator_shelf.list_graft_draft_revisions(candidate_sha256)}
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.get("/api/house-maxhinal/graft/candidates/{candidate_sha256}/draft/revisions/{revision}")
    def graft_draft_revision(candidate_sha256: str, revision: int):
        try:
            candidate_context(creator_shelf, candidate_sha256)
            result = creator_shelf.get_graft_draft_revision(candidate_sha256, revision)
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if result is None:
            raise HTTPException(status_code=404, detail="GRAFT draft revision not found")
        return result

    @app.post("/api/house-maxhinal/graft/preview")
    def graft_structural_preview(payload: GraftWitnessPreviewRequest, request: Request):
        _creator_write_guard(request)
        try:
            return preview_graft(config, creator_shelf, **payload.model_dump())
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc

    @app.post("/api/house-maxhinal/graft/measure")
    def graft_structural_measure(payload: GraftWitnessRunRequest, request: Request):
        _creator_write_guard(request)
        try:
            result = measure_graft(config, creator_shelf, **payload.model_dump())
        except (GraftWitnessError, CreatorConflict) as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        journal.append("house.graft.dogram_witness_saved", {
            "ride_id": payload.ride_id, "witness_sha256": result["witness_sha256"],
            "specimen_sha256": payload.expected_specimen_sha256,
        })
        return result

    @app.get("/api/house-maxhinal/graft/rides/{ride_id}/witnesses")
    def graft_structural_witnesses(ride_id: int):
        if creator_shelf.get_native_ride(ride_id) is None:
            raise HTTPException(status_code=404, detail="Maxhinal ride not found")
        return {"witnesses": creator_shelf.list_graft_witnesses(ride_id)}

    @app.get("/api/house-maxhinal/graft/witnesses/{witness_sha256}")
    def graft_structural_witness(witness_sha256: str):
        try:
            result = creator_shelf.get_graft_witness(witness_sha256)
        except CreatorConflict as exc:
            raise HTTPException(status_code=409, detail=str(exc)) from exc
        if result is None:
            raise HTTPException(status_code=404, detail="GRAFT witness not found")
        return result

    @app.get("/api/broadcast/door")
    def local_broadcast_door():
        repos = discover_repositories(config.roots, config.max_repo_depth)
        return broadcast_door(config, repos)

    @app.get("/api/groundkeeper/first-ignition")
    def groundkeeper_ignition(seed: str = Query(
        default="static-first-ignition", min_length=1, max_length=128
    )):
        """Synthetic-only, deterministic, non-persistent HOUSE experimental view."""
        try:
            return groundkeeper_first_ignition(seed=seed)
        except ValueError as exc:
            raise HTTPException(status_code=422, detail=str(exc)) from exc

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
