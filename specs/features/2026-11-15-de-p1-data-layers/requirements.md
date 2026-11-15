# Requirements: P1 data layers (DE)

## Covers
- **PRD requirements:** section 4.2 (P1 capabilities), 6.1 (source records), FR-12 and NFR-03 (lineage); scale limits for S11, S12, S13.
- **Roadmap exit check satisfied:** each layer is in ClickHouse with lineage and passing checks, or explicitly marked dropped with a reason.

## Inputs
NASS QuickStats API (county), AMS Market News reports and NAIP imagery. Product versions are pinned at pull time.

## Outputs
- `raw/<source>/<version>/<retrieval-date>/` files with a manifest each.
- Tables, only for approved layers: `county_stats`, `market_prices`, `naip_tiles`. Columns are in the draft sheet. Each carries `load_id`, units in the column or schema, and an evidence type.
- A `data_sources` row and a `source_links` row per loaded layer. No derived indicators are planned, so no lineage rows unless one is added.
- A tracker row per layer: approved and loaded, dropped (reason), or no sign-off (dry run only).

## Acceptance criteria
1. Every layer has a recorded decision (approved, changed, dropped, or no sign-off), with the date and who sent it, before anything is loaded.
2. A layer with no sign-off has no objects in S3 and no rows in ClickHouse.
3. PRISM, SMAP/GPM and erosion appear in the tracker as dropped or not assessed, each with its reason.
4. Each loaded layer stays inside its size budget, or the overrun is a recorded decision.
5. Every raw file has a manifest and a checksum that matches after upload (`verify_all` reports 0 problems).
6. Pandera schemas pass: units, ranges, required fields; fill values and withheld values are null with a flag, never 0.
7. Loads are idempotent: a second run gives identical table hashes.
8. A recount from the raw files matches the loaded counts.
9. Every loaded layer has a `data_sources` row.
10. No API key or credential is committed or written in a manifest.

## Evidence labels, scale and limitations to preserve
- NASS: published survey statistics at county scale; not field yield validation.
- AMS: published market reports; context only, with commodity, location, date, unit and report type shown.
- NAIP: observed imagery, one flight date; not crop ground truth.
- Missing stays missing: "unknown is not neutral".

## Out of scope
PRISM vs POWER, SMAP/GPM and erosion susceptibility (dropped or not assessed, 2026-11-15); cutting any layer to a smaller subset than the budget needs; the P1 UI (Phase 13); scientific verdicts on whether a layer adds value (DS decides); P2 layers.
