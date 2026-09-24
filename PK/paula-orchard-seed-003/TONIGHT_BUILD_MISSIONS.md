# Credit-burning missions — bounded build prompts

Use one mission at a time in a builder such as AI Studio with **the extracted Orchard Seed 002 package and the new tonight files**. These are standalone directions, not assertions that the builder has already implemented them. Verify the changed files and tests before attempting the next mission. All new artifacts are experimental until tested with Paula's actual workflow. Do not upload her private/customer material as a build fixture.

## MISSION A — First-door UX (first choice if she gets stuck)

Paste this prompt into your coding environment after attaching/opening the repository:

> You are modifying an EXISTING app, Paula Story Workbench. Read README.md, GIVE_THIS_TO_CHATGPT.md, CHATGPT_PROJECT_INSTRUCTIONS.md, app/server.mjs, app/index.html, existing scripts and tests before editing. Your goal is a mobile-friendly, human-first start screen that allows a creative person to begin immediately from a messy idea and choose a direction without seeing implementation jargon. Preserve the existing storydrop -> 1–3 kernels -> human KEEP/HOLD -> storyboard -> Flow prompt batch functionality and data formats. Make no speculative integration claims. Do not expose experimental systems as required onboarding. Provide obvious text instructions to work via ChatGPT alone if the local app is unavailable. Treat raw input and saved cards as private by default; inspect existing file writes, routes, and .gitignore before any storage changes. No recording, cloud upload, auto-publishing, API key entry, or external network action. Implement a bounded diff, update the relevant first-use docs, add tests for any changed server behavior, run the existing check/test commands, and leave an exact file-by-file receipt plus remaining limitations.

**Acceptance:** An unbriefed person can find the first creative action in one glance, submit a thought through the existing route, and recover their approved continuation without new setup or unauthorized data sharing.

## MISSION B — Orchard selector (only after she asks for something the basic flow cannot do)

> Read TONIGHT_START_HERE.md, ORCHARD_CAPABILITIES.json, ORCHARD_SEED_001.md, WORLDBODY_001.md, ORCHARD_WORLD_BODY_SEEDS_003.md, and the existing app/tests. Build an OPTIONAL "What could help me make this?" experimental bench. It must list the actual available capability descriptors and distinguish current local operations, possible external tools, and unbuilt research frontiers. A user selects a desired creative outcome first. The bench may present 1–3 compatible route candidates and a plain-English explanation of dependencies, limits and fallback; it must not imply that unconnected repositories are installed, automatically execute code from GitHub, grant permissions, record membership, invent results, or auto-adopt story canon. Keep proposal != selection != execution != human creative KEEP. Test no-selection behavior, unavailable-provider behavior, privacy-preserving failure, and a one-tool simpler fallback. No mutation of donor repositories. Report any proposed new adapter separately from implemented behavior.

**Acceptance:** A real creative request reveals a bounded candidate composition while the original ChatGPT + creative-tool path remains fully usable.

## MISSION C — One finished artifact and an actual studio ledger (only when she wants to sell)

> Starting from the existing private creative workflow, add an OPTIONAL, compact production card: approved title, current version, chosen deliverable, actual minutes spent, actual tool cost/credits, asset filenames, sharing status, one next action, and an optional offered price explicitly marked experimental. Separate free community/gift work from customer commissions and commercial offers. Never infer permission to reuse an identifiable person's likeness, voice, story or paid work. No Stripe, payments, CRM, automatic customer outreach, automatic publication, or public metrics. Store private material outside routine Git staging, and include an export format Paula can carry to her own workspace. Write tests for privacy boundaries and export. Preserve the current Story Desk experience and report any unimplemented income features honestly.

**Acceptance:** Paula has one artifact she can return to and an inspectable actual production cost, whether or not she chooses to sell it.

## Credit allocation principle

First make **one actual creative output** before spending all available credits on software. Next spend build credits on the strongest observed friction. If there is no friction, explore one small experimental adapter under a separate clearly labeled boundary and retain a working fallback. Stop building when an experimental change interrupts the creative task.
