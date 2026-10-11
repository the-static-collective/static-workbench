# BRANCH HARBOR 003 — The shelf of possible futures

**Status:** experimental Workbench branch stacked on **BRANCH-DECK 002**, not yet merged or deployed. No new server or outbound network dependency.

Workbench's existing Branch Deck already inventories configured-root refs and, optionally, public GitHub branches. This adds an **ephemeral, human-initiated foreign branch cargo shelf inside the same navigator view**. It does not change Workbench's existing Git discovery or GRAFT workflows.

## Source of the specimen

[FREEPORT 006 draft PR #4](https://github.com/the-static-collective/freeport/pull/4) is a synthetic experiment that stores two exact Git blobs from the CANNON STACK² 017 and Static Workbench OLD-GROWTH 002 branches, produces a Workbench-native unrun proposal with one GHoT synthetic digest-only adapter, then records a destination-owned HOLD.

Its workflow artifact contains `evidence/manifest.json` with exact commit/path/digest **claims**, not raw donor code or secret signing keys. To explore one in the Workbench UI, use Branch Deck → **Branch Harbor** → paste the explicitly selected public synthetic manifest JSON → **Inspect manifest and ancestry**. You may then click **Export pointer-only Free Graph seed**. No manifest is saved in Workbench's SQLite, browser storage or operational journal. Clearing the local shelf removes it from the in-memory view.

A manifest is just foreign input. The importer rejects all unexpected object keys (including nested keys), duplicated JSON keys, more than 16 KiB, unknown donor SHAs, unsupported source paths, claimed ADMIT/KEEP, side effects, Git mutations, publication permissions, nonzero deploy counts, or forged source/child identities. The accepted form is deliberately **only** Freeport 006; it is not a general Git repository ingestion protocol.

## The actual Browser Desk

- Pinned source selectors and Git SHA-1/SHA-256 fields appear in two distinct review cards.
- Branch Deck locally known refs can be compared with the source **claims**, but a coincident commit does not verify all blob bytes or source-owner permission.
- The child remains a **proposed name**. No branch with that name is created.
- `HOLD` is **reported by the Freeport manifest**. This surface does **not** verify the signed Freeport receiver receipt or rerun its native cold verifier. There is no `ADMIT` or `KEEP` button.
- The graph lane shows two `descends-from` links, one `tests` link (reported GHoT digest-only probe, not native donor compatibility), and one `connects` link between the reported local HOLD and proposed artifact.
- Graph has **no `constitutes` relation**: Free Graph's actual grammar reserves owner-local constitution for an independently supported local gate.
- All text is rendered via `textContent`, not injected as HTML.

The request is a session-guarded `POST /api/branches/freeport/preview`, requiring the Workbench's same-origin local session token and a bounded JSON body. The endpoint only constructs an in-memory review projection. It never opens a file chosen in a manifest, fetches GitHub, runs shell or an adapter, talks to Freeport/Supabase, checks out code, or mutates a repository.

## The actual Free Graph owner, not an invented vocabulary

Graph projection uses the real Free Graph v0 schema:
- `schema=free-graph.packet/v0`
- `modes=["seed"]`
- Task World Cut `unresolved`, owner head absent
- one unresolved, pointer-only manifest source with `authority:none`
- two source artifact observations, one proposed candidate, one unresolved native-compatibility claim, one synthetic test question, one reported HOLD receipt observation
- exactly four links: `descends-from` × 2, `tests` × 1, `connects` × 1

Record and packet IDs follow the original Free Graph canonical SHA-256 JSON procedure. The CI workflow **checks out [free-graph](https://github.com/the-static-collective/free-graph) at exact commit `ec0ad8743c5faac3f3675760bbafcbcb1df846c1`** and runs its original `scripts/fg_core.py` `validate_packet` and `packet_id` on Workbench-generated data. Free Graph retains ownership of semantics; Workbench does not copy its validator into a competing format.

### Boundaries

`PINNED COMMIT CLAIM != VERIFIED BLOB`

`MANIFEST HOLD != VERIFIED LOCAL RECEIPT`

`SEED GRAPH != CONSTITUTED WORLD`

`SOURCE RELATIONSHIP != COMPATIBILITY`

`BRANCH SUGGESTION != BRANCH CREATED`

`BRANCH VIEW != MERGE AUTHORITY`

There is no WITNESS private archive, no user Suno ingest, no publishing, no network proxy, no remote authentication and no owner rights inferred.

## Reproduce

```sh
pip install -e '.[dev]'
pytest -q tests/test_branch_harbor.py tests/test_branch_deck.py tests/test_branch_remote.py
pytest -q
```

To include native Graph verification, set `FREE_GRAPH_ORIGINAL_ROOT` to a local checkout at the exact pinned Free Graph commit. Without it, the native donor-core test is **skipped explicitly**, and Workbench does not claim third-party independent verification. GitHub Actions always supplies the pinned donor, executes original Free Graph tests, and runs full Workbench regression and JS syntax checks.

## Next genuine crossing

After explicit owner disclosure approval, one could add a **local-only receipt verifier** that reads a complete FREEPORT 006 evidence directory under an already configured root, checks native Freeport receipts with the original cold verification procedure, and upgrades only the validated claims. This remains a distinct future experiment: the current desk deliberately does not infer verification from manifest text.
