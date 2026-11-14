# Plan: Field selection screen (step 1)

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 7, FE: field selection (first screen of the core journey, PRD §5.2 step 1)

## Goal
Let a user choose a field (the primary demo field or one of the test fields) on a map and in a list, see that its geometry is valid and where it is, and continue to the profile step.

## Approach
- **Data:** the screen reads the 45 demo polygons that DE committed in `data/fields/fields.geojson`, plus the county outlines in `data/reference/`. A small script (`web/scripts/sync-field-data.mjs`) copies only the fields the UI needs (id, role, county, provenance, domain note, class, area, centroid, ring) into `web/src/features/field/data/`. The output is committed and marked generated, because Next.js cannot import files from outside `web/`. No API is needed for this screen; when `POST /fields` exists, this data layer is the only thing that changes.
- **Map:** MapLibre GL JS with Esri World Imagery tiles (satellite, attribution shown). Fields are ~6 to 44 ha, which is a few pixels at county scale, so the map shows numbered circle markers when zoomed out and the real outlines when zoomed in. Selecting a field flies to it.
- **Validation is real, not cosmetic.** A pure, unit-tested module checks a polygon (closed ring, enough points, no self-crossing, inside Story or Boone) and computes its area. The panel shows the result for the selected field. The same module will validate drawn or uploaded boundaries later (FR-01).
- **Selection** lives in the URL (`?field=<field_id>`), so a field can be shared and survives a reload (selection replaces the history entry, so Back returns to the previous page, not the previous field). The primary demo field is selected by default.
- **Honest labelling:** every field shows "Demonstration polygon". The 18 out-of-domain fields (continuous corn, pasture, mixed) are listed separately as edge cases that exercise "not enough evidence", not hidden.
- **Next step:** "Build field profile" goes to `/fields/<field_id>/profile`, a placeholder until the profile task.

## Files, tables and endpoints
- `web/scripts/sync-field-data.mjs`, `web/src/features/field/data/*.generated.json` and a typed accessor.
- `web/src/features/field/` (screen, list, map, validation panel, geometry module and tests).
- `web/src/components/layout/flow-steps.tsx` (the 5-step indicator, reused by later screens).
- `web/src/app/field/page.tsx` (replaces the placeholder), `web/src/app/fields/[fieldId]/profile/page.tsx` (placeholder).
- `web/package.json`: `maplibre-gl`, `vitest`, `test` and `sync:data` scripts.
- `web/scripts/copy-maplibre-worker.mjs`: MapLibre v6 looks for its Web Worker next to the bundled chunk, where the bundler does not emit it. The script copies the worker into the git-ignored `public/vendor/maplibre/` on install, dev and build, and the map calls `setWorkerUrl` with that path.
- No tables or endpoints.

## Steps (in order)
1. Spec, branch, dependencies.
2. Sync script and typed data accessor.
3. Geometry validation module with unit tests.
4. Step indicator, list, map, validation panel, screen composition.
5. Run `npm run check`, test in a browser at desktop and phone widths.

## Dependencies and interfaces with other roles
- Reads DE's `data/fields/fields.geojson` (Phase 0, Done). If DE changes its properties, re-run `npm run sync:data`.
- BE: the profile route is `/fields/{field_id}/profile`, mirroring `GET /fields/{id}/profile` in `specs/tech-stack.md`.

## Risks and open questions
- Esri World Imagery is free for development and demos with attribution; check its terms before any public deployment.
- Satellite tiles need network. If the demo venue has no network, the map shows only the outlines on a plain background. Field choice still works from the list.
- Drawing and uploading a boundary is not in this task. The buttons are shown as unavailable.
