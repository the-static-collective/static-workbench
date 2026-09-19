from __future__ import annotations

from pathlib import Path


class PathOutsideRoot(ValueError):
    """Raised when a requested path escapes a configured root."""


def resolve_under_root(root: Path, relative: str) -> Path:
    root_real = root.expanduser().resolve(strict=True)
    requested = Path(relative)
    if requested.is_absolute():
        raise PathOutsideRoot(f"absolute path is outside root: {relative}")
    if any(part == ".." for part in requested.parts):
        raise PathOutsideRoot(f"parent traversal is not allowed: {relative}")

    candidate = (root_real / requested).resolve(strict=False)
    try:
        candidate.relative_to(root_real)
    except ValueError as exc:
        raise PathOutsideRoot(f"path escapes configured root: {relative}") from exc
    return candidate
