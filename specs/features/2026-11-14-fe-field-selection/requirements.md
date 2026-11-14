# Requirements: Field selection screen (step 1)

## Covers
- **PRD requirements:** FR-01 (field input: validate geometry, report invalid geometry, distinguish demonstration polygons from real boundaries), NFR-02, NFR-08.
- **Roadmap exit check satisfied:** partly. Phase 7's exit check needs the profile screen on real data, which is a later task.

## Inputs
- `data/fields/fields.geojson`: 45 Polygon features in WGS84 with `field_id`, `role`, `boundary_source`, `county`, `provenance`, `domain_note`.
- `data/fields/field_selection_notes.csv`: `cdl_class`, `area_ha`, `lon`, `lat` per field.
- `data/reference/story_boone_counties.geojson`: county outlines.

## Outputs
- `/field`: the selection screen.
- `/fields/[fieldId]/profile`: placeholder that receives the selected id.
- Pure module `validateFieldGeometry(ring, counties)` returning `{ valid, issues[], areaHa, county }`.

## Acceptance criteria
1. All 45 fields can be selected from the list and, at zoom-in, on the map. The primary demo field is selected by default.
2. The selected field is stored in `?field=<id>`; opening that URL selects it; an unknown id falls back to the primary field and says so.
3. The list is grouped into: primary demo field; rotation test fields; edge-case fields (continuous corn, pasture, mixed). The county filter (All, Story, Boone) works on all groups.
4. The validation panel shows: valid or invalid, county, area in hectares, boundary source ("Demonstration polygon" for every current field), and the provenance text.
5. `validateFieldGeometry` reports: unclosed ring, fewer than 4 points, self-crossing edges, a point outside both counties. Unit tests cover each case plus a valid polygon. Computed area for every demo field is within 2% of `area_ha` in the notes file.
6. Every demo field passes validation (so the panel is not showing a hard-coded "valid").
7. Edge-case fields carry a visible label saying the engine is expected to qualify or abstain; no outcome is claimed.
8. The map attribution for Esri imagery is visible. If tiles fail to load, the outlines still render and the list still works.
9. Keyboard: the list is operable with Tab, Arrow keys are not required, Enter/Space selects; the selected item is announced (`aria-pressed` or `aria-current`).
10. The step indicator shows step 1 current.
11. On desktop (1024 px and wider) the map and the summary panel stay in view while the field list scrolls, so a field can be picked from far down the list without scrolling back up. On phones the order is map, summary, list.
12. `npm run check` passes (lint, typecheck, format, tests, build). No horizontal scroll at 360, 768 and 1280 px.

## Evidence labels, scale and limitations to preserve
- Fields are demonstration geometry (assumption / user input), not real farm boundaries. Area is computed from the polygon, not a surveyed value.
- The panel does not claim data availability (crop, soil, weather, satellite). That belongs to the profile step.

## Out of scope
Drawing and uploading boundaries, real field boundaries, profile data, API calls, search by address.
