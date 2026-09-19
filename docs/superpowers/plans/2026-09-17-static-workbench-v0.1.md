# Static Workbench v0.1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a runnable loopback-only Static Workbench that exposes machine telemetry, read-only Git repository discovery, bounded filesystem-object inspection, and a durable SQLite witness rail.

**Architecture:** A FastAPI supervisor serves a dependency-free browser UI and JSON API. Focused Python modules own configuration, path safety, repository inspection, telemetry, and journaling. Project-native execution is explicitly deferred behind typed adapter descriptors.

**Tech Stack:** Python 3.11+, FastAPI, Uvicorn, psutil, SQLite stdlib, pytest, vanilla HTML/CSS/JavaScript.

**Spec:** `docs/superpowers/specs/2026-09-17-static-workbench-v0.1-design.md`

## Global Constraints

- Default bind is `127.0.0.1:13700`.
- Offline-capable; no Docker, cloud account, or model required.
- File access is read-only and restricted to configured roots.
- No arbitrary shell execution from browser input.
- Git calls use argument arrays and bounded timeouts.
- Browser refresh/close does not erase journal state.
- Effectful project adapters are not implemented in v0.1.

---

### Task 1: Configuration, safe roots, and journal

**Files:**
- Create: `pyproject.toml`
- Create: `static_workbench/__init__.py`
- Create: `static_workbench/config.py`
- Create: `static_workbench/paths.py`
- Create: `static_workbench/journal.py`
- Test: `tests/test_paths.py`
- Test: `tests/test_journal.py`

**Interfaces:**
- Produces: `WorkbenchConfig`, `RootConfig`, `resolve_under_root(root, relative) -> Path`, `Journal.append(kind, payload) -> EventRecord`, `Journal.latest(limit) -> list[EventRecord]`.

- [ ] Write traversal/symlink-escape tests and run them to verify failure before `paths.py` exists.
- [ ] Implement canonical root-relative path resolution and make path tests pass.
- [ ] Write durable journal tests and run them to verify failure before `journal.py` exists.
- [ ] Implement SQLite journal with schema initialization and make journal tests pass.
- [ ] Run Task 1 tests together.

### Task 2: Read-only repository scanner

**Files:**
- Create: `static_workbench/repos.py`
- Test: `tests/test_repos.py`

**Interfaces:**
- Consumes: `RootConfig`.
- Produces: `discover_repositories(roots, max_depth) -> list[RepoStatus]` and `inspect_repository(path) -> RepoStatus`.

- [ ] Write fixture-repository tests for clean/dirty state and branch/SHA reporting; verify they fail.
- [ ] Implement bounded Git discovery and fixed-argument Git status inspection.
- [ ] Run repository tests and confirm pass.

### Task 3: Machine telemetry

**Files:**
- Create: `static_workbench/machine.py`
- Test: `tests/test_machine.py`

**Interfaces:**
- Produces: `sample_machine(roots) -> MachineSnapshot` with CPU, memory, disks, load, uptime, and thermal readings or explicit unavailable state.

- [ ] Write shape/availability tests using dependency injection for telemetry providers; verify failure.
- [ ] Implement telemetry sampling with psutil and graceful missing-sensor behavior.
- [ ] Run telemetry tests and confirm pass.

### Task 4: FastAPI supervisor and security floor

**Files:**
- Create: `static_workbench/app.py`
- Create: `static_workbench/schemas.py`
- Test: `tests/test_api.py`

**Interfaces:**
- Consumes: config, journal, repos, machine, safe-root resolver.
- Produces API routes: `GET /api/bootstrap`, `GET /api/machine`, `GET /api/repos`, `GET /api/objects/inspect`, `GET /api/events`.

- [ ] Write API tests for bootstrap, hostile Host rejection, object traversal rejection, and journal emission; verify failure.
- [ ] Implement app factory and API routes with same-origin/host guard.
- [ ] Run API tests and confirm pass.

### Task 5: Browser desk

**Files:**
- Create: `static_workbench/web/index.html`
- Create: `static_workbench/web/app.js`
- Create: `static_workbench/web/styles.css`
- Modify: `static_workbench/app.py`
- Test: `tests/test_ui.py`

**Interfaces:**
- Consumes: JSON API.
- Produces: three-region Navigator / Workspace / Witness UI with Machine, Repositories, and bounded Object inspection views.

- [ ] Write UI-serving tests for required landmarks and static assets; verify failure.
- [ ] Implement the browser surface using the approved dark design language and live API data.
- [ ] Run UI tests and confirm pass.

### Task 6: Adapter descriptor frontier and Linux deployment

**Files:**
- Create: `static_workbench/adapters.py`
- Create: `config.example.toml`
- Create: `scripts/install-user-service.sh`
- Create: `systemd/static-workbench.service`
- Create: `README.md`
- Test: `tests/test_adapters.py`

**Interfaces:**
- Produces: typed `AdapterDescriptor` / `OperationDescriptor`; documents but does not execute `prepare/execute/inspect/cancel/reconcile`.

- [ ] Write adapter-model validation tests and verify failure.
- [ ] Implement descriptor models without execution code.
- [ ] Add example configuration, user-service installer, and concrete Zorin/Linux run instructions.
- [ ] Run adapter tests.

### Task 7: Verification and distributable

**Files:**
- Create: `scripts/smoke.sh`
- Create: `.gitignore`

**Interfaces:**
- Produces: repeatable local verification and a zipped v0.1 source bundle.

- [ ] Run `pytest -q` and require zero failures.
- [ ] Run Python compile check across `static_workbench/`.
- [ ] Start supervisor on loopback, request `/api/bootstrap`, `/api/machine`, `/api/repos`, `/api/events`, and `/`, then terminate it.
- [ ] Verify `git diff --check` is clean.
- [ ] Create a source archive excluding state/cache files.
