"""End-to-end HOUSE -> actual checked-out Dogram impact smoke.

Run from Workbench root after checking out pinned Dogram under .compat/Dogram.
No network access or project execution is used by the smoke itself.
"""
from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.dogram_impact import preview_impact, run_impact


def git(repo: Path, *args: str) -> None:
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


def commit(repo: Path, message: str) -> None:
    git(repo, "add", ".")
    git(repo, "-c", "user.name=Workbench Fixture",
        "-c", "user.email=fixture@example.invalid", "commit", "-m", message)


def main() -> None:
    checked_out_dogram = (Path(__file__).resolve().parents[1] / ".compat" / "Dogram").resolve()
    if not (checked_out_dogram / "dogram" / "repo_impact.py").is_file():
        raise SystemExit("Missing pinned upstream Dogram checkout")
    with tempfile.TemporaryDirectory(prefix="house-dogram-integration-") as directory:
        root = Path(directory)
        source_root = root / "sources"
        source = source_root / "demo"
        source.mkdir(parents=True)
        git(source, "init", "-b", "main")
        (source / "pyproject.toml").write_text('[project]\nname="demo"\nversion="0.0.1"\n')
        (source / "a.py").write_text("x = 1\n")
        commit(source, "baseline")
        (source / "b.py").write_text("from a import x\n")
        commit(source, "candidate")
        config = WorkbenchConfig(
            bind_host="127.0.0.1", port=13700,
            state_dir=root / "house-state",
            roots=(RootConfig("sources", source_root),
                   RootConfig("compat", checked_out_dogram.parent)),
            max_repo_depth=2,
        )
        preview = preview_impact(config, "sources", "demo")
        assert preview["dogram"]["available"] and preview["dogram"]["clean"]
        result = run_impact(config, "sources", "demo", preview["input_sha256"],
                            preview["candidate_commit"], preview["dogram"]["commit"])
        calculation = result["report"]["dogram_internal_result"]
        assert calculation["node_delta"]["added"] == ["b.py"], calculation
        assert ["b.py", "a.py"] in calculation["edge_delta"]["added"], calculation
        assert result["report"]["dogram_commit"] == preview["dogram"]["commit"]
        print("UPSTREAM DOGRAM SMOKE PASS: +b.py, +b.py->a.py, pinned receipt retained")


if __name__ == "__main__":
    main()
