from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path

from .repos import RepoStatus


class AutodiscoApertureError(RuntimeError):
    pass


def _find_autodisco(repos: list[RepoStatus]) -> Path:
    for repo in repos:
        root = Path(repo.path)
        script = root / "scripts" / "first-encounter.mjs"
        canon = root / "FIRST-LISTEN-RADIO.md"
        if script.is_file() and canon.is_file():
            return root
    raise AutodiscoApertureError(
        "A local Autodisco V20 checkout with scripts/first-encounter.mjs is required."
    )


def _sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def run_first_encounter(
    ghot_witness: dict,
    repos: list[RepoStatus],
    timeout: float = 45.0,
) -> dict:
    if not isinstance(ghot_witness, dict):
        raise AutodiscoApertureError("GHoT execution witness is required")
    artifact = ghot_witness.get("creative_artifact")
    if not isinstance(artifact, dict):
        raise AutodiscoApertureError("GHoT witness has no returned creative artifact")
    svg_path = artifact.get("svg_path")
    svg_sha = artifact.get("svg_sha256")
    if not isinstance(svg_path, str) or not isinstance(svg_sha, str):
        raise AutodiscoApertureError("returned SVG evidence is incomplete")

    path = Path(svg_path)
    if not path.is_file():
        raise AutodiscoApertureError("returned SVG is not present in local House state")
    svg_text = path.read_text(encoding="utf-8")
    if _sha256_text(svg_text) != svg_sha:
        raise AutodiscoApertureError("returned SVG no longer matches its witnessed digest")

    root = _find_autodisco(repos)
    script = root / "scripts" / "first-encounter.mjs"
    request = {
        "schema": "autodisco.first-encounter-request/v0",
        "artifact": {
            "media_type": "image/svg+xml",
            "sha256": svg_sha,
            "text": svg_text,
        },
    }
    try:
        completed = subprocess.run(
            ["node", str(script)],
            cwd=root,
            input=json.dumps(request),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AutodiscoApertureError(
            f"Autodisco first encounter could not run: {exc}"
        ) from exc

    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise AutodiscoApertureError(
            f"Autodisco refused the first encounter: {detail or 'unknown error'}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AutodiscoApertureError("Autodisco returned invalid JSON") from exc

    if not isinstance(result, dict):
        raise AutodiscoApertureError("Autodisco returned a non-object")
    if result.get("schema") != "autodisco.first-encounter-result/v0":
        raise AutodiscoApertureError("unexpected Autodisco first-encounter schema")
    if result.get("status") not in {"packet-only", "responded"}:
        raise AutodiscoApertureError("unexpected Autodisco first-encounter status")
    packet = result.get("packet")
    if not isinstance(packet, dict):
        raise AutodiscoApertureError("Autodisco packet is missing")
    source = packet.get("source")
    if not isinstance(source, dict) or source.get("sha256") != svg_sha:
        raise AutodiscoApertureError("Autodisco packet changed the source artifact")
    if packet.get("content") != svg_text:
        raise AutodiscoApertureError("Autodisco packet changed the source bytes")

    if result["status"] == "packet-only":
        if result.get("response") is not None or result.get("model_used") is not None:
            raise AutodiscoApertureError("packet-only result contains a simulated listener")
    else:
        response = result.get("response")
        response_sha = result.get("response_sha256")
        if not isinstance(response, dict) or not isinstance(response_sha, str):
            raise AutodiscoApertureError("fresh listener response is incomplete")
        modes = {
            item.get("mode")
            for item in response.get("observations", [])
            if isinstance(item, dict)
        }
        if "OBSERVED" not in modes or "INTERPRETATION" not in modes:
            raise AutodiscoApertureError("fresh listener did not preserve TAO distinctions")
        if not isinstance(result.get("model_used"), str) or not result["model_used"]:
            raise AutodiscoApertureError("fresh listener response has no real model identity")

    return result
