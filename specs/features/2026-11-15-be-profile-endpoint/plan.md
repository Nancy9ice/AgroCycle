# Plan: Profile endpoint

- **Role:** be (written by the frontend developer at the team's request; the BE owner should review)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 7/13 support, BE: `GET /fields/{id}/profile` (the second endpoint the frontend waits on, after `/compare`)

## Goal

Serve the field profile screen (crop history, weather, greenness, soil) from the API, in the shape the web app already renders (`web/src/features/profile/types.ts`), so the profile, comparison and adviser brief all come from one place.

## Approach

- **The contract is the web app's `FieldProfile`**, camelCase and all, so the web switch is one function. Sections carry `status` (`available`, `sample`, `not_loaded`), `data` and `provenance`.
- **The API never serves sample values.** Where the frontend shows labelled sample weather today, the API says `not_loaded` (or real values if DS2's indicator outputs exist). `sample` is a frontend-only status.
- **Real data only:**
  - *Crop history*: DE's 2015 to 2025 CDL sequence, with the same one-sentence summary the comparison uses (`api/crop_summary.py`).
  - *Soil*: soil series and map unit from DE's field notes; `not_loaded` if absent. Drainage and organic matter are listed as not loaded, because the contract has no field for their values yet.
  - *Weather*: four indicators (rain, very hot days, dry spells, warmth) as the mean over the seasons whose result is `available`, from DS2's `data/out/indicators/field_indicators.csv` when present. `not_loaded` when not. The card says how many seasons were used.
  - *Greenness*: always `not_loaded`: no HLS features exist yet.
- **Provenance comes from the lineage, not retyped.** The technical part of each weather provenance (source, grid scale, missing-data rule, limitation, evidence type, indicator id) is read from DS2's `INDICATOR_LINEAGE`. Only the one-line plain description of each indicator is written here.
- **A season counts only if its status is `available`.** A `partial` or `unknown` season is left out of the mean and counted in "N of M seasons". Same conservative rule as `/compare`.

## Files, tables and endpoints

- `api/profile_view.py`, `api/lineage.py`; additions to `api/facts.py`, `api/repository.py`, `api/schemas.py`, `api/routes.py`; tests.
- `GET /fields/{field_id}/profile`.
- Web: `getFieldProfile` calls it when `AGROCYCLE_API_URL` is set.
- No tables.

## Steps (in order)

1. Spec and tracker.
2. Facts and repository additions (soil series, climate means).
3. Lineage reader and profile view builder with tests.
4. Schema and route; endpoint tests.
5. Web client and tests; end-to-end run with the API and the production web app.

## Dependencies and interfaces with other roles

- **DS2:** reads `INDICATOR_LINEAGE` (so a renamed key breaks a test, which is the point) and the runner's CSV columns.
- **DE:** soil series and map unit currently come from `field_selection_notes.csv`; no ClickHouse table holds them, so the ClickHouse repository returns soil `not_loaded`.
- **FE:** the contract has no place for soil values (organic matter, drainage) or for vegetation features; extending it is a web change.

## Risks and open questions

- `transform.indicators.climate` imports pandas, so the profile route needs pandas installed (it is a project dependency). A missing import raises a clear error at request time, not at startup.
- The weather window label is read from the CSV rows (April to November in DS2's runner), not assumed.
