# ATTENTION-CROSSING-002 — Ubiquitous local button, passage capture, attention shelf

This is an experimental Workbench-owned feature stacked on PR #32.

The existing independent Joyful, Useful and Curiouser marks now have a local
Attention Shelf. It shows only the latest declaration per target, in reverse
declaration chronology, and allows filtering by dimension. It is not a
popularity/quality/importance score or a public feed.

Select text inside an explicitly identified Workbench card, click
"Mark selected passage", inspect the selected text in the floating panel,
then explicitly click a value button. The selection itself does not make
a network request or save anything. Clicking a value stores the source kind
and ID, a selected-text digest and a bounded 160-character excerpt in local
Workbench SQLite. Existing records migrate additively without rewriting their
history. The same exact quote within the same source intentionally shares one
target in this version; occurrence-specific offsets require a later adapter.

Only Workbench-owned, source-identified DOM containers are eligible. No
automatic observation of other applications, browser tabs or cross-origin
frames; no text-field capture, background tracking, auto-action or publishing.
An excerpt can contain private content: make a value declaration only when
you intend to retain that excerpt on the local machine. Human value is
not objective evidence or permission to execute anything.

Verification: CI runs Python tests and JavaScript syntax. Linux browser
selection, keyboard, visual and workstation-restart smoke must be performed
before promoting the draft.
