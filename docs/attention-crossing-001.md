# ATTENTION-CROSSING-001: Human Value Layer

Experimental Workbench-owned, local-only contextual buttons. Joyful, Useful and
Curiouser are independent voluntary declarations, **not** universal quality
ratings, social counts or measurements of the person's worth. A button toggles
its own dimension. None is explicit and distinct from untouched/unmarked.
Turning off the last active dimension creates an unmarked revision.

Existing identified contexts: HOUSE organ cards, repository detail, inspected
objects, HumanTerminal cuts and Creator Desk source hits. Each button group is
attached to one declared local target kind/id. Future Workbench-owned modules
may use data-attention-kind and data-attention-id on a non-interactive container
or call window.HumanValueBar.mount(node, {kind, id}). This is not arbitrary
DOM identification or a cross-origin browser-app extension.

The dedicated state_dir/attention.sqlite3 stores timestamp, target identity,
dimensions, explicit-none and predecessor id. No artifact bodies are copied.
The latest record projects the current declaration; prior records remain.
POST /api/attention is session-token and same-origin gated and requires
expected_previous_id to prevent stale overwrites. GET /api/attention accepts
kind, target_id and optional limit. No remote sync, public feed, behavioral
inference, scoring, automatic recommendation or project execution is wired.

A local target identifier does not establish project-native source identity.
A human declaration does not establish evidence, consensus, truth or an
authorization to execute anything. Source != interpretation != recognition !=
authority.

Verification: run python -m pytest -q tests/test_attention.py and
node --check static_workbench/web/attention.js. Full Linux browser/keyboard
and workstation-restart smoke remains to be run before promotion.
