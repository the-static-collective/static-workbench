"""Synthetic end-to-end 002: Node marker -> finished-media finalizer -> HOUSE browser
API inbox -> reviewed return -> Node verification. No actual OBS/media decoding.
"""
from __future__ import annotations
import json
import subprocess
import tempfile
from pathlib import Path

from fastapi.testclient import TestClient
from static_workbench.app import create_app
from static_workbench.config import RootConfig, WorkbenchConfig

HOUSE = Path(__file__).resolve().parents[1]
LIVE = HOUSE / ".compat" / "static-live-002"
UTC = "2026-09-20T15:00:00.000Z"


def cmd(args, cwd, should_pass=True):
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, check=False)
    if (result.returncode == 0) != should_pass:
        raise AssertionError(f"unexpected command exit: {args}\n{result.stdout}\n{result.stderr}")
    return result


def main():
    assert (LIVE / "src" / "lifestream-002-finalize.js").is_file(), "pinned Live checkout missing"
    with tempfile.TemporaryDirectory(prefix="living-inbox-smoke-") as path:
        root = Path(path)
        recording = root / "finished.raw"
        recording.write_bytes(b"synthetic OBS-finished carrier bytes\n")
        journal = root / "marks.jsonl"
        marker_script = """
import { createMomentMarker } from './src/lifestream-002-marker.js';
const book=createMomentMarker({journalPath:process.argv[1],eventId:'synthetic:session',
  tick:()=>1420,now:()=>'2026-09-20T15:00:00.000Z'});
book.begin();
const mark=book.mark({recording:true,state:'recording_only'});
console.log(JSON.stringify(mark));
"""
        marker = json.loads(cmd(["node", "--input-type=module", "-e", marker_script, str(journal)],
                                LIVE).stdout)
        assert marker["approximateElapsedSinceConfirmationMs"] == 0
        manifest_path = root / "moment.json"
        cmd(["node", "src/lifestream-002-finalize.js", "finalize",
             "--journal", str(journal), "--mark-id", marker["markId"],
             "--source", str(recording), "--start-ms", "100", "--end-ms", "700",
             "--recording-started-at", UTC, "--recording-finished",
             "--out", str(manifest_path)], LIVE)
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        assert manifest["clockWitnesses"][0]["clockId"] == "static-live.monotonic-mark"
        cfg = WorkbenchConfig(bind_host="127.0.0.1", port=13700, state_dir=root / "state",
                              roots=(RootConfig("synthetic", root),))
        with TestClient(create_app(cfg), base_url="http://127.0.0.1") as client:
            token = client.get("/api/bootstrap").json()["session_token"]
            hdr = {"x-workbench-session": token, "origin": "http://127.0.0.1"}
            imported = client.post("/api/lifestream/moments/import", headers=hdr,
                json={"root_id":"synthetic","manifest_path":"moment.json",
                      "source_path":"finished.raw"})
            assert imported.status_code == 200, imported.text
            mid = imported.json()["momentId"]
            assert mid == manifest["momentId"]
            url = f"/api/lifestream/moments/{mid}/returns"
            draft = client.post(url, headers=hdr, json={
                "kind":"lyric", "text":"The road is still becoming.\n",
                "admitted_by":"human:synthetic_fixture", "reviewed":True})
            assert draft.status_code == 200, draft.text
            rid = draft.json()["returnId"]
            exported = client.get(url + "/" + rid)
            assert exported.status_code == 200, exported.text
            returned = exported.json()
        returned_path = root / "returned.json"
        returned_path.write_text(json.dumps(returned, ensure_ascii=False), encoding="utf-8")
        verified = json.loads(cmd(["node", "src/lifestream-001.js", "verify-return",
                                   "--moment", str(manifest_path), "--return",
                                   str(returned_path), "--source", str(recording)], LIVE).stdout)
        assert verified["status"] == "verified_return_not_performed"
        recording.write_bytes(b"changed after return\n")
        refused = cmd(["node", "src/lifestream-001.js", "verify-return",
                       "--moment", str(manifest_path), "--return",
                       str(returned_path), "--source", str(recording)], LIVE, should_pass=False)
        assert "source bytes do not match moment" in refused.stderr
    print("LIFESTREAM-002 synthetic cross-repo PASS: mark -> manual media reconciliation -> "
          "browser reviewed candidate -> return verification -> changed-source refusal")


if __name__ == "__main__":
    main()
