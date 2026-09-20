"""Execute the real STATIC LIVE -> HOUSE -> STATIC LIVE manual file crossing.

This is a synthetic local-only fixture: timestamps are declared, no OBS/media decoding,
no real astronomical positions and no authenticated person are implied.
The upstream checkout is version-pinned by the HOUSE CI workflow.
"""
import json
import subprocess
import sys
import tempfile
from pathlib import Path

HOUSE = Path(__file__).resolve().parents[1]
LIVE = HOUSE / ".compat" / "static-live"
UTC = "2026-09-20T15:00:00.000Z"


def run(command, cwd, *, ok=True):
    result = subprocess.run(command, cwd=cwd, capture_output=True, text=True, check=False)
    if ok and result.returncode != 0:
        raise AssertionError(f"command failed ({result.returncode}): {command}\n{result.stderr}")
    if not ok and result.returncode == 0:
        raise AssertionError(f"command unexpectedly succeeded: {command}")
    return result


def main():
    if not (LIVE / "src" / "lifestream-001.js").is_file():
        raise SystemExit("REFUSED: pinned Static Live checkout missing")
    with tempfile.TemporaryDirectory(prefix="lifestream-cross-") as root:
        p = Path(root)
        recording = p / "recording.raw"
        recording.write_bytes(b"synthetic performance sound carrier\n")
        clock_file = p / "clocks.json"
        clock_file.write_text(json.dumps([{
            "clockId": "house.clockwork.abstract-60",
            "reading": "17",
            "basis": "synthetic abstract counter; not media or UTC time",
            "observedAtUtc": UTC,
            "evidenceRef": "synthetic:clockwork-witness"
        }]), encoding="utf-8")
        moment_file = p / "moment.json"
        returned_file = p / "returned.json"
        draft_file = p / "reviewed.txt"
        draft_file.write_bytes("Road becoming / chorus draft\n".encode("utf-8"))
        capture = ["node", "src/lifestream-001.js", "capture",
                   "--event", "synthetic:take01", "--source", str(recording),
                   "--start-ms", "100", "--end-ms", "800",
                   "--recording-started-at", UTC, "--observed-at", UTC,
                   "--clock-witnesses", str(clock_file), "--out", str(moment_file)]
        run(capture, LIVE)
        moment = json.loads(moment_file.read_text(encoding="utf-8"))
        assert moment["clockWitnesses"][0]["reading"] == "17"
        assert moment["span"] == {"startMs": 100, "endMs": 800}
        inspect = [sys.executable, "-m", "static_workbench.lifestream_001", "inspect",
                   "--moment", str(moment_file), "--source", str(recording)]
        inspected = json.loads(run(inspect, HOUSE).stdout)
        assert inspected["momentId"] == moment["momentId"]
        draft = [sys.executable, "-m", "static_workbench.lifestream_001", "draft",
                 "--moment", str(moment_file), "--source", str(recording),
                 "--draft-file", str(draft_file), "--kind", "lyric",
                 "--admitted-by", "human:synthetic_fixture", "--reviewed",
                 "--out", str(returned_file)]
        run(draft, HOUSE)
        returned = json.loads(returned_file.read_text(encoding="utf-8"))
        assert returned["effects"] == {"broadcast": False, "stage": False, "publish": False}
        verify = ["node", "src/lifestream-001.js", "verify-return",
                  "--moment", str(moment_file), "--return", str(returned_file),
                  "--source", str(recording)]
        checked = json.loads(run(verify, LIVE).stdout)
        assert checked["status"] == "verified_return_not_performed"
        assert checked["momentId"] == moment["momentId"]
        assert checked["returnId"] == returned["returnId"]
        recording.write_bytes(b"source changed after review\n")
        rejected = run(verify, LIVE, ok=False)
        assert "source bytes do not match moment" in rejected.stderr, rejected.stderr
    print("LIFESTREAM-001 cross-repo smoke: PASS (clock independence, source binding, "
          "explicit draft, return digest, changed-source refusal)")


if __name__ == "__main__":
    main()
