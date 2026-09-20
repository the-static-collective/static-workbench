# OLD-GROWTH-002 — locally pinned source → human-reviewed native GRAFT ride

Stacked on [OLD-GROWTH-001 PR #49](https://github.com/the-static-collective/static-workbench/pull/49).
This slice adds no new GRAFT engine, remote fetch, autonomous proposals, checkout write,
Dogram operator, execution route, or source-project state mutation.

## Contract

Two session-guarded loopback endpoints:

- POST /api/house-maxhinal/old-growth/preview: choose TWO source selectors.
  Each has root_id, repo_path, repository (the-static-collective/REPO),
  exact local SHA-1 commit, relative text path, start_byte and end_byte.
  Supply explicit nonblank KEEP, BEND, question, relation_lane and move.
  Workbench checks the configured root and checkout identity, local origin URL
  against the declared GitHub repo, exact commit object, commit-tree file entry
  (regular blob, not symlink/submodule), <=128 KiB UTF-8 blob and <=4 KiB
  Unicode-aligned selected excerpt. It builds a deterministic, nonpersistent
  preview. A modified working tree does not alter the pinned commit blob.

- POST /api/house-maxhinal/old-growth/import: repeat all inputs with
  expected_packet_sha256, the TWO individually reviewed excerpt digests and
  human_confirmed=true. The server recomputes source validation and rejects
  any mismatched preview/digest/declaration. On success it inserts ONE
  Workbench-native, immutable ride, with old_growth_packet_sha256,
  independent source_refs and both the unrun proposal and parallel alternative.
  Exact replay is idempotent via a SQLite transaction. No GRAFT round is
  generated automatically: the operator chooses a native ride then separately
  invokes existing /api/house-maxhinal/graft/rounds/preview and save routes.
  The existing GRAFT draft, optional Dogram measurement and review contracts
  remain owned by their current modules.

## Security / nonclaims

- A local Git blob and tree entry were verified; a local remote URL was
  compared with the declared repository string. **This does NOT independently
  authenticate GitHub custody or prove that the selected commit is reachable
  from the current public remote.** Nothing is fetched over the network.
- Source selectors and excerpts are considered sensitive. They must be
  consciously selected before previewing/importing; imports persist only
  selected excerpts, not full source contents. This is not a safe archive for
  private testimony or secrets.
- Git file content is data. No Python import, build, shell from user input,
  subprocess from source content, or checkout of the selected commit is made.
- The packet digest is not authority. Saving a native ride is not selecting,
  testing, authorizing or implementing any candidate.
- Local review, Git, and SQLite operations are synchronous; Git has an
  explicit five-second timeout, size checks precede blob reads, and all
  source/project paths remain within configured roots.
- Workbench source previews may be invalidated if a local Git object becomes
  unavailable, the configured checkout/origin changes or the supplied source
  selection changes. Imports fail closed in these cases.
- Draft stack must reconcile with PR #49 and rectified Workbench carrier #48
  before any main integration. Real Linux/browser/restart/disclosure review
  remains a separate gate.

## Run

python -m pytest -q tests/test_old_growth.py tests/test_old_growth_import.py
python -m pytest -q

## Browser desk

The existing HOUSE Maxhinal view mounts the OLD GROWTH source selector panel.
It offers two discovered local checkout selections (defaulting to pinned HEAD),
explicit relative paths/UTF-8 byte ranges, KEEP/BEND/human question and the
declared relation/transformation. Preview renders each source's exact locator,
Git blob ID, excerpt SHA-256 and selected text. Each excerpt requires an
individual review checkbox, followed by an explicit separate import checkbox.
Changing form values clears the displayed preview. Imported rides render in
the **existing** native Maxhinal ride/history panel, which exposes the
existing GRAFT round/draft interface; neither preview nor import auto-selects
or executes a GRAFT candidate. Git/source text is rendered via textContent,
never as HTML.

The endpoints and browser panel are live only when this stacked PR is
deployed; their presence in a draft branch is not a claim main has them.
