# BRANCH-DECK-004 — rolling public Collective radar

**Status: experimental, opt-in, stacked on BRANCH-DECK-003.**

Set `branch_radar_enabled = true` in Workbench's top-level TOML and
restart its local service. On startup and then every 30 minutes, the
Workbench supervisor performs one observational cycle. It lists at most the
first 100 public, owned, non-archived repositories of the GitHub account
`the-static-collective`, then checks up to five repositories' first
100 GitHub branches apiece. At most six anonymous GitHub API requests are
made in a successful cycle. An initial full look at 100 repos needs at
least 20 cycles, approximately ten hours; rate limits and failures can
extend it. There is no guarantee that every branch is ever found.

The Branch Deck reads the **Workbench-owned SQLite snapshot** of the last
successful observations, refreshed in its browser every two minutes.
An initial observation of a repository is a baseline, not a claim that its
branches were created that day. A branch first observed later receives
a `first_seen` timestamp distinct from its Git commit date and appears
under **Recently discovered** for 24 hours. HEAD updates retain the
original branch first-seen time; these are not new branch creations.
The radar makes no PR or test-run readiness claim. Scan dates, first-page
limits, repository-list limits, errors, and the rotating cursor remain
visible. Missing or deleted branches are **not** inferred from omitted
pages; previously observed branches are retained with their old timestamp.

The account is a GitHub *user* account, so the scanner uses the public
`/users/the-static-collective/repos` endpoint, not an organization API.
Only returned entries with a matching owner and strict repository name
are accepted. No credential is stored or transmitted. The HTTP host is
fixed to `api.github.com`; network lookup can be stopped by disabling
this config flag and restarting.

**Limits:** public-only, 100-repository initial listing, first page of
100 branch refs per repo, anonymous rate limits, no private or forked
repositories, no guaranteed instantaneous discovery, no PR linkage
at fleet level, no code acquisition, checkout, tests or merge rights.
Each project remains its own authority. This visibility surface does not
replace the separate manual per-repository public PR inspection door.
