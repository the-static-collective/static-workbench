# CLOCKWORK-002: one UTC instant, separate calendars

Status: experimental, read-only, opt-in. Never converts CLOCKWORK-001 abstract ticks into dates or attributes divine/physical meaning to numerical coincidences. No HOUSE routes, filesystem mutation, event scheduler, unapproved runtime composition, or network access. No astronomical kernel bundled.

## Offline installed dependencies

Install optional dependencies with `pip install '.[clockwork]'` (Skyfield 1.55 and Pyluach 2.3.0 pinned in `pyproject.toml`). Supply a suitable `.bsp` ephemeris file from a trusted provider; research its coverage and redistribution rules independently. The adapter refuses nonexistent files, loads only the supplied local file via `skyfield.api.load_file`, hashes its exact bytes, and identifies Skyfield version and coordinate frame. Using Skyfield's bundled timescale tables does not silently download a new timescale file, but those built-in tables should be reviewed and refreshed for future dates.

## Usage

```bash
python -m static_workbench.clockwork_sky \
  --instant 2026-09-20T14:22:00Z \
  --kernel ~/ephemerides/de421.bsp \
  --ayanamsa-degrees YOUR_JUSTIFIED_OFFSET \
  --ayanamsa-name YOUR_NAMED_CONVENTION \
  --hebrew-utc-date
```

Replace both ayanamsa placeholders with a **justified numerical value** and its named convention for that instant. There is no baked-in ayanamsa, and the adapter cannot verify its accuracy; do not treat a guessed value as authoritative. Geocentric, apparent, ecliptic-of-date Sun/Moon longitudes are computed for that instant. Chinese solar terms are 24 equal 15° sectors of Sun's apparent tropical longitude, with index 0 beginning at the vernal equinox position; this is a sector assignment, **not** an exact crossing time or traditional Chinese lunisolar date. Panchanga tithi, nakshatra, yoga and karana are **instantaneous angular coordinates**, not a complete day-specific almanac. A full local Panchanga requires latitude/longitude, locale, sunrise convention, transition times, and a documented sidereal offset convention. The Chinese lunar mansion system must not be collapsed into 28 uniform longitude divisions. The optional Hebrew date corresponds to the UTC civil date, **not** the sunset-starting local religious day.

## Proved and not proved

- Local tests cover ISO timestamp offsets, 24-term sector wrap, daylight-independent UTC Hebrew conversion through Pyluach, invalid inputs, no implicit kernel download, data provenance fields, and the local Skyfield **mock contract**. The mock is **not** an ephemeris-accuracy test.
- At review time this execution environment has no Skyfield or `.bsp` kernel. Live Skyfield computation and astronomical cross-validation are explicitly **UNVERIFIED**. Before upgrading status, run a valid local `.bsp` and compare positions and transitional boundaries against independently published ephemerides/calendars.
- License audit: Skyfield 1.55 / Pyluach 2.3.0 report MIT. No third-party source was copied into this module. The external kernel and its source are intentionally separate; check exact file license and keep attribution before redistribution.

## Next authorized crossing

Add a typed observation intake and read-only UI in HOUSE only after validating a real kernel, plus a local observer/location and sunrise/sunset boundary method. For executable project actions, a separate version-pinned LOADOUT adapter must handle prepare/execute/inspect/reconcile with explicit human authorization. An `instant` never chooses a Biblical Jubilee year or authorizes release of debts or ownership changes.
