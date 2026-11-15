# Plan: Clean POWER and SSURGO, load the indicators

- **Role:** de
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 4, DE: extract and clean POWER and SSURGO; load DS2's indicators with lineage

## Goal
Cleaned, validated daily climate and soil data in ClickHouse, and DS2's indicator tables loaded with their lineage, so the profile endpoint and the timelines have real data. The exit check: indicators loaded with lineage rows and passing schema checks, each stating its scale (grid or field).

## Approach
- **DE cleans and loads separately; DS2's runner is unchanged** (decision 2026-11-15). His runner keeps reading the raw files; a parity test checks both give the same values.
- POWER: one cleaned table per distinct climate cell, not per field (the 46 raw files hold only 7 distinct series sets), with a mapping from point to cell. About 0.6 M rows.
- SSURGO: tidy, checked frames kept locally; the app reads DS2's `soil_properties`, so they are not loaded.
- DS2's CSVs load through `common.load`; every loaded indicator needs a lineage row.
- Dry run by default; `--load` writes.

## Task groups

### 1. Claim and branch
1. Set the Phase 4 DE row to `In progress`; correct two wrong notes in the roadmap (see Risks). Branch from `origin/main`. Done.

### 2. Clean POWER
1. `transform/clean/power.py`: tidy the response into one row per point, variable and date; `-999` to null with `qc_flag = fill`; expected 12,784 dates per variable, a missing-date report per variable; DS2's hard checks fail the run, soft checks set a flag.
2. Group points whose series are identical into a climate cell; write `climate_points` (point to cell, coordinates as returned, elevation).

### 3. Clean SSURGO
1. `transform/clean/ssurgo.py`: one row per field and map unit with its area share, one per component, one per horizon, `_r` columns only, nothing dropped or filled, source units kept.
2. Checks: depths ascending, `comppct_r` in 0-100, components per map unit sum to at most 100, field shares sum to about 1 (flagged, not fixed). Frames and a findings report go to `data/out/clean/` (gitignored).

### 4. Schemas and tables
1. `schema/003_indicators.sql`: `field_indicators`, `soil_properties`, `climate_points`, `climate_daily` (plain `MergeTree`, `load_id`, one partition each).
2. Pandera schemas and registry entries in `common/schemas.py`; `field_indicators` and `soil_properties` set `lineage_column` so `load` runs the orphan check.

### 5. Runners
1. `python -m transform.clean.run [--load]`: POWER and SSURGO cleaning, gap report, `climate_*` load.
2. `python -m transform.indicators.load [--dir DIR] [--load]`: validate and load DS2's three CSVs (default `data/out/indicators/`). Lineage first, so the orphan check can pass.

### 6. Validation and close
1. Parity with DS2's `power_frame`, his golden GDD season on the cleaned frame, gap report against the known fill values, load twice with equal hashes.
2. Fill `validation.md`, update the tracker, `/code-review`, PR.

## Files, tables and endpoints
- New: `transform/clean/{sources,power,ssurgo,run}.py`, `transform/indicators/load.py`, `schema/003_indicators.sql`, tests (`test_clean_*`, `test_indicator_load.py`, live tests).
- `sources.py` reads the local pull folders (`POWER_DIR`, `SSURGO_DIR`) and falls back to S3 for a missing file.
- Changed: `common/schemas.py`, `specs/roadmap.md` (own row, two corrected notes).
- ClickHouse: `field_indicators`, `soil_properties`, `climate_points`, `climate_daily` (new); `indicator_lineage` (loaded).

## Dependencies and interfaces
- **DS2:** the runner and his three CSV file names and columns are the contract. His `indicator_lineage` rows load as they are (verified). `field_indicators` and `soil_properties` keep the names and columns the runner writes, so he does not re-emit; the tables carry `load_id`, not `loaded_at`. The key of `field_indicators` includes `window_start`.
- **BE:** reads `field_indicators`, `soil_properties`, `indicator_lineage`; the Phase 13 timelines read `climate_daily` through `climate_points`.
- **Phase 5 and 6:** reuse `schemas.py`, `load` and the `lineage_column` check.

## Data size
Raw POWER 68 MB and SSURGO 1.2 MB already in S3. Loaded: about 0.6 M climate rows, a few thousand indicator rows.

## Risks and open questions
- **Resolved 2026-11-15:** DS2 re-ran his runner and the lineage is now complete (21 rows); the finding below was made on his first files. **DS2's lineage was incomplete (found on his first real files):** 7 indicator ids used by `field_indicators` and `soil_properties` have no lineage row (`gdd_season_difference_vs_marsden`, `ph1to1h2o_r_0_30cm`, `sandtotal_r_0_30cm`, `silttotal_r_0_30cm`, `drainagecl_dominant`, `hydgrp_dominant`, `map_unit_share`), and 2 lineage rows are used by nothing (`awc_r_0_100cm`, `frost_window`). The loader refuses until DS2 sends a complete file; the DE does not write lineage content.
- **Fixed while building:** `table_hash` returned NULL for tables with nullable columns (it now hashes a text rendering of each row; hash values from Phases 2 and 3 are not comparable with new ones), and pandas 3 parses dates to microseconds while the schemas use nanoseconds (the reader normalises).
- **Corrections:** the roadmap said the lineage table stores arrays and needs an adapter. Wrong: it stores JSON text, and DS2's rows load as they are. Fixed in this PR.
- The earlier table design keyed `field_indicators` on `(field_id, indicator_id)`, which would have merged the 11 seasons into one row; the new key adds `window_start` (null for soil indicators, so uniqueness is checked with `ifNull`).
- POWER cells are grouped by identical content, not by coordinates, because the API returns the coordinates sent. The grouping is a property of this pull; a re-pull may differ.
- POWER precipitation runs about 11 % low against the Marsden station (DS2's review) and shortwave radiation is a 1-degree product; both stay in the lineage, not corrected.
- Two copies of the fill-value rule exist (DS2's second line of defence and the DE's). The parity test is the guard.
