"""STACK² 027 — owner-gated genuine OpenManus LIVE-001 probe in disposable child.

This delegates to original LOADOUT OPENMANUS-LIVE-001 and its own independent
byte/delta/effect verifier. This CLI never runs from HTTP or automatic CI.
No live conformance claim is made unless original pinned OpenManus and actual
model credentials are configured and the provider really finishes.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

from .openmanus_026 import pinned_loadout, LOADOUT_SHA, UPSTREAM_OPENMANUS


class LiveGateRefusal(ValueError):
    pass


def require(ok: bool, reason: str) -> None:
    if not ok:
        raise LiveGateRefusal(reason)


def _outside(inner: Path, outer: Path) -> bool:
    try:
        inner.resolve().relative_to(outer.resolve())
        return False
    except ValueError:
        return True


def live_elf_probe(
    *, loadout_root: Path, provider_checkout: Path, provider_python: Path,
    workspace: Path, output: Path, model_config_class: str,
    forwarded_env_names: tuple[str, ...], source_env: dict[str, str],
    timeout_seconds: int = 60, max_steps: int = 6,
) -> dict:
    require(1 <= max_steps <= 10 and 10 <= timeout_seconds <= 90, "UNBOUNDED_AGENT_BUDGET")
    require(bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,80}", model_config_class)),
            "MODEL_CONFIG_CLASS_REQUIRED")
    require(forwarded_env_names and len(set(forwarded_env_names)) == len(forwarded_env_names) and
            len(forwarded_env_names) <= 5 and all(re.fullmatch(
                r"[A-Z][A-Z0-9_]{2,63}", n) and n in source_env for n in forwarded_env_names),
            "EXPLICIT_MODEL_ENV_ALLOWLIST_REQUIRED")
    root = pinned_loadout(loadout_root)
    require(root.is_dir() and (root / "contrib/openmanus/worker.py").is_file(),
            "ORIGINAL_OPENMANUS_WORKER_MISSING")
    provider = provider_checkout.resolve(strict=True)
    require(provider.is_dir(), "OPENMANUS_CHECKOUT_MISSING")
    interpreter = provider_python.resolve(strict=True)
    require(interpreter.is_file(), "PINNED_PROVIDER_INTERPRETER_MISSING")
    child = workspace.resolve(strict=True)
    require(child.is_dir(), "CHILD_WORKSPACE_MISSING")
    # Local CLI requires a dedicated empty workspace, no incidental source
    # material. This is observational path scoping, not a kernel sandbox.
    require(not any(child.iterdir()), "CHILD_MUST_START_EMPTY")
    out = output.resolve(strict=False)
    require(not out.exists(), "LIVE_RECEIPT_DIR_ALREADY_EXISTS")
    require(_outside(out, child) and _outside(child, provider) and
            _outside(out, provider) and _outside(out, root) and
            _outside(child, root), "HOST_OR_REPO_WORKSPACE_OVERLAP")
    sys.path.insert(0, str(root / "src"))
    from loadout.dev.openmanus_live import (
        run_live_specimen, verify_live_bundle, PINNED_OPENMANUS_SHA
    )
    require(PINNED_OPENMANUS_SHA == UPSTREAM_OPENMANUS, "LOADOUT_UPSTREAM_PROVIDER_PIN_CHANGED")
    # run_live_specimen independently requires the exact original upstream
    # OpenManus git SHA and clean tracked tree before launch.
    bundle = run_live_specimen(
        provider_checkout=provider,
        provider_command=(str(interpreter), str(root / "contrib/openmanus/worker.py")),
        workspace_root=child,
        output_dir=out,
        model_config_class=model_config_class,
        forwarded_env_names=forwarded_env_names,
        source_env=source_env,
        timeout_seconds=timeout_seconds,
        max_steps=max_steps,
    )
    ok, reasons = verify_live_bundle(bundle, child)
    require(ok and not reasons, "OPENMANUS_LIVE_VERIFICATION_HOLD:" + ",".join(reasons))
    report = {
        "schema": "workbench.stack2-elf-live-provider-gate/v0",
        "provider_checkout_pin": UPSTREAM_OPENMANUS,
        "loadout_source_commit": LOADOUT_SHA,
        "loadout_original_live_verifier": "PASS",
        "effect": "LOCAL_MUTATE",
        "provider_occurrence": "OPENMANUS-LIVE-001",
        "live_provider_conformance": "SPECIMEN_SCOPED_PASS",
        "external_model_config_class": model_config_class,
        "forwarded_env_names": list(forwarded_env_names),
        "semantic_authority": False,
        "promotion_authorized": False,
        "elf_successor_identity_inherited": False,
        "seedbank_admitted": False,
        "os_sandbox_verified": False,
    }
    # Deliberately not auto-attach the live evidence to a signed 026
    # certificate or to ELF seedbank. Separate operator review is required.
    (out / "elf-live-gate-summary.json").write_text(json.dumps(report, sort_keys=True, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description="Explicit original OpenManus live probe")
    parser.add_argument("--loadout-root", type=Path, required=True)
    parser.add_argument("--provider-checkout", type=Path, required=True)
    parser.add_argument("--provider-python", type=Path, required=True)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--model-config-class", required=True)
    parser.add_argument("--forward-env", action="append", default=[])
    parser.add_argument("--max-steps", type=int, default=6)
    parser.add_argument("--timeout-seconds", type=int, default=60)
    parser.add_argument("--approve-live-provider", required=True)
    args = parser.parse_args()
    try:
        require(args.approve_live_provider == "yes", "EXPLICIT_OPERATOR_APPROVAL_REQUIRED")
        result = live_elf_probe(
            loadout_root=args.loadout_root,
            provider_checkout=args.provider_checkout,
            provider_python=args.provider_python,
            workspace=args.workspace, output=args.output,
            model_config_class=args.model_config_class,
            forwarded_env_names=tuple(args.forward_env),
            source_env=dict(os.environ), timeout_seconds=args.timeout_seconds,
            max_steps=args.max_steps,
        )
        print(json.dumps(result, sort_keys=True))
    except (LiveGateRefusal, ValueError, OSError) as error:
        parser.exit(1, "LIVE_HOLD: " + str(error)[:220] + "\n")


if __name__ == "__main__":
    main()
