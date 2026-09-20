# HOUSE Native Maxhinal v0.1 — selected computer fuel

This is a **new HOUSE instrument**, inspired by the Daily Slice Hugh Jackman Maxhinal's creative and provenance posture, not an adaptation of its eight-chamber JavaScript engine. The original Daily Slice Maxhinal retains its own corpus/ride format and project-owned semantics. HOUSE's native rides are `house.native-maxhinal-ride/v0.1`; they are not `.maxhinal.json` rides and may not be imported as such.

## What is fuel?

The user selects **one to four** explicit items on HOUSE's local browser page, from either:

- A root-relative file beneath an explicitly configured HOUSE filesystem root. The user chooses the configured root and types the relative path. The engine refuses absolute paths, parent traversal, symlinks and sensitive-looking or hidden path components; it reads only regular nonempty files of at most 16 MiB. The exact bytes are SHA-256 hashed and file size, media type and name are retained. Valid UTF-8 text no larger than 128 KiB yields at most 1,600 characters of reviewable text. Binary, large-text and media files contribute **metadata only**, not inferred contents. No code or scripts are executed.
- A previously **saved, human-reviewed Creator Desk source pack**. Its exact immutable saved selected-line excerpts and pack digest become HOUSE fuel. A saved source pack does not automatically become a Daily Slice.

**Nothing is recursively scanned or auto-selected.** There is no entire-home-directory harvesting, cloud read, image recognition, transcript extraction or use of private Creator Workspace content. The filename filter is not a secret scanner; do not configure roots containing private third-party material.

## How to ride

Open **HOUSE Maxhinal** in the navigator, select a few explicit files and/or a saved Creator Desk pack, then click **Review this fuel before spinning**. HOUSE shows the path, digest, content-reading kind and bounded visible passage (if any). Choose a chamber, optional creative question and reproducible seed. **Spin reviewed fuel and save local ride** re-reads every file and pack and checks that the full fuel digest is identical to the displayed preview. If any fuel changes, the spin is refused and the user must review again.

The five bounded v0.1 chambers are:

- **Discontinuity:** literal token overlap and nonoverlap between available text excerpts, with a declared creative question and explicit warnings against mistaken identity or causation.
- **Braid:** ordered fragments and exact source identities with a creative invitation to consider a third connection.
- **Compose:** a structured composition prompt made of source parts; does not generate a song or claim to publish one.
- **Pressure:** a candidate relation, discriminating question and possible counterexample.
- **Shuffle:** reproducible seeded reordering of fuel fragments; explicitly not a new chronology.

The engine is deterministic for the same previewed fuel, chamber, seed and question. It uses no AI model, automatic interpretation of binary material, network call or arbitrary project code. Text comparison is literal keyword overlap, **not semantic proof**. A metadata-only file leaves an explicit residual stating that its media contents were not interpreted.

## Receipts and persistence

A successful spin writes one new immutable ride to HOUSE's separate local `state_dir/creator.sqlite3` table. It preserves the fuel digest, individual source references, byte hashes or saved pack identity, bounded text excerpts, operation mode, seed, question, projection, unresolved residuals, and rejected interpretations. Saved rides can be reopened after restarting HOUSE. The original files and packs are not changed. The separate operational journal records ride identity, mode and fuel digest only.

Copying a ride for use in Creator Desk is a **separate manual action**. It does not silently insert a draft, invoke Creator Workspace, export files, share content or publish to Bandcamp/GitBook. The full ride is available in HOUSE locally only; treat the shelf and any backups as private.

## Limits and unbuilt features

The user selects configured roots, not arbitrary absolute files anywhere on the host; expand the configured roots only deliberately. File cap is 16 MiB, UTF-8 text is inspectable only up to 128 KiB, and text snapshots are limited to 1,600 characters per fuel. For video, audio, images or huge artifacts, this release captures fingerprints and declared metadata but **does not digest their visual/audio content semantically**. Future source-owned media adapters could add explicit, consented derived text descriptions or thumbnails without silently promoting them to facts.

An automatic draft-linked native-ride field, cross-machine transport, version-pinned Daily Slice engine adapter and interruption/reconciliation for project effects are out of scope. No project file writes, model training, or automatic social-media publishing occur.
