# HOUSE Return Desk v0.1 — write / carry / return

**Status:** experimental, HOUSE-owned local working surface. It is not yet
GOATnote interoperability, an ALEX identity claim, a 3rdi observation, a
LOADOUT/TranchNode receipt, or a project-native event.

## First local loop

1. Open **Return Desk** in the HOUSE navigator.
2. Save a note with a title and RAW writing. Margin/context and identity carry
   are stored in distinct fields. The saved RAW and its first margin/carry are
   immutable; preserve later interpretation in a new note or session checkpoint.
3. Select that note and explicitly open a work session with an intention, a
   human-declared project label (optional), a next physical action, and what is
   unresolved. The selected note SHA-256 must match the saved original.
4. Work elsewhere. Return to the session and append a checkpoint describing
   what changed, the next action, and what remains unresolved. The previous
   checkpoint is never overwritten; stale revisions are refused with HTTP 409.
5. Restart the browser or supervisor and reopen Return Desk. The newest saved
   session is displayed, with the original note and complete checkpoint chain.
   A user can select any of the 100 most recent listed sessions or notes.
   Older records remain in SQLite, retrievable by exact known ID via the API.

The digest covers local field content / checkpoint linkage; it is **not**
independent proof that a proposed action occurred or a project changed.
The session project string is a human-entered label, not a discovered Git
identity. No checkouts or third-party apps are written or launched.

## Storage and security

Data stays on the same machine at
\`state_dir/return.sqlite3\`; include this file and
\`state_dir/creator.sqlite3\`, \`state_dir/workbench.sqlite3\` in a
private, tested backup plan. SQLite persistence alone is not a backup.

The same loopback Host, Origin, and per-supervisor-session token guards used
for HOUSE Creator writes protect Return Desk writes. This is a local
single-user desk, not a multi-user login or remotely authenticated service.
Other processes with filesystem access to the state directory may read the
plain-text notes. Do not expose the supervisor on a network.

## Boundaries and future doors

- RAW != margin != identity carry != interpretation != project effect.
- A Workbench checkpoint != GOATnote persistence or protocol compatibility.
- An optional later GOATnote integration must require a deliberate,
  versioned import/export contract, explicit consent and source attribution;
  do not silently synchronize private writing.
- A session's intention or next action is not evidence that it was completed.
- A checkpoint receipt records **what the user wrote in HOUSE**. It does not
  attest to external action or award project authority.

The bounded proof for this landing is note preservation, guarded writes,
append-only revision chain, stale-editor refusal, project-root non-mutation,
and read-after-restart recovery. Real Zorin workstation smoke remains a
separate on-device check.
