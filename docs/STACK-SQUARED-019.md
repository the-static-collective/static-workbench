# STACK² 019 — the Living Lego Floor in Static Workbench

**Experiment only.** Branch \`experiment/stack-squared-019-lego-floor\` stacks on the still-unmerged \`experiment/return-room-workbench-001\`, preserving that full native Workbench shell. This is a **genuine interactive browser instrument**, not an autonomous execution framework.

## The new room

\`GET /stack-floor\` serves \`stack-floor.html\`. Static Workbench's actual main navigator and GHoT home both link to it. No new server POST, direct arbitrary checkout/file read, command shell, public service, database, account, network API, key import, or deployment is introduced.

Five original, exact source-addressed capability cards:
- CANNON native 018 source verifier, at \`53a1b439161210c03168bb0bb3f6f178ee1da315\`;
- planZ native SENSE at \`e8111fdb64c5587b33aece0fed639ed3d03375ac\`;
- GHoT local hash worker at \`e35dd470384d864b7b0b629a68dad570875a7df0\`;
- reLATTE R14 signed HOLD carrier at \`dcc8cdca84c440aa4294134f020fb7095bf87f24\`;
- deliberately incompatible CANNON 017 fixture \`3aa5b0d0e9403e90affe05ec4056825e8d166fe4\`.

The human can **drag** a card to an unoccupied socket or **tap** to place it in the next empty slot, click × to remove it, scatter the whole floor, and inspect all exact source commit/file links. Typed compatibility is determined by four narrow **Workbench-declared recipe port labels**. It **does not verify** native donor APIs, owner licenses, or executable compatibility.

The only fully aligned recipe is **CANNON → planZ → GHoT → reLATTE**. Misordered and mixed fixture cards visibly HOLD. The earlier native execution did source verification before sense computation, and now the floor makes that distinction visible.

## Exactly one local experiment

The operator selects two **local files** originating from the independently passing CANNON 018 experiment:

1. \`public-inspection.json\` — redacted historical CANNON 018 summary.
2. \`native-planz-output.json\` — exact native planZ program output, including original local path text. **Do not assume this file is public or privacy-scrubbed; import locally only.**

The browser structurally checks the reported source record IDs, two PlanZ mutation candidates, non-authority, held disposition and report's expected fields. **Source Git objects and reLATTE signatures are *not* verified in-browser.** The CANNON 018 CI is an independently locatable historical witness, not authority to run local operations.

A human must connect all four matching sockets and explicitly check the consent statement **before** a real browser-local trial becomes enabled. The trial:

- recomputes SHA-256 over canonicalized native planZ JSON (same bounded canonical value family as CANNON 018);
- computes SHA-256 of the resulting hex digest (the original GHoT \`system.hash\` input/output relationship);
- compares it to the public CANNON 018 \`ghot_result_sha256\`;
- returns a newly addressed **unsigned browser-only inspection packet** listing exact card pins, checked and unchecked claims, and zero execution/admission effects.

No original planZ, GHoT, CANNON native verifier, or reLATTE code runs during this browser trial. The original native chain remains independently demonstrated by [CANNON 018 CI](https://github.com/the-static-collective/CANNON/actions/runs/38156936591). Files are read through user-selected File inputs only, capped at 192 KiB / 2 MiB, and not uploaded, stored, or sent by the page.

## Reproduce

With local Static Workbench installed:
\`\`\`sh
node --test tests/stack-floor-019.test.mjs
node --check static_workbench/web/stack-floor-core.mjs
node --check static_workbench/web/stack-floor-ui.mjs
python -m pytest -q tests/test_stack_floor_019.py
\`\`\`

Route smoke checks ensure the native FastAPI shell includes the real new page, both nav doors, JS and CSS assets, loopback Host guard, blocked POST, and no \`/api/stack-floor\` executor.

## Limits

- **CARD ≠ EXECUTION PERMISSION.**
- **DECLARED SOCKET ≠ VERIFIED DONOR API.**
- **IMPORT ≠ REVERIFICATION OF FOREIGN SIGNATURE.**
- **MATCHED SHA-256 ≠ AUTHENTICATED SOURCE OWNER.**
- **LOCAL BROWSER TRIAL ≠ NATIVE GHoT RUN.**
- **RECEIPT INSPECTION ≠ RE-LATTE ADMIT.**

No automatic branch discovery, native subprocess execution, Git mutation, external API polling, CANNON selection, publication, or unsigned fixture promotion. Any future native operator action requires a new, narrowly scoped Workbench executor with one-use owner-local authorization, original Git source validation, and separate destination-owned admission.

## Human witness gate before release

CI verifies source modules, cryptographic relation, hostile tampering and host routes. A real mobile pointer/drag, keyboard focus, file-picker and accessibility walkthrough is separately required before any production Workbench rollout. Do not auto-merge.
