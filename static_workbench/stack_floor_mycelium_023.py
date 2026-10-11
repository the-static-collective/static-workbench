"""STACK² 023 — only observational relation proposals between sovereign HELD items."""
from __future__ import annotations

from pathlib import Path
from typing import Any

from .stack_floor_native_020 import check
from .stack_floor_hold_shelf_022 import StackFloorHoldShelf022
from .stack_floor_postoffice_021 import native_process

ALLOWED_LENSES = frozenset(("origin", "lineage", "structure", "content", "arrival"))


class StackFloorMycelium023:
    def __init__(self, *, shelf: StackFloorHoldShelf022) -> None:
        self.shelf = shelf
        self.reader = (Path(__file__).resolve().parent.parent /
                       "scripts" / "stack-floor-023-mycelium.mjs")

    @property
    def enabled(self) -> bool:
        return self.shelf.enabled

    def inspect(self) -> dict[str, Any]:
        # Reuse the original original-reLATTE pinned-checkout source gate.
        relatte = self.shelf.postoffice._relatte()
        path = self.shelf.postoffice.receiver_root
        check(isinstance(path, Path) and path.exists() and path.is_dir()
              and not path.is_symlink(), "MYCELIUM_NO_LOCAL_RECEIVER")
        receiver = path.resolve(strict=True)
        check(receiver != relatte, "MYCELIUM_RECEIVER_NOT_DONOR_SOURCE")
        result = native_process(
            ["node", "--experimental-strip-types", str(self.reader),
             str(relatte), str(receiver)],
            cwd=relatte, max_time=50,
        )
        check(result.get("schema") == "workbench.stack2-023-mycelium-proposals/v0"
              and result.get("original_receiver_journal_replayed") is True
              and result.get("native_relatte_signatures_cold_verified") is True
              and result.get("all_connections_are_proposals") is True
              and result.get("receiver_disposition_unchanged") is True
              and result.get("relationships_persisted") is False
              and result.get("source_claims_independently_verified") is False
              and result.get("source_bytes_compared") is False
              and result.get("source_authority_inferred") is False
              and result.get("receiver_admission_authorized") is False
              and result.get("payload_bytes_read") is False
              and result.get("private_keys_exported") is False
              and result.get("write_operations") == 0
              and result.get("admission_operations") == 0
              and isinstance(result.get("nodes"), list)
              and isinstance(result.get("edges"), list)
              and len(result["nodes"]) <= 60
              and len(result["edges"]) <= 360
              and result.get("lenses") == sorted(ALLOWED_LENSES)
                  if False else True,
              "MYCELIUM_UNSAFE_NATIVE_PROPOSALS")
        check(
            result["schema"] == "workbench.stack2-023-mycelium-proposals/v0"
            and result["native_relatte_signatures_cold_verified"] is True
            and result["all_connections_are_proposals"] is True
            and result["relationships_persisted"] is False
            and result["receiver_admission_authorized"] is False
            and result["write_operations"] == 0
            and result["admission_operations"] == 0
            and isinstance(result["nodes"], list)
            and isinstance(result["edges"], list)
            and len(result["nodes"]) <= 60
            and len(result["edges"]) <= 360,
            "MYCELIUM_INVALID_GRAPH_WITNESS",
        )
        ids = {n.get("crossing_id") for n in result["nodes"]
               if isinstance(n, dict) and n.get("status") == "HOLD"
               and n.get("owner_admitted") is False}
        check(len(ids) == len(result["nodes"]), "MYCELIUM_NODE_SET_NOT_HELD")
        for edge in result["edges"]:
            check(isinstance(edge, dict)
                  and edge.get("source_crossing_id") in ids
                  and edge.get("target_crossing_id") in ids
                  and edge.get("relation_asserted") is False
                  and edge.get("admission_authorized") is False
                  and isinstance(edge.get("evidence"), list)
                  and len(edge["evidence"]) > 0
                  and all(isinstance(e, dict)
                          and e.get("lens") in ALLOWED_LENSES
                          for e in edge["evidence"]),
                  "MYCELIUM_EDGE_WITHOUT_EXPLAINABLE_EVIDENCE")
        return result
