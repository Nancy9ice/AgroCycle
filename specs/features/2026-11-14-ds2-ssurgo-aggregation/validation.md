# Validation: SSURGO soil aggregation for a field

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Hand-computed chain = 2.48 % OM | `test_golden_weighting_chain_matches_hand_computation`, with all three stages written out in a comment above the fixtures | pytest output; `GOLDEN_*` fixtures |
| 2. Horizons clipped to the interval | `test_horizon_is_clipped_to_the_requested_interval`, `test_component_below_the_interval_contributes_nothing`, `test_depth_interval_must_be_positive` | pytest output |
| 3. A null property is not a zero | `test_null_horizon_property_lowers_coverage_rather_than_becoming_zero` | pytest output |
| 4. Null `area_share` returns unknown | `test_a_null_area_share_makes_the_field_unknown`, `test_class_shares_are_unknown_when_the_area_is_not_weighted` | pytest output |
| 5. Horizon-less components stay in the denominator | `test_component_without_horizons_counts_against_depth_coverage` | pytest output |
| 6. Coverage threshold, with coverage still reported | `test_area_coverage_below_the_threshold_is_unknown_but_reported`, `test_a_lower_threshold_accepts_partial_coverage`, `test_property_absent_everywhere_is_unknown` | pytest output |
| 7. Class shares, dominant class, dual groups | `test_class_shares_are_area_and_percent_weighted`, `test_dual_hydrologic_group_is_kept_as_one_class`, `test_class_shares_below_the_threshold_keep_the_shares_but_name_no_dominant` | pytest output |
| 8. Input checks report and raise | `test_check_soil_tables_is_quiet_on_clean_input` plus the six reporting and raising cases | pytest output |
| 9. A field with no map units raises | `test_a_field_with_no_map_units_is_a_geometry_problem` | pytest output |
| 10. Lineage complete and honest | `test_every_soil_property_has_a_complete_lineage_row`, `test_lineage_ids_are_unique`, `test_every_lineage_row_carries_the_survey_caveat`, `test_texture_lineage_says_components_are_not_renormalised` | pytest output; `SOIL_PROPERTY_LINEAGE` |
| Available water storage arithmetic | `test_available_water_storage_sums_thickness_times_awc`, `test_available_water_storage_reports_short_profiles` | pytest output |
| Component-level numeric aggregation | `test_component_property_is_percent_then_area_weighted`, `test_component_property_ignores_components_without_a_value` | pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:**
  - `python -m pytest transform/indicators/tests/test_soil.py -q` -> **31 passed**
  - `python -m pytest transform -q` -> **89 passed, 1 xfailed** (31 soil, 34 climate, 24 Marsden plus its
    documented strict `xfail`)
  - `ruff check` with the DE branch's settings (line-length 100) -> **All checks passed!**, after splitting one
    aliased `dataclasses` import that it flagged
  - `make check` **not run:** the Makefile is on the DE's branch, and `transform/indicators` will need the same
    `testpaths` entry as `transform/marsden` before it covers any of this.
- **Passed:** all ten acceptance criteria. The hand-computed chain returns exactly 2.48 % organic matter, with
  the horizon clipping (25 cm at 4.0 plus 5 cm at 2.0 inside 0-30 cm), the `comppct_r` weighting and the
  `area_share` weighting each contributing a verifiable step. Available water storage over 0-100 cm returns
  15.0 cm for the hand case (50 cm x 0.20 + 50 cm x 0.10).
- **Failed or skipped:**
  - **Not run against real SSURGO data.** S3 holds only smoke-test objects and every ClickHouse table is empty,
    so every test uses synthetic frames shaped like the documented contract. Two risks follow: a column the SDA
    service rejects would change the contract, and `kffact`/`tfact` arrive as strings in some SSURGO releases,
    in which case the numeric aggregator raises rather than coercing. That is deliberate, but it means the
    first real pull may need a decision rather than just a review.
  - **No expert review.** The depth intervals (0-30 cm, 0-100 cm), the 75 % coverage threshold and the choice
    to report a dominant class at all are team judgements. The tests assert the arithmetic, not that the
    conventions are agronomically right.
  - **Texture is not re-normalised.** Clay, sand and silt are aggregated independently, so after weighting they
    need not sum to 100. This is recorded in the lineage rather than corrected, because re-normalising would
    conceal missing horizons. A consumer that assumes they sum to 100 will be wrong.
  - `hydricrating`, `ksat_r`, `dbthirdbar_r` and `cec7_r` are supported by the generic aggregators but have no
    dedicated lineage row yet; they need one before they are shown.
  - The `majcompflag` column is deliberately unused: non-major components are kept in the weighting per the
    source sheet. If the team later wants major components only, that is a new argument and a new decision.
- **Evidence location:** `transform/indicators/soil.py`, `transform/indicators/tests/test_soil.py`. No output
  files: the module is pure functions, so the test run is the evidence.
- **Roadmap exit check met:** **partially — the DS2 soil half only.** The aggregation exists with survey
  caveats and lineage rows stating the mapped-unit scale. Nothing is loaded and there is no Pandera schema;
  both are the DE's half of Phase 4 and blocked on Phase 1.
- **Roadmap tracker updated:** yes, 2026-11-14 (the existing `4 — DS2` row now covers both the climate and the
  soil work)
