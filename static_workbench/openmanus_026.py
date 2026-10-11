"""STACK² 026 — use original LOADOUT OpenManus OBSERVE limb to examine a
separately verified public portable certificate.

This module makes no OpenManus live-provider claims. Production is gated on a
true isolated provider occurrence and independent credential/security review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from typing import Any

LOADOUT_SHA = "dd5456d45946271e2d20d1dc6145b71576d2380b"
UPSTREAM_OPENMANUS = "3309bf4e416fb1c74b008f3e86494439a31bad53"
BODY_ID = "openmanus.worker.json-stdio/v0@" + UPSTREAM_OPENMANUS
SOURCE_PATHS = (
    "src/loadout/dev/openmanus.py",
    "src/loadout/dev/membrane.py",
    "src/loadout/dev/compiler.py",
    "src/loadout/dev/model.py",
)
CERTIFICATE_NAME = "public-026.json"
CERTIFICATE_MAX_BYTES = 16384


class ObservationRefusal(ValueError):
    pass


def require(acceptable: bool, code: str) -> None:
    if not acceptable:
        raise ObservationRefusal(code)


def digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def pinned_loadout(root: Path) -> Path:
    root = root.resolve(strict=True)
    require(root.is_dir(), "LOADOUT_NOT_A_DIRECTORY")
    head = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"],
                          capture_output=True, check=True, timeout=12, text=True)
    require(head.stdout.strip() == LOADOUT_SHA, "LOADOUT_SOURCE_HEAD_NOT_PINNED")
    for source in SOURCE_PATHS:
        local = root / source
        require(local.is_file() and not local.is_symlink(), "LOADOUT_SOURCE_NOT_PRESENT")
        original = subprocess.run(["git", "-C", str(root), "show",
                                   f"{LOADOUT_SHA}:{source}"],
                                  capture_output=True, check=True, timeout=12)
        require(hashlib.sha256(local.read_bytes()).digest() ==
                hashlib.sha256(original.stdout).digest(),
                "LOADOUT_SOURCE_FILE_CHANGED")
    return root


def specimen_snapshot(workspace: Path) -> dict[str, str]:
    require(workspace.is_dir() and not workspace.is_symlink(), "WORKSPACE_NOT_LOCAL")
    visible = sorted(workspace.iterdir())
    require(len(visible) == 1 and visible[0].name == CERTIFICATE_NAME and
            not visible[0].is_symlink() and visible[0].is_file(),
            "UNEXPECTED_WORKSPACE_FILES")
    content = visible[0].read_bytes()
    require(0 < len(content) <= CERTIFICATE_MAX_BYTES, "CERTIFICATE_SIZE_REFUSED")
    require(len(content) == visible[0].stat().st_size, "CERTIFICATE_CHANGED_WHILE_READ")
    return {CERTIFICATE_NAME: digest(content)}


def native_verify(certificate: Path, *, verification_script: Path,
                  trust_fingerprint: str) -> dict[str, Any]:
    require(verification_script.is_file(), "NATIVE_VERIFIER_NOT_FOUND")
    result = subprocess.run([
        "node", str(verification_script), "verify",
        "--bundle", str(certificate), "--trust-fingerprint", trust_fingerprint
    ], capture_output=True, text=True, check=False, timeout=12)
    require(result.returncode == 0, "INDEPENDENT_SIGNATURE_VERIFIER_REFUSED")
    value = json.loads(result.stdout)
    require(isinstance(value, dict) and
            value.get("status") == "PORTABLE_SOURCE_BOUNDED_SIGNATURE_VERIFIED"
            and value.get("admitted") is False and
            value.get("agent_authority") is False and
            value.get("issuer_key_fingerprint") == trust_fingerprint,
            "NATIVE_PROOF_NOT_VALIDATED")
    return value


def observe(*, loadout_root: Path, workspace: Path,
            verification_script: Path, trust_fingerprint: str,
            provider_command: tuple[str, ...]) -> dict[str, Any]:
    loadout_root = pinned_loadout(loadout_root)
    workspace = workspace.resolve(strict=True)
    first = specimen_snapshot(workspace)
    certificate = workspace / CERTIFICATE_NAME
    verified = native_verify(certificate, verification_script=verification_script,
                             trust_fingerprint=trust_fingerprint)
    # Import the original pinned donor module, never a substitute Workbench
    # implementation. The adapter body-time ID pins upstream contract identity
    # but does not itself prove live OpenManus was installed or executed.
    donor_src = str(loadout_root / "src")
    if donor_src not in sys.path:
        sys.path.insert(0, donor_src)
    from loadout.dev.compiler import compile_world
    from loadout.dev.membrane import invoke_effect
    from loadout.dev.model import (
        AdapterBody, CapabilityRequest, CapabilitySpec, CompileRequest,
        EffectClass, EffectIntent,
    )
    from loadout.dev.openmanus import OpenManusJsonStdioAdapter, OPENMANUS_ADAPTER_ID

    target = "workspace:" + CERTIFICATE_NAME
    request = "OBSERVE public-026.json only; do not mutate, sign, browse, or admit it."
    body = AdapterBody(
        adapter_id=OPENMANUS_ADAPTER_ID, body_time_id=BODY_ID,
        source_sha=UPSTREAM_OPENMANUS,
        capabilities=(CapabilitySpec("worker.perform", EffectClass.OBSERVE),),
    )
    compiled = compile_world(CompileRequest(
        task_id="STACK2-026-OPENMANUS-OBSERVE",
        task_text="Bounded public portable receipt observation",
        cut_targets=frozenset({target}),
        requested_capabilities=(CapabilityRequest(
            "worker.perform", EffectClass.OBSERVE, target, body_time_id=BODY_ID),),
        available_bodies=(body,),
    ))
    adapter = OpenManusJsonStdioAdapter(
        provider_command=provider_command,
        workspace_root=workspace,
        body_time_id=BODY_ID,
        child_env={"PATH": "/usr/bin:/bin"},
        max_steps=3,
        timeout_seconds=12,
    )
    intent = EffectIntent(
        capability="worker.perform", effect=EffectClass.OBSERVE,
        target=target, body_time_id=BODY_ID,
        precondition_state=first[CERTIFICATE_NAME],
        parameters_digest=digest(request.encode("utf8")),
        parameters=(("request", request),),
    )
    receipt = invoke_effect(compiled, intent, {BODY_ID: adapter},
                            current_state=first[CERTIFICATE_NAME])
    require(len(adapter.provider_receipts) == 1, "PROVIDER_RECEIPT_MISSING")
    provider = adapter.provider_receipts[0]
    # A provider can hallucinate a completed read. Do not use provider claims
    # for any cryptographic, authority, or certificate decision.
    second = specimen_snapshot(workspace)
    require(first == second, "WORKSPACE_MUTATED_DURING_OBSERVE")
    verified_again = native_verify(certificate, verification_script=verification_script,
                                   trust_fingerprint=trust_fingerprint)
    require(verified_again == verified, "CERTIFICATE_VERIFICATION_CHANGED")
    require(receipt.effect == EffectClass.OBSERVE and
            receipt.semantic_authority is False and
            receipt.provider_disposition == "COMPLETED" and
            provider.disposition == "COMPLETED" and
            provider.steps_executed <= 3,
            "PROVIDER_OBSERVATION_NOT_ACCEPTED")
    return {
        "schema": "workbench.stack2-openmanus-carrier-observation/v0",
        "loadout_source_commit": LOADOUT_SHA,
        "openmanus_contract_body_id": BODY_ID,
        "effect": "OBSERVE",
        "provider_disposition": provider.disposition,
        "provider_steps": provider.steps_executed,
        "effect_receipt_semantic_authority": False,
        "local_certificate_sha256": first[CERTIFICATE_NAME],
        "independent_verifier_result": verified["status"],
        "issuer_fingerprint": verified["issuer_key_fingerprint"],
        "source_authorship_established": False,
        "openmanus_live_provider_conformance": "NOT_RUN_OR_ATTESTED",
        "agent_can_sign": False, "agent_can_admit": False,
        "agent_can_publish": False, "workspace_content_mutated": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--loadout-root", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--verification-script", type=Path, required=True)
    parser.add_argument("--trust-fingerprint", required=True)
    parser.add_argument("--provider-script", type=Path, required=True)
    parser.add_argument("--approve-observe", required=True)
    args = parser.parse_args()
    try:
        require(args.approve_observe == "yes", "EXPLICIT_OBSERVE_APPROVAL_REQUIRED")
        result = observe(
            loadout_root=args.loadout_root,
            workspace=args.workspace,
            verification_script=args.verification_script,
            trust_fingerprint=args.trust_fingerprint,
            provider_command=(sys.executable, str(args.provider_script)),
        )
        print(json.dumps(result, sort_keys=True))
    except (ObservationRefusal, OSError, ValueError, subprocess.SubprocessError) as error:
        parser.exit(1, "HOLD: " + str(error)[:220] + "\n")


if __name__ == "__main__":
    main()
