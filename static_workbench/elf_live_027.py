"""STACK² 027 — owner-gated genuine OpenManus LIVE-001 probe in disposable child.

This delegates to original LOADOUT OPENMANUS-LIVE-001 and its own independent
byte/delta/effect verifier. This CLI never runs from HTTP or automatic CI.
No live conformance claim is made unless original pinned OpenManus and actual
model credentials are configured and the provider really finishes.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tomllib

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



def verify_original_live_loadout_files(root: Path) -> None:
    """Pinned LOADOUT adapter alone is insufficient: live worker must match too."""
    for name in (
        "src/loadout/dev/openmanus_live.py",
        "contrib/openmanus/worker.py",
        "contrib/openmanus/bounded_ops.py",
    ):
        file = root / name
        require(file.is_file() and not file.is_symlink(), "LIVE_DONOR_SOURCE_MISSING")
        result = subprocess.run(
            ["git", "-C", str(root), "show", f"{LOADOUT_SHA}:{name}"],
            capture_output=True, check=True, timeout=12,
        )
        require(hashlib.sha256(file.read_bytes()).digest() ==
                hashlib.sha256(result.stdout).digest(),
                "LIVE_DONOR_SOURCE_CHANGED")


def live_elf_probe(
    *, loadout_root: Path, provider_checkout: Path, provider_python: Path,
    workspace: Path, output: Path, model_config_class: str,
    forwarded_env_names: tuple[str, ...], source_env: dict[str, str],
    timeout_seconds: int = 60, max_steps: int = 6,
    provider_diagnostic_path: Path | None = None,
) -> dict:
    require(1 <= max_steps <= 10 and 10 <= timeout_seconds <= 90, "UNBOUNDED_AGENT_BUDGET")
    require(bool(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]{0,80}", model_config_class)),
            "MODEL_CONFIG_CLASS_REQUIRED")
    # New 028 credential-free local model exception: explicit pinned loopback
    # profile, NEVER implicitly inherited runtime environment.
    credentialless_ollama = model_config_class == "local-ollama"
    require((credentialless_ollama and not forwarded_env_names) or
            (not credentialless_ollama and bool(forwarded_env_names) and
             len(set(forwarded_env_names)) == len(forwarded_env_names) and
             len(forwarded_env_names) <= 5 and all(re.fullmatch(
                 r"[A-Z][A-Z0-9_]{2,63}", n) and n in source_env
                 for n in forwarded_env_names)),
            "EXPLICIT_MODEL_ENV_ALLOWLIST_REQUIRED")
    root = pinned_loadout(loadout_root)
    verify_original_live_loadout_files(root)
    if credentialless_ollama:
        config_path = provider_checkout / "config/config.toml"
        require(config_path.is_file() and not config_path.is_symlink(),
                "LOCAL_OLLAMA_CONFIG_MISSING")
        require(config_path.stat().st_size <= 4096, "LOCAL_OLLAMA_CONFIG_TOO_LARGE")
        with config_path.open("rb") as stream:
            config = tomllib.load(stream)
        require(set(config) == {"llm", "daytona"} and
                config["daytona"] == {"daytona_api_key": "disabled-local-placeholder"} and
                set(config["llm"]) == {
                "api_type", "model", "base_url", "api_key",
                "max_tokens", "temperature"} and
                config["llm"]["api_type"] == "ollama" and
                config["llm"]["model"] == "qwen2.5:1.5b" and
                config["llm"]["base_url"] == "http://127.0.0.1:11434/v1" and
                config["llm"]["api_key"] == "ollama" and
                type(config["llm"]["max_tokens"]) is int and
                100 <= config["llm"]["max_tokens"] <= 1024 and
                config["llm"]["temperature"] == 0.0,
                "LOCAL_OLLAMA_NONLOCAL_OR_CREDENTIAL_CONFIGURATION")
    require(root.is_dir() and (root / "contrib/openmanus/worker.py").is_file(),
            "ORIGINAL_OPENMANUS_WORKER_MISSING")
    require(not provider_checkout.is_symlink() and not workspace.is_symlink() and
            not output.is_symlink(), "LIVE_SYMLINK_REFUSED")
    provider = provider_checkout.resolve(strict=True)
    require(provider.is_dir(), "OPENMANUS_CHECKOUT_MISSING")
    # A venv/bin/python is commonly a symlink to the base Python binary.
    # Executing its *resolved* realpath silently loses pyvenv.cfg detection,
    # runs system Python, and misses installed OpenManus dependencies.
    # Retain the explicitly operator-selected invocation path.
    require(provider_python.is_absolute(), "PROVIDER_INTERPRETER_MUST_BE_ABSOLUTE")
    interpreter = provider_python.absolute()
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
    # Only the credential-free exact-loopback profile may use this temporary
    # diagnostic relay. It runs the ORIGINAL pinned worker unmodified and
    # preserves stdout/exit, but privately records stderr outside the child.
    worker = root / "contrib/openmanus/worker.py"
    provider_command = (str(interpreter), str(worker))
    if provider_diagnostic_path is not None:
        require(credentialless_ollama, "DIAGNOSTIC_RELAY_LOCAL_ONLY")
        diagnostic = provider_diagnostic_path.resolve(strict=False)
        require(not provider_diagnostic_path.is_symlink()
                and not diagnostic.exists() and diagnostic.parent.is_dir()
                and _outside(diagnostic, child)
                and _outside(diagnostic, provider)
                and _outside(diagnostic, root),
                "PRIVATE_DIAGNOSTIC_PATH_REFUSED")
        relay = Path(__file__).resolve().parents[1] / "scripts/stack2-028-provider-relay.py"
        require(relay.is_file() and not relay.is_symlink(), "DIAGNOSTIC_RELAY_MISSING")
        provider_command = (
            str(interpreter), str(relay), str(worker), str(diagnostic)
        )
    # run_live_specimen independently requires the exact original upstream
    # OpenManus git SHA and clean tracked tree before launch.
    bundle = run_live_specimen(
        provider_checkout=provider,
        provider_command=provider_command,
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
    parser.add_argument("--private-provider-diagnostic", type=Path)
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
            provider_diagnostic_path=args.private_provider_diagnostic,
        )
        print(json.dumps(result, sort_keys=True))
    except (LiveGateRefusal, ValueError, OSError) as error:
        parser.exit(1, "LIVE_HOLD: " + str(error)[:220] + "\n")


if __name__ == "__main__":
    main()
