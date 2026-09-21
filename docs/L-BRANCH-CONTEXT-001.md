# L BRANCH CONTEXT 001 — reference-only composition proof

Status: **experimental, proposal-only, no UI, no database, no Toaster integration.**
Parent: [human-facing Workbench #53](https://github.com/the-static-collective/static-workbench/issues/53).
Contract and next staged work: [#54](https://github.com/the-static-collective/static-workbench/issues/54).

This file and `static_workbench/context_mix.py` adapt the **routing** part of Haunted
Toaster [L BRANCH #225](https://github.com/the-static-collective/the-haunted-toaster/issues/225)
rather than confusing it with Git branches or parallel project workspaces.

The three separate questions are:

1. **Context / availability:** What attributable material could be considered?
2. **Influence Diet:** Which material was used, ignored, absent, or influence-only?
3. **Mix proposal:** Which declared source lane is routed to which declared target,
   at what scope, influence weight, detail request and response mode?

This v0 proof is *reference-only*. A source ref/hash and a permitted target are
**caller declarations**. They are NOT proof that the file exists, its bytes
match, the target is installed, or the user granted transfer permission.
The module never reads a path, fetches a repo, copies content, calls a model,
opens Toaster, writes a source, runs code from a project or publishes a result.

## Runnable fixture

```python
from static_workbench.context_mix import ContextLane, Send, propose_mix

song = ContextLane("song", "local:song:v1", "a" * 64,
                   "human-supplied", ("video", "draft"))
lyrics = ContextLane("lyrics", "local:lyrics:v3", "b" * 64,
                     "human-supplied", ("video", "draft"),
                     ("whole", "section:verse_1"))
art = ContextLane("art", "local:art:v1", "c" * 64,
                  "observed", ("video",))
bank = (song, lyrics, art)

video = propose_mix(bank, (
    Send("song", "video", weight="strong", response="follow"),
    Send("lyrics", "video", scope="section:verse_1",
         weight="light", detail="excerpt", response="contrast"),
))
writing = propose_mix(bank, (
    Send("lyrics", "draft", weight="strong", response="accent"),
))
assert video.context_sha256 == writing.context_sha256
assert video.plan_sha256 != writing.plan_sha256
assert video.ignored == ("art",)
assert writing.ignored == ("art", "song")
```

`weight`, `detail`, and `response` are *declared qualitative routing controls*
rather than computed audio/visual effects. `detail="excerpt"` is a request for
a future **reviewed** bounded excerpt, not an export of excerpt text here.
This does not implement Toaster's numeric gain, actual temporal resolution,
GRAB spatial masking, smoothing, renderer MixPlan or audio evidence lanes.

## Authority and privacy gates

- `available != consumed != authorized != executed`.
- `source_sha256` is an unverified declaration until a separate source owner
  confirms the actual bytes; `context_sha256` is a digest of the declared
  reference set, not proof of source authenticity or remote authorship.
- `plan_sha256` identifies a descriptive proposal only. No proposal can
  grant project authority, infer tastes, approve transfers, or mint a KEEP.
- The same original may be routed in multiple mutually independent proposals;
  proposal order does not change identity.
- Missing evidence remains unavailable. A declared destination or scope must
  already be listed for the source; inferred evidence remains visibly labeled.
- A candidate can ignore all available material; there is no mandatory
  automatic consumption, "best" candidate, success claim or execution verdict.

## Verification

Run `python -m pytest -q tests/test_context_mix.py`, then full
`python -m pytest -q` on the *exact* PR head. This isolated specimen does not
show that the new Home screen, carrier #48, ARK #51 or the Linux Toaster
handoff has been integrated or field-tested.

Next proof: an existing CreatorShelf source/revision must be validated by
its actual owning module before constructing this context. Proposals may then
be *previewed* in the human-facing Creator Desk after reconciling #48; any
source-byte transfer to Toaster needs a separately verified destination
contract and fresh human approval at the effect boundary.
