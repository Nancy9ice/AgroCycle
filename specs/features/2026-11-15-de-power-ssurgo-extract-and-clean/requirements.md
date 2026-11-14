# Requirements: Clean POWER and SSURGO, load the indicators

## Covers
- **PRD requirements:** FR-03 (soil and climate profile), FR-06 (data adequacy), NFR-01 (reproducibility), NFR-03 (auditability).
- **Roadmap exit check satisfied:** "indicators loaded with lineage rows and passing schema checks. Each states its scale (grid, not field)."

## Decisions (2026-11-15)
- Scope: clean POWER with a gap report, clean SSURGO with checks, Pandera and the ClickHouse tables, load DS2's indicators and lineage. Out: indicator maths (DS2), HLS (Phase 5), Marsden (Phase 6), the API.
- The DE cleans and loads separately; DS2's runner is unchanged.
- Validation: offline golden tests plus a live parity check, which skips without S3.

## Inputs
- POWER: `raw/power/daily-point-api-v2.10.3/2026-11-14/` (46 point files plus the Marsden site, 1991-2025, 7 variables, fill value from the response header).
- SSURGO: `raw/ssurgo/soil-data-access/2026-11-14/<field>/step_a..d` (45 fields).
- DS2's CSVs: `field_indicators.csv`, `soil_properties.csv`, `indicator_lineage.csv` in `data/out/indicators/` (or `--dir`), written by `transform/indicators/runner.py`.
- DS2's source sheet `docs/sources/ds2-power-ssurgo-marsden.md` for the checks.

## Outputs

| Table | Key | Columns |
|---|---|---|
| `climate_points` | `point_id` | point_id (field id or `marsden-site`), cell_id, latitude, longitude, elevation_m (as returned), load_id |
| `climate_daily` | `cell_id, variable, date` | cell_id, variable, date, value (null when missing), unit, qc_flag (`fill`, `soft_t_order`, `soft_t_range` or empty), load_id |
| `field_indicators` | `field_id, indicator_id, window_start` | the 11 columns DS2's runner writes (category, value, unit, status, window_start, window_end, valid_obs, unknown_reason, run_id) + load_id |
| `soil_properties` | `field_id, mukey, property, value_text` | the 10 columns the runner writes + load_id |
| `indicator_lineage` | `indicator_id, code_version` | already exists (Phase 2); DS2's 15 columns load as they are |

Local, not loaded: cleaned SSURGO frames and a findings report in `data/out/clean/`, and the POWER gap report.

## Acceptance criteria
1. POWER: no `-999` remains; each former fill value is null with `qc_flag = fill`; each point has 12,784 dates per variable or its missing dates are listed per variable; nothing is interpolated.
2. POWER hard checks fail the run (`PRECTOTCORR`, `ALLSKY_SFC_SW_DWN`, `WS2M` >= 0; `RH2M` in 0-100); soft checks flag and keep the row.
3. Every field and the Marsden site maps to exactly one cell; cells are grouped by identical content across all variables.
4. SSURGO: `_r` columns only; nothing dropped, filled or reweighted; keys kept; depths ascending, `comppct_r` in 0-100, component sums at most 100, field area shares summing to about 1 (flagged when not).
5. All loaded frames pass Pandera; `schema_check` shows the SQL and schemas agree.
6. DS2's three CSVs load; every `indicator_id` in `field_indicators` and `soil_properties` has a lineage row, else the load is refused; a null value has a status of `unknown`, `partial` or `not_assessed` and a reason.
7. Loads are idempotent: a second run leaves identical table hashes.
8. Parity: the cleaned POWER values equal DS2's `power_frame` output for every point (same nulls); her golden GDD season (36.0 degree-days C) still holds computed from the cleaned frame.
9. `make check` passes without S3 or ClickHouse access.

## Evidence labels, scale and limitations to preserve
- POWER: `model_reanalysis`, grid about 50 km, not field; precipitation about 11 % low against the Marsden station; solar radiation from a 1-degree grid.
- SSURGO: `survey`, mapped soil units, not a lab sample; hydrologic group strings such as `B/D` kept verbatim.
- DS2's `scale`, `evidence_type` and `limitation` per indicator are kept as written. Missing data stays null: unknown is not neutral.

## Out of scope
Indicator formulas and thresholds, optional variables (`GWETROOT`, `GWETTOP`), a re-pull of any source, the API, and expert review of DS2's thresholds.
