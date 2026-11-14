# Validation: Field selection screen (step 1)

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1 Select any of 45 fields; primary by default | Click through list and map in a browser | Notes below |
| 2 URL holds selection; unknown id falls back | Open `/field?field=test-010` and `/field?field=nope` | Notes below |
| 3 Grouping and county filter | Count items per group and filter | Notes below |
| 4 Panel content | Compare panel values with the notes CSV | Notes below |
| 5 Geometry module | `npm test`: unit tests and the area cross-check on all 45 fields | Test output |
| 6 All demo fields valid | Test over `fields.generated.json` | Test output |
| 7 Edge-case labelling | Read the UI copy | Notes below |
| 8 Attribution and tile failure | Look at the map; block the tile host and reload | Notes below |
| 9 Keyboard | Tab through, press Enter on a list item | Notes below |
| 10 Step indicator | Look | Notes below |
| 11 Sticky map and summary | Scroll the list in Chrome at 1280×800, 1440×900 and 1024×700 and read the map's position | Notes below |
| 12 Check and layout | `npm run check`; 360, 768, 1280 px | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); two manual checks still open, listed below
- **What was run:** `npm run check` (ESLint, `tsc --noEmit`, Prettier check, `vitest run`, `next build`); a scripted Chrome session (DevTools protocol) against the running app at 1280 px and 390 px that clicked list items, filters and the call to action, read the URL and page text, captured console output and took screenshots.
- **Passed:**
  - 1: 27 buttons in the default list (primary + 26 rotation tests) and 18 more in the edge-case group; selecting a list item updates the panel and the map; the primary field is selected by default. Map-click selection was not scripted; it uses the same `onSelect` path as the list.
  - 2: `?field=test-010` and `?field=test-030` select those fields on load; `?field=nope` falls back to the demo field and shows a notice.
  - 3: county filter Story shows 23 field buttons in the list (matches Story's 23 fields once the edge group is opened); the edge-case group opens automatically when an edge field is selected.
  - 4: the panel shows county, size in ha and acres, boundary source, crop-history type, provenance and evidence badges.
  - 5 and 6: 56 unit tests pass. They cover each failure mode (too few points, unclosed, bow-tie, outside the pilot area, non-finite values), a valid L-shape, a hand-calculated area, and all 45 demo fields: each passes validation, sits in its stated county, and has a computed area within 2% of the recorded value.
  - 7: edge-case fields show a note saying they are expected to be qualified or abstained; no outcome is claimed.
  - 8 (partly): the Esri attribution is visible on the map.
  - 10: the step indicator shows step 1 current (compact text on phones).
  - 11: `npm run check` passes; document width equals viewport width at 1280 px and 390 px; the browser console is empty (headless GPU-driver notices excluded).
  - 11 (sticky layout, added after review): scrolled 1200 px at 1280×800, 1440×900 and 1024×700; the map's top stays at 97 px (heights 350, 414 and 286 px) and the summary with its "Build field profile" button stays in view. At 390 px the map is 350 px tall with no horizontal overflow. Bug found and fixed: MapLibre forces its container to `position: relative`, which collapsed the map to zero height inside a flex layout; the map now sits in an absolutely positioned wrapper.
- **Failed or skipped:**
  - 8: tile failure was not tested (the fallback message is implemented but I did not block the tile host).
  - 9: keyboard use was not tested by hand. All list items, filters and map buttons are native `<button>` elements.
  - 11: 360 px and 768 px were not re-measured for this screen; 390 px and 1280 px were.
  - Bugs found and fixed during testing: MapLibre's worker did not load under the bundler, so outlines and markers were missing (fixed with the copied worker); the profile route read `params` outside Suspense; the selected field's tiny outline covered its own marker at county zoom; on phones the expanded attribution covered the map key (key moved below the map).
  - Esri World Imagery terms were not checked for public deployment.
- **Evidence location:** commands run in the session; screenshots were kept in the session scratchpad, not committed.
- **Roadmap exit check met:** not for Phase 7 as a whole (needs the profile screen on real data).
- **Roadmap tracker updated:** 2026-11-14, left `In progress` until the keyboard and tile-failure checks are done.
