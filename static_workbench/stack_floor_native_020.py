"""STACK² 020: opt-in local GHoT 030 *exact source hash only*.

Workbench owns the web preview nonce. GHoT owns its signed one-use ACT
ticket, atomic claim, fresh preflight and execution receipt.
Neither grants human identity, Git ownership, reLATTE admission or generic
execution permission.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import secrets
import sqlite3
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

GHOT_REPO = "the-static-collective/GHoT"
GHOT_SHA = "b01758bee55d66d699160715ec377b45f7589707"
PLANZ_REPO = "the-static-collective/planZ"
PLANZ_SHA = "e8111fdb64c5587b33aece0fed639ed3d03375ac"
PLANZ_PATH = "002/bin/sense-global.mjs"
BRANCH_HINT = "experiment/fatherhand-grant-chain-residue-001"
SOURCE_SPEC = {"repository": PLANZ_REPO, "commit": PLANZ_SHA, "path": PLANZ_PATH}
ACT_TTL = 90
MAX_STDOUT = 256 * 1024
HASH_64 = re.compile(r"^[a-f0-9]{64}$")


class StackFloorActHold(ValueError):
    pass


def check(ok: bool, code: str) -> None:
    if not ok:
        raise StackFloorActHold(code)


def _git(repo: Path, *args: str, binary: bool = False) -> bytes | str:
    result = subprocess.run(
        ["git", "-C", str(repo), *args],
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=10, check=False, env={**os.environ, "GIT_CONFIG_NOSYSTEM": "1"},
    )
    check(result.returncode == 0, "PINNED_GIT_OBJECT_UNAVAILABLE")
    check(len(result.stdout) <= 1024 * 1024, "SOURCE_TOO_LARGE")
    return result.stdout if binary else result.stdout.decode("utf8").strip()


def _root(path: Path | None, repository: str, commit: str) -> Path:
    check(isinstance(path, Path) and path.exists(), "NATIVE_CHECKOUT_NOT_CONFIGURED")
    root = path.resolve(strict=True)
    check(root.is_dir(), "NATIVE_CHECKOUT_NOT_DIRECTORY")
    check(_git(root, "rev-parse", "--show-toplevel") == str(root), "NATIVE_NOT_GIT_ROOT")
    check(_git(root, "rev-parse", "HEAD") == commit, "NATIVE_DONOR_HEAD_NOT_PINNED")
    origin = _git(root, "config", "--get", "remote.origin.url")
    check(origin in {
        f"https://github.com/{repository}", f"https://github.com/{repository}.git",
        f"git@github.com:{repository}", f"git@github.com:{repository}.git",
    }, "NATIVE_DONOR_ORIGIN_MISMATCH")
    return root


def _files(ghot_root: Path, planz_root: Path) -> dict[str, str]:
    for relative in ["ghot/branch_worker.py", "ghot/activation_ticket.py", "ghot/branch_work.py"]:
        check(_git(ghot_root, "cat-file", "-t", f"{GHOT_SHA}:{relative}") == "blob",
              "GHOT_ORIGINAL_PROGRAM_UNAVAILABLE")
        # Refuse locally modified or replaced original native executable.
        actual = (ghot_root / relative).read_bytes()
        expected = _git(ghot_root, "show", f"{GHOT_SHA}:{relative}", binary=True)
        check(actual == expected, "GHOT_EXECUTABLE_WORKTREE_TAMPERED")
    check(_git(planz_root, "cat-file", "-t", f"{PLANZ_SHA}:{PLANZ_PATH}") == "blob",
          "PLANZ_PINNED_SOURCE_NOT_BLOB")
    source = _git(planz_root, "show", f"{PLANZ_SHA}:{PLANZ_PATH}", binary=True)
    source_hash = hashlib.sha256(source).hexdigest()
    check(HASH_64.fullmatch(source_hash) is not None, "BAD_SOURCE_HASH")
    return {"sha256": source_hash}


def _context(source: dict[str, str]) -> dict[str, str]:
    return {
        "repository": PLANZ_REPO,
        "commit": PLANZ_SHA,
        "path": PLANZ_PATH,
        "sha256": source["sha256"],
        "branchHint": BRANCH_HINT,
    }


def _native(argv: list[str], *, checkout: Path, home: Path) -> dict[str, Any]:
    check(len(argv) in (2, 3, 7, 9), "INVALID_FIXED_NATIVE_INVOCATION")
    run = subprocess.run(
        [sys.executable, str(checkout / "ghot/branch_worker.py"), *argv],
        cwd=checkout, env={**os.environ, "GHOT_HOME": str(home)},
        stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        timeout=35, check=False,
    )
    check(len(run.stdout) <= MAX_STDOUT and len(run.stderr) <= 8192,
          "NATIVE_RESPONSE_TOO_LARGE")
    try:
        record = json.loads(run.stdout.decode("utf-8"))
    except (UnicodeError, ValueError) as exc:
        raise StackFloorActHold("GHOT_NATIVE_RESPONSE_INVALID") from exc
    check(isinstance(record, dict), "GHOT_NATIVE_RESPONSE_NOT_OBJECT")
    if run.returncode != 0:
        raise StackFloorActHold("GHOT_NATIVE_HOLD: " + str(record.get("reason", "blocked"))[:140])
    return record


class StackFloorNative020:
    def __init__(
        self, *, state_dir: Path, enabled: bool,
        ghot_checkout: Path | None, planz_checkout: Path | None,
        ghot_home: Path | None,
    ) -> None:
        self.enabled = enabled
        self.ghot_checkout = ghot_checkout
        self.planz_checkout = planz_checkout
        self.ghot_home = ghot_home
        self.state_dir = state_dir
        self.db_path = state_dir / "stack-floor-020.sqlite3"
        self.candidate_file = state_dir / "stack-floor-020-fixed-candidate.json"
        if enabled:
            check(all(isinstance(v, Path) for v in
                [ghot_checkout, planz_checkout, ghot_home]), "NATIVE_OPT_IN_PATHS_REQUIRED")
            state_dir.mkdir(parents=True, exist_ok=True)
            with self._db() as db:
                db.execute("""CREATE TABLE IF NOT EXISTS previews (
                    nonce_hash TEXT PRIMARY KEY, proposal TEXT NOT NULL,
                    source_sha256 TEXT NOT NULL, expires REAL NOT NULL,
                    consumed INTEGER NOT NULL DEFAULT 0
                )""")

    def _db(self) -> sqlite3.Connection:
        return sqlite3.connect(self.db_path, timeout=15, isolation_level=None)

    def _ready(self) -> tuple[Path, Path, Path, dict[str, str]]:
        check(self.enabled, "NATIVE_FLOOR_DISABLED")
        ghot = _root(self.ghot_checkout, GHOT_REPO, GHOT_SHA)
        planz = _root(self.planz_checkout, PLANZ_REPO, PLANZ_SHA)
        check(isinstance(self.ghot_home, Path), "GHOT_HOME_NOT_CONFIGURED")
        home = self.ghot_home.resolve(strict=True)
        check(home.is_dir() and not home.is_symlink(), "GHOT_HOME_NOT_LOCAL")
        check(home != ghot and home != planz, "GHOT_HOME_CANNOT_BE_SOURCE")
        source = _files(ghot, planz)
        return ghot, planz, home, _context(source)

    def _write_candidate(self, context: dict[str, str]) -> None:
        expected = (json.dumps({
            "schema": "ghot.branch-worker-candidate/v0",
            "context": context,
        }, sort_keys=True, separators=(",", ":")) + "\n").encode()
        if self.candidate_file.exists():
            check(not self.candidate_file.is_symlink(), "CANDIDATE_SYMLINK_REFUSED")
            check(self.candidate_file.read_bytes() == expected, "CANDIDATE_ALREADY_DIFFERENT")
            return
        with self.candidate_file.open("xb") as out:
            out.write(expected)
            out.flush()
            os.fsync(out.fileno())

    def _source_policy(self, home: Path, context: dict[str, str]) -> None:
        # Workbench cannot mint GHoT's owner-selected allowlist. Fail closed.
        path = home / "branch-worker" / "sources.json"
        check(path.is_file() and not path.is_symlink(), "OWNER_GHOT_POLICY_REQUIRED")
        try:
            policy = json.loads(path.read_text(encoding="utf8"))
        except (ValueError, UnicodeError) as exc:
            raise StackFloorActHold("OWNER_GHOT_POLICY_INVALID") from exc
        check(isinstance(policy, dict) and policy.get("schema") ==
            "ghot.branch-worker-sources/v0", "OWNER_GHOT_POLICY_INVALID")
        entries = policy.get("entries")
        check(isinstance(entries, list) and 0 < len(entries) <= 32,
              "OWNER_GHOT_POLICY_INVALID")
        matches = [x for x in entries if isinstance(x, dict) and
                   x.get("context") == context and
                   x.get("reviewed_for_local_read") is True]
        check(len(matches) == 1, "SOURCE_NOT_OWNER_ALLOWLISTED")
        # Original GHoT will recheck this policy and its pinned checkout at ACT.

    def preview(self) -> dict[str, Any]:
        ghot, _, home, context = self._ready()
        self._source_policy(home, context)
        self._write_candidate(context)
        result = _native(["preview", str(self.candidate_file)], checkout=ghot, home=home)
        check(result.get("schema") == "ghot.branch-worker-preview/v0" and
              result.get("status") == "READY" and
              result.get("act_authorized") is False and
              result.get("execution_performed") is False and
              isinstance(result.get("proposal_address"), str) and
              result["proposal_address"].startswith("sha256:"),
              "GHOT_NOT_READY_FOR_CONSENT")
        nonce = secrets.token_urlsafe(32)
        expires = time.time() + ACT_TTL
        with self._db() as db:
            db.execute("INSERT INTO previews (nonce_hash,proposal,source_sha256,expires) VALUES (?,?,?,?)",
                       (hashlib.sha256(nonce.encode()).hexdigest(),
                        result["proposal_address"], context["sha256"], expires))
        return {
            "schema": "workbench.stack-floor-020-preview/v0",
            "status": "READY",
            "consent_nonce": nonce,
            "expires_in_seconds": ACT_TTL,
            "proposal_address": result["proposal_address"],
            "fixed_source": SOURCE_SPEC | {"sha256": context["sha256"],
                                            "branchHint": BRANCH_HINT},
            "exact_operation": "GHoT 030 / hash-exact-source",
            "scope": "ONE_OWNER_LOCAL_GIT_SOURCE_HASH_ONLY",
            "owner_identity_authenticated": False,
            "executed": False,
            "relatte_admitted": False,
        }

    def act(self, *, nonce: str, proposal_address: str,
            phrase: str, acknowledge: bool) -> dict[str, Any]:
        check(self.enabled, "NATIVE_FLOOR_DISABLED")
        check(type(nonce) is str and 20 <= len(nonce) <= 100 and
              re.fullmatch(r"[A-Za-z0-9_-]+", nonce) is not None,
              "INVALID_CONSENT_NONCE")
        check(type(proposal_address) is str and
              re.fullmatch(r"sha256:[a-f0-9]{64}", proposal_address) is not None,
              "INVALID_PROPOSAL_ADDRESS")
        check(phrase == "ACT" and acknowledge is True, "EXPLICIT_LOCAL_ACT_REQUIRED")
        # Consume atomically BEFORE any native work. No second ACT on refresh or retry.
        with self._db() as db:
            db.execute("BEGIN IMMEDIATE")
            try:
                row = db.execute(
                    "SELECT proposal,source_sha256,expires,consumed FROM previews WHERE nonce_hash=?",
                    (hashlib.sha256(nonce.encode()).hexdigest(),),
                ).fetchone()
                check(row is not None, "UNKNOWN_OR_SPENT_PREVIEW")
                check(row[3] == 0 and row[2] >= time.time() and
                      row[0] == proposal_address, "PREVIEW_EXPIRED_SPENT_OR_CHANGED")
                changed = db.execute(
                    "UPDATE previews SET consumed=1 WHERE nonce_hash=? AND consumed=0",
                    (hashlib.sha256(nonce.encode()).hexdigest(),),
                ).rowcount
                check(changed == 1, "ONE_USE_PREVIEW_ALREADY_CONSUMED")
                db.execute("COMMIT")
            except Exception:
                db.execute("ROLLBACK")
                raise
        ghot, _, home, context = self._ready()
        check(row[1] == context["sha256"], "SOURCE_CHANGED_AFTER_PREVIEW")
        self._source_policy(home, context)
        self._write_candidate(context)
        native = _native([
            "act", str(self.candidate_file), "--expected", proposal_address,
            "--confirm", "ACT", "--ttl", "90",
        ], checkout=ghot, home=home)
        receipt = native.get("execution_receipt")
        job = native.get("job")
        check(native.get("schema") == "ghot.branch-worker-result/v0" and
              native.get("activation_ticket_verified") is True and
              native.get("execution_receipt_verified") is True and
              native.get("verified_success") is True and
              native.get("additional_work_permission") is False and
              isinstance(receipt, dict) and
              receipt.get("status") == "EXECUTED" and
              receipt.get("ticket_spent") is True and
              receipt.get("operation_attempted") is True and
              receipt.get("success") is True and
              isinstance(job, dict) and
              job.get("repository") == PLANZ_REPO and
              job.get("commit") == PLANZ_SHA and
              job.get("path") == PLANZ_PATH and
              job.get("blob_sha256") == context["sha256"] and
              job.get("operation") == "hash-exact-source" and
              job.get("branch_program_executed") is False and
              job.get("remote_effects") == 0, "NATIVE_030_EXECUTION_NOT_VERIFIED")
        return {
            "schema": "workbench.stack-floor-020-native-act/v0",
            "status": "EXECUTED_AND_LOCAL_RECEIPT_VERIFIED",
            "ticket_id": native["ticket_id"],
            "receipt_id": receipt["receipt_id"],
            "body_signer_particular": receipt["issuer_particular"],
            "sha256": job["blob_sha256"],
            "source_commit": PLANZ_SHA,
            "source_path": PLANZ_PATH,
            "operation": "hash-exact-source",
            "native_ghot_030_signature_verified": True,
            "execution_attempts": 1,
            "branch_program_executed": False,
            "remote_effects": 0,
            "ticket_spent": True,
            "owner_identity_authenticated": False,
            "new_relatte_crossing_created": False,
            "receiver_admitted": False,
            "external_owner_permission_inferred": False,
            "receipt": receipt,
        }
