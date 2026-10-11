"""Temporary CI-only transparent relay for pinned OpenManus provider diagnostics.

This is NOT an agent, source authority, verifier or a production execution
surface. It executes the exact original worker unmodified, passes stdin/stdout
byte-for-byte, and stores provider stderr only in an operator-selected private
local path. No diagnostic material is published as a CI artifact.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys

MAX_STDIN=131072
MAX_STDERR=32768

def main() -> int:
    if len(sys.argv) != 3:
        return 2
    worker=Path(sys.argv[1])
    output=Path(sys.argv[2])
    if (not worker.is_absolute() or not worker.is_file()
            or worker.is_symlink() or not output.is_absolute()
            or output.exists() or not output.parent.is_dir()
            or output.is_symlink()):
        return 2
    raw=sys.stdin.buffer.read(MAX_STDIN+1)
    if len(raw)>MAX_STDIN:
        return 2
    try:
        result=subprocess.run(
            [sys.executable,str(worker)],input=raw,
            capture_output=True,env=os.environ.copy(),shell=False,timeout=78
        )
    except (OSError,subprocess.TimeoutExpired) as error:
        # This is diagnostic-only; NEVER manufacture a success result.
        print("PINNED_WORKER_EXECUTION_REFUSED",file=sys.stderr)
        return 1
    # Original standard output is retained byte-for-byte for the immutable
    # LOADOUT adapter's original JSON schema check.
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.buffer.flush()
    sys.stderr.buffer.write(result.stderr[:MAX_STDERR])
    sys.stderr.buffer.flush()
    fd=os.open(str(output),os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,"wb") as out:
        out.write(result.stderr[:MAX_STDERR])
    return result.returncode

if __name__=="__main__":
    raise SystemExit(main())
