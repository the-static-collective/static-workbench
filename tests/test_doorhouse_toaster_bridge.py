import hashlib
import json

import pytest

from static_workbench.doorhouse_ghot import (
    GHotApertureError,
    _materialize_toaster_artifact,
)


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def donor(svg="<svg><circle/></svg>"):
    recipe_text = json.dumps(
        {
            "schema": "witness-sigil.recipe/v0.1",
            "projection": "witness-sigil/v0.1",
            "digest": "a" * 64,
        },
        indent=2,
    ) + "\n"
    receipt = {
        "schema": "haunted-toaster/ghot-witness-sigil-receipt/v0",
        "instrument": "witness-sigil/v0.1",
        "source_digest_sha256": "a" * 64,
    }
    receipt_text = json.dumps(receipt, indent=2) + "\n"
    return {
        "artifact": {
            "svg_text": svg,
            "svg_sha256": sha(svg),
            "recipe_text": recipe_text,
            "recipe_sha256": sha(recipe_text),
            "receipt_text": receipt_text,
            "receipt_sha256": sha(receipt_text),
        },
        "receipt": receipt,
    }


def test_materializes_exact_returned_toaster_bytes(tmp_path):
    result = _materialize_toaster_artifact(donor(), tmp_path, "receipt-001")
    assert result["instrument"] == "witness-sigil/v0.1"
    assert result["source_digest_sha256"] == "a" * 64
    assert result["svg_sha256"] == sha("<svg><circle/></svg>")
    assert open(result["svg_path"], encoding="utf-8").read() == "<svg><circle/></svg>"


def test_refuses_toaster_bytes_that_changed_in_transit(tmp_path):
    value = donor()
    value["artifact"]["svg_sha256"] = "0" * 64
    with pytest.raises(GHotApertureError, match="hashes changed in transit"):
        _materialize_toaster_artifact(value, tmp_path, "receipt-001")
