# Requirements: Climate indicators from NASA POWER daily meteorology

## Covers

- **PRD requirements:** FR-03 (environmental profile: temperature, precipitation and seasonal indicators from
  documented products, stating spatial and temporal scale and units), FR-06 (data adequacy: identify missing
  inputs and inadequate observations), FR-12 (traceability), NFR-01 (reproducibility), NFR-03 (auditability),
  NFR-05 (source failures or missing data must not silently create misleading outputs), NFR-06 (modularity).
- **Roadmap exit check satisfied:** partially — the DS2 half of "indicators loaded with lineage rows and passing
  schema checks; each states its scale (grid, not field)". This task delivers the indicator functions, their
  lineage rows and a golden-file test. Loading and the Pandera schema are the DE's half and are not done.

## Inputs

The DE's cleaned POWER daily table (`power_daily`), one row per point per day, with POWER's -999 fill value
already converted to null. Required columns and units, as fixed in `docs/sources/ds2-power-ssurgo-marsden.md`:

| Column | Meaning | Unit |
|---|---|---|
| `date` | calendar day | date |
| `T2M_MAX`, `T2M_MIN`, `T2M` | daily max, min and mean air temperature at 2 m | deg C |
| `PRECTOTCORR` | corrected precipitation | mm/day |
| `RH2M` | relative humidity at 2 m | % |
| `ALLSKY_SFC_SW_DWN` | all-sky downward shortwave radiation | MJ/m2/day |
| `WS2M` | wind speed at 2 m | m/s |

Reference ET additionally needs the point's latitude (degrees) and elevation (m), which POWER returns with the
series.

## Outputs

Every indicator returns an `IndicatorValue`: `indicator_id`, `value` (float or **null**), `unit`,
`window_start`, `window_end`, `days_expected`, `days_valid`, `status` (`ok` or `unknown`) and `reason` (set only
when unknown). `frost_window` returns a `FrostWindow` with `last_spring_frost`, `first_autumn_frost`,
`frost_free_days` and the same coverage and status fields.

| `indicator_id` | Unit | Definition |
|---|---|---|
| `gdd` | degree-days C | sum of max(0, (clamp(T2M_MAX) + clamp(T2M_MIN)) / 2 − base), both extremes clamped to [base, cap]; base 10 C, cap 30 C |
| `heat_days` | days | count of days with `T2M_MAX` >= 30 C |
| `precipitation_total` | mm | sum of `PRECTOTCORR` |
| `mean_temperature` | C | mean of `T2M` |
| `longest_dry_spell` | days | longest run of days below 1 mm; an unknown day ends the run |
| `dry_spell_count` | spells | number of dry runs of at least 10 days |
| `frost_window` | date, date, days | last frost on or before the season split, first after it, days strictly between |
| `reference_et_total` | mm | sum of daily FAO-56 Penman-Monteith ET0, soil heat flux zero |

`INDICATOR_LINEAGE` holds one row per indicator with `indicator_id`, `variables`, `formula`, `unit`,
`evidence_type`, `source`, `source_url`, `spatial_scale`, `temporal_window`, `missing_data_rule` and
`limitation`, ready for the `indicator_lineage` table.

## Acceptance criteria

Each is testable, and each is covered by a test in `transform/indicators/tests/test_climate.py`.

1. A hand-computed five-day GDD season returns exactly 36.0 degree-days C, with the clamping at both ends
   visible in the per-day arithmetic.
2. GDD never returns a negative daily contribution, and honours a caller-supplied base and cap.
3. A null day is never read as zero: it lowers `days_valid`, does not drag `mean_temperature` towards zero, and
   **breaks** a dry spell rather than extending it. An absent date behaves the same as a null one.
4. Below `min_coverage` (default 90 %) every indicator returns `value=None`, `status="unknown"` and a reason
   naming the counts.
5. `days_expected` and `days_valid` are present on every result, whatever the status.
6. `heat_days` treats the threshold as inclusive and counts only days with data.
7. `frost_window` returns both dates and the span when the window contains a frost on each side of the split,
   and returns `unknown` otherwise rather than inferring a span from one side.
8. A duplicate date, a missing variable column, a missing `date` column, a window whose end precedes its start,
   a cap at or below the base, and a dry-spell minimum below 1 all raise rather than returning a number.
9. Reference ET is non-negative, lands in single-figure mm/day for a central-Iowa July day, and rises with
   radiation, with wind and with dryness.
10. Every indicator has a complete lineage row; ids are unique; each of the five threshold-bearing indicators
    declares "not expert-reviewed", and `reference_et_total` declares "not independently validated".

## Evidence labels, scale and limitations to preserve

- **Evidence type:** `model_reanalysis` for all eight. POWER is a modelled reanalysis product, so a derived
  indicator inherits that label; none of these is an observation of the field.
- **Scale:** a POWER cell is about 0.5 x 0.625 degrees, roughly 50 km at this latitude. Every lineage row says
  "a grid value, not a field measurement; two fields in one cell share it". Fields sharing a cell are expected
  to show identical climate, and that must not be presented as agreement between independent measurements.
- **Limitations to carry downstream:** every threshold (GDD base and cap, 30 C heat day, 0 C frost, 1 mm wet
  day, 10-day dry spell) and the 90 % coverage rule are team-proposed and unreviewed; `PRECTOTCORR` is a
  bias-corrected reanalysis field, not a gauge reading, and convective rainfall varies well below cell size; a
  gridded 2 m minimum understates local frost risk; a rainfall dry spell is not agricultural drought, since it
  ignores soil water storage, rooting depth and irrigation; reference ET is grass-surface demand, not any
  rotation crop's water use, and is not independently validated yet.
- `status="unknown"` must reach the user as "unknown / not assessed", never as 0 and never as a gap in a chart.

## Out of scope

The POWER extraction and cleaning (DE, Phase 1 and 4), the Pandera schema (DE owns the shared module), the
ClickHouse load, the SSURGO indicators (separate task), the `/fields/{id}/profile` endpoint, choosing the
growing-season windows per field, and any comparison of POWER against PRISM (Phase 12).
