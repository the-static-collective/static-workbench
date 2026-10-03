from __future__ import annotations

import base64
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


def _run_autodisco_json(
    repos: list[RepoStatus],
    script_name: str,
    payload: dict,
    timeout: float = 90.0,
) -> dict:
    root = _find_autodisco(repos)
    script = root / "scripts" / script_name
    if not script.is_file():
        raise AutodiscoApertureError(
            f"Autodisco checkout does not contain scripts/{script_name}"
        )
    try:
        completed = subprocess.run(
            ["node", str(script)],
            cwd=root,
            input=json.dumps(payload),
            text=True,
            capture_output=True,
            check=False,
            timeout=timeout,
            env={**os.environ, "LC_ALL": "C"},
        )
    except (OSError, subprocess.SubprocessError) as exc:
        raise AutodiscoApertureError(
            f"Autodisco {script_name} could not run: {exc}"
        ) from exc
    if completed.returncode != 0:
        detail = completed.stderr.strip()
        raise AutodiscoApertureError(
            f"Autodisco {script_name} refused the request: "
            f"{detail or 'unknown error'}"
        )
    try:
        result = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise AutodiscoApertureError(
            f"Autodisco {script_name} returned invalid JSON"
        ) from exc
    if not isinstance(result, dict):
        raise AutodiscoApertureError(
            f"Autodisco {script_name} returned a non-object"
        )
    return result


def build_audio_window(
    source_path: Path,
    receipt_id: str,
    state_dir: Path,
    repos: list[RepoStatus],
    *,
    start_ms: int,
    end_ms: int,
    window_label: str,
) -> dict:
    source_path = Path(source_path)
    if not source_path.is_file():
        raise AutodiscoApertureError("selected audio source is not a file")

    result = _run_autodisco_json(
        repos,
        "audio-window.mjs",
        {
            "schema": "autodisco.audio-window-request/v0",
            "source_path": str(source_path),
            "start_ms": start_ms,
            "end_ms": end_ms,
            "declared_metadata": {
                "window_label": window_label,
            },
        },
    )
    if result.get("schema") != "autodisco.audio-window/v0":
        raise AutodiscoApertureError("unexpected Autodisco audio-window schema")

    window_id = result.get("window_id")
    canonical = result.get("canonical_audio")
    if (
        not isinstance(window_id, str)
        or not window_id.startswith("autodisco-audio-window-v0:")
        or not isinstance(canonical, dict)
        or canonical.get("media_type") != "audio/wav"
    ):
        raise AutodiscoApertureError("Autodisco audio-window result is incomplete")
    encoded = canonical.get("base64")
    expected_sha = canonical.get("sha256")
    expected_size = canonical.get("size_bytes")
    if (
        not isinstance(encoded, str)
        or not isinstance(expected_sha, str)
        or not isinstance(expected_size, int)
    ):
        raise AutodiscoApertureError("Autodisco audio-window bytes are missing")
    try:
        audio_bytes = base64.b64decode(encoded, validate=True)
    except (ValueError, TypeError) as exc:
        raise AutodiscoApertureError("Autodisco audio-window base64 is invalid") from exc
    if len(audio_bytes) != expected_size:
        raise AutodiscoApertureError("Autodisco audio-window size changed in transit")
    if hashlib.sha256(audio_bytes).hexdigest() != expected_sha:
        raise AutodiscoApertureError("Autodisco audio-window digest changed in transit")

    target = (
        Path(state_dir)
        / "doorhouse-audio"
        / receipt_id
        / (window_id.replace(":", "-") + ".wav")
    )
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists():
        existing = target.read_bytes()
        if hashlib.sha256(existing).hexdigest() != expected_sha:
            raise AutodiscoApertureError(
                "existing House audio materialization conflicts with window digest"
            )
    else:
        target.write_bytes(audio_bytes)

    stored_window = json.loads(json.dumps(result))
    stored_window["canonical_audio"].pop("base64", None)
    stored_window["canonical_audio"]["base64_sha256"] = hashlib.sha256(
        encoded.encode("utf-8")
    ).hexdigest()

    return {
        "schema": "workbench.audio-window-materialized/v0",
        "window_id": window_id,
        "source_path": str(source_path),
        "audio_path": str(target),
        "audio_sha256": expected_sha,
        "audio_size_bytes": expected_size,
        "window": stored_window,
        "laws": [
            "LOCAL SOURCE PATH != LISTENER CONTEXT",
            "MATERIALIZED WAV != WHOLE TRACK",
            "WINDOW DIGEST BINDS HEARD BYTES",
        ],
    }


def inflate_audio_window(materialized: dict) -> dict:
    if (
        not isinstance(materialized, dict)
        or materialized.get("schema") != "workbench.audio-window-materialized/v0"
    ):
        raise AutodiscoApertureError("invalid materialized audio-window witness")
    stored = materialized.get("window")
    audio_path = materialized.get("audio_path")
    if not isinstance(stored, dict) or not isinstance(audio_path, str):
        raise AutodiscoApertureError("materialized audio-window witness is incomplete")
    path = Path(audio_path)
    if not path.is_file():
        raise AutodiscoApertureError("materialized audio window is missing from House state")
    audio_bytes = path.read_bytes()
    audio_sha = hashlib.sha256(audio_bytes).hexdigest()
    if (
        audio_sha != materialized.get("audio_sha256")
        or len(audio_bytes) != materialized.get("audio_size_bytes")
    ):
        raise AutodiscoApertureError(
            "materialized audio window no longer matches its House witness"
        )
    result = json.loads(json.dumps(stored))
    encoded = base64.b64encode(audio_bytes).decode("ascii")
    expected_b64_sha = result.get("canonical_audio", {}).pop("base64_sha256", None)
    if (
        not isinstance(expected_b64_sha, str)
        or hashlib.sha256(encoded.encode("utf-8")).hexdigest() != expected_b64_sha
    ):
        raise AutodiscoApertureError(
            "materialized audio window transport identity changed"
        )
    result["canonical_audio"]["base64"] = encoded
    return result


