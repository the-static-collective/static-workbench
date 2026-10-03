# HOUSE-REMEMBERS-DOORS-002 — reLATTE Aperture

## Earned crossing

A completed Workbench-local DoorHouse receipt may now be offered to a **real local reLATTE checkout**.

The Workbench does not construct or sign a reLATTE envelope itself. It translates its local receipt into reLATTE's generic opaque-organ input and invokes reLATTE's own `scripts/opaque-roundtrip.ts` bridge.

```text
DoorHouse local crossing receipt
        ↓
Workbench donor adapter
        ↓
relatte.opaque-organ-spec/v0
        ↓
reLATTE-owned signer
        ↓
OPAQUE_ORGAN_ARTIFACT crossing
        ↓
reLATTE file transport
        ↓
reLATTE LocalReceiver
        ↓
RECEIVED receipt
        ↓
HOLD disposition
        ↓
signed HOLD receipt
        ↓
Workbench external witness
```

## Authority split

Workbench owns the donor semantics:

- which local receipt is being offered;
- its local receipt digest;
- the local artifact digest;
- the fact that a human selected and crossed the Door;
- the requested effect.

reLATTE owns:

- the canonical crossing envelope;
- P-256 signing;
- transport frame;
- crossing verification;
- LocalReceiver history;
- RECEIVE receipt;
- receiver-local HOLD receipt.

The shared substrate never branches on DoorHouse concepts.

## Runtime requirement

The configured Workbench roots must contain a local repository named `reLATTE` with:

```text
scripts/opaque-roundtrip.ts
```

and its Node dependency installation available.

If this surface is absent or refuses the crossing, Workbench records no external witness and reports the failure. It does not synthesize a successful receipt.

## Retry law

The reLATTE request timestamps are derived deterministically from the immutable local receipt timestamp. Paths are deterministic by local receipt id.

reLATTE durably stores its round-trip result and reuses the exact signed crossing and receipts on retry.

```text
RETRY != NEW CROSSING
LOCAL RECEIPT != reLATTE RECEIPT
RECEIVED != ADMITTED
HOLD != INTERPRETATION
RETURNED RECEIPT != NEW AUTHORITY
```

## Workbench witness

Workbench stores only a bounded external witness linking:

- local receipt id + digest;
- reLATTE request id;
- crossing id;
- transport id;
- RECEIVE receipt id;
- HOLD receipt id;
- receiver world + state ref;
- semantic effect = none.

A conflicting second result for the same local receipt is refused.

## Next earned door

The next useful crossing is **GHoT body offer**:

1. keep the reLATTE crossing in HOLD;
2. discover one GHoT body and its advertised capabilities;
3. present assignment as a new human-authorized act;
4. execute one bounded artifact transform;
5. return the GHoT execution receipt beside the reLATTE HOLD witness.

The reLATTE HOLD must not silently become GHoT assignment.
