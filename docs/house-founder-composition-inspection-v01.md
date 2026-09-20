# HOUSE × Founder Node — composition inspection v0.1

Status: bounded proposed feature on review branch. No remote or project-native execution.

## Entry

In Founder Node, review a successful authority-gated compilation's Ecosystem Composition view and click **Copy Workbench inspection descriptor**. Manually paste that JSON into Static Workbench > **Composition inspection**; choose **Inspect local candidates**. This version has no live connector between the two applications, no registry fetch and no cross-application trust handshake.

Founder Node's [proposed v0.1 descriptor](https://github.com/the-static-collective/founder-node/pull/5) is the only supported input. HOUSE refuses unknown fields, missing required boundaries, wrong schema/status, duplicate claimed identities, historically classified participants and any claim of execution authority. It limits the incoming JSON to 64 KiB and up to four participants.

## What the preview actually proves

- The human supplied a descriptor that conforms to a known *shape*. It may have been forged; the claimed registry source/version/date remain unverified testimony.
- The local repo scanner found zero, one or more Git worktrees with a basename matching each declared repository's GitHub slug within configured roots. Missing, present, ambiguous are **name matches**, not authenticated GitHub identities.
- For one name match, HOUSE displays root-relative path, branch, short HEAD, dirty/detached and upstream status where available. Multiple matches are **ambiguous** and intentionally have no selected default.
- Role, declared owns/nonAuthority, relation evidence, and projectId are caller claims only. No checkout identity, project service, adapter contract, interface compatibility, or human admission is verified.

### Crossing

    declared composition (untrusted)
        -> bounded parsing and refusal
        -> configured-root Git inventory
        -> name-match candidate states
        -> human review, if warranted

## Authority and privacy

No content is exported. No imported descriptor is stored as a receipt, no event or project file is modified by inspection, no project executable or adapter runs, and no command, URL or credential from the descriptor is followed. The local HTTP request uses the existing Workbench origin/session guard. Local users should nevertheless avoid pasting secrets: the JSON is processed by the loopback app and remains in the browser input until cleared or navigated away from.

The response always reports source_authenticated=false, execution_authorized=false, runtime_readiness=unknown, compatibility=unverified, and admission=not-requested; imported values cannot promote these fields.

## Next slice, only after field proof

Bind exact remote identity and pinned project commit to a project-owned adapter descriptor, review per-project permissions with an explicit human gate, and require project-native receipts for any effects. A name-match-only inspection must never be used as an authorization token.
