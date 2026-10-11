#!/usr/bin/env python3
"""Credential-free OpenManus adapter contract fixture, NOT the live OpenManus model."""
import hashlib
import json
import pathlib
import sys

try:
    envelope = json.loads(sys.stdin.read())
    assert envelope["schema"] == "loadout.openmanus-worker-envelope/v0"
    assert envelope["effect"] == "OBSERVE"
    assert envelope["target"] == "workspace:public-026.json"
    assert envelope["capability"] == "worker.perform"
    assert envelope["max_steps"] <= 3
    workspace = pathlib.Path(envelope["workspace_root"]).resolve(strict=True)
    public = workspace / "public-026.json"
    assert public.is_file() and not public.is_symlink()
    content = public.read_bytes()
    assert len(content) < 16384
    # This is a provider observation, not independent signature verification.
    result = {
        "schema": "loadout.openmanus-worker-result/v0",
        "disposition": "COMPLETED",
        "observed_post_state": None,
        "artifacts": [],
        "observations": [{
            "tool": "loadout_read_text",
            "path": "public-026.json",
            "content_sha256": hashlib.sha256(content).hexdigest(),
            "claim": "OBSERVED_NOT_VERIFIED",
        }],
        "provider_receipt": {"steps_executed": 1, "termination": "COMPLETED"},
    }
except (AssertionError, KeyError, OSError, ValueError, TypeError):
    result = {
        "schema": "loadout.openmanus-worker-result/v0",
        "disposition": "REFUSED",
        "observed_post_state": None,
        "artifacts": [],
        "observations": [],
        "provider_receipt": {"steps_executed": 0, "termination": "BOUNDARY_REFUSED"},
    }
print(json.dumps(result, sort_keys=True))
