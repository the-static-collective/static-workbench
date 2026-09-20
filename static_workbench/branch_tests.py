"""BRANCH-DECK-005: human-approved runs of administrator-declared test suites.

CAUTION: A Git worktree is NOT an OS sandbox. The selected test program has
the permissions of the Workbench operating-system user; it may access files,
the network, and spawn children. Never run untrusted branch code here.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import os
import re
import secrets
import signal
import sqlite3
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path

from .branch_remote import _origin_slug, RemoteDiscoveryError
from .branch_worktree import _destination, _git_checked, WorktreeError
from .config import BranchTestSuite, WorkbenchConfig
from .repos import RepoStatus

_SHA = re.compile(r"^[0-9a-f]{40}$")


class SuiteError(ValueError):
    pass


def available_suites(config: WorkbenchConfig, repo: RepoStatus) -> tuple[BranchTestSuite, ...]:
    if not config.branch_test_suites:
        return ()
    try:
        slug = _origin_slug(repo)
    except RemoteDiscoveryError:
        return ()
    return tuple(suite for suite in config.branch_test_suites
                 if suite.repo.casefold() == slug.casefold())


def _prepared(config: WorkbenchConfig, repo: RepoStatus,
              ref: str, expected_commit: str) -> Path:
    if not config.branch_worktrees_enabled:
        raise SuiteError("worktree_effect_disabled")
    if not _SHA.fullmatch(expected_commit) or not ref.startswith("refs/heads/"):
        raise SuiteError("only_verified_local_branch_supported")
    destination = _destination(config, repo, expected_commit)
    try:
        if not destination.is_dir() or destination.is_symlink():
            raise SuiteError("prepared_worktree_missing_or_symlink")
        destination_real = destination.resolve(strict=True)
        state_real = config.state_dir.resolve(strict=True)
        if not destination_real.is_relative_to(state_real):
            raise SuiteError("prepared_worktree_outside_state")
        # Never execute tests in the original repo or in a worktree that
        # is nested inside any configured source root.
        for root in config.roots:
            if destination_real.is_relative_to(root.path.resolve(strict=False)):
                raise SuiteError("prepared_worktree_overlaps_source_root")
        if _git_checked(Path(repo.path), "rev-parse", "--verify", ref + "^{commit}") != expected_commit:
            raise SuiteError("branch_moved_refresh_before_testing")
        if _git_checked(destination_real, "rev-parse", "--verify", "HEAD") != expected_commit:
            raise SuiteError("worktree_head_changed")
    except WorktreeError as exc:
        raise SuiteError(str(exc)) from exc
    return destination_real


def _verify_detached_clean(repo: RepoStatus, destination: Path, expected_commit: str) -> None:
    # Detached symbolic-ref command exits 1; inspect branch using rev-parse.
    if _git_checked(destination, "rev-parse", "--abbrev-ref", "HEAD") != "HEAD":
        raise SuiteError("worktree_must_be_detached")
    if _git_checked(destination, "status", "--porcelain=v1", "--untracked-files=normal"):
        raise SuiteError("worktree_not_clean")
    # Verify this checkout really belongs to the selected local Git repository.
    listing = _git_checked(Path(repo.path), "worktree", "list", "--porcelain")
    known = {Path(line[9:]).resolve(strict=False) for line in listing.splitlines()
             if line.startswith("worktree ")}
    if destination not in known:
        raise SuiteError("worktree_not_registered_for_selected_repository")
    if _git_checked(destination, "rev-parse", "--verify", "HEAD") != expected_commit:
        raise SuiteError("worktree_head_changed")


def preview_test(config: WorkbenchConfig, repo: RepoStatus, ref: str,
                 expected_commit: str, suite_id: str) -> dict:
    suites = available_suites(config, repo)
    suite = next((s for s in suites if s.id == suite_id), None)
    if suite is None:
        raise SuiteError("suite_not_declared_for_repository")
    destination = _prepared(config, repo, ref, expected_commit)
    _verify_detached_clean(repo, destination, expected_commit)
    data = {
        "root_id": repo.root_id, "repo_path": repo.relative_path,
        "ref": ref, "commit": expected_commit, "suite_id": suite.id,
        "argv": list(suite.argv), "timeout_seconds": suite.timeout_seconds,
        "destination": str(destination), "effect": "execute_project_test_program",
        "runtime_isolation": "none_process_runs_as_workbench_user",
    }
    digest = hashlib.sha256(json.dumps(data, sort_keys=True,
               separators=(",", ":")).encode("utf-8")).hexdigest()
    return {**data, "preview_digest": digest}


def run_test(config: WorkbenchConfig, repo: RepoStatus, ref: str,
             expected_commit: str, suite_id: str, expected_preview_digest: str) -> dict:
    preview = preview_test(config, repo, ref, expected_commit, suite_id)
    if preview["preview_digest"] != expected_preview_digest:
        raise SuiteError("test_preview_changed_review_again")
    # Advisory cross-process lock prevents two Workbench suites from running
    # simultaneously. It does not prevent unrelated local shell processes.
    state = config.state_dir.resolve(strict=True)
    lock_path = state / "branch-deck-test.lock"
    with lock_path.open("a+") as lock:
        try:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise SuiteError("another_branch_test_in_progress") from exc
        preview = preview_test(config, repo, ref, expected_commit, suite_id)
        if preview["preview_digest"] != expected_preview_digest:
            raise SuiteError("test_preview_changed_review_again")
        run_id = secrets.token_hex(12)
        started = datetime.now(timezone.utc).isoformat()
        destination = Path(preview["destination"])
        # Minimal process environment, not a sandbox: a test may still reach
        # the OS, user files, network, and forked processes.
        with tempfile.TemporaryDirectory(prefix="branch-test-", dir=state) as home:
            environment = {
                "PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                "HOME": home, "TMPDIR": home, "XDG_CACHE_HOME": home,
                "CI": "true", "PYTHONDONTWRITEBYTECODE": "1",
                "GIT_OPTIONAL_LOCKS": "0", "LC_ALL": "C",
            }
            with tempfile.TemporaryFile(mode="w+b", dir=state) as log:
                process = None
                try:
                    process = subprocess.Popen(
                        preview["argv"], cwd=destination, stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT, env=environment,
                        start_new_session=True, close_fds=True,
                    )
                    import time
                    deadline = time.monotonic() + preview["timeout_seconds"]
                    timed_out = False
                    output_limit_exceeded = False
                    while process.poll() is None:
                        if os.fstat(log.fileno()).st_size > 262144:
                            output_limit_exceeded = True
                            break
                        if time.monotonic() >= deadline:
                            timed_out = True
                            break
                        try:
                            process.wait(timeout=0.2)
                        except subprocess.TimeoutExpired:
                            pass
                    if timed_out or output_limit_exceeded:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    process.wait()
                    returncode = process.returncode
                except OSError as exc:
                    raise SuiteError("test_program_could_not_start") from exc
                finally:
                    if process is not None and process.poll() is None:
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                        process.wait()
                log.flush()
                log.seek(0)
                digest = hashlib.sha256()
                snippet = b""
                output_bytes = 0
                while True:
                    chunk = log.read(65536)
                    if not chunk:
                        break
                    digest.update(chunk)
                    output_bytes += len(chunk)
                    if len(snippet) < 8192:
                        snippet += chunk[:8192 - len(snippet)]
        result = {
            "run_id": run_id, "started_at": started,
            "finished_at": datetime.now(timezone.utc).isoformat(),
            "root_id": repo.root_id, "repo_path": repo.relative_path,
            "ref": ref, "commit": expected_commit, "suite_id": suite_id,
            "preview_digest": expected_preview_digest,
            "destination": str(destination), "exit_code": returncode,
            "timed_out": timed_out, "output_limit_exceeded": output_limit_exceeded,
            "status": "timed_out" if timed_out else ("output_limit_exceeded" if output_limit_exceeded else
                      ("passed" if returncode == 0 else "failed")),
            "output_sha256": digest.hexdigest(), "output_bytes": output_bytes,
            "output_excerpt": snippet.decode("utf-8", errors="replace"),
            "output_truncated": output_bytes > len(snippet),
            "execution_isolation": "none", "project_native_test_receipt": False,
        }
        receipt = json.dumps(result, sort_keys=True, separators=(",", ":"))
        result["receipt_sha256"] = hashlib.sha256(receipt.encode("utf-8")).hexdigest()
        db_path = state / "branch-test-receipts.sqlite3"
        with sqlite3.connect(db_path, timeout=5) as db:
            db.execute("""CREATE TABLE IF NOT EXISTS runs
                       (run_id TEXT PRIMARY KEY, receipt TEXT NOT NULL)""")
            db.execute("INSERT INTO runs VALUES (?,?)", (run_id, json.dumps(result)))
        return result
