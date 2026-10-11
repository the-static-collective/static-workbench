"""Transparent local-only diagnostic relay must not change donor output."""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

RELAY=Path(__file__).parents[1]/"scripts/stack2-028-provider-relay.py"

def test_relay_preserves_original_subprocess_streams_and_private_stderr(tmp_path):
    original=tmp_path/"original-pinned-worker.py"
    original.write_text(
        "import sys\n"
        "assert sys.stdin.buffer.read()==b'ORIGINAL\\n'\n"
        "sys.stdout.buffer.write(b'{\\\"schema\\\":\\\"original\\\"}\\n')\n"
        "sys.stderr.write('OpenManus provider import failed: MISSING_LIBRARY\\n')\n"
    )
    private=tmp_path/"private.stderr"
    result=subprocess.run(
        [sys.executable,str(RELAY),str(original),str(private)],
        input=b"ORIGINAL\n",capture_output=True,check=True,
    )
    assert result.stdout==b'{"schema":"original"}\n'
    assert result.stderr==b"OpenManus provider import failed: MISSING_LIBRARY\n"
    assert private.read_bytes()==result.stderr
    assert private.stat().st_mode & 0o777 == 0o600
    assert not (tmp_path/"unrequested.txt").exists()
    again=subprocess.run(
        [sys.executable,str(RELAY),str(original),str(private)],
        input=b"ORIGINAL\n",capture_output=True,
    )
    assert again.returncode!=0