def prepare_audio_look_twice(
    materialized: dict,
    repos: list[RepoStatus],
) -> dict:
    window = inflate_audio_window(materialized)
    pair = _run_autodisco_json(
        repos,
        "audio-look-twice.mjs",
        {
            "action": "prepare",
            "request": {
                "schema": "autodisco.audio-look-twice-prepare-request/v0",
                "window": window,
            },
        },
    )
    if pair.get("schema") != "autodisco.audio-look-twice-pair/v0":
        raise AutodiscoApertureError("unexpected audio LOOK TWICE pair schema")
    ref = pair.get("window_ref")
    if (
        not isinstance(ref, dict)
        or ref.get("window_id") != materialized.get("window_id")
        or ref.get("audio_sha256") != materialized.get("audio_sha256")
    ):
        raise AutodiscoApertureError("audio LOOK TWICE pair changed window identity")
    packets = pair.get("packets")
    if not isinstance(packets, list) or len(packets) != 2:
        raise AutodiscoApertureError("audio LOOK TWICE did not prepare two booths")
    return pair


def run_audio_look_twice_encounters(
    materialized: dict,
    pair: dict,
    repos: list[RepoStatus],
) -> dict:
    window = inflate_audio_window(materialized)
    result = _run_autodisco_json(
        repos,
        "audio-look-twice.mjs",
        {
            "action": "encounter",
            "request": {
                "schema": "autodisco.audio-look-twice-encounter-request/v0",
                "pair": pair,
                "window": window,
            },
        },
        timeout=120.0,
    )
    if result.get("schema") != "autodisco.audio-look-twice-encounter-result/v0":
        raise AutodiscoApertureError("unexpected audio LOOK TWICE encounter schema")
    if (
        result.get("pair_id") != pair.get("pair_id")
        or result.get("window_id") != materialized.get("window_id")
    ):
        raise AutodiscoApertureError("audio LOOK TWICE encounter changed identity")
    if result.get("status") == "packets-only":
        if result.get("first_responses") != [] or result.get("model_used") is not None:
            raise AutodiscoApertureError(
                "audio packets-only result contains simulated first listens"
            )
        return result
    if result.get("status") != "two-first-responses-sealed":
        raise AutodiscoApertureError("unexpected audio LOOK TWICE encounter status")
    firsts = result.get("first_responses")
    if not isinstance(firsts, list) or len(firsts) != 2:
        raise AutodiscoApertureError("audio LOOK TWICE did not seal two first listens")
    listener_ids = {
        item.get("listener", {}).get("id")
        for item in firsts
        if isinstance(item, dict)
    }
    if len(listener_ids) != 2 or None in listener_ids:
        raise AutodiscoApertureError("audio LOOK TWICE listeners are not distinct")
    return result


def run_audio_look_twice_dialogue(
    pair: dict,
    first_responses: list[dict],
    repos: list[RepoStatus],
) -> dict:
    result = _run_autodisco_json(
        repos,
        "audio-look-twice.mjs",
        {
            "action": "dialogue",
            "request": {
                "schema": "autodisco.audio-look-twice-dialogue-request/v0",
                "pair": pair,
                "first_responses": first_responses,
            },
        },
        timeout=120.0,
    )
    if result.get("schema") != "autodisco.audio-look-twice-dialogue-result/v0":
        raise AutodiscoApertureError("unexpected audio LOOK TWICE dialogue schema")
    packet = result.get("dialogue_packet")
    if not isinstance(packet, dict) or packet.get("pair_id") != pair.get("pair_id"):
        raise AutodiscoApertureError("audio LOOK TWICE dialogue changed pair identity")
    serialized = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    if '"base64"' in serialized or "UklGR" in serialized:
        raise AutodiscoApertureError(
            "audio LOOK TWICE dialogue reopened the audio window"
        )
    if result.get("status") == "dialogue-packet-only":
        if result.get("dialogue") is not None or result.get("model_used") is not None:
            raise AutodiscoApertureError(
                "audio dialogue-packet-only result contains simulated dialogue"
            )
        return result
    if result.get("status") != "dialogue-sealed":
        raise AutodiscoApertureError("unexpected audio LOOK TWICE dialogue status")
    dialogue = result.get("dialogue")
    if not isinstance(dialogue, dict):
        raise AutodiscoApertureError("audio LOOK TWICE dialogue is missing")
    if (
        dialogue.get("lingering_intrigue") is not True
        and dialogue.get("door_seed") is not None
    ):
        raise AutodiscoApertureError(
            "audio LOOK TWICE door seed lacks lingering intrigue"
        )
    return result
