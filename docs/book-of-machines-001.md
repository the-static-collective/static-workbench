# BOOK-OF-MACHINES-001 — Folios as dominoes

## The mechanism

The Book of Machines is an invention notebook, not a library of executable agents.

Each folio (a domino / mechanical plate) is a human-authored description pinned to one immutable MADDLOOP revision. It freezes all human-entered layers with their source ids, declared input/output classes and exact synthetic port identifiers, source revision id and source digest. A subsequent MADDLOOP overdub does not rewrite the page. Folio origin is not a project-native capability or execution permit.

The /machines Workbench door displays source-linked folios as mechanical plates. Users can arrange two to eight folios in order, repeat folios, inspect exact joins between adjacent pages and preserve an arrangement as an append-only board receipt. A composition is a domino sentence:

    page A output: Q:q_in
       -> page B input: Q:q_out

Both legs may project to Q, but the exact join is missing. A gap remains visible. The board also retains internal gaps in each folio, even when its outer ports match another folio. An arrangement cannot silently skip them.

A board with no declared port obstructions reports synthetic_route_matched. This means only that given human-entered port tokens match; it does not establish an actual capability, real-world result, safe adapter, or executable train.

## First-use path

1. Record a loop with human-authored layers at /maddloop. Give its layers explicit port identifiers when testing an exact-join hypothesis.
2. Open /machines from the Workbench navigator. Select the source loop, inspect its current revision, title a folio and write a bounded human purpose.
3. Click Inscribe folio. The book freezes the revision without modifying it.
4. Click Lay this domino on multiple folios. Read the inspected gaps.
5. Click Preserve this arrangement to save an append-only receipt, even when the arrangement has unresolved gaps. Repair by making a new explicit folio and preserving a new arrangement.

## Local ownership and boundaries

- Workbench-owned state_dir/machine_book.sqlite3 stores folios and boards. Existing MADDLOOP events and revisions stay in their own store.
- New folios require an exact source loop id and its current reviewed head revision id. If that head changed, the request refuses. The selected revision digest is independently checked against its frozen layer snapshot.
- POST routes use the existing local session-token and same-origin write guard; new pages inherit Workbench loopback host guard. There is no new project execution, media playback, autonomous expansion, token currency, agent promotion, model invocation, network integration, or silent adapter construction.
- Human descriptions are displayed with textContent, never interpreted as code or rich HTML.
- Board receipts preserve ordered full folio snapshots. Re-opening a board never recomputes its historical result from mutable contemporary state.
- This is not an independently authenticated multi-user service.

## Important unbuilt directions

- Use verifiable typed adapters, never arbitrary label matching, when turning speculative joins into demonstrable real integrations.
- Carry concrete source references and project-native receipts if real execution is later authorized and actually performed.
- A future machine that proposes new pages must present drafts for human review; it must not generate self-authorizing capabilities or alter the prior book.
- Drawings and temporal mechanisms can be added as separately versioned instruments; this first prototype uses static mechanical plates.


## GAP-WORKSHOP-001 — Choose how to build through a hole

Preserve a domino board with one or more exact obstructions. The Gap Workshop
opens a specific **recorded** obstruction, including within-folio gaps, and
offers five human-selectable non-effectful construction strategies:

- invent_adapter: specify the missing bridging mechanism;
- find_existing: look for an already documented compatible domino;
- replace_domino: propose a different incompatible page;
- branch_route: choose a different mechanical sequence;
- leave_open: retain the gap without making up a solution.

Each human choice is recorded as an immutable *design-only* plan with its own ID,
board ID, digest of the frozen source board and result, exact gap index and frozen
obstruction, strategy, title, and human notes. Plans do not revise the original
board, synthesize new source capabilities, execute tools, or claim that a gap is
repaired. Multiple contradictory proposals for one hole may coexist.

Local routes: GET/POST /api/machines/boards/{board_id}/gap-plans.
Writes use Workbench's pre-existing same-origin and local-session guard.
The UI opens the workshop for a saved arrangement, then disables old workshop
selection when its unsaved working domino sequence is changed. The source board
and its gaps remain immutable and available for comparison.

A later verified repair would require a separate explicit new folio/board,
with an independently checked join; a plan itself is not the repair.
