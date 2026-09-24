# PK / Paula Story Orchard — tonight handoff (experimental)

This PK/ landing preserves the editable source of **Orchard Seed 003 — Tonight**, including the working Paula Story Workbench, Orchard/Worldbody local specimens, standalone session board, staged builder missions, and the research seed harvest. The original conversation ZIP is a transport snapshot; this directory is the durable, inspectable source landing.

## First doors

- **Paula:** [`paula-orchard-seed-003/TONIGHT_PAULA_OPEN_FIRST.md`](paula-orchard-seed-003/TONIGHT_PAULA_OPEN_FIRST.md). She begins with her own ChatGPT and her own creative idea.
- **Lu / call facilitator:** [`paula-orchard-seed-003/TONIGHT_START_HERE.md`](paula-orchard-seed-003/TONIGHT_START_HERE.md) and the standalone local [`session board`](paula-orchard-seed-003/tonight/SESSION_BOARD.html).
- **Build credits:** [`paula-orchard-seed-003/TONIGHT_BUILD_MISSIONS.md`](paula-orchard-seed-003/TONIGHT_BUILD_MISSIONS.md). Choose a bounded mission in response to observed friction.
- **Research orchard:** [`paula-orchard-seed-003/ORCHARD_WORLD_BODY_SEEDS_003.md`](paula-orchard-seed-003/ORCHARD_WORLD_BODY_SEEDS_003.md) (canon candidate, not adopted); [`TONIGHT_EXPERIMENT_RACK.md`](paula-orchard-seed-003/TONIGHT_EXPERIMENT_RACK.md) (candidate routes, not live integrations).

## Local proof

From `PK/paula-orchard-seed-003/`, run `npm run check` and `npm run test:all` using Node.js 20+. The board can be opened directly from its HTML file; it does not write to the Story Desk or auto-save. The original Story Desk has its own local start command (`npm start`).

## Boundaries

This is **a nested experimental PK/ specimen**, not a replacement for Static Workbench's shipped runtime, and it does not wire the donor Git repositories into an executable orchestration layer. Keep the main Workbench read-only against its neighboring projects. Nothing in this source directory creates a world identity, enrolls Paula, publishes a film, or authorizes a payment.

`static-workbench` is public. **Do not commit filled session boards, exported JSON, private storydrops, client assets, API keys, signed receipts, or customer information to this branch.** The bundled story card is synthetic; the shared handoff templates are blank. Private outputs must remain outside the repository. The nested `.gitignore` is an additional convenience, not a substitute for careful review before staging.

Status: experimental source landing; a future adapter or UI integration requires an independent, tested PR. Source archive SHA-256 and content inventory are in [`SOURCE_ARCHIVE_RECEIPT.json`](paula-orchard-seed-003/SOURCE_ARCHIVE_RECEIPT.json).
