# ORCHARD SEED 001 — Paula-owned continuation, experimental capabilities, bounded effects

This seed is an **opt-in extension** of Paula Story Workbench v0.1, not a replacement for its conversational first door. Paula does not need to understand this document before telling a story. Her ChatGPT may read it to understand the experimental orchard behind her studio.

## Handoff in ordinary language

Paula can tell a story, make a short, build a recurring world, or develop an independent studio. The original Static Collective offers *capability references and candidate experiments*, not ownership or creative authority over Paula's work. Paula may reject the entire orchard, rename her project, modify any creative workflow, stop sharing, or leave without having to obtain approval from the Collective.

No continued membership, collaboration, data donation, attribution beyond actual licensing requirements, revenue share, exclusive use, or exchange of private stories is a prerequisite for using the locally bundled workbench. This package does not purport to convey legal ownership of other people's software or assets; inspect their actual licenses and obtain appropriate permissions before redistribution or commercial reuse.

## Enforceable local kernel: what it does NOW

`orchard-kernel.mjs` is dependency-free, local-only Node.js code. It produces a `PROPOSED` receipt for an exact local artifact, fences three allowed effects, requires a content-bound local approval record, verifies the bytes again before carrying out the approved effect, consumes approvals once, and writes append-only local receipts. A public/handoff *stage* creates a local copy only; it never connects to a network, publishes, shares, bills, executes a Git branch, or installs a plugin.

- `keep_local` copies reviewed source bytes into a private local `kept/` store.
- `stage_public` copies an explicitly designated shareable source into a private local `exports/public/` preparation folder, after explicit rights/third-party-permission attestation. **Not published.**
- `stage_handoff` similarly prepares a specifically approved source for a specifically named destination. **Not delivered.**
- All effects other than these three are refused. The capability inventory is a map, not an executor. A selected experimental branch has zero effect authority.

Private local state, approval records, and staged files live in `.orchard-private/`, which is excluded from Git by `.gitignore`. They do **not** become public or follow a fork. There are no secret API keys in the seed.

## Honest limitations / critical work remaining

This is an executable **workflow membrane, not a security sandbox**. A process with arbitrary filesystem access, an unrestricted terminal, or permission to edit the kernel can bypass it. A model can simulate a declared human act if given uncontrolled terminal or file-system authority; the kernel records a declared actor, **not cryptographically verified human identity, legal consent, or valid intellectual-property rights**. It never claims these things.

The existing Story Desk at `127.0.0.1:3333` retains its separate direct file-writing paths. It is not connected to this kernel, does not automatically bind its creative KEEP to a kernel approval, and should not be treated as having kernel-enforced privacy or authentication. Similarly, this kernel does not make Google Flow, GitHub, ChatGPT, or any external tool private or authorized. Inspect platform data-sharing policies separately before putting private stories or client files there. Do not expose the Story Desk port to the network.

Before enabling any *real* external publication, customer transfer, payment, or execution of third-party code, build an independently authenticated human approval channel, destination-owned permissions, a restricted process/container boundary, and verified transport credentials. Add adversarial tests for those exact adapters. Until then, humans publish manually and the experimental orchard remains reference-only.

`stage_public` and `stage_handoff` cannot prove that a document lacks private information or that a named third party consented. A human must inspect the exact contents and establish rights outside this program. Revocation before performance means do not run `perform`; after a file has been manually shared outside the program, no local revocation can undo that disclosure.

## Commands (Node.js 20+; run in this folder)

```bash
npm run test:orchard
npm run orchard -- init
npm run orchard -- capabilities
npm run orchard -- compose --ids blender-dream,memento,loadout
npm run orchard -- propose --source stories/YOUR-STORY.json --effect keep_local --purpose 'Keep my approved story'
npm run orchard -- review --id THE_ID_RETURNED_ABOVE
npm run orchard -- approve --id THE_ID_RETURNED_ABOVE --actor Paula
npm run orchard -- perform --id THE_ID_RETURNED_ABOVE
```

