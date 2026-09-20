# BRANCH-DECK-005 — operator-declared, manually authorized test suites

**Status: experimental, stacked on BRANCH-DECK-004.**

An exact-SHA detached worktree prepared by BRANCH-DECK-003 can now run an
explicitly configured *project-specific* test command, subject to two
distinct browser interactions: **Preview exact test execution** and
**Run this approved test program**. The selected local branch, checked
commit, repository GitHub origin, test suite id/argv, timeout and planned
worktree are pinned into the preview digest; stale branches, changed
worktrees, missing suites and changed previews refuse.

## Owner-owned suite declaration

No test suite is inferred from the branch, README, package.json, PR
description or source code. An operator must first declare it in the
**Workbench's own** TOML configuration, e.g.:

```toml
branch_worktrees_enabled = true

[[branch_test_suites]]
repo = "the-static-collective/static-workbench"
id = "python-pytest"
argv = ["python3", "-m", "pytest", "-q"]
timeout_seconds = 90
```

Place these top-level keys and suite array in the Workbench TOML, separately
from the configured `[[roots]]` entries. Install any approved dependencies
outside this route; this capability never runs package installation.
Suite identity is an exact Collective GitHub repository origin, not a
fuzzy checkout-name match. Up to 32 suites can be declared globally,
1–12 literal argv elements per suite, 5–180 seconds timeout.

## Execution and risk

**This is not a security sandbox.** Tests execute as the local Workbench
operating-system user, with access to host files, local services, the network,
and potentially spawned processes. A clean detached Git worktree isolates
the selected checkout location, NOT the privileges of the code. Do not run
untrusted feature branches through this route. The fixed argv and minimal
child environment do not prevent malicious or mistaken test code from
changing the rest of the machine.

Workbench rechecks the local ref exact SHA, detached worktree HEAD,
clean tree and Git worktree registration, and refuses executing from
a checkout nested inside any configured source root. It runs only a suite
predeclared by the Workbench operator for that repository and does not
evaluate the project's branch-owned test manifest as a command source.
One active test at a time is permitted by a Workbench-owned advisory
cross-process lock. Processes run with a bounded timeout (5–180s), output
volume limit (256 KiB checked while running), closed stdin, and a separate
temporary HOME; a timeout kills the launched process group. Detached
grandchildren can outlive that group and nothing prevents filesystem
or network access. These limits mitigate accidental resource use but
cannot contain hostile code.

An append-only Workbench-local SQLite receipt records exact source commit,
suite, preview digest, exit status, timeout, output SHA-256, output length,
bounded UTF-8 excerpt, start/finish timestamps and receipt digest.
This is a **Workbench operational test receipt**, not a project-native
acceptance, runtime compatibility, merge recommendation or deployment proof.
Test logs can contain sensitive data; they stay on the local workstation and
are not automatically uploaded, published or sent to a model.

Failed runs report failed or timed-out, never silently pass. If project
tests dirty the prepared worktree, review its state manually; subsequent
preview requests refuse until the worktree is clean. No automatic cleanup,
rollback or merge occurs.

## Scope remaining

No GitHub-only branch download; use a separately authorized exact-SHA
fetch before a remote-only branch becomes locally testable. No container/VM
runtime sandbox, dependency resolver, credential broker, parallel test
scheduler, CI interpretation or automatic merge. A future sandbox adapter
must be a separate, reviewed capability.
