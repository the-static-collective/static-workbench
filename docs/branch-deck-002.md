# BRANCH-DECK-002 — opt-in public GitHub observation

Status: stacked experimental candidate on BRANCH-DECK-001 (#34).
It gives the local browser a **human-triggered** public remote lookup for one
configured local checkout; it is not a periodic organization-wide subscription.

## Enable and use

Set `github_remote_discovery = true` in the top-level Workbench TOML
configuration, then restart the service. The default is false.
Open **Branch Deck**, choose a discovered repository that has a public
`https://github.com/the-static-collective/<repo>.git`, GitHub SSH or scp-style
origin, then press **Check public GitHub branches**.

A dated GitHub-only observation appears next to, never in place of, the local
branch data. Filter for **Not found locally** to find branches not matched by
a locally known branch of the same name or an `origin/<name>` cached ref.
Click a GitHub observation to inspect its full commit SHA, exact-commit
browser link and same-repository *open* PR links (drafts labeled).

The scanner uses HTTPS GET directly against the *fixed* `api.github.com`
host. It accepts no user-supplied URL, token, credential, arbitrary owner or
repository path. It does not invoke a git remote command or fetch repository
content. Every call is explicitly triggered from the browser, with at most
2 × 100 branch records and 2 × 100 open PR records for that selected repo.
A full final page is reported as incomplete; blocked/failed PR lookup leaves
branch discovery visible with an explicit unresolved gap.

Public API access is anonymous and subject to GitHub rate limits; private
repositories are not supported. HTTP failures (including 403 rate limit)
remain errors rather than stale cached data masquerading as fresh.

## Contract

- Local SHA equality, name agreement, and same-repo PR association are distinct
  observations; none constitutes semantic equivalence, test readiness or
  a merge verdict.
- A GitHub-only branch is **not installed or runnable locally**. Only a separately
  authorized fetch and exact-SHA verification can change that.
- PR association is an *open same-repository head-ref* observation only.
  Missing a PR is not proof that no closed PR, fork PR or unmatched PR exists.
- No OAuth or PAT, persistent remote cache, autonomous background network
  polling, checkout, worktree creation, command execution or project-native
  receipt is introduced here.
- Browser display uses text nodes for remote titles and names. PR URLs are
  constructed from the fixed validated repo slug and numeric PR ID.

## Next boundary

A separate opt-in, exact-SHA verified fetch/worktree route needs a dedicated
project-effect fence and human review. Executing project-owned test commands
requires a second authorization and an explicitly declared project-owned test
contract, with isolated runtime, timeout, cancellation and result receipts.
