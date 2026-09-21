# STATIC-ARG-001 — The First Door

Status: **playable, experimental, Workbench-owned local slice**. This is not a claim that the
multi-project ARG, Full Measure shared world, or physical trading-card network is connected.

## Play

Run ordinary Workbench and open **STATIC ARG · First Door** in its navigator
(or visit `http://127.0.0.1:13700/arg`). Choose **Enter the House** to opt into
a persistent, single-local-user game shelf. Normal Workbench stays usable without opting in.

1. Make three original, human-entered **Seeds**. Each is an immutable local text artifact.
2. Compose two *distinct* Seeds into a **Machine**. It freezes each exact input ID and
   SHA-256 and stores a deterministic paired creative prompt. It does not execute the prompt.
3. Combine that Machine with a *third, unused* Seed, name a **World**, and declare one
   playable fictional rule. This freezes both input identities/digests.
4. On a World choose a fixed, local door: House, MADDLOOP, or Book of Machines.
   The user-initiated crossing appends an encounter entry, then navigates to the normal
   destination. This is navigation only, not admission to another project's runtime.
5. Return to `/arg` after restarting Workbench. The original Seeds, Machine, World,
   exact digests, and crossing records remain in `state_dir/static_arg.sqlite3`.

This first slice gives a person a complete seed → machine → world → door → return
loop. It does *not* turn a MADDLOOP composition into a real effectful machine, import
actual music or video, generate an autonomous world, or claim another project observed
the crossing. The creative content is typed by the human; a future reviewed adapter
may explicitly carry external project references and verified receipts.

## Contract

- **Opt-in only:** the page and state-read do not enroll or write game progress. An
  explicit guarded `POST /api/arg/enter` enables this local game shelf.
- **Local only:** uses Workbench's existing loopback Host boundary and same-origin
  session-token write guard. There is no multi-user authentication or remote account.
- **Append only:** no update/delete APIs; artifacts and crossings receive unique IDs.
  Inputs are frozen by exact IDs and content hashes and never consumed or overwritten.
- **No silent authority:** a game artifact is neither a project-native receipt nor proof
  of real execution, human worth, spiritual standing, or empirical truth. Game worlds
  cannot award Full Measure Deeds or Jubilee Harvests.
- **No source ingestion:** user-entered Seed text does not read repositories, execute
  project code, contact a model, import private notes, or publish elsewhere. Arbitrary
  HTML entered by players is displayed using `textContent`, not interpreted.
- **Fixed door destinations:** only `/`, `/maddloop`, and `/machines`; never a
  user-supplied arbitrary URL, shell command, or access token.
- **No automatic progression:** creating a Seed does not perform another action until
  the human explicitly chooses to compose or cross.

All game state remains on the user's local machine. Existing Workbench operational
journal entries reference only new artifact/encounter IDs; the full creative payload
remains confined to the ARG shelf.

## Test it

```bash
python -m pytest -q tests/test_first_door.py
node --check static_workbench/web/arg.js
```

The tests cover explicit enrollment, source IDs/digests, distinct/fresh input gates,
fixed destinations, bad origin/session refusal, local persistence after restart, and
an existing destination page.

## Next measured frontier

Let an explicitly selected Creator Desk source pack or immutable MADDLOOP folio be
*reviewed and imported by reference* into a Seed, with the input snapshot and
destination admission independently validated. Only after that should an opt-in
adapter connect a Full Measure quest to a local ARG object. The player should
always be able to use every underlying Workbench tool without game progression.
