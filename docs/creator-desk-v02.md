# Creator Desk v0.2 — selected source packs and local draft shelf

Creator Desk v0.2 is a **local, Workbench-owned creative surface**. It does not run the Creator Workspace plugin, train a model, transmit selected text to an external app, mutate a source checkout, or publish work. Sources and interpretations must remain separate.

## Flow

1. Open Creator Desk in HOUSE, choose a discovered checkout, and search Markdown/plain-text material.
2. Explicitly select up to eight matching lines; change checkouts and repeat if needed. Merely returning a search hit does **not** select it.
3. Select **Preview selected source pack**. HOUSE reopens the selected local source files and verifies the full-file SHA-256 digest from search, as well as exact selected line and path. Each preview carries root ID, repository-relative checkout path, source-relative file, line range, excerpt digest, working-tree HEAD and dirty state. The displayed preview is the material to review, not an opaque background corpus.
4. Select **Save exactly this pack locally**. HOUSE recomputes all source checks and the entire pack digest. Any intervening source edit or changed packet identity rejects the save. A saved pack is an immutable snapshot in `state_dir/creator.sqlite3`.
5. Choose a saved pack and write a lyric, podcast script, post, brief, or other draft. Declare creative assumptions and unresolved gaps separately. Each save appends a revision; stale revision numbers are refused. The source pack cannot silently be changed on a draft. Opening HOUSE after restart retains saved packs and drafts.
6. Only when you choose **Copy draft + source references** does the browser attempt a clipboard handoff. An editable work-in-progress is not implicitly copied, shared, exported, or published. The handoff includes selected source paths, line references, file digests, worktree flags, assumptions, gaps, and draft content.

## Limits and privacy

- Local source selection: at most eight lines, 8 KiB serialized pack, 128 KiB per inspected UTF-8 Markdown/text file, source-depth and traversal constraints; no symlinks, hidden or sensitive-looking path components. The source-search step remains bounded to one explicitly selected checkout per search.
- This filter is **not a secret scanner**. A person must review every preview and intentionally configure the roots HOUSE may inspect. Do not configure roots containing secrets or other people's private material.
- Source file digests cover exact local bytes. HEAD and dirty markers describe a working tree, not a cryptographically verified frozen commit or authorship. Saved excerpts stay unchanged if original files later change; this is a snapshot, not an ongoing sync.
- Local draft body is capped at 32 KiB; title, assumptions, and unresolved gap fields are bounded. Draft edits append SQLite revisions. The shelf never writes back into Git repositories, GitBook, NanaSpork, the Autodiscography or Static Live.
- Creator writes require a per-process browser session token and reject cross-origin requests. The app still runs as a local **single-user loopback workbench**, not as a multi-user service. The shelf SQLite file has owner-only permissions on POSIX. Protect your home directory and backups accordingly.
- The separate HOUSE operational journal records only saved pack/draft identifiers and counts or revision numbers, not creative text.
- No automatic AI calls, whole-corpus ingestion, background scan, external sync, publish action, project-native receipt, or permission to infer source meaning.

## Restart and error semantics

Pack preview and save are separate steps. Source changes, unreadable or oversized files, symlinks and stale pack preview digests fail closed. Source packs are append-only. Draft creation and revision insertion use SQLite transactions; failure does not replace the prior saved revision. The editor retains unsaved text on a reported save error, although unsaved text can be lost by navigating away or reloading: save a local revision before leaving.

## Test proof and remaining frontier

Tests cover selected passages from different checkouts sharing a filename, SHA mismatch after source edit, path/symlink refusal, private path filters, explicit session and origin guard, preview-digest mismatch, local persistence across restart, stale draft edit rejection, source-pack immutability on a draft and failed revision preservation. CI also syntax-checks the browser module.

Next: explicit source-pack import/export as user-owned files, version-pinned project adapters, and a deliberate handoff into the user-selected Creator Workspace conversation. No automatic connector invocation is implemented.
