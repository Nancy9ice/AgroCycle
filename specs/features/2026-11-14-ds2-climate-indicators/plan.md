# Plan: Climate indicators from NASA POWER daily meteorology

- **Role:** ds2
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 4, DS2: engineer the POWER temperature and precipitation indicators (GDD, heat days, frost, dry spells, seasonal totals, reference ET), each with units, window and scale

## Goal

A tested, deterministic module that turns a cleaned daily POWER series into the climate indicators the field
profile and the decision engine need, with every value carrying its own observation count and an explicit
`unknown` state when the window is not covered well enough to compute it.

## Approach

Pure functions over a daily DataFrame, no I/O and no network, so the indicators can be tested without the
extraction existing yet. The column names and units are the ones fixed in `docs/sources/ds2-power-ssurgo-marsden.md`
(`T2M_MAX`, `T2M_MIN`, `T2M`, `PRECTOTCORR`, `RH2M`, `ALLSKY_SFC_SW_DWN`, `WS2M`), so when the DE's first pull
lands it either matches this contract or the mismatch is the finding of the first-pull review.

Each function returns an `IndicatorValue` carrying the value, unit, window, days expected, days valid, a status
and, when unknown, the reason. The missing-data rule is the one principle that shapes the whole module: a null day
is never read as zero. A missing precipitation day does not shorten a dry spell or reduce a seasonal total; it
breaks the run and lowers the coverage, and below a coverage threshold (default 90 %) the indicator returns
`value=None, status="unknown"`.

Thresholds (GDD base 10 °C and upper cap 30 °C, heat day >= 30 °C, frost <= 0 °C, wet day >= 1 mm, dry spell
>= 10 days) are **team-proposed defaults, not expert-reviewed**. Every one is a keyword argument, so a review can
change them without touching the computation.

Reference ET is FAO-56 Penman-Monteith with daily soil heat flux taken as zero. It is the one indicator here with
no independent published cross-check yet, and is labelled accordingly.

## Files, tables and endpoints

Created:
- `transform/indicators/climate.py` — the indicator functions, their dataclasses and the lineage metadata
- `transform/indicators/tests/test_climate.py` — unit tests, including the hand-computed GDD golden case
- `transform/indicators/__init__.py`, `transform/indicators/tests/__init__.py`

Consumes: the DE's cleaned POWER table (`power_daily`, Phase 4) — not yet in S3 or ClickHouse, so the tests run on
synthetic frames shaped like that contract.

Produces (for the DE to load once the real series exists): one indicator row per field-point, window and
indicator, plus the matching `indicator_lineage` rows built from `INDICATOR_LINEAGE` in the module.

No endpoints, no ClickHouse DDL, no Pandera schema (the DE owns the shared module).

## Steps (in order)

1. Fix the input contract: required columns, units, the `date` column, duplicate and missing-column handling.
2. Write the window/coverage helper that every indicator shares, so the missing-data rule is implemented once.
3. Temperature indicators: GDD (clamped both ends), heat days, frost dates and the frost-free window.
4. Precipitation indicators: seasonal total, longest dry spell, count of dry spells at or above a minimum length.
5. Reference ET: FAO-56 Penman-Monteith, per day and summed over a window.
6. Lineage metadata for every indicator: variables, formula, unit, scale, window, missing-data rule, limitation.
7. Tests, including a hand-computed GDD season and the cases where a null day must not be read as zero.

## Dependencies and interfaces with other roles

- **Upstream, not yet done:** Phase 1 (POWER raw into S3) and the DE's cleaning step. S3 currently holds only
  smoke-test objects and every ClickHouse table is empty, so there is no real series to run against. This task is
  deliberately built and tested against the documented contract instead of waiting.
- **DE:** owes the cleaned `power_daily` table with -999 converted to null, the per-variable missing-date report,
  and the Pandera schema. My coverage counts are only meaningful if nulls really are nulls.
- **DS1:** the same `IndicatorValue` shape should carry the HLS/NDVI features, so the profile and the engine see
  one indicator contract rather than two. To agree before Phase 10.
- **BE:** `GET /fields/{id}/profile` must render `status="unknown"` as "unknown / not assessed", never as 0 or as a
  gap in a chart.

## Data size and subsets

Tiny. One point per unique POWER grid cell (a handful for all 45 fields plus the Marsden site), 12,784 daily rows
per point for 1991-2025. Indicators are computed per window in memory; nothing is downloaded here.

## Risks and open questions

- **Every threshold is unreviewed.** Base 10 °C and a 30 °C cap are the common maize convention, not a local
  calibration; a 30 °C heat-day threshold and a 10-day dry spell are our own choices. They need an agronomist.
- **Scale.** A POWER cell is roughly 50 km across, so two fields in the same cell get identical climate. Every
  output must say so; it is not field measurement and must never be presented as such.
- **Reference ET is unvalidated.** FAO-56 is implemented from the published equations but not yet checked against a
  worked example from the paper, so it is labelled "not independently validated" and the cross-check is listed as
  outstanding. It should not drive any conclusion until that is closed.
- **Frost dates need a season split** to separate the last spring frost from the first autumn one. The default is
  the midpoint of the window, which is right for a calendar-year window and wrong for an arbitrary one; the split
  is therefore an explicit argument.
- The coverage threshold itself (90 %) is a judgement call, not a standard.
