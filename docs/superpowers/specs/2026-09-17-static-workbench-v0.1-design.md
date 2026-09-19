# Static Workbench v0.1 Design

## Goal

Create a local-first browser workbench for a dedicated Linux Static Collective machine. The browser is the desk; a loopback-only supervisor owns presentation, local job supervision, and its operational journal. Connected projects retain ownership of native identities, schemas, validation, semantics, receipts, and consequential decisions.

## Constitutional boundaries

- The browser is never the source of truth for project-native state.
- Closing or refreshing the browser does not cancel or erase supervised work.
- Workbench operational state is durable in SQLite and distinct from native project receipts.
- The Workbench does not create a universal truth record.
- Project adapters support only explicit versions and operations.
- Acceptance, process observation, native completion, and verification are separate states.
- Native refusal/degraded/hold outcomes are preserved verbatim; the bridge cannot relabel them as success.
- Browser actions never execute arbitrary shell strings.
- File access is bounded to configured roots and must reject traversal and symlink escape.
- The initial release is loopback-only and offline-capable. LAN/phone access is a separate future deployment decision.

## v0.1 scope

### 1. Supervisor

A Python FastAPI service binds only to `127.0.0.1` by default and serves the browser UI plus a small JSON API. It owns:

- Workbench configuration
- SQLite operational journal
- repository discovery/read-only status
- machine telemetry
- bounded filesystem object discovery/inspection
- event/witness feed

The supervisor does not dispatch Toaster, Dogram, ALEX, 3rdi, LOADOUT, or Static Live operations in v0.1.

### 2. Browser surface

The default layout has three conceptual regions:

- **Navigator**: repositories, machine, objects
- **Workspace**: selected repository/object/machine details
- **Witness rail**: Workbench operational events

The initial UI must remain useful without any connected project adapter.

### 3. Machine telemetry

Expose CPU, memory, root disk, configured-root disk information when available, load average, uptime, and thermal sensor readings when supported by the host. Missing sensor support is an explicit unavailable state, not an error.

### 4. Repository discovery

Configured roots are scanned to a bounded depth for Git repositories. For each repository expose:

- name and path relative to its configured root
- current branch or detached state
- HEAD short SHA when available
- clean/dirty state
- ahead/behind counts when an upstream exists

Repository inspection is read-only.

### 5. Filesystem objects

A filesystem object is a bounded Workbench view of a file or directory under a configured root. v0.1 exposes metadata and a limited text preview for small UTF-8 files. It does not edit files.

Every object reference contains an owner root ID and root-relative path. The API resolves paths against the root and rejects `..`, absolute paths, and symlink escapes.

### 6. Witness journal

The Workbench writes operational events to SQLite before or as it performs Workbench-owned actions. v0.1 event kinds include:

- `workbench.started`
- `repos.scanned`
- `object.inspected`
- `machine.sampled`

The journal exposes newest-first retrieval and survives process restarts.

### 7. Adapter frontier

The repository includes a typed adapter descriptor model documenting the future boundary:

- `prepare(operation, native_input_refs, requested_output_scope)`
- `execute(preview_ref, attributable_authorization_ref, invocation_id)`
- `inspect(job_handle)`
- `cancel(job_handle)`
- `reconcile(invocation_id)`

v0.1 includes descriptors only; effectful adapter execution is out of scope.

## Deployment

- Python 3.11+
- FastAPI + Uvicorn
- SQLite via Python stdlib
- psutil for host telemetry
- no Docker requirement
- no cloud account requirement
- no model requirement
- browser assets served by the supervisor
- default URL: `http://127.0.0.1:13700`

A `systemd --user` service template and install helper are included, but installation is opt-in and does not require root.

## Security floor

- Bind loopback by default.
- Reject non-loopback Host headers except the explicit configured host set.
- Mutating API routes require a local session token delivered through a same-origin bootstrap response, not a URL.
- No permissive CORS.
- No browser-supplied shell commands.
- Git subprocess calls use fixed argument arrays and bounded timeouts.
- Configured roots are canonicalized at startup.
- File resolution verifies the final real path remains under its configured root.
- Text previews have a fixed byte ceiling.

## Acceptance evidence

1. Supervisor starts offline and serves the UI on loopback.
2. API reports machine telemetry with explicit unavailable fields where unsupported.
3. Repository scanner finds fixture repos and reports branch/clean/dirty status correctly.
4. Traversal and symlink escape attempts are rejected.
5. Inspecting a text object emits a durable journal event.
6. Restarting the app against the same state directory retains witness events.
7. Host-header enforcement rejects an unapproved host.
8. Full automated test suite passes.
