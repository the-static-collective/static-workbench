"""HOUSE Staged Rocket v0.1: short-lived, allowlisted, read-only compositions.

A mission has at most three immutable stage receipts: prepare, execute, separate.
Only a person may create a descendant mission; no project executable runs here.
"""
from __future__ import annotations

import hashlib
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field

from .config import WorkbenchConfig
from .paths import PathOutsideRoot, resolve_under_root
from .repos import discover_repositories, _git


class RocketConflict(ValueError):
    pass


class RocketSelection(BaseModel):
    root_id: str = Field(min_length=1, max_length=64)
    repo_path: str = Field(min_length=1, max_length=300)
    expected_sha: str = Field(pattern=r"^[a-f0-9]{40}$")


class RocketMissionInput(BaseModel):
    title: str = Field(min_length=1, max_length=160)
    purpose: str = Field(min_length=1, max_length=2000)
    mode: Literal["source-preview", "body-overlap"]
    selections: list[RocketSelection] = Field(min_length=1, max_length=2)
    source_path: str = Field(default="", max_length=300)
    parent_id: int | None = Field(default=None, ge=1)
    expected_parent_sha256: str | None = Field(default=None, pattern=r"^[a-f0-9]{64}$")


class RocketAdvanceInput(BaseModel):
    expected_stage_sha256: str = Field(pattern=r"^[a-f0-9]{64}$")


class RocketSeparateInput(RocketAdvanceInput):
    next_action: str = Field(min_length=1, max_length=2000)
    residual_fog: str = Field(default="", max_length=2000)


