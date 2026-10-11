# STACK² 025 — Native Verification Porter

**Draft, local-first, additive to STACK² 024.** The browser can now receive a
**bounded host-native verification result** while every private original
processing report, signed crossing, transport bundle, receiver journal and key
remains outside the browser. The host does **not** execute native code on an
HTTP request: an operator must explicitly run the CLI first.

## Two distinct boundaries

1. **Operator's terminal:** `python -m static_workbench.receipt_porter`
   invokes **only** the actual CANNON STACK² 023 `verify` command from
   original exact-pinned CANNON source commit
   `2fab6e142f21f6213bbcf4e290030acfce756061`.
   The original CANNON script rechecks the pinned GHoT
   `6194d91ba83bad63606f6f6741723007227518f2` and original reLATTE R14
   `dcc8cdca84c440aa4294134f020fb7095bf87f24` source and durable evidence.
   This is the original **cold verification** path, *not* a donor rerun,
   fresh crossing, or new signature. Exact original CANNON source files are
   checked against pinned local Git blob bytes before invoking Node.
2. **Browser:** `GET /receipt-verification` serves a new static room and
   an explicit read-only button requests only the loopback
   `GET /api/receipt-verification/latest` summary.
   No browser-selected file paths, shell strings, signer material, input text,
   model output or durable receiver artifacts enter the HTTP handler.
   The host endpoint does not provide a POST, execution action or workflow scheduler.
   `GET` is withheld for non-loopback Workbench bindings.

## Operator command

Install Static Workbench in the local Python environment, and use Node 24,
Python 3.11+, and original local source checkouts at the precise pins above.
The existing STACK² 023 experiment must already have produced an immutable
private `ghot-report.json` and private crossing output directory; its
original R14 npm dependencies must be installed.

```sh
python3 -m static_workbench.receipt_porter \
  --cannon-root /absolute/private/checkouts/CANNON-023 \
  --ghot-root /absolute/private/checkouts/GHoT-AI-001 \
  --relatte-root /absolute/private/checkouts/reLATTE-R14 \
  --original-report /absolute/private/evidence/ghot-report.json \
  --crossing-output /absolute/private/evidence/stack2-023 \
  --state-dir ~/.local/state/static-workbench
```

`--state-dir` must equal the `state_dir` of the local Static Workbench
server configuration. The private `ghot-report.json`, R14 receiver keys
and the full crossing output directory must **never** be uploaded to the
Workbench UI or committed to Git. Protect both the source and Workbench
state directories using OS file permissions. The CLI writes an atomically
replaced mode-0600 `receipt-porter/latest.json` inside a mode-0700
`receipt-porter/` directory.

That summary contains only: pinned source commits, verification time, exact
redacted public witness SHA-256 and canonical SHA-256, native report ID,
crossing ID, independently signed RECEIVED and R3_HOLD receipt IDs, checked
contract names, and explicit negative human-identity / ACT / ADMIT claims.

## Using the browser

Launch local Static Workbench and visit **`/receipt-verification`** from
the navigation or old Receipt Floor. Click "Read local verification status".
The server reads its one fixed, bounded, validated `latest.json`.
Select the matching *redacted* `public-inspection.json` from the original
native STACK² 023 output and click "Compare with native verification".
The browser independently computes the local file's SHA-256 and its
canonical JSON SHA-256, checks reported receipt identities, and refuses any
differing content.

This does not make the browser a cryptographic reLATTE verifier.
The message means **the user-provided bytes are the same bytes that the
operator-invoked host verifier recorded during its most recent verification**.
The summary itself is locally generated and **unsigned**; anyone who can
write the host's state or control its runtime can falsify it. There is no
independent anti-rollback anchor or remote signer identity certificate.

## CI proof

Dedicated two-stage GitHub Actions workflow:
- native Python and Node strict field, redaction, symlink, host and
  authority promotion tests; historic STACK² 024 regression;
- checkouts of exact original GHoT, CANNON and reLATTE;
- **real original GHoT deterministic native processing** and signed
  Instrument Rack packet (not an actual GGUF model in hosted CI);
- real original CANNON STACK² 023 R14 crossing to independent
  RECEIVED/R3_HOLD with original durable receiver journal;
- subsequent *separate* invocation of Workbench's porter to reverify
  the existing private evidence and issue a bounded new local Workbench
  summary, without rerunning donor work;
- only the safe bounded summary is exported as a CI artifact.
  Full originals never leave the CI sandbox as artifacts.

## Non-collapses

- `NATIVE VERIFICATION != ORIGINAL EXECUTION`
- `GHoT SIGNATURE != RELATTE RECEIVER SIGNATURE`
- `RECEIVED != R3_HOLD != ADMIT`
- `HOST SUMMARY != CRYPTOGRAPHICALLY SIGNED ATTESTATION`
- `P-256 SIGNATURE != HUMAN OWNER AUTHORITY`
- `PUBLIC FILE MATCH != PROOF OF CORRECT MODEL INTERPRETATION`
- `BROWSER READ != LOCAL NATIVE COMMAND`
- `VERIFIED AT TIME T != CURRENT RECEIVER STATE`

No source repo changes outside Static Workbench are made. Branch STACK² 025
builds from the still-unmerged STACK² 024 and STACK² 019 branches.

**Possible STACK² 026:** Explicitly owner-approved receipt export from the
local host into a portable *publicly verifiable* signed certificate, with a
separately selected trust anchor, expiry, and bounded verifier keys. Do not
treat this current unsigned local summary as such a certificate.
