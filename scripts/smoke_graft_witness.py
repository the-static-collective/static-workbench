"""Smoke GRAFT's public operator invocation against pinned upstream Dogram."""
from __future__ import annotations

import tempfile
from pathlib import Path

from static_workbench.config import RootConfig, WorkbenchConfig
from static_workbench.creator_shelf import CreatorShelf
from static_workbench.graft_witness import measure, preview


def main() -> None:
    dogram = (Path(__file__).resolve().parents[1] / ".compat" / "Dogram").resolve()
    if not (dogram / "dogram" / "engine.py").is_file():
        raise SystemExit("Missing pinned upstream Dogram checkout")
    with tempfile.TemporaryDirectory(prefix="house-graft-upstream-") as temporary:
        base = Path(temporary)
        config = WorkbenchConfig(
            bind_host="127.0.0.1", port=13700, state_dir=base / "state",
            roots=(RootConfig("compat", dogram.parent),), max_repo_depth=2,
        )
        shelf = CreatorShelf(config.state_dir / "creator.sqlite3")
        ride = shelf.save_native_ride({
            "format": "house.native-maxhinal-ride/v0.1",
            "fuel_sha256": "e" * 64,
            "mode": "pressure", "outputs": [{"kind": "pressure_questions"}],
            "authority": "none", "promotion": "NONE",
        })
        common = {
            "ride_id": ride["id"], "ride_sha256": ride["ride_sha256"],
            "graph": {"nodes": ["seed", "candidate", "saved_proposal"],
                      "edges": [["seed", "candidate"]]},
            "queries": [["seed", "saved_proposal"]],
        }
        for operator, change, expected in [
            ("reach", {"op": "ADD_EDGE", "source": "candidate", "target": "saved_proposal"},
             {"reachable_before": False, "reachable_after": True}),
            ("ablate", {"kind": "edge", "source": "seed", "target": "candidate"},
             {"reachable_before": False, "reachable_after": False}),
        ]:
            specimen = {**common, "operator": operator, "change": change}
            reviewed = preview(config, shelf, **specimen)
            saved = measure(
                config, shelf, **specimen,
                expected_specimen_sha256=reviewed["specimen_sha256"],
                expected_dogram_commit=reviewed["dogram_commit"],
            )
            receipt = saved["witness"]["dogram_receipt"]
            assert receipt["status"] == "OK" and receipt["operator"] == operator
            assert receipt["input_digest"] == "sha256:" + reviewed["specimen_sha256"]
            result = receipt["result"]
            if operator == "reach":
                query = result["queries"][0]
            else:
                query = result["requested_targets"][0]
            for key, value in expected.items():
                assert query[key] is value, (operator, query)
            assert shelf.get_graft_witness(saved["witness_sha256"]) == saved
            print(f"UPSTREAM DOGRAM {operator}@1 PASS: unchanged receipt / pinned commit / saved HOUSE witness")


if __name__ == "__main__":
    main()
