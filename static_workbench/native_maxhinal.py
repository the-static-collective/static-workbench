"""HOUSE's native deterministic Maxhinal: explicitly selected local fuel only.

Not Daily Slice Maxhinal. No code execution, automatic file discovery, semantic
model, remote access, project write, inferred image/audio contents, or promotion.
"""
from __future__ import annotations

import hashlib
import json
import mimetypes
import random
import re
import stat
from pathlib import Path
from typing import Any

from .config import RootConfig
from .creator_shelf import CreatorShelf

MAX_FUELS = 4
MAX_FILE_BYTES = 16 * 1024 * 1024
MAX_TEXT_BYTES = 128 * 1024
MAX_EXCERPT = 1600
MAX_PATH_DEPTH = 12
_MODES = ("discontinuity", "braid", "compose", "pressure", "shuffle")
_UNSAFE_NAMES = ("secret", "token", "password", "credential", "private", ".env", "keyring")
_SKIP_DIRS = (".git", ".ssh", ".gnupg", ".config", "node_modules", ".venv", "__pycache__")
_STOP = frozenset("the a an and or of to in is it that this for from with at by on not are was were".split())


class FuelConflict(ValueError):
    """Fuel changed since the last human preview."""


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _checked_file(roots: tuple[RootConfig, ...], item: dict[str, Any]) -> dict[str, Any]:
    root = next((r for r in roots if r.id == item["root_id"]), None)
    if root is None:
        raise ValueError("choose an explicitly configured root")
    name = item["path"]
    p = Path(name)
    if (not name or len(name) > 512 or p.is_absolute() or len(p.parts) > MAX_PATH_DEPTH
        or any(part in ("", ".", "..") or part.startswith(".")
               or part.casefold() in _SKIP_DIRS
               or any(word in part.casefold() for word in _UNSAFE_NAMES) for part in p.parts)):
        raise ValueError("only safe root-relative file paths may be used as fuel")
    base = root.path.resolve(strict=True)
    target = base
    for component in p.parts:
        target = target / component
        if target.is_symlink():
            raise ValueError("symlinked fuel is refused")
    target = target.resolve(strict=True)
    target.relative_to(base)
    info = target.stat()
    if not stat.S_ISREG(info.st_mode) or not 0 < info.st_size <= MAX_FILE_BYTES:
        raise ValueError("fuel must be a regular nonempty file of at most 16 MiB")
    # Exclude named pipes, devices and symlink swaps; bounded reads of ordinary files only.
    with target.open("rb") as handle:
        raw = handle.read(MAX_FILE_BYTES + 1)
        opened = handle.stat()
    if (len(raw) != info.st_size or len(raw) > MAX_FILE_BYTES or opened.st_ino != info.st_ino
        or opened.st_dev != info.st_dev or opened.st_mtime_ns != info.st_mtime_ns):
        raise FuelConflict("file changed during fuel inspection; select again")
    mime, _ = mimetypes.guess_type(target.name)
    text = None
    if len(raw) <= MAX_TEXT_BYTES and b"\x00" not in raw:
        try:
            decoded = raw.decode("utf-8")
            if all(ch.isprintable() or ch in "\n\r\t" for ch in decoded):
                text = decoded[:MAX_EXCERPT]
        except UnicodeError:
            pass
    return {
        "kind": "file", "root_id": root.id, "path": name, "name": target.name,
        "byte_size": len(raw), "sha256": digest(raw), "media_type": mime or "application/octet-stream",
        "reading": "bounded_utf8_excerpt" if text is not None else "metadata_only",
        "excerpt": text, "excerpt_truncated": text is not None and len(raw.decode("utf-8")) > MAX_EXCERPT,
        "authority": "none",
    }


def preview_fuels(roots: tuple[RootConfig, ...], shelf: CreatorShelf, items: list[dict[str, Any]]) -> dict[str, Any]:
    if not 1 <= len(items) <= MAX_FUELS:
        raise ValueError("select between one and four explicit fuel items")
    result = []
    for item in items:
        if item["kind"] == "file":
            result.append(_checked_file(roots, item))
        elif item["kind"] == "source_pack":
            pack = shelf.get_pack(item["pack_id"])
            if pack is None:
                raise ValueError("selected Creator Desk source pack is missing")
            sources = pack.get("sources")
            if not isinstance(sources, list) or not 1 <= len(sources) <= 8:
                raise ValueError("selected Creator Desk source pack is invalid")
            result.append({
                "kind": "source_pack", "pack_id": item["pack_id"],
                "pack_sha256": pack["pack_sha256"], "source_count": pack["source_count"],
                "excerpt": "\n".join(str(src.get("excerpt", "")) for src in sources)[:MAX_EXCERPT],
                "reading": "saved_human_selected_excerpts", "authority": "none",
            })
        else:
            raise ValueError("unsupported HOUSE fuel kind")
    identities = [(row["kind"], row.get("root_id"), row.get("path"), row.get("pack_id")) for row in result]
    if len(set(identities)) != len(identities):
        raise ValueError("repeated fuel selections are not allowed")
    return {
        "format": "house.maxhinal-fuel-preview/v0.1", "fuels": result,
        "fuel_sha256": digest(canonical(result)), "authority": "none",
        "notice": "Explicit local fuel only; binary material supplies metadata, not inferred visual or auditory meaning.",
    }


