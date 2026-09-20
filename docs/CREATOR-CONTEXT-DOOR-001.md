# CREATOR-CONTEXT-DOOR-001 — local, human-reviewed composition

Parent human interface: [#53](https://github.com/the-static-collective/static-workbench/issues/53).
L BRANCH research contract: [#54](https://github.com/the-static-collective/static-workbench/issues/54).
Standalone reference-only Python proposal kernel: [draft #55](https://github.com/the-static-collective/static-workbench/pull/55).

## First bounded human route

In the existing Creator Desk, select a *previously saved* source pack to
open its local draft editor. Above the editor, choose one or more of the
pack's saved source lines. Select either **Build from these lines** (follow)
or **Try a contrasting direction** (contrast). Review exactly which sources
were selected, how they will influence the draft, which saved sources are
ignored, and which local destination is involved. Only a separate press of
**Use this direction in my new draft** inserts the proposal into the existing
optional creative-assumptions field. The user then writes a draft and saves
it using Creator Desk's existing explicit revision-save API.

Changing the selection invalidates the preview; clicking the proposal control
a second time cannot silently save another draft. If an existing draft is
open, this path is unavailable. If the optional creative-assumptions field
already contains text, the proposal refuses to overwrite it.

## Evidence and authority

- The context comes **only from the selected historical CreatorShelf pack**,
  with its saved pack ID/digest and source file digests. Neither the browser
  nor this control re-reads the current working tree. Historical snapshots
  must not be described as current source verification.
- A simple direction is **proposed creative use**, never an inferred fact
  about the source, learned user preference, project permission, or canonical
  Toaster MixPlan.
- The proposal is in the browser until a person intentionally adds it to an
  otherwise-empty notes field; adding the notes does not save or transfer.
- The existing Creator Desk save action is the sole persistent write path,
  with its ordinary revision and session checks. No model, file-system write,
  tool execution, clipboard action, Git operation, Toaster launch, or external
  transmission is added.
- This is a **human-facing reference-routing proof**, not the Python engine in
  draft #55. Do not claim that the two kernels have already been integrated.
  Their proposal identities, validation boundaries, and UI mappings require
  an exact-head reconciliation before one may replace or compose with the other.

## Verification

- `node --check static_workbench/web/creator-context-door.js`
- `node tests/creator-context-door.cjs`
- `python -m pytest -q` and the repository's existing Dogram/Static Live
  smokes on the exact PR head.
- Manual Linux browser/keyboard/390px check: saved pack -> choose lines ->
  preview two distinct directions -> change selection invalidates preview ->
  apply to an empty new-draft notes field -> edit -> Save explicitly ->
  reopen exact saved draft. Check non-overwrite of existing notes, refusal on
  previously opened drafts, no apparent Toaster/external launch, and absence
  of success claims before actual save. This manual gate is not asserted
  complete by source tests or CI.

No main-carrier merge, Toaster receiver, current-source validation or full
Context Pantry service is implied by this optional door.
