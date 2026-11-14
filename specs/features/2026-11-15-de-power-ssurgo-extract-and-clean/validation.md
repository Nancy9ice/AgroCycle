# Validation: Clean POWER and SSURGO, load the indicators

## Checks

| Criterion | How it is verified | Evidence |
|---|---|---|
| 1. POWER fill and gaps | Offline: the primary-001 sample and synthetic frames with a `-999` and a missing date. Live (skips without S3): 12,784 dates per variable for every point; the report names exactly the known fill values | pytest output, gap report |
| 2. Hard and soft checks | Offline tests for each rule at its boundary; a hard failure stops the run | pytest output |
| 3. Cells | Offline: identical series group, different series do not. Live: every field and `marsden-site` has one cell; the cell count matches the 7 distinct series sets found in Phase 1 | output |
| 4. SSURGO checks | Offline with the sample and synthetic bad frames (descending depths, `comppct_r` 120, shares summing to 0.8) | pytest output, findings report |
| 5. Schemas agree | `make schema-check`, Pandera rejection tests | output |
| 6. DS2's CSVs load | Offline: her runner's real lineage rows and synthetic indicator frames; an indicator without lineage is refused. Live: the three CSVs | pytest output, row counts |
| 7. Idempotent | Live: load twice, compare content hashes (the Phase 2 and 3 pattern) | hash values |
| 8. Parity and golden | Live: cleaned values equal `power_frame` for all points; the GDD golden season is re-run on the cleaned frame | pytest output |
| 9. `make check` portable | Run with S3 and ClickHouse settings absent | output |
| Hand-check | DS2 reviews the cleaned table against her indicators, the key of `field_indicators` and the unchanged column names | PR comment |

Merge when: every row is green, DS2 has confirmed the tables and the unchanged CSV contract, the code review findings are fixed, and the tracker row is updated.

## Results

- **Date:** 2026-11-15. **Status: the cleaning and the climate load are done; the indicator load is not.** The roadmap exit check ("indicators loaded with lineage rows") is **not met**: DS2's lineage file lacks rows for 7 indicators and the loader refuses it.
- **What was run:** `ruff` (clean for this work), `common.schema_check` (10 tables agree), the full `pytest` suite (464 passed, 1 xfailed, including 13 live ClickHouse tests in scratch tables), dry runs of both runners on the real data, and the real climate load (`python -m transform.clean.run --load`, migration 003 applied), repeated to prove it idempotent.
- **Passed (real data):**
  - POWER: 46 points (45 fields and the Marsden site), 12,784 days x 7 variables each, no date missing, **7 distinct cells** (as Phase 1 found), and exactly **4 fill values** (all `ALLSKY_SFC_SW_DWN`, 1991-11-29, in test-019, -023, -036 and -042), now null with `qc_flag = fill`; no `-999` remains. 626,416 `climate_daily` rows. Every point maps to a cell with data.
  - The cleaned values equal DS2's `power_frame` for every one of the 46 points, and her growing-degree-day totals are identical on the cleaned frame (2015, 2020, 2025).
  - SSURGO: 45 fields, 274 map units, 872 components, 3,422 horizons, **0 findings**, and DS2's own check agrees on all 45.
  - DS2's real files: `indicator_lineage` (16 rows), `field_indicators` (4,410) and `soil_properties` (626) fit the schemas and the row counts in her `run_manifest.json`; no duplicate keys (3,600 rows would collide without `window_start` in the key).
  - Live: the nulls in DS2-shaped files (value, window dates, `valid_obs`, reason, `value_text`) round-trip through ClickHouse; an indicator with no lineage row is refused by the loader itself, with the table unchanged; loads are idempotent.
- **Not done / failed:**
  - **Indicator load:** refused. 7 indicator ids have no lineage row: `gdd_season_difference_vs_marsden`, `ph1to1h2o_r_0_30cm`, `sandtotal_r_0_30cm`, `silttotal_r_0_30cm`, `drainagecl_dominant`, `hydgrp_dominant`, `map_unit_share`; 2 lineage rows are used by nothing (`awc_r_0_100cm`, `frost_window`). Waiting on DS2.
  - (Resolved 2026-11-15.) The climate tables were first loaded with 8-character cell ids; after the code review lengthened the id to 12 characters and added units and dates to the fingerprint, `--load` was rerun with the DE's go and replaced both tables. Now: 7 cells with 17-character ids (`cell-` plus 12), 46 points, 626,416 daily rows, 12,784 days per cell and variable, no `-999`, the post-load check found no point without a series and no series without a point.
  - DS2 has not yet reviewed the cleaned table, and her thresholds are not expert-reviewed.
  - Lint: 16 errors in other people's files (`scripts/` from DS1, `web/scripts/`) fail `make check` on `main` already.
- **Code review (`/code-review medium`, 9 findings):** all 9 fixed and tested. SSURGO now reports a missing `comppct_r` or depth, and its "rows dropped" check can fire (it was dead). A JSON null in a POWER series is flagged `null` and reported; a text value stops the run; a header with no `fill_value` is refused instead of defaulted. Cell ids are 12 hex characters, the fingerprint covers units and dates, and a collision between different series raises. The runner reports any bad or absent file cleanly, validates before writing, and checks after loading that points and series agree. The indicator loader reports a manifest without `rows` or an empty CSV, and refuses an empty frame before loading anything. `share_pct` tolerates float overshoot, and empty `value_text` is rejected so the frame and the database agree on duplicates.
- **Evidence location:** `tests/test_clean_*.py`, `tests/test_indicator_load.py`, `tests/live/test_clickhouse_live.py`; local outputs and the gap report in `data/out/clean/` (gitignored).
- **Roadmap exit check met:** no (see above). **Tracker updated:** 2026-11-15, row left `In progress`.
