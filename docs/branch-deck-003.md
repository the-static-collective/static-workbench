# BRANCH-DECK-003 — prepare a local branch for isolated manual testing

Status: experimental local filesystem/Git metadata effect, **stacked on #38**.
This is not a general test-runner, remote-fetcher or merge controller.

## Enable

Set `branch_worktrees_enabled = true` in the top-level Workbench TOML
configuration and restart. The default is disabled. A local operator must
visit **Branch Deck**, choose a **local** branch card, press **Preview isolated
checkout**, review its exact commit and destination, and separately press
**Create this isolated checkout**.

The action creates a detached worktree at
`<state_dir>/branch-deck-worktrees/candidate-<stable-id>`, outside ordinary
project roots in a typical Workbench configuration. The current project
working files and branch remain untouched, but Git's administrative worktree
registration is updated. The result is a Workbench operational receipt
containing the exact before/after commit, selected ref, preview digest and
destination. A second attempt at an existing path refuses, rather than
overwriting or silently returning success.

The action pins and rechecks a preexisting *local* branch exact 40-character
commit SHA; cached remote-tracking and GitHub-only refs cannot be used. For
remote-only branches, a separately authorized download and SHA verification
is needed first.

The worktree creation executes only a fixed Git argv (no shell), disables
checkout hooks and fsmonitor, ignores ambient user/system Git configuration
(including global Git LFS drivers), and refuses configured local process/smudge
filters before checkout. Repositories needing locally configured filter drivers
require separate manual review. It does not
install dependencies or run project-owned scripts/tests. A checkout is not
a full security sandbox: inspect files, symlinks and project instructions
before running code. A real test runner requires a separate owner-approved
test manifest, isolated runtime and effect receipt.

## Uncertain outcomes

An interrupted or failed `git worktree add` may leave a directory or Git
administrative registration behind. The adapter does not automatically delete
either. Inspect the returned planned destination and
`git -C <original_repo> worktree list --porcelain` before any retry.
Do not run `git worktree prune` or remove another worktree automatically.

## Boundary

Opt-in and separately confirmed effect; never create from a remote-only card;
exact SHA is an identity not authorization or proof of quality; prepared
worktree is not a successful test and is not project-native adoption.
