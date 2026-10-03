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


def _returned_svg(ghot_witness: dict) -> tuple[str, str]:
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
    return svg_text, svg_sha


def _run_look_twice(
    repos: list[RepoStatus],
    action: str,
    request: dict,
    timeout: float = 60.0,
) -> dict:
    root = _find_autodisco(repos)
    script = root / "scripts" / "look-twice.mjs"
    if not script.is_file():
        raise AutodiscoApertureError(
            "Autodisco checkout does not contain scripts/look-twice.mjs"
        )
    try:
        completed = subprocess.run(
            ["node", str(script)],
            cwd=root,
            input=json.dumps({"action": action, "request": request}),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AutodiscoApertureError(
            f"Autodisco LOOK TWICE {action} could not run: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise AutodiscoApertureError(
            f"Autodisco LOOK TWICE {action} refused the request: "
            f"{detail or 'unknown error'}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AutodiscoApertureError(
            f"Autodisco LOOK TWICE {action} returned invalid JSON"
        ) from exc
    if not isinstance(result, dict):
        raise AutodiscoApertureError(
            f"Autodisco LOOK TWICE {action} returned a non-object"
        )
    return result


def prepare_look_twice(
    ghot_witness: dict,
    repos: list[RepoStatus],
) -> dict:
    svg_text, svg_sha = _returned_svg(ghot_witness)
    pair = _run_look_twice(
        repos,
        "prepare",
        {
            "schema": "autodisco.look-twice-prepare-request/v0",
            "artifact": {
                "media_type": "image/svg+xml",
                "sha256": svg_sha,
                "text": svg_text,
            },
        },
    )
    if pair.get("schema") != "autodisco.look-twice-pair/v0":
        raise AutodiscoApertureError("unexpected LOOK TWICE pair schema")
    if pair.get("source", {}).get("sha256") != svg_sha:
        raise AutodiscoApertureError("LOOK TWICE pair changed the source artifact")
    packets = pair.get("packets")
    if not isinstance(packets, list) or len(packets) != 2:
        raise AutodiscoApertureError("LOOK TWICE did not prepare exactly two packets")
    listener_ids = {
        packet.get("listener", {}).get("id")
        for packet in packets
        if isinstance(packet, dict)
    }
    if len(listener_ids) != 2 or None in listener_ids:
        raise AutodiscoApertureError("LOOK TWICE packets do not name two listeners")
    for packet in packets:
        if packet.get("content") != svg_text:
            raise AutodiscoApertureError(
                "LOOK TWICE packet changed the returned SVG bytes"
            )
        if "NO OTHER LISTENER RESPONSE" not in packet.get("prohibitions", []):
            raise AutodiscoApertureError(
                "LOOK TWICE packet lost cross-listener isolation law"
            )
    return pair


def run_look_twice_encounters(
    pair: dict,
    repos: list[RepoStatus],
) -> dict:
    result = _run_look_twice(
        repos,
        "encounter",
        {
            "schema": "autodisco.look-twice-encounter-request/v0",
            "pair": pair,
        },
        timeout=90.0,
    )
    if result.get("schema") != "autodisco.look-twice-encounter-result/v0":
        raise AutodiscoApertureError("unexpected LOOK TWICE encounter schema")
    if result.get("pair_id") != pair.get("pair_id"):
        raise AutodiscoApertureError("LOOK TWICE encounter changed the pair identity")
    status = result.get("status")
    responses = result.get("first_responses")
    if status == "packets-only":
        if responses != [] or result.get("model_used") is not None:
            raise AutodiscoApertureError(
                "packets-only LOOK TWICE result contains simulated responses"
            )
        return result
    if status != "two-first-responses-sealed":
        raise AutodiscoApertureError("unexpected LOOK TWICE encounter status")
    if not isinstance(responses, list) or len(responses) != 2:
        raise AutodiscoApertureError("LOOK TWICE did not seal two first responses")
    packet_ids = {
        packet.get("packet_id")
        for packet in pair.get("packets", [])
        if isinstance(packet, dict)
    }
    seen_packets: set[str] = set()
    seen_listeners: set[str] = set()
    for response in responses:
        if not isinstance(response, dict):
            raise AutodiscoApertureError("LOOK TWICE sealed response is malformed")
        if response.get("pair_id") != pair.get("pair_id"):
            raise AutodiscoApertureError("LOOK TWICE response changed pair identity")
        packet_id = response.get("packet_id")
        listener_id = response.get("listener", {}).get("id")
        if packet_id not in packet_ids or packet_id in seen_packets:
            raise AutodiscoApertureError("LOOK TWICE response packet binding is invalid")
        if not isinstance(listener_id, str) or listener_id in seen_listeners:
            raise AutodiscoApertureError("LOOK TWICE response listener binding is invalid")
        if not str(response.get("first_response_id", "")).startswith(
            "autodisco-look-twice-response-v0:"
        ):
            raise AutodiscoApertureError("LOOK TWICE first response identity is missing")
        seen_packets.add(packet_id)
        seen_listeners.add(listener_id)
    return result


def run_look_twice_dialogue(
    pair: dict,
    first_responses: list[dict],
    repos: list[RepoStatus],
) -> dict:
    result = _run_look_twice(
        repos,
        "dialogue",
        {
            "schema": "autodisco.look-twice-dialogue-request/v0",
            "pair": pair,
            "first_responses": first_responses,
        },
        timeout=90.0,
    )
    if result.get("schema") != "autodisco.look-twice-dialogue-result/v0":
        raise AutodiscoApertureError("unexpected LOOK TWICE dialogue schema")
    packet = result.get("dialogue_packet")
    if not isinstance(packet, dict):
        raise AutodiscoApertureError("LOOK TWICE dialogue packet is missing")
    if packet.get("pair_id") != pair.get("pair_id"):
        raise AutodiscoApertureError("LOOK TWICE dialogue changed pair identity")
    if "content" in packet or "artifact" in packet:
        raise AutodiscoApertureError("LOOK TWICE dialogue reopened the source artifact")
    sealed = packet.get("sealed_first_responses")
    if not isinstance(sealed, list) or len(sealed) != 2:
        raise AutodiscoApertureError(
            "LOOK TWICE dialogue does not contain two sealed responses"
        )
    status = result.get("status")
    if status == "dialogue-packet-only":
        if result.get("dialogue") is not None or result.get("model_used") is not None:
            raise AutodiscoApertureError(
                "dialogue-packet-only result contains simulated dialogue"
            )
        return result
    if status != "dialogue-sealed":
        raise AutodiscoApertureError("unexpected LOOK TWICE dialogue status")
    dialogue = result.get("dialogue")
    if not isinstance(dialogue, dict):
        raise AutodiscoApertureError("LOOK TWICE sealed dialogue is missing")
    if not isinstance(result.get("dialogue_id"), str):
        raise AutodiscoApertureError("LOOK TWICE dialogue identity is missing")
    if dialogue.get("lingering_intrigue") is not True and dialogue.get("door_seed") is not None:
        raise AutodiscoApertureError(
            "LOOK TWICE supplied a door seed without lingering intrigue"
        )
    return result
