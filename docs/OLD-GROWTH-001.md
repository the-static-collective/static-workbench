# OLD-GROWTH-001 — bounded archaeological composition

**Status: isolated, proposal-only experiment.** Source ideas: seedFORK's
[Nearby Growth Workbench](https://github.com/the-static-collective/seedFORK/blob/main/src/components/NearbyGrowthWorkbench.tsx)
(human-selected excerpts and declared relation lanes) and
[mundaneWORMHOLE](https://github.com/the-static-collective/mundaneWORMHOLE)
(two intact parent archives, one optional proposed graft). reCURVrePAIR's
uncertainty vocabulary inspires the PROPOSED_UNRUN / LEFT_OPEN distinction.
This implementation does not copy or replace those applications or HOUSE's
existing native GRAFT draft/revision flow.

## Exact bounded slice

The pure function static_workbench.old_growth.compose(a, b, *, keep, bend,
question, relation_lane, move="fuse") is deterministic.

Each input must explicitly supply:
- a claimed owner/repo, lowercase 40-hex commit and relative source path;
- exact UTF-8 content of at most 131072 bytes and its SHA-256 digest;
- an operator-selected nonempty [start_byte, end_byte) range of up to 4096
  UTF-8 bytes, with both boundaries falling on Unicode character boundaries.

The function validates digest vs **the supplied bytes**, rejects duplicate
source locators and unknown fields, and returns only the selected excerpts,
two separately pinned source identities, human-declared relation/KEEP/BEND,
an unrun proposal, a separately preserved parallel alternative, and
deterministic packet/calculation digests.

Full unselected source text is not included in the returned packet. No
retrieval, persistence, browser route, background action, source-file write,
fork, Git ref update, Dogram invocation or downstream adapter is introduced.

The receipt is **calculated_not_persisted** checksum over this local
calculation. It is not an append-only event, remotely authenticated origin,
project-native receipt, human acceptance or execution evidence.

## Use on an explicitly supplied synthetic fixture

~~~python
import hashlib
from static_workbench.old_growth import compose

def selected(repository, content):
    raw = content.encode("utf-8")
    return {
        "repository": repository, "commit": "a" * 40,
        "path": "synthetic/fixture.txt", "content": content,
        "content_sha256": hashlib.sha256(raw).hexdigest(),
        "start_byte": 0, "end_byte": len(raw),
    }

result = compose(
    selected("the-static-collective/seedFORK", "selected fragment A"),
    selected("the-static-collective/mundaneWORMHOLE", "selected fragment B"),
    keep="Keep both source identities",
    bend="A local, inert experiment",
    question="What minimal reversible test might compare these fragments?",
    relation_lane="human_link",
)
assert result["packet"]["authority"] == "none"
assert result["receipt"]["status"] == "calculated_not_persisted"
~~~

The all-a commit in this example is a **synthetic placeholder**, not a
verified GitHub commit. A real caller must pin the actual commit and fetch
or supply its exact bytes separately; this module intentionally does not
authenticate that remote binding. Even a valid 40-hex hash alone is not
proof that a repository, source, person or permission was verified.

## Composition and next gate

A human may compare this proposed source packet with the existing
graft_round.py declarations and **separately** choose whether to make a
HOUSE-native GRAFT ride or draft. No automatic conversion/admission exists.
Native source authority and existing Workbench GRAFT identities remain
unchanged. Before any live integration: verify claimed repo/commit/path
against actual checked-out bytes, design explicit disclosure and admission,
add local persistence under Workbench's own receipt contract, reconcile
the rectified-main carrier (#48 / #23), and run project-wide tests plus
real Linux/browser/restart smoke.

Run focused checks:

~~~sh
python -m pytest -q tests/test_old_growth.py
python -m compileall -q static_workbench/old_growth.py
~~~

source similarity != source identity != permission != implementation.