def _digest(value: dict) -> str:
    raw = json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class RocketDesk:
    def __init__(self, path: Path, config: WorkbenchConfig):
        self.path = Path(path)
        self.config = config
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self._connect() as db:
            db.executescript("""
                CREATE TABLE IF NOT EXISTS rocket_missions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    created_at TEXT NOT NULL,
                    title TEXT NOT NULL,
                    purpose TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    selections_json TEXT NOT NULL,
                    source_path TEXT NOT NULL,
                    parent_id INTEGER REFERENCES rocket_missions(id),
                    parent_sha256 TEXT,
                    mission_sha256 TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS rocket_stages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    mission_id INTEGER NOT NULL REFERENCES rocket_missions(id),
                    ordinal INTEGER NOT NULL CHECK (ordinal BETWEEN 1 AND 3),
                    kind TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    previous_sha256 TEXT,
                    output_json TEXT NOT NULL,
                    sha256 TEXT NOT NULL,
                    UNIQUE(mission_id, ordinal)
                );
            """)

    def _connect(self) -> sqlite3.Connection:
        db = sqlite3.connect(self.path, timeout=5)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys = ON")
        return db

    @staticmethod
    def _stage_from_row(row: sqlite3.Row) -> dict:
        value = dict(row)
        value["output"] = json.loads(value.pop("output_json"))
        return value

    @staticmethod
    def _mission_from_row(row: sqlite3.Row) -> dict:
        value = dict(row)
        value["selections"] = json.loads(value.pop("selections_json"))
        return value

    def _mission(self, db: sqlite3.Connection, mission_id: int) -> dict:
        row = db.execute("SELECT * FROM rocket_missions WHERE id = ?", (mission_id,)).fetchone()
        if row is None:
            raise RocketConflict("mission not found")
        return self._mission_from_row(row)

    def _stages(self, db: sqlite3.Connection, mission_id: int) -> list[dict]:
        rows = db.execute(
            "SELECT * FROM rocket_stages WHERE mission_id = ? ORDER BY ordinal", (mission_id,)
        ).fetchall()
        return [self._stage_from_row(row) for row in rows]

    def get(self, mission_id: int) -> dict | None:
        with self._connect() as db:
            row = db.execute("SELECT * FROM rocket_missions WHERE id = ?", (mission_id,)).fetchone()
            if row is None:
                return None
            result = self._mission_from_row(row)
            result["stages"] = self._stages(db, mission_id)
            return result

    def list(self) -> list[dict]:
        with self._connect() as db:
            rows = db.execute("""
                SELECT m.*, COALESCE(MAX(s.ordinal), 0) AS completed_stages
                FROM rocket_missions AS m
                LEFT JOIN rocket_stages AS s ON s.mission_id = m.id
                GROUP BY m.id ORDER BY m.id DESC LIMIT 100
            """).fetchall()
            return [self._mission_from_row(row) for row in rows]

    def catalog(self) -> dict:
        """Discovery is a visibility surface, not permission or readiness."""
        found = discover_repositories(self.config.roots, self.config.max_repo_depth)
        entries = []
        for repo in found:
            head = _git(Path(repo.path), "rev-parse", "HEAD")
            sha = head.stdout.strip() if head.returncode == 0 else ""
            ready = len(sha) == 40 and not repo.dirty
            entries.append({
                "root_id": repo.root_id, "repo_path": repo.relative_path, "name": repo.name,
                "expected_sha": sha if ready else None,
                "clean": not repo.dirty, "detached": repo.detached,
                "selectable": ready, "branch": repo.branch,
            })
        return {
            "tools": [
                {"kind": "repo.snapshot/v0", "effect": "read-only", "stage": "prepare"},
                {"kind": "source.preview/v0", "effect": "read-only", "stage": "execute"},
                {"kind": "body.overlap/v0", "effect": "read-only", "stage": "execute",
                 "notice": "HOUSE-local exact protocol comparison; does not run Free Graph"},
                {"kind": "mission.seed/v0", "effect": "HOUSE-local receipt only", "stage": "separate"},
            ],
            "repos": entries,
        }

    def _observe(self, selection: dict) -> dict:
        found = discover_repositories(self.config.roots, self.config.max_repo_depth)
        matches = [r for r in found if r.root_id == selection["root_id"]
                   and r.relative_path == selection["repo_path"]]
        if len(matches) != 1:
            raise RocketConflict("selected repository is missing or ambiguous in configured roots")
        repo = matches[0]
        actual = _git(Path(repo.path), "rev-parse", "HEAD")
        sha = actual.stdout.strip() if actual.returncode == 0 else ""
        if len(sha) != 40 or sha != selection["expected_sha"] or repo.dirty:
            raise RocketConflict("repository moved or became dirty; start a new exact-source mission")
        return {"root_id": repo.root_id, "repo_path": repo.relative_path,
                "sha": sha, "branch_hint": repo.branch,
                "stacks": list(repo.stacks), "clean_at_observation": True}

    def create(self, payload: RocketMissionInput) -> dict:
        if not payload.title.strip() or not payload.purpose.strip():
            raise RocketConflict("title and purpose must not be blank")
        selections = [item.model_dump() for item in payload.selections]
        distinct = {(v["root_id"], v["repo_path"]) for v in selections}
        if len(distinct) != len(selections):
            raise RocketConflict("duplicate source selections")
        if payload.mode == "source-preview" and (len(selections) != 1 or not payload.source_path.strip()):
            raise RocketConflict("source-preview requires one repo and an explicit file path")
        if payload.mode == "body-overlap" and (len(selections) != 2 or payload.source_path):
            raise RocketConflict("body-overlap requires two repos and no file path")
        if (payload.parent_id is None) != (payload.expected_parent_sha256 is None):
            raise RocketConflict("parent id and its exact final-stage digest must be supplied together")
        carrier = payload.model_dump()
        # No implicit execution: creation records a declared plan only.
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            if payload.parent_id is not None:
                parent = self._mission(db, payload.parent_id)
                stages = self._stages(db, parent["id"])
                if len(stages) != 3 or stages[-1]["sha256"] != payload.expected_parent_sha256:
                    raise RocketConflict("parent has not separated with the selected exact receipt")
            created = _now()
            digest = _digest(carrier)
            cursor = db.execute("""
                INSERT INTO rocket_missions
                (created_at, title, purpose, mode, selections_json, source_path,
                 parent_id, parent_sha256, mission_sha256)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (created, payload.title, payload.purpose, payload.mode,
                  json.dumps(selections, sort_keys=True), payload.source_path,
                  payload.parent_id, payload.expected_parent_sha256, digest))
            mission_id = int(cursor.lastrowid)
        return self.get(mission_id)

    @staticmethod
    def _append(db: sqlite3.Connection, mission: dict, ordinal: int, kind: str,
                previous: str | None, output: dict) -> dict:
        content = {"mission_sha256": mission["mission_sha256"],
                   "mission_id": mission["id"], "ordinal": ordinal,
                   "kind": kind, "previous_sha256": previous, "output": output}
        digest = _digest(content)
        created = _now()
        cursor = db.execute("""
            INSERT INTO rocket_stages
            (mission_id, ordinal, kind, created_at, previous_sha256, output_json, sha256)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (mission["id"], ordinal, kind, created, previous,
              json.dumps(output, sort_keys=True, ensure_ascii=False), digest))
        return {"id": cursor.lastrowid, "mission_id": mission["id"],
                "ordinal": ordinal, "kind": kind, "created_at": created,
                "previous_sha256": previous, "output": output, "sha256": digest}

    def _read_source(self, observed: dict, source_path: str, body: bool = False) -> dict:
        root = next((item for item in self.config.roots if item.id == observed["root_id"]), None)
        if root is None:
            raise RocketConflict("unknown root")
        repo = resolve_under_root(root.path, observed["repo_path"])
        requested = Path(source_path)
        if requested.is_absolute() or not requested.parts or any(
            part in {".", ".."} or part.startswith(".") for part in requested.parts
        ):
            raise RocketConflict("source path must be a non-hidden, repository-relative file")
        if not body and (requested.suffix.lower() not in {".md", ".txt", ".json", ".toml"} or
                         any(word in part.lower() for part in requested.parts for word in ("secret", "token", "password", "credential", "keyfile"))):
            raise RocketConflict("unsupported or sensitive-looking source path")
        candidate = resolve_under_root(repo, source_path)
        if any((repo.joinpath(*requested.parts[:i])).is_symlink() for i in range(1, len(requested.parts) + 1)):
            raise RocketConflict("symlink-backed source is not admitted")
        if not candidate.is_file():
            raise RocketConflict("source file not found")
        tracked = _git(repo, "ls-files", "--error-unmatch", "--", source_path)
        if tracked.returncode != 0:
            raise RocketConflict("source file is not tracked in selected Git checkout")
        limit = 32768 if body else 65536
        with candidate.open("rb") as stream:
            raw = stream.read(limit + 1)
        if len(raw) > limit or b"\x00" in raw:
            raise RocketConflict("source is too large or not UTF-8 text")
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise RocketConflict("source is not UTF-8 text") from exc
        return {"root_id": observed["root_id"], "repo_path": observed["repo_path"],
                "sha": observed["sha"], "source_path": source_path,
                "file_sha256": hashlib.sha256(raw).hexdigest(), "bytes": len(raw), "text": text}

    @staticmethod
    def _interfaces(surface: dict) -> set[tuple[str, str, str, str]]:
        if surface.get("schema") != "body.surface/v0" or surface.get("authority") != "none":
            raise RocketConflict("BODY manifest has wrong schema or authority declaration")
        declared = surface.get("interfaces")
        if not isinstance(declared, list) or len(declared) > 100:
            raise RocketConflict("BODY interfaces malformed or over limit")
        result = set()
        for item in declared:
            if not isinstance(item, dict):
                raise RocketConflict("BODY interface must be a declared object")
            fields = [item.get(k) for k in ("direction", "kind", "protocol", "version")]
            if not all(isinstance(v, str) and 0 < len(v) <= 160 for v in fields):
                raise RocketConflict("BODY interface lacks a typed protocol/version declaration")
            if fields[0] not in {"emit", "accept"}:
                raise RocketConflict("unsupported BODY interface direction")
            result.add(tuple(fields))
        return result

    def prepare(self, mission_id: int) -> dict:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            mission = self._mission(db, mission_id)
            if self._stages(db, mission_id):
                raise RocketConflict("mission has already prepared; stage receipts cannot be replaced")
            observed = [self._observe(s) for s in mission["selections"]]
            return self._append(db, mission, 1, "prepare", None, {
                "tool": "repo.snapshot/v0", "sources": observed, "effect": "read-only",
                "authority": "none",
            })

    def execute(self, mission_id: int, expected_stage_sha256: str) -> dict:
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            mission = self._mission(db, mission_id)
            stages = self._stages(db, mission_id)
            if len(stages) != 1 or stages[0]["sha256"] != expected_stage_sha256:
                raise RocketConflict("prepare receipt is missing, stale, or already consumed")
            observed = [self._observe(s) for s in mission["selections"]]
            if observed != stages[0]["output"]["sources"]:
                raise RocketConflict("prepared source observation changed; start a fresh mission")
            if mission["mode"] == "source-preview":
                source = self._read_source(observed[0], mission["source_path"])
                result = {"tool": "source.preview/v0",
                          "source": {k: v for k, v in source.items() if k != "text"},
                          "excerpt": source["text"][:4000],
                          "truncated": len(source["text"]) > 4000,
                          "authority": "none"}
            else:
                manifests = []
                for entry in observed:
                    # The .body directory is intentionally allowlisted only for this operation.
                    root = next(x for x in self.config.roots if x.id == entry["root_id"])
                    repo = resolve_under_root(root.path, entry["repo_path"])
                    manifest = repo / ".body" / "surface-v0.json"
                    if manifest.is_symlink() or manifest.parent.is_symlink():
                        raise RocketConflict("BODY manifest must not be symlink-backed")
                    if not manifest.is_file():
                        raise RocketConflict("selected repo lacks .body/surface-v0.json")
                    tracked = _git(repo, "ls-files", "--error-unmatch", "--", ".body/surface-v0.json")
                    if tracked.returncode != 0:
                        raise RocketConflict("BODY manifest is not tracked")
                    with manifest.open("rb") as stream:
                        raw = stream.read(32769)
                    if len(raw) > 32768:
                        raise RocketConflict("BODY manifest exceeds 32 KiB")
                    try:
                        value = json.loads(raw)
                    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                        raise RocketConflict("BODY manifest is not valid UTF-8 JSON") from exc
                    if not isinstance(value, dict):
                        raise RocketConflict("BODY manifest must be an object")
                    self._interfaces(value)
                    manifests.append({"source": {"root_id": entry["root_id"],
                                                "repo_path": entry["repo_path"], "sha": entry["sha"],
                                                "file_sha256": hashlib.sha256(raw).hexdigest()},
                                      "owner_declared": value.get("owner"),
                                      "interfaces": value["interfaces"]})
                left = self._interfaces({"schema": "body.surface/v0", "authority": "none",
                                          "interfaces": manifests[0]["interfaces"]})
                right = self._interfaces({"schema": "body.surface/v0", "authority": "none",
                                           "interfaces": manifests[1]["interfaces"]})
                overlaps = set()
                for a in left:
                    for b in right:
                        if a[0] != b[0] and a[1:] == b[1:]:
                            overlaps.add((a[1], a[2], a[3]))
                result = {
                    "tool": "body.overlap/v0", "sources": manifests,
                    "exact_interface_overlaps": [
                        {"kind": k, "protocol": p, "version": v}
                        for k, p, v in sorted(overlaps)
                    ],
                    "unresolved": ["No identical typed emit/accept interface is declared."]
                    if not overlaps else [],
                    "notice": "HOUSE-local read-only calculation; Free Graph and Dogram were not executed.",
                    "authority": "none",
                }
            # Refuse if a checkout moved during the bounded read/calculation.
            if [self._observe(s) for s in mission["selections"]] != observed:
                raise RocketConflict("source changed during execution; no receipt saved")
            return self._append(db, mission, 2, "execute", stages[-1]["sha256"], result)

    def separate(self, mission_id: int, payload: RocketSeparateInput) -> dict:
        if not payload.next_action.strip():
            raise RocketConflict("next action must not be blank")
        with self._connect() as db:
            db.execute("BEGIN IMMEDIATE")
            mission = self._mission(db, mission_id)
            stages = self._stages(db, mission_id)
            if len(stages) != 2 or stages[-1]["sha256"] != payload.expected_stage_sha256:
                raise RocketConflict("execute receipt is missing, stale, or already separated")
            return self._append(db, mission, 3, "separate", stages[-1]["sha256"], {
                "tool": "mission.seed/v0", "parent_execute_sha256": stages[-1]["sha256"],
                "next_action_proposed_by_human": payload.next_action,
                "residual_fog": payload.residual_fog,
                "status": "proposal_only",
                "next_mission_requires": "new explicit selection, clean pinned source, and separate stage action",
                "authority": "none",
            })
