"""WEBZ-NATIVE-001: strict first-party, read-only logical world address resolution.

Only the two explicitly installed Workbench fixture worlds resolve in v0.
A resolved address does not authenticate the publisher or grant admission.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

_SEGMENT = re.compile(r"[a-z0-9][a-z0-9_-]{0,63}", re.ASCII)
_WORLDS = {
    "webz::static/sanctuary": {
        "slug": "sanctuary",
        "world_id": "webz:the-static-collective/sanctuary",
        "manifest_file": "webz-sanctuary.json",
        "entry_route": "/webz/world/sanctuary",
    },
    "webz::static/orchard/022100": {
        "slug": "orchard",
        "world_id": "webz:the-static-collective/orchard-022100",
        "manifest_file": "webz-orchard.json",
        "entry_route": "/webz/world/orchard",
    },
}
_ALIAS_FIELDS = {"typed_address", "manifest_file", "entry_route"}
_MANIFEST_FIELDS = {"schema", "world_id", "revision", "title", "entry", "doors", "origin_note"}
_DOOR_FIELDS = {"door_id", "label", "to_world_id", "to_address", "carry_mode"}


class WebzRegistryError(ValueError):
    """An installed first-party registry or world declaration is invalid."""


def parse_webz_address(text: str) -> tuple[str, ...]:
    """Parse the Workbench-native address text; never interpret it as a URL."""
    if not isinstance(text, str) or len(text) > 256 or not text.startswith("webz::"):
        raise ValueError("invalid_webz_syntax")
    segments = text[len("webz::"):].split("/")
    if not 2 <= len(segments) <= 4 or any(
        _SEGMENT.fullmatch(part) is None for part in segments
    ):
        raise ValueError("invalid_webz_syntax")
    return tuple(segments)


def _read_json(path: Path) -> dict:
    try:
        if path.stat().st_size > 32768:
            raise WebzRegistryError("fixture exceeds the size limit")
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        raise WebzRegistryError("first-party world declaration unavailable or invalid") from exc
    if not isinstance(value, dict):
        raise WebzRegistryError("world declaration must be an object")
    return value


def _exact_keys(value: dict, expected: set[str], label: str) -> None:
    if not isinstance(value, dict) or set(value) != expected:
        raise WebzRegistryError(f"{label} has missing or unknown fields")


def load_registry(web_dir: Path) -> dict:
    """Load only built-in manifests; no caller-controlled file or URL is fetched."""
    folder = Path(web_dir)
    registry = _read_json(folder / "webz-registry.json")
    _exact_keys(registry, {"schema", "aliases"}, "registry")
    if registry["schema"] != "webz/registry/v0" or not isinstance(registry["aliases"], list):
        raise WebzRegistryError("unsupported webZ registry")
    if len(registry["aliases"]) != len(_WORLDS):
        raise WebzRegistryError("expected the two explicit first-party aliases")
    aliases: dict[str, dict] = {}
    for alias in registry["aliases"]:
        _exact_keys(alias, _ALIAS_FIELDS, "alias")
        address = alias["typed_address"]
        if not isinstance(address, str) or address not in _WORLDS or address in aliases:
            raise WebzRegistryError("duplicate or unexpected world alias")
        expected = _WORLDS[address]
        if alias["manifest_file"] != expected["manifest_file"] or (
            alias["entry_route"] != expected["entry_route"]
        ):
            raise WebzRegistryError("unapproved manifest path or entry route")
        aliases[address] = alias
    if set(aliases) != set(_WORLDS):
        raise WebzRegistryError("missing world alias")

    by_address: dict[str, dict] = {}
    by_slug: dict[str, dict] = {}
    ids: set[str] = set()
    for address, entry in _WORLDS.items():
        manifest = _read_json(folder / entry["manifest_file"])
        _exact_keys(manifest, _MANIFEST_FIELDS, "world")
        if (
            manifest["schema"] != "webz/world/v0"
            or manifest["world_id"] != entry["world_id"]
            or manifest["world_id"] in ids
            or manifest["revision"] != "genesis-001"
            or manifest["entry"] != entry["entry_route"]
            or not isinstance(manifest["title"], str)
            or not 1 <= len(manifest["title"]) <= 120
            or not isinstance(manifest["origin_note"], str)
            or len(manifest["origin_note"]) > 1000
            or not isinstance(manifest["doors"], list)
            or len(manifest["doors"]) != 1
        ):
            raise WebzRegistryError("world identity, schema, or metadata invalid")
        ids.add(manifest["world_id"])
        seen_doors: set[str] = set()
        for door in manifest["doors"]:
            _exact_keys(door, _DOOR_FIELDS, "door")
            target = _WORLDS.get(door["to_address"]) if isinstance(door["to_address"], str) else None
            if (
                not isinstance(door["door_id"], str)
                or _SEGMENT.fullmatch(door["door_id"]) is None
                or door["door_id"] in seen_doors
                or not isinstance(door["label"], str)
                or not 1 <= len(door["label"]) <= 120
                or door["carry_mode"] != "none"
                or target is None
                or target["world_id"] != door["to_world_id"]
                or target["slug"] == entry["slug"]
            ):
                raise WebzRegistryError("door identifier, target or carry contract invalid")
            seen_doors.add(door["door_id"])
        by_address[address] = {
            "status": "resolved",
            "typed_address": address,
            "world_id": manifest["world_id"],
            "title": manifest["title"],
            "entry_route": entry["entry_route"],
            "manifest_revision": manifest["revision"],
            "source": "trusted-workbench-fixture",
        }
        by_slug[entry["slug"]] = manifest
    return {"by_address": by_address, "by_slug": by_slug}


def resolve_webz_address(address: str, registry: dict) -> dict:
    try:
        parse_webz_address(address)
    except ValueError:
        return {"status": "invalid", "error_code": "invalid_webz_syntax"}
    result = registry["by_address"].get(address)
    if result is None:
        return {"status": "unresolved", "typed_address": address}
    return dict(result)


def world_by_slug(slug: str, registry: dict) -> dict | None:
    """Return the local declaration for a fixed first-party slug only."""
    if slug not in {"sanctuary", "orchard"}:
        return None
    world = registry["by_slug"].get(slug)
    return json.loads(json.dumps(world)) if world is not None else None
