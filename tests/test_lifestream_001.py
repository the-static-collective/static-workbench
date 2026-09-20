import json
from pathlib import Path

import pytest

from static_workbench.lifestream_001 import (
    canonical, digest, hash_object, main, make_return, source_bytes, verify_moment
)


INSTANT = "2026-09-20T15:00:00.000Z"
CLOCK = {
    "clockId": "clockwork.abstract-60",
    "reading": "17",
    "basis": "declared abstract tick; not UTC",
    "observedAtUtc": INSTANT,
    "evidenceRef": "clockwork-001:fixture",
}


def sample(tmp_path: Path):
    src = tmp_path / "recording.raw"
    src.write_bytes(b"one physical occurrence\n")
    unsigned = {
        "schema": "static-lifestream.moment/v0.1",
        "eventId": "live001:take1",
        "source": source_bytes(src),
        "span": {"startMs": 200, "endMs": 1400},
        "time": {"recordingStartedAtUtc": INSTANT, "observedAtUtc": INSTANT},
        "clockWitnesses": [CLOCK],
    }
    return src, {**unsigned, "momentId": hash_object(unsigned)}


def test_exact_source_time_and_independent_clock(tmp_path):
    src, moment = sample(tmp_path)
    assert verify_moment(moment, src) == moment
    assert moment["clockWitnesses"][0]["reading"] == "17"
    assert moment["span"]["startMs"] == 200
    assert moment["time"]["recordingStartedAtUtc"] == INSTANT


def test_source_change_forged_witness_and_fake_time_refuse(tmp_path):
    src, moment = sample(tmp_path)
    src.write_bytes(b"something else")
    with pytest.raises(ValueError, match="source bytes"):
        verify_moment(moment, src)
    src.write_bytes(b"one physical occurrence\n")
    moment["clockWitnesses"][0] = {**CLOCK, "reading": "18"}
    with pytest.raises(ValueError, match="manifest digest"):
        verify_moment(moment, src)
    moment["clockWitnesses"][0] = CLOCK
    moment["time"]["observedAtUtc"] = "2026-09-20"
    with pytest.raises(ValueError, match="UTC instant"):
        verify_moment(moment, src)


def test_reviewed_draft_has_only_non_effectful_return_and_exact_utf8_digest(tmp_path):
    src, moment = sample(tmp_path)
    raw = "The road is still becoming.\n".encode("utf-8")
    returned = make_return(moment, src, raw, "lyric", "human:operator", INSTANT)
    assert returned["artifact"]["sha256"] == digest(raw)
    assert returned["artifact"]["sourceMomentId"] == moment["momentId"]
    assert returned["review"]["disposition"] == "reviewed_local_draft"
    assert returned["effects"] == {"broadcast": False, "stage": False, "publish": False}
    assert returned["returnId"] == hash_object({k: v for k, v in returned.items() if k != "returnId"})
    with pytest.raises(ValueError, match="invalid attribution"):
        make_return(moment, src, raw, "lyric", "../outside", INSTANT)


def test_cli_inspection_review_required_and_exclusive_output(tmp_path, capsys):
    src, moment = sample(tmp_path)
    manifest = tmp_path / "moment.json"
    manifest.write_text(json.dumps(moment), encoding="utf-8")
    main(["inspect", "--moment", str(manifest), "--source", str(src)])
    assert json.loads(capsys.readouterr().out)["status"] == "source_verified_no_effect"
    draft = tmp_path / "draft.txt"
    draft.write_text("A reviewed chorus\n", encoding="utf-8")
    output = tmp_path / "returned.json"
    base = ["draft", "--moment", str(manifest), "--source", str(src), "--draft-file", str(draft),
            "--kind", "lyric", "--admitted-by", "human:operator", "--out", str(output)]
    with pytest.raises(SystemExit):
        main(base)
    assert not output.exists()
    main(base + ["--reviewed"])
    assert json.loads(output.read_text(encoding="utf-8"))["effects"]["publish"] is False
    with pytest.raises(FileExistsError):
        main(base + ["--reviewed"])


def test_cross_language_canonical_json_shape_matches_javascript_expectation():
    # ASCII-keyed protocol payload: the Node canonicalStringify emits this exact UTF-8 sequence.
    assert canonical({"z": 1, "a": {"y": "hello", "x": [False, None]}}) == (
        b'{"a":{"x":[false,null],"y":"hello"},"z":1}'
    )
