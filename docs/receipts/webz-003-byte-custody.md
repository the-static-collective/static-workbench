# WEBZ-003 — Executable Material-Custody Witness

**Status:** Feature branch delivered for review, **not merged or deployed**; paired with reLATTE owner PR #63.  
**Source:** `the-static-collective/static-workbench`, PR #109, `feat/webz-003-independent-byte-custody`.  
**Verified code revision:** `c520425b563ef829a16d9813be7785c90eb711e9` (later README/spec/script-docstring-only changes retain the same functional tree).  
**Exact protocol-owner revision:** `the-static-collective/reLATTE` `743e5705c1e397c40aff82960e361d0b36eb11a5`; **owner PR #63 pending review**. This pin is used by both WEBZ-002 envelope signing and WEBZ-003 actual-byte destination delivery. Unrelated Field Reseed keeps its previous R14 owner `87006f3265103a8abe387d81597c58aeb39b0beb`.

## Independently executable evidence

**Owner protocol:** [reLATTE verify run 37572916671](https://github.com/the-static-collective/reLATTE/actions/runs/37572916671) completed successfully: `npm run verify` (TypeScript typecheck + test + build), **119 tests passed; 0 failed**. New tests use the real `LocalReceiver` signing key and prove: exact literal bytes accepted only for a previously signed crossing, receiver-local signed `PAYLOAD_BYTES_VERIFIED` receipt, binding to original RECEIVE/HOLD or RECEIVE/REFUSE IDs, immutable receipt replay, retained HOLD bytes re-read and re-hashed after cold restart, refused bytes verified but never retained, invalid bytes/foreign crossing rejected, and changed retained bytes or journal signature causing cold replay failure. The standalone receiver program reads a **bounded material carrier file** and never resolves the sender's original source path.

**Workbench:** [Actions run 37573886833](https://github.com/the-static-collective/static-workbench/actions/runs/37573886833) completed both CI jobs successfully on the verified code SHA:

- Full `python -m pytest -q`: **302 passed, 1 warning** (existing Starlette TestClient deprecation warning), including fixed first-party parcel gates, session/Origin guard, safe native `webz::` resolver, two independently declared worlds, no-carry navigation, corrupt byte/ref refusal, and a new exact-commit multiversion owner selection test.
- Native JavaScript test gate: **16 passed, 0 failed**, plus browser-controller syntax checks.
- Real reLATTE R14 signed WEBZ-002 envelope smoke remained passing: two real owner-signed crossings with RECEIVE + HOLD and RECEIVE + REFUSE, and an explicit tamper rejection.
- `python scripts/smoke_webz_custody.py` used two separately pinned clean checkout roots and a fresh temporary Workbench state. The sender signed the original exact artifact SHA-256; a distinct recipient Node process opened and verified the **actual base64 material carrier bytes** and the preexisting receiver journal, producing **receiver-key signed byte-custody receipts**. For fruit, HOLD retained the verified physical bytes in destination-local quarantine; for spore, REFUSE verified actual bytes and retained nothing. Repeated delivery from a cold Workbench returned the **same** signed custody IDs without re-signing or admitting content.
- The integration explicitly replaced the carrier bytes while leaving its original signed crossing intact: the receiver refused the mismatched digest. It then mutated a previously held destination file: the read-only Orchard custody view refused to present it as verified. Restoring source-matching bytes restored the visible local witness.
- Real headless Chromium on **desktop 1366×880** and **mobile-sized 390×844** ran the original no-carry webZ voyage, the earlier signed parcel flow, and the new **second human authorization**: Inspect existing crossing → review SHA → explicitly check consent → Deliver actual bytes → see signed receiver result. Both policies were exercised, the Orchard displayed both read-only byte receipts and public proofs, and reload preserved the results. Page load and GET alone created no transfer. Browser screenshots were uploaded in the `webz-native-001-browser-witness` artifact.

### What the signed new receipt asserts

- `relatte.receipt/v0`, `kind: PAYLOAD_BYTES_VERIFIED`, signed using the **same Orchard LocalReceiver P-256 key** as earlier RECEIVE/disposition.
- Exact SHA-256 digest and byte count observed from **the carried bytes**, not a claimed sender filename, path or metadata string.
- Bindings to the earlier signed crossing ID, receiver-local RECEIVE ID, and independent HOLD/REFUSE disposition ID.
- HOLD: verified bytes retained under receiver-owned local quarantine and revalidated on cold replay. REFUSE: bytes verified and **not retained**. Neither is local admission.

### Explicit non-claims

The source carrier file and recipient process operate on the **same GitHub Actions test-runner filesystem**, though receiver bytes are independently obtained and verified by a **different executable**, with a separately owned receiver journal and signer. This is **not** a two-machine, authenticated remote-network, independent operating-system account, peer-to-peer protocol, or fully federated trust proof. A public key proves continuity of the fixture signer, **not a human identity or legal world owner**. No personal image, uploaded file, third-party artifact, STORYSHIP canonical event, SupaBardo crossing, COM⁵ transformation or content admission was involved.

### Reproduction

```bash
# Two independently pinned, clean reLATTE clones:
# .compat/reLATTE — 87006f... legacy field-reseed owner
# .compat/custody/reLATTE — 743e57... custody-compatible webZ owner
python -m pytest -q
node --test tests/webz-*.test.mjs
python scripts/smoke_webz_relatte.py
python scripts/smoke_webz_custody.py
python scripts/smoke_webz_custody_browser.py --out browser-artifacts
```

**Human review gate:** Both reLATTE #63 and Workbench #109 are separate PRs; neither is merged or installed merely because this executable witness passed. The upstream exact pin should be updated to the reviewed merged commit before treating the code as release-pinned. No independent reviewer subagent was available; these results represent actual CI tests and documented author review, not third-party security certification.

> **Reference ≠ bytes. Receipt ≠ admission. The receiving world independently sees what arrived.**
