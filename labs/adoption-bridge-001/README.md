# Orchard Bridge — Adoption Support Workbench 001

> Experimental, public-information-only capability atlas + fictional, offline human-reviewed referral simulator. No real referrals. No sensitive records. No adoption placement or legal decisions.

## Run it immediately

Open [index.html](./index.html) in a modern browser; it is self-contained, works via `file://`, and requires no build, account, network access, or dependency installation. Public source links require internet to visit. No case data is sent to a server, and demo state is not persisted; Reset starts a fresh fictional case. "Export synthetic receipt JSON" downloads the in-memory **fictional** event trail only.

To run the repeatable state-machine checks, from the repository root:

```bash
node --test labs/adoption-bridge-001/tests/referral-core.test.cjs
```

The test reads the exact `advanceCase` function from the shipped HTML; no separately implemented test double is substituted. Requires Node 20+.

## Scope

1. **Atlas**: five real, publicly documented organizations, public official-site sources, purpose tags, service region, audience/capacity notes, search, and filtering. These are research leads **not** members, integration partners, guaranteed referrals, available providers, or a comprehensive survey. Do not infer a link between the listed organizations from co-listing.
2. **Desk**: one entirely synthetic adult request for records-navigation guidance; fictional sending and receiving desks; a fixed service-topic-only disclosure; explicit authorization → sending → acceptance/decline → reported assistance → recipient confirmation or withdrawal. Every occurrence is labeled simulated.
3. **Boundary**: no names, addresses, live forms, sensitive case details, real records, network requests, organizational messaging, child matching/placement, identity verification, consent validity, clinical/legal advice, or child-welfare decision-making. The public branch MUST NOT be used to collect real cases.

The simulated receipt is neither a Human Witness receipt nor a cryptographic signature. `subjectDigest: synthetic-referral-v1` is a **demo identifier**, not a content hash, and the UI never asserts otherwise. The act log is a local transient program trace, not evidence of an actual encounter. Browser actions do not communicate with a listed organization.

## Source directory / research provenance (checked 2026-09-23)

Official sites were checked against each organization's publicly described services, and entries intentionally keep claims narrow. Verify current policy, jurisdiction, eligibility, and availability directly:

| Organization | Public source | Publicly described capability / caveat |
|---|---|---|
| International Social Service – USA | https://www.iss-usa.org/ | Cross-border family/social-service coordination, documentation and post-adoption services; not proof of case acceptance. |
| Adoptees United | https://adopteesunited.org/ | Adoptee-led records, identity, and citizenship work; individual intake cannot be presumed. |
| InterCountry Adoptee Voices | https://intercountryadopteevoices.com/ | Adoptee-led education, origins and lived-experience resources; not a placement agency. |
| National Family Preservation Network | https://www.nfpn.org/ ; https://www.nfpn.org/contact-us/contact-us/ | Agency training, tools and technical assistance; explicitly states it cannot provide direct assistance to individual families. |
| Center for Adoption Support and Education (C.A.S.E.) | https://adoptionsupport.org/ ; https://adoptionsupport.org/counseling-at-c-a-s-e/ | Adoption-competent mental-health services within stated regional scope; broader education and national professional directory. |

The directory intentionally links to source organizations rather than copying private data or ingesting partner databases.

## Responsibility map

- **Orchard Bridge** owns service discovery, proposed referral policy, recipient-scoped disclosure, jurisdiction-specific review, and actual handoff **only if a separate future product passes appropriate approvals**. None is implemented as real-world execution here.
- **Human Witness** (https://github.com/the-static-collective/Human-Witness) is a candidate *encounter-evidence* adapter for what exact subject was presented and which deliberate act/refusal occurred. Receipt does **not** authenticate identity or capacity, prove legal consent, or authorize disclosure.
- **Garden / Band Runtime** are possible later holders of limited request/accept/report/confirm semantics, never automatic sources of identity, eligibility or legal authority.
- **Jubilee** is a possible bounded evidence/receipt consumer, not a replacement for child-welfare authorities, legal consent rules, or custody and record governance.

No external adapter is wired in this proof. Integration must be separately reviewed, tested, and authorized.

## Gate before a real-world pilot

Obtain adoptee-led, family-preservation and relevant tribal/child-welfare domain review; participant organizational agreements; jurisdiction-specific legal/privacy analysis; purpose limitation and data minimization; meaningful consent/authority and withdrawal semantics; independent identity/access checks; tested tenant isolation and incident response; record-retention and deletion strategy; no public child/person directory; no child matching/placement; human appeals and correction processes; a documented, deliberately tiny adult-service pilot. A synthetic state-machine green check does not satisfy these gates.

## First receipt

- Branch: `PK/adoption-bridge-workbench-001` (not merged).
- Delivered: browser-native atlas, user-visible synthetic referral workflow, exportable fictional trail, and a repeatable Node state-machine suite.
- Evidence boundary: directory entries are source-linked public descriptions, not partner enrollment or direct-contact data.
- Unresolved: service eligibility and availability, referral terms, human/organization feedback, live security and consent models, actual Human Witness adapter conformance, and any real-world outcomes.
