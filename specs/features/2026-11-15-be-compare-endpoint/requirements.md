# Requirements: Compare endpoint and API skeleton

## Covers

- **PRD requirements:** FR-09, FR-10, FR-11, FR-12 (the endpoint returns the engine's traceable result), NFR-01 (same inputs, same output), NFR-05 (missing data never produces a misleading output), NFR-06. PRD 8.4 and 8.5.
- **Roadmap exit check satisfied:** the `/compare` half of Phase 10: "the `/compare` endpoint returns the structured result".

## Inputs

`POST /fields/{field_id}/compare` with JSON:
`manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor` (each `true`, `false` or `null`, default `null`), `priorities` (list of `soil`, `water`, `inputs`, `income`, `forage`; default empty), `sample_indicators` (bool, default `false`).

## Outputs

`{ field, decision, preview }` where `decision` is the engine's `Decision` as JSON with the engine's own field names (`outcome`, `outcome_reason`, `strategies`, `outcomes` each with `statement`, `caution`, `caution_reference`, `findings`, `unknowns`, `constraints_recorded`, `priorities_recorded`, `rules_version`, `limitations`) and `UNKNOWN` as `null`.

## Acceptance criteria

1. A known field returns 200 and a `decision` whose `outcome` is one of the three permitted values; an unknown field returns 404; a malformed body or an unknown priority returns 422.
2. The response equals `engine.decision.assess` for the same profile and constraints (the test calls both).
3. A `null` or omitted answer reaches the engine as `UNKNOWN` and is returned as `null`; it is never read as `false`.
4. With no indicator outputs on disk, a rotation field abstains and `unknowns` lists the four required indicators; a field that is not a maize-soybean rotation abstains with every strategy `unavailable`.
5. With indicator outputs present, statuses map as written in the plan (`frost_free_days` to `frost_window`; `ok` only if every season row is `available`) and the drainage class is the one with the largest share. Tested on fixture CSVs.
6. `sample_indicators: true` returns `preview: true`, reaches all three outcomes depending on the answers, and is refused (403) when `AGROCYCLE_ALLOW_SAMPLE_PREVIEW` is false.
7. The response for the 27 rotation fields and 18 out-of-domain fields matches the web app's TypeScript port for the same answers (checked on a sample of requests).
8. The result contains no field named score, rank, winner, best, recommendation or weight.
9. `GET /fields` returns all 45 fields; `GET /health` reports the data source and rules version.
10. `uv run pytest` and `ruff check` pass; the server starts and serves `/openapi.json`.

## Evidence labels, scale and limitations to preserve

Everything comes from the engine unchanged. The preview response says `preview: true`.

## Out of scope

Profile, Marsden evidence and lineage endpoints, polygon upload, authentication (the product has no accounts), caching, deployment.
