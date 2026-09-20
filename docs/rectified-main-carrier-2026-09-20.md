# Rectified main carrier — integration ledger (2026-09-20)

**Status:** integration candidate; not merged, deployed, or production-certified. This document records observed repository state and a bounded landing contract, not an automated authority or an assertion that every source branch is compatible. The project-owned code and current GitHub PR/CI state outrank this snapshot.

## Exact starting state and first additive crossing

- Carrier branch: `integration/rectified-main-carrier-20260920`, created at main commit `25efe8487efaf4af003cb887a8f0072ffcb77c9e` (LIFESTREAM-002 #33).
- Source: [Flight Cards #29](https://github.com/the-static-collective/static-workbench/pull/29), head `1a2fc2f8bc8167b4ab753797d9a84fb5d55f4085`. This first crossing copied three standalone, non-executing files byte-for-byte from that exact head; **it did not merge or close PR #29 and does not imply its external Lovable adapter exists**.
- Source blob receipts: `static_workbench/flight_cards.py` = `217d924d20e9113d7d7e50f70e2fd9ad8cab08dd`; `tests/test_flight_cards.py` = `4eed52670489ca1542a9c53f1932c92198908551`; `docs/flight-card-handoff-v0.md` = `4e1b4f5c309b15e3937c74a716b0609fe0b88e65`.
- No app routes, UI, automatic actions, or main-branch changes are authorized by that file transfer. Run checks on the **carrier head**, not only on source PR #29.
- Second independent crossing: [Capability Return Ledger #41](https://github.com/the-static-collective/static-workbench/pull/41), head `92b0b89c07028c7c6690e51de55d18edd3de5a37`. Copied three standalone, non-executing files byte-for-byte: `static_workbench/capability_returns.py` = `6101a2a7a888b3279c4b9b62bb1f9626e1830079`; `tests/test_capability_returns.py` = `29e92c0dcec8798f43a7715fadb254bf901be56f`; `docs/HOUSE-FLYWHEEL-001.md` = `b1b4bdb46c7342a7e7d1ba57f1be7f79c75fe846`. The source remains a **draft** and was not merged or closed; its dependent #43/#46 UI/preview branches were **not** adopted. These files are a local reported-return backend only, not an executed or independently verified capability.


## Ownership and order of the next crossings

1. **HOUSE foundation** — [#23](https://github.com/the-static-collective/static-workbench/pull/23) owns the consolidated Founder inspection / Living Main / Relation Chamber / Return Desk / Staged Rocket / Flight Two result. Earlier #16, #19, #20, #21 and #22 are overlapping ancestry, **not five independent feature merges**. As observed, #23 head `73883e8165916f3d42d9546cd5504fa706908f34` diverged three commits behind main and GitHub reported `mergeable=false`. Reconcile #23's app/router/schema/browser/CI edits with main's Groundkeeper and LIFESTREAM-001/002 changes; preserve both feature families, migrations, tests and guards. Do not replace current main files wholesale with #23's older versions.
2. **Local-to-remote Branch Deck** — #34 → #38 → #39 → #44 → #47. Keep local/remote evidence distinct; exact-SHA worktree preparation remains opt-in and is **not a sandbox**; running project test commands requires a separate reviewed declaration and authorization. Do not squash away original source IDs or promote a scanner observation into an action.
3. **Attention Crossing** — #32 → #35 → #45. Preserve the human-selected, source-scoped Joyful / Useful / Curiouser / explicit None semantics; no implied ranking, automatic publication, source mutation or project-effect authority. #45's GOATnote/Static Live imports are source-reported and must keep their original identities.
4. **Capability Flywheel** — #41 → #43 → #46. Return Ledger → read-only Shelf → inert Loom preview; source reports and locally hashed records do not independently verify a source or authorize an effect. Neither the operational journal nor a proposal digest may silently become a project-native receipt.
5. **Visual Workbench** — #31 depends on HOUSE #23; #40 depends on #31 and carries a copy of Attention Crossing #32. Before landing #40, reconcile the duplicate Attention module against #32/#35 instead of registering two stores, duplicate routes or competing browser listeners.
6. **Experimental specimens** — #27 CLOCKWORK and #28 COMPOSABLE-OCCURRENCE remain separable experiments unless explicitly selected and verified. Real ephemeris validation is not established by #27's mocked adapter tests.

These are integration dependencies, not a claim that source PRs are reviewed, current-head green, or ready to merge. Retain original feature branches, open PR discussions, and issue ancestry until exact equivalent behavior is demonstrated in the carrier and each original is dispositioned with a link.

## Hard gates for each adopted slice

- **Identity:** record source PR, full head SHA, changed files, source-to-carrier file mapping, copied versus reconciled code and original nonclaims. Re-fetch source and main immediately before applying the slice. A changed head invalidates the old inspection.
- **Diff and conflict audit:** compare against *current carrier*, not an old fork point. For shared files check duplicated routes, module names, DOM IDs, schema migrations, SQLite stores, listeners, API permissions, source ownership and backwards-compatible restarts.
- **Functional/negative checks:** run `python -m pytest -q` on the resulting combined tree, relevant pinned Dogram/LIFESTREAM smokes and `node --check` for all touched browser scripts. New interfaces require regression tests of stale refs, dirty/unknown checkouts, origin/session refusal, replay, partial failure and nonmutation.
- **Current-head CI/review:** confirm GitHub Actions passed for the *exact carrier PR head*, verify required review threads and reconcile any meaningful regression before promoting another slice. An old source-PR green check is not a carrier check.
- **Actual workstation gate:** Linux browser/keyboard navigation, project-root permissions, SQLite migration + restart, backup/recovery and explicitly reviewed effect boundaries remain manual checks before declaring a main carrier fit for daily use. Remote CI is not a substitute.
- **Promotion:** stage on this isolated integration branch. Do not silently retarget original PRs, force-push shared branches, delete branches, enable automatic effects, or move main until the combined tree has passed its own checks and the original PRs' dispositions are recorded.

## Immediate verification for the two copied inert slices

```sh
python -m pytest -q tests/test_flight_cards.py tests/test_capability_returns.py
python -m pytest -q
```

Both commands must be run on this **carrier**, not inferred from the source head's CI. The Flight Cards v0 receiver and Capability Return Ledger remain inert and standalone; neither is wired into HOUSE action routes.

## Current unresolved boundary

The #23 HOUSE conflict is the primary integration blocker, not a license to discard the later LIFESTREAM/GROUNDKEEPER files. #40's duplicated Attention implementation is a separate semantic integration blocker. A green branch-level CI run for any single PR does not prove the combined app works, and none of the unresolved branches is counted as landed here.
