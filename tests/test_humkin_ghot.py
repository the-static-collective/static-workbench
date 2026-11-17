from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pytest

from static_workbench.humkin_ghot import (
    APPROVAL, HumkinGhotError, execute_catalog_hash,
    verify_origin,
)


def test_no_implicit_action(tmp_path: Path) -> None:
    with pytest.raises(HumkinGhotError, match="Explicit"):
        execute_catalog_hash(
            tmp_path / "relatte", tmp_path / "ghot", tmp_path / "origin",
            tmp_path / "work", None,
        )


def test_public_origin_must_have_native_relatte_verifier(tmp_path: Path) -> None:
    (tmp_path / "relatte").mkdir()
    with pytest.raises(HumkinGhotError, match="native catalog verifier"):
        verify_origin(tmp_path / "relatte", tmp_path / "origin")


def test_failed_origin_cannot_trigger_ghot(tmp_path: Path) -> None:
    (tmp_path / "relatte" / "scripts").mkdir(parents=True)
    (tmp_path / "relatte" / "scripts" / "humkin-gh-relatte-001.mjs").write_text(
        "// fixture - not run", encoding="utf-8"
    )
    (tmp_path / "origin").mkdir()
    (tmp_path / "origin" / "source-manifest.json").write_text(
        json.dumps({"revision": "a" * 40, "files": {"tracks.json": "b" * 64}}),
        encoding="utf-8",
    )
    with patch(
        "static_workbench.humkin_ghot._run",
        return_value={
            "disposition": "RECEIVED",
            "source_revision": "a" * 40,
            "public_bytes_verified": True,
            "signed_receipts_verified": True,
            "receiver_admitted": False,
            "catalog_count": 12,
        },
    ):
        with patch("static_workbench.humkin_ghot._native_ghot_hash") as native:
            with pytest.raises(HumkinGhotError, match="not verified into HOLD"):
                execute_catalog_hash(
                    tmp_path / "relatte", tmp_path / "ghot", tmp_path / "origin",
                    tmp_path / "work", APPROVAL,
                )
            native.assert_not_called()
