# BRANCH-DECK-001 — find every locally known development branch

Status: experimental local read-only candidate; branch-specific execution and remote
GitHub ingestion are **not** part of this slice.

## Discovery

HOUSE previously surfaced only the current checked-out branch of each discovered
repository. The Branch Deck adds the `Branch Deck` navigator entry and a prominent
HOUSE landing card. Its `GET /api/branches` scan enumerates up to 400 local Git
refs **per discovered checkout**, recording for each ref:

- configured root + repository-relative path, branch name and full observed SHA;
- local branch versus **cached** remote-tracking ref, last commit date;
- checked out here / in a different worktree / not checked out;
- a lexical feature-like filter and explicit `not_tested` state.

Search by repo, branch and SHA, filter by feature-like/local/cached-remote/
other-worktree, and open the per-ref manual isolated test route. Refresh
manually with the Workbench Refresh control; an open, visible browser also
rescans locally every 120 seconds.

## Scope and exclusions

- No Git network fetch, remote GitHub branch discovery, authentication,
  checkout, new worktree creation, package install, project execution, CI
  integration, PR linkage, or automatic merge. **A remotely created branch that
  has not been fetched to a configured local checkout is not visible.**
- The cached remote-tracking SHA may be stale. This API never claims
  the remote server still has that SHA or that the branch has been tested.
- Incomplete or failed scans emit explicit `gaps`. Reaching the per-repository
  400-ref ceiling is **not** reported as a complete inventory.
- The Git subprocesses use fixed read-only argv and existing configured-root
  checkout paths. Branch names are returned as inert data and inserted into
  the browser using text nodes, not evaluated as HTML, scripts or commands.
- The per-ref "Test route" describes a **manual** safe isolation sequence; it
  does not execute it or advertise one-click tests.

## Next authorized slice

Add a separately enabled GitHub remote discovery adapter with bounded
pagination, provenance/freshness, branch-to-PR association, and distinct local
versus remote-only labels. Then implement a human-approved worktree creator
with owner-specific test descriptors, explicit command preview, runtime
isolation, exact-SHA/dirty-tree guards, cancellations and receipts. Never infer
a runnable test command from the branch name or execute repository content
merely because a scanner discovered it.
