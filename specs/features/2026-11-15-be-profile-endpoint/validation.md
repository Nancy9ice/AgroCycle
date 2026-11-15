# Validation: Profile endpoint

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
| --- | --- | --- |
| 1 Status codes | `pytest api` | Test output |
| 2 Crop history | `pytest api`; compare with the web builder's output | Test output |
| 3 Soil | `pytest api` | Test output |
| 4 No sample values | `pytest api` | Test output |
| 5 Weather means | `pytest api` on fixture CSVs | Test output |
| 6 Lineage-derived provenance | `pytest api` | Test output |
| 7 All 45 fields | `pytest api` | Test output |
| 8 Web renders from the API | Browser run with API on | Notes below |
| 9 Checks | `pytest`, `ruff`, `npm run check` | Command output |

## Results (fill in after implementation)

- **Date completed:** 2026-11-15 (implementation); items under "Failed or skipped" are still open
- **What was run:** `pytest api engine` -> **143 passed** (62 API tests) in a Python 3.12 virtualenv with pandas installed; `ruff check api web/scripts engine` passes; `npm run check` -> **195 web tests** pass and the build succeeds; an end-to-end run with the API (pointed at a fixture indicator folder through `AGROCYCLE_INDICATORS_DIR`) under the production web app (`AGROCYCLE_API_URL`) in headless Chrome: two fields, the provenance drawer, widths 360, 390, 768 and 1280, console capture, a screenshot.
- **Passed:**
  - 1: 200 for a known field, 404 for an unknown one.
  - 2: crop history has 11 years, the codes `SCSCSCSCSCS` for the primary field, the same summary sentence as the comparison, repeated years (empty for the primary field; correct for a pasture field and a mostly-corn field), and CDL provenance of type `classified`.
  - 3: soil series and map unit from the field notes; the not-loaded list; provenance of type `survey`.
  - 4: with no indicator outputs, climate and vegetation are `not_loaded` with `data: null`; across all 45 fields no section has the status `sample`.
  - 5: weather means use only `available` seasons (fixture: seasons of 600, 700 and a `partial` 100 give 650 mm, and the card says "2 of 3 seasons"); an indicator with no available season is omitted, not shown as zero; a season without dates is left out.
  - 6: each card's source, grid scale, limitation, evidence type and indicator id are read from DS2's `INDICATOR_LINEAGE` (a test fails if a shown indicator is missing from it), and the plain text uses the thresholds from `climate.py` (30 °C, base 10, cap 30, 10-day spells) rather than retyped numbers. In the browser the drawer showed DS2's own caveat that POWER ran about 11 % low against the station record.
  - 7: all 45 profiles validate; no key name contains score, rank, winner, best or recommendation.
  - 8: with the API on, the profile page shows no sample label, crop history and soil from the API, four weather cards for the fixture field and "Not loaded" for a field without outputs; no overflow at the four widths; console empty; the API log shows the `GET /fields/{id}/profile` calls.
  - 9: checks as above.
- **Found while testing:** the profile page was pre-rendered at build time, when the API address is not set, so it silently kept showing sample data after the API was switched on. The page now always renders per request (`connection()`); the comparison pages already did because they read the URL.
- **Failed or skipped:**
  - **The indicator outputs used in the browser run were a fixture I wrote** (3 seasons for one field), shaped like DS2's runner output. No real runner output exists in the repository. Real data will exercise the same path but has not been seen.
  - The ClickHouse repository returns soil `not_loaded` (no table holds the series) and no weather.
  - The web contract has no place for soil values (organic matter, drainage) or greenness features; the API cannot serve them until the contract grows.
  - The weather cards show means of 4 indicators; the other four computed indicators (mean temperature, longest dry spell, frost-free days, reference ET) are not shown.
  - The profile page is no longer pre-rendered, so it is slightly slower to open.
- **Evidence location:** `api/tests/`, screenshot `profile-api.png` in the scratchpad; this file.
- **Roadmap exit check met:** partly. The profile screen renders real crop history, soil and (when produced) weather from the API; greenness is not available.
- **Roadmap tracker updated:** yes, 2026-11-15 (left "In progress": BE review and a real runner output are open)
