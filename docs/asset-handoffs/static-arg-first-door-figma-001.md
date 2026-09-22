# STATIC ARG — First Door / World Entry visual asset handoff 001

**Status:** experimental visual study, intended for selective reuse in Workbench's existing First Door and World Entry. This document preserves the source and a durable screenshot; **it is not a new game runtime or project-native receipt**.

## Durable artifacts
- **Editable source:** [Figma STATIC ARG — First Door / World Entry UI study](https://www.figma.com/design/JV2jNJjmvQ2uy63jmrIKPU) — design file key `JV2jNJjmvQ2uy63jmrIKPU`, main screen frame `1:2`, 1440 × 900.
- **Checked-in static reference:** [static-arg-first-door-figma-001.png](static-arg-first-door-figma-001.png), a 1440 × 900 screenshot of frame `1:2`. This is a *snapshot*; Figma remains the editable source. The PNG is preserved in Git, not merely linked through a short-lived Figma asset URL.
- **Related 3D environmental source:** [STATIC FIELD — The First Bell / Porch r1 handoff](https://github.com/the-static-collective/static-field/blob/main/experiments/first-bell-porch-3d/README.md), separate project authority.

## Screen structure
- `1:2`: main experimental screen, 1440 × 900.
- `1:3`: House navigation rail.
- `1:4`: First Door / illuminated journey, Seed → Machine → World → Door → Return.
- `1:5`: World Entry / four-location map.
- `1:6`: source-linked discovery journal.

This is a **layout and visual-direction prototype**: its map panel is not an implemented map, the navigation labels are not linked to real routes, and its screenshot does not establish accessible behavior or responsive mobile performance.

## Existing runtime is authoritative
Workbench `main` already has the local-only STATIC-ARG-001 seed/machine/world/door sequence and STATIC-ARG-002 World Entry with Threshold, Workshop, Seed Garden, Return Archive, source-linked discoveries, and SQLite persistence. Inspect those existing components before implementing a design change; this handoff must not silently replace or invent game state.

## Reuse checklist
- [ ] Compare the source Figma screen and checked-in PNG with the actual First Door/World Entry UI in `main`.
- [ ] Extract only the useful visual patterns into the existing HTML/CSS/JS; keep Workbench's existing APIs, event identity, and local storage intact.
- [ ] Make map and journal panels reflect existing *actual* room visits, discoveries, locked states and source references. No visual symbol implies a historical action.
- [ ] Respect reduced motion, keyboard navigation, contrast, mobile widths, screen reader labels and existing touch semantics.
- [ ] Consider an optional 3D Porch presentation as a separately approved adapter; no asset may grant crossing authority or rewrite the source event trail.
- [ ] Test the existing local ARG flows and screenshot mobile/desktop before describing the new visual pass as integrated.

**Preservation ≠ integration.** Keep this source discoverable even if plugin access changes, and track any implementation in a separate reviewed change.
