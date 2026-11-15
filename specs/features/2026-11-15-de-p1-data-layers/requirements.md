# Requirements: P1 data layers (DE)

## Covers
- **PRD requirements:** section 4.2 (P1 capabilities), 6.1 (source records), FR-12 and NFR-03 (lineage); scale limits for S11, S12, S13, S14, S16, S17.
- **Roadmap exit check satisfied:** each layer is in ClickHouse with lineage and passing checks, or explicitly marked dropped with a reason.

## Inputs
NASS QuickStats API (county), AMS Market News reports, PRISM 4 km grids, NAIP imagery, SMAP and GPM IMERG products, and the POWER point map (`field_id -> point_id`) already in ClickHouse. Product versions are pinned at pull time.

## Outputs
- `raw/<source>/<version>/<retrieval-date>/` files with a manifest each.
- Tables, only for approved layers: `county_stats`, `market_prices`, `prism_daily` (and monthly), `naip_tiles`, `regional_context`. Columns are in the draft sheet. Each carries `load_id`, units in the column or schema, and an evidence type.
- A `data_sources` row and a `source_links` row per loaded layer, and `indicator_lineage` rows for anything derived (for example the PRISM-POWER difference).
- A tracker row per layer: approved and loaded, dropped (reason), or no sign-off (dry run only).

## Acceptance criteria
1. Every layer has a recorded decision (approved, changed, dropped, or no sign-off), with the date and who sent it, before anything is loaded.
2. A layer with no sign-off has no objects in S3 and no rows in ClickHouse.
3. Erosion susceptibility appears as "not assessed" in the tracker.
4. Each loaded layer stays inside its size budget, or the overrun is a recorded decision.
5. Every raw file has a manifest and a checksum that matches after upload (`verify_all` reports 0 problems).
6. Pandera schemas pass: units, ranges, required fields; fill values and withheld values are null with a flag, never 0.
7. Loads are idempotent: a second run gives identical table hashes.
8. A recount from the raw files matches the loaded counts.
9. Every loaded layer has a `data_sources` row, and every derived indicator a lineage row.
10. No API key or credential is committed or written in a manifest.

## Evidence labels, scale and limitations to preserve
- NASS: published survey statistics at county scale; not field yield validation.
- AMS: published market reports; context only, with commodity, location, date, unit and report type shown.
- PRISM: gridded model output at 4 km; kept only if it adds detail over POWER.
- NAIP: observed imagery, one flight date; not crop ground truth.
- SMAP/GPM: retrieval/model products at 9 to 10 km; not field moisture or a rain gauge.
- Missing stays missing: "unknown is not neutral".

## Out of scope
Erosion susceptibility; cutting any layer to a smaller subset than the budget needs; the P1 UI (Phase 13); scientific verdicts on whether a layer adds value (DS decides); P2 layers.
