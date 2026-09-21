# STATIC-ARG-002 — World Entry / the inhabited sketch

Status: **experimental, opt-in, single-local-user gameplay**. A World created by STATIC-ARG-001
can now be entered as a small explorable four-location fiction without changing the original
artifact, importing real project state, creating project-native receipts, or contacting a model.

## First use

1. Open Workbench → STATIC ARG, opt in, and compose three Seeds, one Machine, and one World.
2. Under the World card choose **Enter World**.
3. Begin at **The Threshold**; inspect its inscription to rediscover your original World rule.
4. Choose the adjacent Workshop, inspect the two-Seed Machine; return to the Threshold.
5. Choose the adjacent Seed Garden and examine the fresh Seed.
6. With those three discoveries recorded, the Return Archive becomes accessible from the
   Threshold. Enter it and examine the World Chronicle.
7. Return to the House, close/restart Workbench, and enter the same World again. The prior
   room, discoveries, and latest encounters remain available on the same machine.

Each World derives its objects from its exact immutable world → machine → seed snapshot links.
The server verifies each stored content hash against the frozen ancestor reference before
projecting an object. A source mismatch refuses further play instead of silently replacing
a fictional history.

## Boundaries

- Game actions require the pre-existing loopback Host guard, local session token, same-origin
  write guard, and explicit enrollment. Reading a World does not create encounter history.
- Rooms, objects, and adjacency are fixed by this version's declared fiction. A player
  must choose Travel or Examine to create one append-only arg_world_moves entry.
- Travel validates current room, adjacent destination, and archive gate on the server,
  inside an immediate SQLite transaction. Stale room assumptions, invented doors, remote
  objects, uncreated Worlds, and non-World IDs refuse.
- Objects are shown as fictional source-linked discoveries; the original text and exact
  SHA-256 remain attributable. Re-examining creates a fresh encounter but does not inflate
  unique discovery count.
- The Archive is a *local narrative reward* for three inspections, not a project permission,
  Full Measure Deed, proof of real-world occurrence, token, or automatic publication.
- Earlier STATIC-ARG-001 artifacts and Workbench state survive unchanged. The exploration
  table is new and append-only. Multiple browsers on one local profile share one position;
  there is no multiplayer synchronization or authenticated personhood in this version.
- All user-authored content is inserted with textContent, not executed, rendered as HTML,
  posted to an external model, or embedded into project-native commands.

## Local checks

    python -m pytest -q tests/test_world_entry.py tests/test_first_door.py
    node --check static_workbench/web/arg-world.js

The normal repository CI also exercises all existing Workbench integrations. A visual
browser inspection on an actual target machine remains separate from CI's static and
route checks.

## Next frontier

Allow the player to author a bounded branch from one inspected World object, preserving
a new child artifact with exact source lineage and a separate game-local rule. Later,
explicitly reviewed adapters could connect real Creator Desk source packs, Book of Machines
folios, physical cards, and Full Measure encounters without importing their authority.
