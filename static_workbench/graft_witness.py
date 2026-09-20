"""GRAFT × Dogram: bounded, explicitly declared structural measurement.

This instruments a saved HOUSE-native Maxhinal ride without interpreting its
content, inferring relationships, changing any project, or promoting a proposal.
Only a user-declared finite graph is passed to Dogram's public v0 operator floor.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

from .config import WorkbenchConfig
from .creator_shelf import CreatorShelf
from .dogram_impact import ImpactDeskError, _git, _selected_dogram

MAX_NODES = 12
MAX_EDGES = 32
MAX_QUERIES = 8
_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}$")
_SCRIPT = (
    "import json,sys;"
    "sys.path.insert(0,sys.argv[1]);"
    "from dogram.engine import evaluate_specimen;"
    "print(json.dumps(evaluate_specimen(json.load(sys.stdin)),sort_keys=True))"
)


class GraftWitnessError(ValueError):
    pass


def canonical(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def sha(value: Any) -> str:
    return hashlib.sha256(canonical(value)).hexdigest()


def _ride(shelf: CreatorShelf, ride_id: int, ride_sha256: str) -> dict[str, Any]:
    if type(ride_id) is not int or ride_id < 1:
        raise GraftWitnessError("Choose an existing saved Maxhinal ride")
    ride = shelf.get_native_ride(ride_id)
    if ride is None or ride["ride_sha256"] != ride_sha256:
        raise GraftWitnessError("Maxhinal ride is missing or changed; select it again")
    content = {k: v for k, v in ride.items() if k not in ("id", "created_at", "ride_sha256")}
    if sha(content) != ride_sha256:
        raise GraftWitnessError("Stored Maxhinal ride no longer matches its digest")
    return ride


def _graph(raw: Any) -> dict[str, Any]:
    if not isinstance(raw, dict) or set(raw) != {"nodes", "edges"}:
        raise GraftWitnessError("Graph needs exactly nodes and edges")
    nodes, edges = raw["nodes"], raw["edges"]
    if (
        not isinstance(nodes, list) or not 2 <= len(nodes) <= MAX_NODES
        or any(not isinstance(n, str) or not _LABEL.fullmatch(n) for n in nodes)
        or len(set(nodes)) != len(nodes)
        or not isinstance(edges, list) or len(edges) > MAX_EDGES
    ):
        raise GraftWitnessError("Invalid or unbounded graph nodes/edges")
    node_set = set(nodes)
    pairs = []
    for edge in edges:
        if (not isinstance(edge, list) or len(edge) != 2
            or any(not isinstance(e, str) or e not in node_set for e in edge)):
            raise GraftWitnessError("Every graph edge must reference two declared nodes")
        pairs.append((edge[0], edge[1]))
    if len(set(pairs)) != len(pairs):
        raise GraftWitnessError("Duplicate graph edges")
    return {"nodes": sorted(nodes), "edges": [list(edge) for edge in sorted(pairs)]}


def _specimen(graph: dict[str, Any], operator: str, change: Any, queries: Any,
              ride_id: int, ride_sha256: str) -> dict[str, Any]:
    if operator not in {"reach", "ablate"} or not isinstance(change, dict):
        raise GraftWitnessError("Choose public reach@1 or ablate@1 with one declared change")
    if not isinstance(queries, list) or len(queries) > MAX_QUERIES:
        raise GraftWitnessError("Choose at most eight explicit graph-path queries")
    for query in queries:
        if (not isinstance(query, list) or len(query) != 2
            or any(not isinstance(n, str) or n not in graph["nodes"] for n in query)):
            raise GraftWitnessError("Query nodes must exist in the declared baseline graph")
    node_set = set(graph["nodes"])
    edge_set = {tuple(e) for e in graph["edges"]}
    if operator == "reach":
        if set(change) != {"op", "source", "target"} or change.get("op") not in {"ADD_EDGE", "REMOVE_EDGE"}:
            raise GraftWitnessError("GRAFT v0.1 measures one explicit ADD_EDGE or REMOVE_EDGE")
        edge = (change["source"], change["target"])
        if not all(type(n) is str and n in node_set for n in edge):
            raise GraftWitnessError("Changed edge endpoints must already exist")
        if (change["op"] == "ADD_EDGE") == (edge in edge_set):
            raise GraftWitnessError("Requested edge addition/removal conflicts with the baseline graph")
        inputs = {"graph": graph, "mutation": change, "queries": queries}
    else:
        if set(change) != {"kind", "source", "target"} or change.get("kind") != "edge":
            raise GraftWitnessError("GRAFT v0.1 ablates exactly one existing graph edge")
        edge = (change["source"], change["target"])
        if not all(type(n) is str and n in node_set for n in edge) or edge not in edge_set:
            raise GraftWitnessError("Ablated edge must exist in the declared baseline graph")
        inputs = {"graph": graph, "target": change, "requested_targets": queries}
    return {
        "schema": "dogram.specimen/v0",
        "specimen_id": f"house-graft-ride-{ride_id}-{ride_sha256[:12]}",
        "operator": operator, "operator_version": 1, "inputs": inputs,
        "assumptions": [
            "Graph is human-declared hypothetical structure, not an observed system.",
            "Edges assert only the user's proposed graph relation, not causation or implemented data flow.",
        ],
        "metadata": {"origin": "house.graft-structural-witness/v0.1", "ride_sha256": ride_sha256},
    }


def _dogram_version(config: WorkbenchConfig) -> tuple[Path, str]:
    try:
        path = _selected_dogram(config)
        commit = str(_git(path, "rev-parse", "--verify", "HEAD^{commit}"))
        if _git(path, "status", "--porcelain=v1", "--untracked-files=normal"):
            raise GraftWitnessError("Dogram checkout is dirty; choose a clean checkout")
        # Only the public operator floor is invoked, not an experimental parser.
        if not (path / "dogram" / "engine.py").is_file():
            raise GraftWitnessError("Selected Dogram checkout has no public operator engine")
        return path, commit
    except ImpactDeskError as exc:
        raise GraftWitnessError(str(exc)) from exc


def preview(config: WorkbenchConfig, shelf: CreatorShelf, ride_id: int,
            ride_sha256: str, graph: Any, operator: str,
            change: Any, queries: Any) -> dict[str, Any]:
    _ride(shelf, ride_id, ride_sha256)
    checked_graph = _graph(graph)
    specimen = _specimen(checked_graph, operator, change, queries, ride_id, ride_sha256)
    _path, dogram_commit = _dogram_version(config)
    return {
        "schema": "house.graft-structural-preview/v0.1",
        "ride_id": ride_id, "ride_sha256": ride_sha256,
        "dogram_commit": dogram_commit, "specimen_sha256": sha(specimen),
        "specimen": specimen, "authority": "none",
        "notice": "Review every declared node, edge, change and query. No graph relation was inferred from source content.",
    }


def measure(config: WorkbenchConfig, shelf: CreatorShelf, ride_id: int,
            ride_sha256: str, graph: Any, operator: str, change: Any,
            queries: Any, expected_specimen_sha256: str,
            expected_dogram_commit: str) -> dict[str, Any]:
    reviewed = preview(config, shelf, ride_id, ride_sha256, graph, operator, change, queries)
    if (reviewed["specimen_sha256"] != expected_specimen_sha256
        or reviewed["dogram_commit"] != expected_dogram_commit):
        raise GraftWitnessError("Graph, ride or Dogram version changed; review again")
    path, _ = _dogram_version(config)
    try:
        proc = subprocess.run(
            [sys.executable, "-I", "-B", "-c", _SCRIPT, str(path)],
            input=canonical(reviewed["specimen"]), capture_output=True,
            timeout=15, check=False, env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise GraftWitnessError("Dogram calculation failed or timed out") from exc
    if proc.returncode or len(proc.stdout) > 500_000:
        raise GraftWitnessError("Dogram calculation failed or exceeded output limit")
    _, after_commit = _dogram_version(config)
    if after_commit != expected_dogram_commit:
        raise GraftWitnessError("Dogram changed during calculation")
    try:
        receipt = json.loads(proc.stdout)
    except (UnicodeError, ValueError) as exc:
        raise GraftWitnessError("Dogram returned malformed JSON") from exc
    if (
        not isinstance(receipt, dict)
        or receipt.get("schema") != "dogram.receipt/v0"
        or receipt.get("status") != "OK"
        or receipt.get("operator") != operator
        or receipt.get("operator_version") != 1
        or receipt.get("input_digest") != expected_specimen_sha256
    ):
        raise GraftWitnessError("Dogram did not produce an OK receipt for the reviewed specimen")
    record = {
        "schema": "house.graft-structural-witness/v0.1",
        "ride_id": ride_id, "ride_sha256": ride_sha256,
        "dogram_commit": expected_dogram_commit,
        "specimen_sha256": expected_specimen_sha256,
        "specimen": reviewed["specimen"],
        "dogram_receipt": receipt,
        "non_claims": [
            "Human-declared graph; edges were not inferred from source material.",
            "Dogram receipt is a calculation witness, not evidence of implementation, causation or artistic continuity.",
            "No candidate was harvested, no project was changed, and no authority was granted.",
        ],
    }
    return shelf.save_graft_witness(record)
