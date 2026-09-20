# CLOCKWORK-001 — Experimental clock-of-clocks

Status: experimental, non-canonical, read-only. `static_workbench.clockwork` has no runtime or UI hook, uses only Python standard library, and makes no project-native receipts. Run `python -m static_workbench.clockwork --tick 960`; run `pytest tests/test_clockwork.py -q`.

## Boundaries

- `tick_state(tick)`: abstract integer ticks only. `stem_branch` and gate advance together as an experiment; **NOT** the actual Chinese calendar for a date, and `gate.index` is binary order, **NOT** the King Wen hexagram number. The gate's Egyptian source/receiver/direction arrangement is an original experimental mapping, not ancient doctrine.
- `jubilee_period=50|49`: counter convention, **NOT** a calendar determination or authority to release debts, change ownership, or act on a project.
- `panchanga_coordinates(sun_longitude, moon_longitude, ayanamsa)`: accepts explicitly supplied, epoch/frame-compatible geocentric tropical ecliptic longitudes and named sidereal offset from a separate provider; returns angular sector indices only. No sunrise, vara, locale, ephemeris, tithi transition time, lunar month, or festival date can be inferred. A future adapter must carry provider, version, epoch, observer, longitude convention, ayanamsa convention, and uncertainty.
- `gematria` and `els_matches` are original minimal algorithms. Do not include sacred text corpora without checking each edition's source, license, and normalization. An ELS match is not evidence of an intentional biblical code; controls must record search terms, all tested skip values, corpus variants, and negative/comparison results.
- `CLOCKWORK-001` has NO action execution or write access; all new authority requires a separate human-approved gate and reconciliation contract.

## First exact arithmetic

`lcm(60,64)=960`: 16 revolutions of the 60 counter and 15 of the 64 counter. `lcm(60,64,50)=4800`; substituting 49 gives `47040`. These are mathematical results on **chosen abstract tick units**, not natural astronomical alignments.

## External code and license intake ledger — evaluate, do not copy yet

| Candidate | Function | Reported license | Integration decision |
|---|---|---|---|
| Hebcal `@hebcal/core` (hebcal/hebcal-es6) | Hebrew calendrical calculations | GPL-2.0-only | Do not vendor/import until project-wide compatibility and notices reviewed. |
| `@hebcal/hdate` | Jewish civil/Hebrew date conversion | inspect exact installed version | Same hold; prefer optional isolated adapter only after review. |
| `webresh/drik-panchanga` | Panchanga using Swiss Ephemeris | AGPL-3.0-or-later | Research reference only until copyright/license review. |
| Swiss Ephemeris and `pyswisseph` | High-precision positions | Swiss dual AGPL/professional; Python bindings AGPL | No incorporation under current license assumptions. |
| Skyfield | Astronomical computation | MIT | Candidate for separate future adapter; record ephemeris kernel/data provenance and verify license of each dataset. |
| `solarlunar` | Chinese lunisolar calendar | ISC (npm) | Candidate for adapter; verify exact pinned release and license before intake. |
| Open Scriptures / Sefaria | Hebrew Bible text and annotations | varies by dataset/edition | Review individual texts/exports before bundling or redistribution. |
| Third-party gematria / ELS repositories | Text numerical/search algorithms | repo-specific | Algorithmic ideas only here; no third-party code or corpus copied. |

This is an engineering audit, not a legal opinion. Source algorithms are distinct from an author's implementation, edition, translation, and dataset license. See primary project license files at integration time.

## Suggested next vertical slice

Add a version-pinned ephemeris adapter that maps one timestamp+location to verified Sun/Moon positions and records its coordinate frame, then a separate real calendrical adapter for sunrise-based day labels. Compare independently generated samples to external almanac and astronomy references. Only afterward permit temporal alignments to emit proposals for human review.
