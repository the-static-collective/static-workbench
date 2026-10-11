"""STACK² 022 — read-only receiver-owned HOLD shelf. No receiver mutations."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .stack_floor_native_020 import StackFloorActHold, check
from .stack_floor_postoffice_021 import StackFloorPostOffice021, native_process

CROSSING_ID = re.compile(r"^relatte-crossing-v0:[a-f0-9]{64}$")


class StackFloorHoldShelf022:
    def __init__(self, *, postoffice: StackFloorPostOffice021) -> None:
        self.postoffice = postoffice
        self.reader = (
            Path(__file__).resolve().parent.parent / "scripts"
            / "stack-floor-022-shelf.mjs"
        )

    @property
    def enabled(self) -> bool:
        return self.postoffice.enabled

    def read(self, *, crossing_id: str | None = None) -> dict[str, Any]:
        # Exact original-owner source check is the same as native Post Office,
        # but a shelf view does not use GHoT's sender grant or receiver policy.
        native = self.postoffice._relatte()
        configured = self.postoffice.receiver_root
        check(
            isinstance(configured, Path) and configured.exists() and
            configured.is_dir() and not configured.is_symlink(),
            "SHELF_RECEIVER_NOT_CONFIGURED",
        )
        receiver = configured.resolve(strict=True)
        check(receiver != native, "SHELF_SOURCE_IS_NOT_RECEIVER")
        if crossing_id is not None:
            check(isinstance(crossing_id, str) and
                  CROSSING_ID.fullmatch(crossing_id) is not None,
                  "SHELF_INVALID_CROSSING_ID")
        mode = "detail" if crossing_id else "list"
        cmd = [
            "node", "--experimental-strip-types",
            str(self.reader), mode, str(native), str(receiver),
        ]
        if crossing_id:
            cmd.append(crossing_id)
        result = native_process(cmd, cwd=native, max_time=40)
        check(
            result.get("schema") == "workbench.stack-squared-022-shelf/v0"
            and result.get("mode") == mode
            and result.get("original_receiver_journal_replayed") is True
            and result.get("original_relatte_signatures_verified") is True
            and result.get("original_ghot_signature_reverified") is False
            and result.get("receiver_admission_authorized") is False
            and result.get("payload_bytes_read") is False
            and result.get("private_keys_exported") is False
            and result.get("mutations_performed") is False
            and isinstance(result.get("records"), list)
            and isinstance(result.get("state_ref"), str),
            "SHELF_NATIVE_READ_ONLY_WITNESS_INVALID",
        )
        if crossing_id:
            check(len(result["records"]) == 1 and
                  result["records"][0].get("crossing_id") == crossing_id,
                  "SHELF_DETAIL_NOT_HELD")
        return result
