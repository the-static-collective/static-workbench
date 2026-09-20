"""HOUSE Impact Desk 001: bounded committed-source snapshots for Dogram research.

The target repository is never imported or executed. Dogram is a separate,
explicitly selected clean local checkout; its experimental repo-impact kernel
is invoked by a fixed, isolated Python command only after human confirmation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

from .config import WorkbenchConfig
from .repos import RepoStatus, discover_repositories

MAX_FILES = 64
MAX_FILE_BYTES = 65536
MAX_TOTAL_BYTES = 2 * 1024 * 1024
_SAFE_PATH = re.compile(r"^[A-Za-z0-9_.\-/]+$")
_DOGRAM_SCRIPT = (
    "import json,sys;"
    "sys.path.insert(0,sys.argv[1]);"
    "from dogram.repo_impact import build_repo_impact;"
    "print(json.dumps(build_repo_impact(sys.argv[2],sys.argv[3]),sort_keys=True))"
)


class ImpactDeskError(ValueError):
    """A refused snapshot, invocation or receipt boundary."""


def _git(repo: Path, *args: str, binary: bool = False) -> str | bytes:
    try:
        completed = subprocess.run(
            ["git", "-C", str(repo), *args],
            capture_output=True,
            check=False,
            timeout=8,
            env={**os.environ, "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C"},
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise ImpactDeskError("Git snapshot unavailable") from exc
    if completed.returncode:
        raise ImpactDeskError("Git snapshot unavailable or repository has no parent commit")
    if binary:
        return completed.stdout
    try:
        return completed.stdout.decode("utf-8").strip()
    except UnicodeDecodeError as exc:
        raise ImpactDeskError("Git returned an undecodable reference") from exc


def _selected_repo(config: WorkbenchConfig, root_id: str, repo_path: str) -> RepoStatus:
    for repo in discover_repositories(config.roots, config.max_repo_depth):
        if repo.root_id == root_id and repo.relative_path == repo_path:
            return repo
    raise ImpactDeskError("Repository is not present under the selected configured root")


def _entries(repo: Path, commit: str) -> list[tuple[str, str]]:
    raw = _git(repo, "ls-tree", "-rz", "--full-tree", commit, binary=True)
    assert isinstance(raw, bytes)
    entries: list[tuple[str, str]] = []
    total = 0
    for row in raw.split(b"\0"):
        if not row:
            continue
        try:
            metadata, raw_path = row.split(b"\t", 1)
            mode, kind, raw_sha = metadata.decode("ascii").split()
            path = raw_path.decode("utf-8")
        except (UnicodeDecodeError, UnicodeError, ValueError) as exc:
            raise ImpactDeskError("Invalid tree entry") from exc
        if not path.endswith(".py"):
            continue
        if (
            kind != "blob" or mode not in {"100644", "100755"}
            or not _SAFE_PATH.fullmatch(path)
            or any(part in {"", ".", "..", ".git", "__pycache__"} for part in path.split("/"))
        ):
            raise ImpactDeskError("Unsafe Python source entry in selected Git tree")
        size = int(_git(repo, "cat-file", "-s", raw_sha))
        if size > MAX_FILE_BYTES:
            raise ImpactDeskError("Python source exceeds the per-file snapshot limit")
        total += size
        entries.append((path, raw_sha))
        if len(entries) > MAX_FILES or total > MAX_TOTAL_BYTES:
            raise ImpactDeskError("Python source exceeds the bounded snapshot limits")
    if not entries:
        raise ImpactDeskError("Selected Git tree has no supported Python source files")
    return sorted(entries)


def _snapshot_digest(commit: str, entries: list[tuple[str, str]]) -> str:
    data = json.dumps({"commit": commit, "entries": entries}, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def preview_impact(config: WorkbenchConfig, root_id: str, repo_path: str) -> dict[str, Any]:
    selected = _selected_repo(config, root_id, repo_path)
    if "python" not in selected.stacks:
        raise ImpactDeskError("Select a discovered Python repository")
    repo = Path(selected.path)
    head = str(_git(repo, "rev-parse", "--verify", "HEAD^{commit}"))
    baseline = str(_git(repo, "rev-parse", "--verify", "HEAD^1^{commit}"))
    old = _entries(repo, baseline)
    new = _entries(repo, head)

    dogram = next(
        (item for item in discover_repositories(config.roots, config.max_repo_depth)
         if item.name.lower() == "dogram" and item.root_id is not None),
        None,
    )
    dogram_info: dict[str, Any] = {"available": False, "clean": False, "commit": None}
    if dogram is not None and (Path(dogram.path) / "dogram" / "repo_impact.py").is_file():
        dogram_info = {
            "available": True, "clean": not dogram.dirty,
            "commit": str(_git(Path(dogram.path), "rev-parse", "--verify", "HEAD^{commit}")),
        }

    base_digest = _snapshot_digest(baseline, old)
    candidate_digest = _snapshot_digest(head, new)
    input_digest = hashlib.sha256(
        json.dumps([root_id, repo_path, base_digest, candidate_digest],
                   separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    return {
        "root_id": root_id, "repo_path": repo_path,
        "baseline_commit": baseline, "candidate_commit": head,
        "baseline_file_count": len(old), "candidate_file_count": len(new),
        "baseline_snapshot_sha256": base_digest,
        "candidate_snapshot_sha256": candidate_digest,
        "input_sha256": input_digest,
        "working_tree_excluded": True,
        "working_tree_dirty": selected.dirty,
        "dogram": dogram_info,
    }


def _materialize(repo: Path, commit: str, dest: Path) -> None:
    for path, sha in _entries(repo, commit):
        data = _git(repo, "cat-file", "blob", sha, binary=True)
        assert isinstance(data, bytes)
        if len(data) > MAX_FILE_BYTES:
            raise ImpactDeskError("Python source grew beyond the snapshot limit")
        target = dest.joinpath(*path.split("/"))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)


def run_impact(
    config: WorkbenchConfig, root_id: str, repo_path: str,
    expected_input_sha256: str, expected_candidate_commit: str, expected_dogram_commit: str,
) -> dict[str, Any]:
    preview = preview_impact(config, root_id, repo_path)
    if (
        expected_input_sha256 != preview["input_sha256"]
        or expected_candidate_commit != preview["candidate_commit"]
        or expected_dogram_commit != preview["dogram"]["commit"]
    ):
        raise ImpactDeskError("Snapshot or Dogram version changed; review the preview again")
    if not preview["dogram"]["available"] or not preview["dogram"]["clean"]:
        raise ImpactDeskError("A clean, discovered Dogram checkout is required for this experiment")
    repo = Path(_selected_repo(config, root_id, repo_path).path)
    dogram = _selected_dogram(config)
    if str(_git(dogram, "rev-parse", "--verify", "HEAD^{commit}")) != expected_dogram_commit:
        raise ImpactDeskError("Dogram HEAD moved before invocation")
    if _git(dogram, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise ImpactDeskError("Dogram checkout became dirty before invocation")

    with tempfile.TemporaryDirectory(prefix="house-dogram-") as folder:
        baseline = Path(folder) / "baseline"
        candidate = Path(folder) / "candidate"
        baseline.mkdir()
        candidate.mkdir()
        _materialize(repo, preview["baseline_commit"], baseline)
        _materialize(repo, preview["candidate_commit"], candidate)
        try:
            proc = subprocess.run(
                [sys.executable, "-I", "-c", _DOGRAM_SCRIPT, str(dogram), str(baseline), str(candidate)],
                capture_output=True, timeout=20, check=False,
                env={**os.environ, "PYTHONNOUSERSITE": "1"},
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise ImpactDeskError("Dogram invocation failed or timed out") from exc
    if proc.returncode or len(proc.stdout) > 1_000_000:
        raise ImpactDeskError("Dogram calculation refused or exceeded its output limit")
    try:
        calculation = json.loads(proc.stdout)
        if not isinstance(calculation, dict) or not all(
            field in calculation for field in
            ("graph_before_digest", "graph_after_digest", "node_delta", "edge_delta", "reachability_delta")
        ):
            raise ValueError("unexpected Dogram result")
    except (UnicodeDecodeError, ValueError) as exc:
        raise ImpactDeskError("Invalid Dogram calculation output") from exc

    report = {
        "schema": "house.dogram-impact-report/v0.1",
        "scope": "first-parent committed Python source only; working tree excluded",
        "source": {key: preview[key] for key in (
            "root_id", "repo_path", "baseline_commit", "candidate_commit",
            "baseline_snapshot_sha256", "candidate_snapshot_sha256", "input_sha256",
            "working_tree_excluded", "working_tree_dirty"
        )},
        "dogram_commit": expected_dogram_commit,
        "dogram_internal_result": calculation,
        "non_claims": [
            "not a dogram.receipt/v0 public operator receipt",
            "import graph reachability is not execution or causation",
            "structural impact is not a quality, safety, or merge verdict",
            "Workbench storage is not project authority",
        ],
    }
    canonical = json.dumps(report, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")
    report_id = hashlib.sha256(canonical).hexdigest()
    folder = config.state_dir / "dogram-impact"
    folder.mkdir(mode=0o700, parents=True, exist_ok=True)
    path = folder / f"{report_id}.json"
    if path.exists():
        if path.read_bytes() != canonical:
            raise ImpactDeskError("Stored report digest collision or corruption")
    else:
        with tempfile.NamedTemporaryFile(dir=folder, prefix=".impact-", delete=False) as temp:
            temp_path = Path(temp.name)
            os.chmod(temp_path, 0o600)
            try:
                temp.write(canonical)
                temp.flush()
                os.fsync(temp.fileno())
            finally:
                pass
        try:
            os.replace(temp_path, path)
        finally:
            temp_path.unlink(missing_ok=True)
    return {"report_id": report_id, "report": report}


def _selected_dogram(config: WorkbenchConfig) -> Path:
    choices = [
        Path(item.path) for item in discover_repositories(config.roots, config.max_repo_depth)
        if item.name.lower() == "dogram" and (Path(item.path) / "dogram" / "repo_impact.py").is_file()
    ]
    if len(choices) != 1:
        raise ImpactDeskError("Exactly one local Dogram checkout is required")
    return choices[0]


def read_report(config: WorkbenchConfig, report_id: str) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{64}", report_id):
        raise ImpactDeskError("Invalid report identity")
    path = config.state_dir / "dogram-impact" / f"{report_id}.json"
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise ImpactDeskError("Report not found") from exc
    if hashlib.sha256(data).hexdigest() != report_id:
        raise ImpactDeskError("Report digest does not match saved bytes")
    return json.loads(data)
