# GHoT IDLE OPERATOR 001

Status: integration candidate

GHoT — the **Giant Heap of Things** — is the first game-shaped control shell for Static Workbench.

It is not a game layered over a hidden operator console. The game board is a bounded projection of the operator state already present in Workbench.

## Core law

> **THE GAME STATE MUST NEVER CLAIM MORE THAN THE REAL STATE CAN PROVE.**

Frozen companion laws:

```text
GAME STATE != CLAIMED REALITY
QUEST READY != AUTHORIZED
XP == WITNESS COUNT, NOT CAPABILITY
OBSERVATION != EXECUTION
HUMAN GATE != AGENT DECISION
```

## Vocabulary

| RPG surface | Workbench meaning |
| --- | --- |
| world / biome | bounded local context |
| party member | available operator role / organ |
| quest | a real Workbench door or explicitly held experiment |
| witness XP | number of locally recorded Workbench journal events in the bounded projection |
| resources | literal observed counts, never invented currency |
| loot | future durable artifacts or receipts; no loot is claimed in this slice |
| boss gate | explicit human authority boundary |
| idle tick | refresh observational projections only |
| foreign kingdom | external system with no implied authority |

Witness XP deliberately does **not** mean competence, truth, importance, model confidence, or authorization.

## First quest board

GHoT projects existing Workbench surfaces as quests:

- **Inventory the Body** → House;
- **Survey the Branch Wilds** → Branch Deck;
- **Craft from Attributable Sources** → Creator Desk;
- **Crossings at the Threshold** → Road Desk;
- **Leave a Checkpoint** → Return Desk;
- **The Public Door** → Staged Rocket;
- **STATICJACK-001 · Polsia in a Jar** → visibly HELD because no Polsia credentials or authority are wired.

The first six buttons route to actual existing Workbench surfaces. They do not reimplement or bypass those surfaces' authority checks.

## Idle tick

The operator can explicitly request one idle tick.

The browser refreshes bounded local projections for:

- repositories;
- House state;
- RoadKit observation;
- GHoT state;
- witness events.

No repository command, RoadKit pull/accept/send, external API action, deployment, publication or credential use is introduced by the tick.

```text
IDLE != UNBOUNDED AUTONOMY
REFRESH != EXECUTION
```

The observation itself may create ordinary Workbench journal records because existing House/repository/Road views already journal their scans.

## Polsia boundary

Polsia currently exists only as a foreign-system specimen quest.

```text
CONCEIVED QUEST != CONNECTED SYSTEM
FOREIGN SYSTEM != AUTHORIZED ORGAN
HELD != FAILED
```

A future STATICJACK crossing must separately define credentials, budget, data exposure, requested effect, stop conditions and receipts before this quest can become executable.

## Why this is a control shell

The GHoT board does not create alternate effectful implementations. It routes into the existing desks that already own the relevant work and gates.

That gives the game projection a stable rule:

> **Playing correctly means operating the existing system correctly.**

## Claims not made

This slice does not prove:

- autonomous project execution;
- scheduled background execution;
- Polsia integration;
- verified capability scoring;
- financial-resource accounting;
- external credential safety;
- booted STATIC OS operation;
- physical two-House operation.

Those remain separate empirical gates.
