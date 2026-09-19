# Creator Desk v0.1 — selected local source handoff

## What is wired

HOUSE now offers a **Creator Desk** reachable from the navigator and House action row. It borrows **workflow ordering** from Creator Workspace: narrow recall before a brief or draft, preserve source and interpretation separately, and route to the project-owned organ for live media, community help, or executable development.

The local registry lists five doors: Recall / research brief, Create from the brain, Live / podcast, Community / whole return, and Research -> executable. For each, the desk identifies **locally discovered** checkout names under configured roots and allows inspection through the existing read-only repository detail surface.

The explicit local source picker searches **one human-selected discovered checkout** using `GET /api/creator/sources?root_id=...&repo_path=...&query=...`. Results return root-qualified worktree path, line, bounded excerpt, short HEAD, and dirty state. The user may copy **one selected source handoff** into a separate Creator Workspace conversation. The handoff calls out that an excerpt is not a full source, frozen commit, or project-native receipt.

## Local source boundaries

- Only discovered repositories inside an explicitly configured root may be selected.
- Only Markdown and plain-text files are inspected, with a four-level directory cap and a maximum of 200 inspected files, 128 KiB per file, and 20 matching lines per request.
- Symlinked directories and files, hidden paths, build/cache directories, and filenames suggestive of secrets or credentials are excluded. These are defensive filters, **not a general secret scanner**; configure roots accordingly.
- Read-only scanning does not execute repository code, install packages, modify project state, or index an entire drive.
- No automatic cross-repository joining, background crawling, remote upload, AI inference, plugin execution, stream start, or help-slip mutation occurs.
- The current worktree may differ from HEAD, including uncommitted text. Compare a selected source against its project-owned version before promoting a consequential claim.

## Using the bridge

1. Install or open HOUSE and configure only the roots you intentionally want it to inspect.
2. Select **Creator Desk**; inspect available workflow doors and source checkouts.
3. Choose one local checkout, enter a phrase of at least two characters, and search.
4. Inspect the source path and worktree marker; use **Copy source handoff** for one result.
5. In your Creator Workspace conversation, paste the handoff and optionally provide the complete source or ask for narrow retrieval. The plugin's real workspace files, connectors, and memory remain outside HOUSE unless separately integrated.

The route labels refer to workflow design, not to installed plugin availability on the Linux machine. A discovered checkout means **present**, not **ready**, **compatible**, or **authorized**.

## Next bounded adapters

- Source-set handoff: explicit multi-selection, immutable hashes and digest/size checks, no unreviewed corpus upload.
- Creator drafts: a Workbench-owned local draft store, never overwriting source notes or project-native canon; author approval before publication.
- Static Live: bounded, explicit local OBS console door with controller-owned preflight and recording/streaming state; HOUSE never provides browser-supplied shell commands.
- Garden / Nourish: read-only presentation of project-native help case references and confirmation state, followed by separately authorized project-specific actions.
- Research to executable: one version-pinned adapter with prepare/execute/inspect/reconcile and restart/interruption tests before more authority is added.

**Law:** a local source can carry into a new work without its source identity, original state, or unresolved remainder being erased.