def _tokens(value: dict[str, Any]) -> set[str]:
    material = (value.get("excerpt") or "") if value["kind"] == "source_pack" or value["reading"] == "bounded_utf8_excerpt" else ""
    return {w for w in re.findall(r"[a-z0-9]{3,}", material.casefold()) if w not in _STOP}


def spin(preview: dict[str, Any], mode: str, seed: str, question: str) -> dict[str, Any]:
    if mode not in _MODES:
        raise ValueError("unsupported native HOUSE chamber")
    if len(seed) > 100 or len(question) > 400:
        raise ValueError("seed or question exceeds bounded input")
    fuels = preview["fuels"]
    refs = [{"kind": f["kind"], "root_id": f.get("root_id"), "path": f.get("path"),
             "pack_id": f.get("pack_id"), "sha256": f.get("sha256", f.get("pack_sha256"))} for f in fuels]
    words = [_tokens(f) for f in fuels]
    overlap = sorted(set.intersection(*words)) if len(words) >= 2 else []
    outputs = []
    residuals = []
    bad_spins = []
    if mode == "discontinuity":
        outputs = [{
            "kind": "discontinuity_map",
            "surviving_literal_tokens": overlap,
            "nonoverlapping_tokens": [sorted(w - set(overlap))[:14] for w in words],
            "creative_question": question or "Which relation survives if surface resemblance is removed?",
            "status": "CREATIVE_HYPOTHESIS_ONLY",
        }]
        if len(fuels) < 2:
            residuals.append("One source cannot establish a cross-source discontinuity.")
        elif not overlap:
            residuals.append("No literal token overlap across the selected textual fuel.")
        bad_spins.append("Matching words do not establish shared identity, lineage, intent, or causation.")
    elif mode == "braid":
        outputs = [{
            "kind": "ordered_braid", "path": [
                {"source_index": i + 1, "ref": refs[i], "fragment": (f.get("excerpt") or f["name"] if f["kind"] == "file" else f.get("excerpt") or "")[:320]}
                for i, f in enumerate(fuels)
            ], "creative_question": question or "What new third thing could connect these independent roads?",
        }]
        residuals.append("Juxtaposition is not evidence of a relationship; order is a creative choice.")
    elif mode == "compose":
        outputs = [{
            "kind": "composition_prompt",
            "parts": [{"source_index": i + 1, "reference": refs[i],
                       "fragment": (f.get("excerpt") or f.get("name", "saved source pack"))[:320]} for i, f in enumerate(fuels)],
            "instruction": question or "Compose a new draft while preserving the separate sources and any disagreement.",
        }]
        residuals.append("Composition was proposed, not generated or published.")
    elif mode == "pressure":
        outputs = [{
            "kind": "pressure_questions",
            "candidate": question or "What is the apparent relation among these selected materials?",
            "discriminator": "What attributable observation would distinguish this relation from coincidence or shared vocabulary?",
            "counterexample": "What source or context would make the proposed relation fail?",
        }]
        bad_spins.append("A pleasing narrative is not a source-owned claim.")
    else:
        order = list(range(len(fuels)))
        random.Random(digest(canonical([seed, preview["fuel_sha256"], question]))).shuffle(order)
        outputs = [{
            "kind": "seeded_reorder", "order": [i + 1 for i in order],
            "fragments": [
                {"source_index": i + 1, "fragment": (fuels[i].get("excerpt") or fuels[i].get("name", "unknown"))[:320]}
                for i in order
            ],
            "creative_question": question or "What changes when the sources are read in this order?",
        }]
        residuals.append("Seeded reordering changes presentation, not source identity or chronology.")
    if any(f.get("reading") == "metadata_only" for f in fuels):
        residuals.append("At least one selected file was only inspected as metadata; no image, sound or binary meaning was inferred.")
    return {
        "format": "house.native-maxhinal-ride/v0.1",
        "engine": "house.native-maxhinal/v0.1", "mode": mode, "seed": seed,
        "question": question, "fuel_sha256": preview["fuel_sha256"],
        "fuels": fuels, "source_refs": refs, "outputs": outputs,
        "residuals": residuals, "bad_spins": bad_spins,
        "authority": "none", "promotion": "NONE",
        "notice": "HOUSE native deterministic creative projections; not a Daily Slice Maxhinal ride or independent evidence.",
    }
