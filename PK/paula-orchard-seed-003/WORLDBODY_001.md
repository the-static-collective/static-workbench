# WORLDBODY 001 — A local, non-sovereign genealogical specimen

**Purpose:** show how a seed may become an independently continued world without treating a repo fork, creative similarity, model interpretation, or a recorded claim as verified membership or transferred authority.

This is an *additive, opt-in experimental organ* behind the ordinary Paula Story Workbench. Do not interrupt Paula's first creative conversation with registration forms. Do not register her as a world, Collective member, or legal actor merely because this ZIP has been uploaded or opened. A world is declared in the local registry only after the human using that copy chooses to make a declaration.

## Three donor organs, three separate jobs

- **Founder Node** (`https://github.com/the-static-collective/founder-node`): project orientation and evidenced nearby doors. Its current Pollen Scout is a reviewable discovery surface, not a world-birth authority or auto-dispatcher.
- **TranchNode** (`https://github.com/the-static-collective/tranchnode`): preserved particulars, ancestry, revisions, unresolved contradiction, and witnessed continuity. Its present Continuity Spine evaluates transitions; it does not execute them.
- **Corpus OS** (`https://github.com/the-static-collective/corpus-os`): distinct authority, bounded consequential execution, causal reconciliation, and constituted-world projection. Its present warranted execution is local/in-process and does not authenticate a remote person or create network-wide authority.

**This version imports no donor runtime and makes no cross-repo authority claim.** It implements a tiny *local observation/projection* inspired by those contracts, then points to a later explicit adapter experiment. Source repositories remain their own owners.

## Worlds, not just projects or accounts

A declared world gets an independent randomly generated local URI, exact SHA-256 of one locally readable seed, a human-supplied operator label, zero or more *previously registered local* parent-world IDs, and optionally a plainly unresolved external-origin reference. The local birth record says `membership: not_established`, `identity_verified: false`, `authority: none`. A child is not a rewrite or an owner of its parent. A new version is not automatically a new world. A film scene inside a studio and a human-owned creative environment should not be conflated.

Additional edges can be asserted only as typed, evidenced **local claims**, including inspiration, collaboration, capability-sharing and offered/reported seed handoffs. They do **not** prove independent counterpart acceptance, transfer licenses, spend a warrant, give a child access to a parent's resources, or enlarge either world's reach. Unregistered foreign origins remain unresolved labels rather than invented local world entries. The first birth registry cannot establish a global census.

## What is executable today

`worldbody-kernel.mjs` uses Node.js built-ins only. The append-only-by-API JSON event chain is stored under `.orchard-private/worldbody/events/`, already Git-ignored. Each numbered event binds its previous digest, and projection refuses missing, reordered or altered event records. Births may refer only to already-declared local parents, eliminating ancestry cycles in this local floor. Relation records cannot invent endpoints or new effect authority.

`receipt` can reference one *already completed local* Orchard kernel receipt after checking its supported status and present local output hash. This establishes only that a matching local receipt file and output were available at inspection time. It is **not** a publish event, delivery, customer acceptance, payment, verified real-world act, valid contract, or legal conclusion. No remote calls or source-repo mutations occur. Receipts and approval labels from the prior Orchard kernel do not independently authenticate Paula.

The projection counts **local declarations** and **local receipt references** and shows unresolved external-origin count. `global_world_count` is always `null`. It never computes a human membership count, scores people, establishes responsibility for another actor's actions, or claims that any registered world still exists outside the local record.

## Local commands

Run from the folder containing `worldbody-kernel.mjs`, after a human chooses to begin a local record:

```bash
npm run test:worldbody
npm run worldbody -- init
npm run worldbody -- map
# Illustrative syntax ONLY: choose a local seed and name yourself, do not auto-register Paula.
npm run worldbody -- birth --label 'My own story orchard' --operator 'self-declared owner label' --seed ORCHARD_SEED_001.md --external-origin 'Static Collective Orchard Seed 001; independent acceptance not verified here'
npm run worldbody -- verify
```

Copy the `world_id` from `birth` if you want to create a new local world descended from an already registered local parent:

```bash
npm run worldbody -- birth --label 'Independent new world' --operator 'self-declared second operator' --seed ORCHARD_SEED_001.md --parents 'worldbody://local/EXACT-PARENT-ID'
```

To record a *local claim* about two distinct registered worlds:

```bash
npm run worldbody -- relation --from 'worldbody://local/SOURCE-ID' --to 'worldbody://local/TARGET-ID' --type inspired_by --evidence 'specific-local-evidence-reference'
```

To reference an existing completed local Orchard receipt without executing it again:

```bash
npm run worldbody -- receipt --world 'worldbody://local/WORLD-ID' --id 'EXACT-ORCHARD-RECEIPT-ID'
```

Allowed relation types: `inspired_by`, `collaborated_with`, `capability_from`, `seed_offered_to`, `seed_reportedly_received_from`. These are typed **assertions** and cannot alone prove assent, authorship, permission, causal impact, or biological/familial relations.

## Truthful countability and accountability

- **Countable:** count what this one verified local ledger actually records. Missing remote worlds cannot be counted as zero; a reimport of the same world into another device is not globally deduplicated.
- **Traceable:** a known birth records a content digest and exact local parent IDs. External ancestry without matching independently authenticated provenance remains visibly unresolved.
- **Mappable:** typed relation edges can be rendered without treating similarity as genealogy or collaboration as ownership.
- **Accountable:** attach consequence evidence only after the relevant operation; preserve attempt/refusal/failure/completion distinctions in future Corpus OS adapters. Here, only *local Orchard completed/staged* receipts can be referenced. A recorded label never establishes legal identity, permission, or moral culpability.

The hash chain detects accidental or naive editing of the current directory, **not an attacker who can rewrite the entire directory, recompute hashes, or replace the program**. No authenticated multi-party signatures, cross-device consensus, verifiable global identity, durable legal/financial accounting, privacy-preserving public export, deletion/redaction policy, or distributed anti-Sybil census exists. Keep this file and local log off public repos; do not store customer stories, legal names, private addresses, or other unnecessary personal information in event labels. No local append-only ledger can guarantee erasure of copies already exported.

## Next falsifiable cross-repo experiment

Take one **synthetic** Collective-origin seed and one **synthetic** independent recipient. Compare a recorded offered handoff with a separately authenticated recipient acceptance; do not equate either with the other. Pin exact donor commits, verify provenance and licenses, pass the handoff through Project 0/TranchNode continuity testimony, and ask destination-owned Corpus OS to admit a single bounded capability under a genuinely issued one-use warrant. Feed the resulting terminal receipt to a Founder Node-derived read-only map; prove that search relevance, ancestry, and receipt possession cannot mint authority. Then test refusal, source loss, rescinded future permission, duplicated import, conflicting witness, replay, and successor handoff. Leave every unproved crossing as a named gap.