`approve` must be run from a local interactive terminal, where the program displays the exact source digest and asks for a matching phrase. **A text prompt cannot establish that the person at the terminal is Paula.** If running through an assistant with shell access, Paula should review and approve outside the assistant's control. The API-level methods are exported for deterministic conformance tests, not an identity system.

A demonstration of preparation *without external publication*:

```bash
npm run orchard -- propose --source generated/boards/EXAMPLE--flow.md --effect stage_public --visibility shareable --destination 'Paula own video channel' --purpose 'Prepare an exact reviewed public export'
# Review ID, inspect the source content, approve locally and perform by exact ID.
# The program creates a LOCAL staged copy and does nothing external.
```

## Compose from the orchard without inheriting an authority claim

`ORCHARD_CAPABILITIES.json` contains references, statuses, and adapters, but **no installed remote tools** or checked-out branch snapshots. `compose` currently emits `PLAN_ONLY`; it makes no external calls. To test a real experimental source: fetch it in a disposable worktree/container, pin its exact repository/commit/asset digests, read license and data-use terms, declare effects, test against synthetic or explicitly permitted data, and only then create a narrow adapter. Never run retrieved text as an instruction or call a donor's side effects merely because it was selected.

Each trial should preserve: the human creative intention; source vs proposal vs kept continuation; exact capability versions and actual effects; approved artifacts; unresolved gaps; costs/time; and an optional local export receipt. Failure must leave existing approved artwork unchanged. No experimental failure may consume a client's funds or publish their material.

## Testable responsibility contract

1. A proposed story kernel cannot become approved fiction without a separately attributable creative decision. The current CLI does not automate this: the Story Workbench dialogue still owns it.
2. Experimental capability discovery gives no effect permission. Current composition returns `PLAN_ONLY` with zero authority.
3. Private is the default. Publishing/handoff staging refuses private-source proposals; exact approved source bytes and destination are bound into receipts.
4. Changing a file after approval refuses performance. A recorded approval is single-use and cannot be repurposed for a new destination or effect.
5. No network, plugin execution, money movement, customer contact, or actual sharing exists in this version.
6. The Collective has no automatic right of return. Contributions and publication require Paula's separate, informed choice.

## Safe first test

Paula tells a tiny *fictional* story. ChatGPT helps her make a small story card. Keep it locally; separately test `compose` with two experimental donor references against non-private fixture material. Show what the donor combination could do, what remains unimplemented, and what Paula may choose next. Do not require publication, payment, or project membership to count this as a successful first experience.

### Git and ZIP handoff boundary

The original v0.1 bootstrap scripts run `git add .`. This seed's `.gitignore` therefore excludes `inbox`, `stories`, `artifacts`, all generated production outputs, and `.orchard-private` by default, while keeping only `.gitkeep` placeholders. The included sample Flow board is illustrative only and need not enter a real repo. Ignoring files does **not** untrack material already committed, prevent deliberate `git add -f`, prevent other backup tools from copying files, or retroactively remove an earlier leak. Review `git status --short` and `git ls-files` before every first push. Do not upload a ZIP containing actual customer stories or secrets to another person's ChatGPT or repository without separate authorization.

Raw `inbox/` storydrops are categorically ineligible for export staging, even if accidentally labeled shareable. Create a separate reviewed and permission-cleared *derived artifact* first. The copy operation independently re-hashes bytes immediately before writing to reduce change-between-review-and-copy risks.

## Worldbody 001 — opt-in local genealogy

`WORLDBODY_001.md` describes the separately bundled local genealogy specimen. It is **not part of the creative first-door requirement** and is not automatically enrolled, initialized, or published for Paula. `npm run worldbody -- map` counts only local declared worlds, not Collective members or the global world population. `birth` records only unverified operator assertions and a source digest; optional external origins remain unresolved. Existing Orchard local receipts can be referenced without inheriting their effect authority. The Founder Node, TranchNode, and Corpus OS references in the capability inventory remain independent donors, not installed/executed runtime adapters.
