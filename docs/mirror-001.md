# MIRROR-001 — Workbench-owned visual editing specimen

**Status:** experimental, one fixture only. This is a source-backed demo, **not** a universal WYSIWYG editor or an adapter for arbitrary running apps. It is stacked on the consolidated HOUSE branch ([PR #23](https://github.com/the-static-collective/static-workbench/pull/23)) so this implementation does not attempt to reconcile parallel HOUSE interfaces on main.

## What actually runs

Open the local Workbench, choose **MIRROR · visual editor**, and click the card inside the embedded demo. The inspector exposes two closed design tokens: card width (220–600 px) and accent color (six-digit lowercase hex). Input changes are visible immediately through temporary CSS custom-property overrides in the preview DOM; they do not modify source.

**Preview source patch** takes the exact SHA-256 of the currently observed Workbench-owned stylesheet, re-reads and validates its content, and presents a unified source diff plus proposed SHA-256. **Apply reviewed patch** submits the same parameters, observed-source hash and reviewed-proposal hash. The server re-validates both identities under a local lock, writes one bounded CSS file atomically under `state_dir/mirror-001/demo.css`, and appends a Workbench journal event containing before/after hashes. Reloading the iframe observes the new stored style. A repeat or stale application is refused.

The demo is generated from a fixed HTML template and served under `/api/mirror/demo` with a restrictive CSP. It has no arbitrary HTML editor, scripts, network fetch, external asset request, repository path selection, development-server launch, generic shell runner, plugin call, or external project file mutation.

## Boundaries

- The source filename, directory, markup and editable CSS tokens are code-owned. Neither a browser request nor an AI instruction can name another path through these endpoints.
- The local Host restriction is inherited from HOUSE. Preview and apply also require the session header and exact same-origin browser Origin when present.
- Source patch preview is not approval to apply. Applying requires a separate user click and exact proposed-result hash.
- Source changes outside the known fixture format, symlinked state, stale source hashes, unknown request fields and unsupported property values are refused.
- An event receipt records the local demo write; it is **not** project-native acceptance, an observed user interaction trace, a Git commit, an automatic merge, or evidence that a third-party app was edited.
- Other apps can be loaded only in future adapters, with explicit ownership, source mapping, iframe/origin permissions, build isolation and separate project-owned patch authority. A third-party iframe's DOM cannot generally be inspected across origins.

## Suggested next proof

Build a second **read-only** adapter to a declared, locally running web app, then a source mapping for one known framework/component under a separate project-owned authorization contract. Keep the demo fixture and adapter source edits separate. After running this branch's checks, perform an actual Linux browser test of click selection, drag/keyboard inputs, preview, apply, iframe reload, and restart preservation before expanding permissions.

## Run

```bash
python -m pip install -e '.[dev]'
python -m pytest -q tests/test_mirror.py
node --check static_workbench/web/mirror.js
static-workbench
```

Use a configured loopback Workbench instance and its existing session guard. The first apply creates the fixture stylesheet under the selected Workbench state directory; no external project checkout is modified.
