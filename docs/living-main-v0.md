# Living Main v0 — Chronobody-inspired inspection

This bounded slice adds `POST /api/living-main/preview` to the local Workbench. It is an **inspection only** composition preview, not an implementation of ALEX's Chronobody registry or executor. It does not install, fetch, checkout, merge, launch or save code.

## Request

After `GET /api/bootstrap`, use the returned local session token as `x-workbench-session` with the same-origin request to the Workbench loopback host. The route accepts only:

```json
{
  "selections": [
    {
      "root_id": "static",
      "relative_path": "sources/ALEX.2",
      "expected_sha": "<full 40-character lowercase Git commit SHA>"
    }
  ]
}
```

`root_id` and `relative_path` must identify a checkout in the current configured-root inventory. The example path is illustrative; use the path actually reported by `GET /api/repos`. Fetch the *full* SHA with `git -C /path/to/checkout rev-parse HEAD`, not the abbreviated `head` field from `/api/repos`. Selections must be unique, one to 24 checkouts, and clean. A changed HEAD, unresolved path or dirty checkout returns a conflict rather than silently falling forward to a branch tip.

The response includes a content-addressed `configuration_id`, member exact-SHA identities and navigation-only branch labels; branch renaming does not alter the configuration identity. The identity binds the manifest of selected source commits and root-qualified checkout names, **not** an executable build, full environment lock, runtime test or true Git remote repository identity.

## Explicit limits

- No independent remote-origin identity verification, dependency/environment lock or branch dependency analysis.
- No project-owned Chronobody status assignment; `CLEAN_CHECKOUT` is an observation, **not** `PRESENT` or `INCUBATING`.
- `NOT_TESTED` does not assert cross-repo compatibility or admission.
- The UI is not yet wired: call the local API explicitly.
- The preview is not persisted; subsequent source or dependency changes require a new observation.
- The existing sync utility remains a separate acquisition step. Do not make a read-only preview endpoint mutate local Git state.

Next bounded frontier: read-only UI selection and lineage-aware comparison, followed by an explicit operator-authorized installation/test path with its own receipts. No automatic promotion into source-repository `main`.
