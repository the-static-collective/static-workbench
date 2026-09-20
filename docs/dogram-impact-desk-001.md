# HOUSE × Dogram Impact Desk 001

**Status:** experimental local integration; no public Dogram operator or autonomous project execution.

Impact Desk offers a human-selected comparison of the two most recent **committed**
states of one discovered Python repository. The baseline is the first parent
of HEAD, the candidate is HEAD. It intentionally does not compare arbitrary
branches, parse the working tree, inspect non-Python languages, run project code,
grade PR quality or make a merge recommendation.

## Linux setup

1. Put a normal checkout of [Dogram](https://github.com/the-static-collective/Dogram)
   and at least one Python repository with two commits under configured HOUSE roots.
   HOUSE must discover exactly one checkout named `Dogram` for the run.
2. Keep the Dogram checkout clean. HOUSE will explicitly show its **full HEAD SHA**
   and refuse a run if HEAD moves or tracked/untracked work makes it dirty.
3. Open HOUSE → **Dogram Lab** at `http://127.0.0.1:13700`. Select the Python
   repository and choose **Preview committed source**.
4. Inspect both commits, file counts, exact input digest, dirty-worktree flag and
   pinned Dogram SHA. Choose **Run exactly this Dogram comparison**.
5. Inspect the resulting node/edge/reachability deltas. The saved report has a
   SHA-256 identity; paste that ID under *Return to an earlier measurement* to
   reopen the same immutable Workbench-owned report after a restart.

Dogram is loaded from the selected checkout by an isolated fixed Python command.
The checked-out Dogram code itself is executed; treat that local repository as
trusted software. The target repository is **never imported or executed**:
HOUSE takes only Python blob bytes from two immutable Git commits, stores them
in temporary snapshot directories, and passes those directories to Dogram's
existing `repo_impact` *research* kernel. Do not confuse this research kernel
with Dogram's four public `dogram.specimen/v0` operators.

## Fixed boundaries

- One repository selected from existing HOUSE root discovery, not an arbitrary
  path or user-supplied shell command. Python source paths must be safe ordinary
  Git blobs; symlinks/submodules for `.py` paths are refused.
- Max **64 Python files per snapshot**, **64 KiB per Python file**, **2 MiB per
  snapshot**. Unsupported, oversized, missing-parent or malformed snapshots refuse.
  Complex or invalid Python that cannot be parsed refuses when Dogram runs.
- Preview and execution independently compare the exact source-tree object
  identities, baseline/candidate commits, and local Dogram HEAD. Changed inputs
  require a fresh human preview. Uncommitted source edits remain out of scope,
  even if the selected worktree is dirty.
- The output is a **Workbench-owned report** with both Git snapshot identities,
  the pinned Dogram HEAD, Dogram's internal graph digests and exact structural
  delta. The report is saved in `state_dir/dogram-impact/<sha256>.json`; its
  stored content digest is verified when reopened. The Workbench operational
  journal records only the report ID and input address, not source content.
- This is NOT a public `dogram.receipt/v0`, an ALEX interpretation, a LOADOUT
  grant, a historical/causal claim, a correctness verdict, or authorization to
  merge code. No automatic trigger, background indexing, project mutation,
  publishing or network call is introduced.
- HOUSE runs a fixed Python subprocess under an isolated interpreter with a
  20-second timeout, a bounded result and an explicitly discovered clean
  Dogram checkout. The user selects when to run. This is a single-user,
  loopback-only development instrument, **not a sandbox for malicious local
  Dogram code**.
- SHA-256 identities and Git blobs document source addresses and the calculation,
  not semantic truth. The selected Dogram checkout and local HOUSE process
  remain within the user's Linux-machine trust boundary.

## Verification

The Workbench suite covers guarded API requests, exact two-commit selection,
a dirty-but-excluded source worktree, moved HEAD refusal, changed/dirty Dogram
refusal, symlinked Python blob refusal, an isolated subprocess contract fixture,
persistent report retrieval and digest tamper refusal. That stub calculation
is an **integration contract fixture**, not a claim of a measured full upstream
Dogram run. A real-machine end-to-end check with the actual Dogram checkout
remains required before claiming field deployment.

## Next seams

After a real Linux witness: expose pinned explicit baseline/candidate selections,
add a testable interruption/reconciliation protocol for any effectful project
adapter, and reuse the same reviewed snapshot/receipt boundary for the already
developed Toaster paired-render research. Those are separate permissions and
not granted by this read-only first instrument.
