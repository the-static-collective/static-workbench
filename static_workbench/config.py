from __future__ import annotations

import os
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path

_ROOT_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,63}$")


@dataclass(frozen=True)
class RootConfig:
    id: str
    path: Path


@dataclass(frozen=True)
class WorkbenchConfig:
    bind_host: str
    port: int
    state_dir: Path
    roots: tuple[RootConfig, ...]
    max_repo_depth: int = 4
    preview_bytes: int = 131072
    broadcast_port: int | None = None
    github_remote_discovery: bool = False
    branch_worktrees_enabled: bool = False


def _expand_path(value: str | os.PathLike[str]) -> Path:
    return Path(value).expanduser().resolve(strict=False)


def _root_from_mapping(item: dict[str, object]) -> RootConfig:
    root_id = str(item.get("id", "")).strip()
    if not _ROOT_ID.fullmatch(root_id):
        raise ValueError(f"invalid root id: {root_id!r}")
    raw_path = item.get("path")
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError(f"root {root_id!r} requires a path")
    return RootConfig(root_id, _expand_path(raw_path))


def load_config(path: Path | None = None) -> WorkbenchConfig:
    config_path = path or Path(
        os.environ.get(
            "STATIC_WORKBENCH_CONFIG",
            "~/.config/static-workbench/config.toml",
        )
    ).expanduser()

    if config_path.exists():
        with config_path.open("rb") as handle:
            raw = tomllib.load(handle)
        roots = tuple(_root_from_mapping(item) for item in raw.get("roots", []))
        if not roots:
            raise ValueError("configuration must define at least one [[roots]] entry")
        bind_host = str(raw.get("bind_host", "127.0.0.1"))
        port = int(raw.get("port", 13700))
        state_dir = _expand_path(str(raw.get("state_dir", "~/.local/state/static-workbench")))
        max_repo_depth = int(raw.get("max_repo_depth", 4))
        preview_bytes = int(raw.get("preview_bytes", 131072))
        broadcast_port = raw.get("broadcast_port")
        github_remote_discovery = raw.get("github_remote_discovery", False)
        if type(github_remote_discovery) is not bool:
            raise ValueError("github_remote_discovery must be a boolean")
        branch_worktrees_enabled = raw.get("branch_worktrees_enabled", False)
        if type(branch_worktrees_enabled) is not bool:
            raise ValueError("branch_worktrees_enabled must be a boolean")
        if broadcast_port is not None and (type(broadcast_port) is not int):
            raise ValueError("broadcast_port must be an integer")
    else:
        home = Path.home()
        roots = (RootConfig("static", (home / "static").resolve(strict=False)),)
        bind_host = "127.0.0.1"
        port = 13700
        state_dir = (home / ".local" / "state" / "static-workbench").resolve(strict=False)
        max_repo_depth = 4
        preview_bytes = 131072
        broadcast_port = None
        github_remote_discovery = False
        branch_worktrees_enabled = False

    if bind_host not in {"127.0.0.1", "::1", "localhost"}:
        raise ValueError("v0.1 only supports loopback bind hosts")
    if not 1 <= port <= 65535:
        raise ValueError("port must be between 1 and 65535")
    if not 0 <= max_repo_depth <= 12:
        raise ValueError("max_repo_depth must be between 0 and 12")
    if not 1024 <= preview_bytes <= 4 * 1024 * 1024:
        raise ValueError("preview_bytes must be between 1 KiB and 4 MiB")

    if broadcast_port is not None and (not 1 <= broadcast_port <= 65535 or broadcast_port == port):
        raise ValueError("broadcast_port must be a valid, separate TCP port")

    ids = [root.id for root in roots]
    if len(ids) != len(set(ids)):
        raise ValueError("root ids must be unique")

    return WorkbenchConfig(
        bind_host=bind_host,
        port=port,
        state_dir=state_dir,
        roots=roots,
        max_repo_depth=max_repo_depth,
        preview_bytes=preview_bytes,
        broadcast_port=broadcast_port,
        github_remote_discovery=github_remote_discovery,
        branch_worktrees_enabled=branch_worktrees_enabled,
    )
