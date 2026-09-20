# HOUSE Flight Two — guarded Creator Desk effect

Status: review candidate on HOUSE rectification PR #23. This is a single-owner executable proof, not a general-purpose tool executor, Git mutation, or publishing adapter.

## Sequence

1. Declare, prepare, execute and separate a normal source-preview Staged Rocket mission. The source is a clean, exact-SHA local checkout and an explicitly selected tracked UTF-8 file.
2. Inspect the source excerpt and proposed next action. Type or edit the seed title and body. Explicitly check the consent notice and press "Authorize and save Creator seed".
3. The server validates its local Host/Origin/session guard, fixed creator.seed/v0 target and save_creator_seed authorization, exact separation receipt, exact source checkout HEAD and source byte identity, then invokes the Workbench CreatorShelf owner.
4. The Creator Desk stores one immutable native creator.rocket-seed/v0 record with source identity, excerpt, newly proposed content, SHA-256, mission and separation reference. The rocket independently records the actual effect receipt. The user can retrieve the native artifact from Staged Rocket or the /api/creator/rocket-seeds/{seed_id} route.
5. A new child mission may cite the effect receipt; it receives no automatic action authorization.

## Interruption and idempotency

The native Creator seed table uses a unique key derived from mission id and separation receipt. A same-payload retry returns the existing seed; a changed payload cannot overwrite it. The rocket effect table permits one outcome per mission.

The two owner-local SQLite databases use separate transactions. A process interruption after native insertion but before the rocket receipt can leave an orphan native seed. Reissuing the exact same authorized request returns that native seed and completes the rocket receipt without repeating the effect. Never interpret a failed HTTP response as proof that the native save did not happen.

A parent with an existing child cannot later add an effect that would retroactively change the parent receipt cited by that child.

## Claims and boundaries

This is a real local Creator Desk save, not a write to the inspected repository, not a committed patch or pull request, not an external action witness, and not an execution of Free Graph, Dogram, LOADOUT or a third-party AI service. Plain-text local data requires a private backup. The local session-token guard is not multi-user authentication. HASH != AUTHORITY; PROPOSAL != SOURCE; STORED != ADOPTED.

A future effectful project.patch/v0 adapter requires an owner-published versioned interface, a separately evaluated effect fence, precise destination authorization, clean exact source HEAD, durable attempt identity, interruption/outcome reconciliation, native receipts and hostile replay tests. It must not be smuggled through the narrower creator.seed/v0 gate.
