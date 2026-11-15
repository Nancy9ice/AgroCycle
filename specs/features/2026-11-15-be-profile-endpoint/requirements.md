# Requirements: Profile endpoint

## Covers

PRD FR-02, FR-03, FR-05 (surfaced), FR-12 (provenance for each material output), NFR-05 (missing data never produces a misleading output). Roadmap Phase 7 exit check ("the profile screen renders real data end to end"), partly: greenness is not loaded.

## Inputs

`GET /fields/{field_id}/profile`.

## Outputs

JSON matching `FieldProfile` in `web/src/features/profile/types.ts` (camelCase): `fieldId`, `cropHistory`, `climate`, `vegetation`, `soil`.

## Acceptance criteria

1. Known field returns 200; unknown returns 404.
2. `cropHistory` has 11 years (2015 to 2025) with the crop code per year, the summary sentence, and the repeated years; it carries the CDL provenance (evidence type `classified`, 30 m). A field with no sequence gives `not_loaded`.
3. `soil` has series and map unit from the field notes, the not-loaded list, and survey provenance (`survey`); absent soil gives `not_loaded`.
4. With no indicator outputs, `climate` and `vegetation` are `not_loaded` with `data: null`. No value in the response is sample data and no section has status `sample`.
5. With indicator outputs, `climate` is `available` with up to four indicators; each value is the mean over `available` seasons only, the card says "N of M seasons", and a season that is `partial` or `unknown` is not in the mean. An indicator with no available season is omitted, not shown as zero.
6. Each weather indicator's provenance technical fields come from `INDICATOR_LINEAGE` (source, scale, indicator id, evidence type); a test fails if an indicator the profile uses is missing from the lineage.
7. The 45 fields all return a valid profile; the response validates against the model and has no field named score, rank or winner.
8. The web app, with `AGROCYCLE_API_URL` set, renders the profile from the API: crop history and soil as before, weather and greenness as "not loaded". Without the variable nothing changes.
9. `pytest api`, `ruff`, `npm run check` pass.

## Evidence labels, scale and limitations to preserve

Evidence types and scales from DE's and DS2's records, unchanged: `classified` (CDL), `survey` (SSURGO), `model_reanalysis` (POWER, grid not field).

## Out of scope

Serving soil values, vegetation features, the Marsden and lineage endpoints, polygon upload.
