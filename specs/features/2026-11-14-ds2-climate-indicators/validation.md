# Validation: Climate indicators from NASA POWER daily meteorology

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Golden GDD season = 36.0 | `test_gdd_golden_season_matches_hand_computation`, with the five days and their arithmetic written out in the test | pytest output; `GOLDEN_ROWS` in the test file |
| 2. GDD never negative; honours base and cap | `test_gdd_cold_day_contributes_zero_not_a_negative`, `test_gdd_respects_a_different_base_and_cap` | pytest output |
| 3. A null day is not a zero | `test_mean_temperature_does_not_pull_a_null_day_towards_zero`, `test_null_day_breaks_a_dry_spell_instead_of_extending_it`, `test_absent_date_breaks_a_dry_spell`, `test_gdd_reports_the_denominator_when_a_day_is_null` | pytest output |
| 4. Short coverage returns unknown with a reason | `test_gdd_is_unknown_when_coverage_is_short`, `test_frost_window_is_unknown_when_coverage_is_short`, `test_reference_et_is_unknown_when_one_input_is_missing` | pytest output |
| 5. Denominators always present | asserted on every result in the tests above | pytest output |
| 6. Heat-day threshold inclusive, data-only | `test_heat_days_threshold_is_inclusive`, `test_heat_days_counts_only_days_with_data` | pytest output |
| 7. Frost span only when bounded on both sides | `test_frost_window_finds_both_dates_and_the_span`, `test_frost_window_is_unknown_without_a_frost_on_both_sides`, `test_frost_window_accepts_an_explicit_split` | pytest output |
| 8. Bad input raises rather than returning a number | `test_duplicate_date_is_rejected`, `test_missing_variable_column_is_rejected`, `test_missing_date_column_is_rejected`, `test_window_end_before_start_is_rejected`, `test_gdd_rejects_a_cap_at_or_below_the_base`, `test_dry_spell_count_rejects_a_zero_minimum` | pytest output |
| 9. ET0 physically sensible | `test_et0_summer_day_is_physically_plausible`, `test_et0_rises_with_radiation_wind_and_dryness`, `test_et0_is_never_negative_in_midwinter`, `test_extraterrestrial_radiation_follows_the_season`, `test_et0_pins_the_current_implementation` | pytest output |
| 10. Lineage complete, labels honest | `test_every_indicator_has_a_complete_lineage_row`, `test_lineage_ids_are_unique_and_cover_every_indicator`, `test_unreviewed_thresholds_are_declared_in_the_lineage`, `test_reference_et_declares_that_it_is_not_validated` | pytest output; `INDICATOR_LINEAGE` |
| Precipitation and dry-spell arithmetic | `test_precipitation_total_sums_the_window`, `test_longest_dry_spell_finds_the_longest_run`, `test_dry_spell_count_applies_the_minimum_length` | pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:**
  - `python -m pytest transform/indicators -q` -> **34 passed**
  - `python -m pytest transform -q` -> **58 passed, 1 xfailed** (the 34 here plus the 24 Marsden tests and its
    documented strict `xfail`)
  - `ruff check` with the DE branch's settings (line-length 100) -> **All checks passed!**
  - `make check` **not run here:** the Makefile is on the DE's branch, which this branch has not merged. The
    two `pyproject.toml` changes it needs (`python-docx`, and `transform` in `testpaths`) are still outstanding,
    and `transform/indicators` will need the same `testpaths` entry as `transform/marsden`.
- **Passed:** all ten acceptance criteria. The golden GDD season returns exactly 36.0 degree-days C from the
  hand-computed five days. The missing-data rule holds in all four of its forms: a null day lowers the
  denominator, does not pull the mean towards zero, and ends a dry spell rather than extending it, and an absent
  date behaves identically to a null one.
- **Failed or skipped:**
  - **Reference ET has no independent cross-check.** It is implemented from the published FAO-56 equations and
    passes physical-sanity tests (non-negative, single-figure mm/day for a central-Iowa July day, rising with
    radiation, wind and dryness, seasonal extraterrestrial radiation), but it has **not** been checked against a
    worked example from FAO-56 itself. `test_et0_pins_the_current_implementation` is a change detector, not a
    correctness check, and says so in a comment. Until the cross-check is done, `reference_et_total` carries
    "not independently validated" in its lineage and must not drive a conclusion. **This is the one piece of
    this task I could not validate, and the limitation is recorded in the output rather than waved away.**
  - **Every threshold is unreviewed.** GDD base 10 C and cap 30 C, heat day 30 C, frost 0 C, wet day 1 mm, dry
    spell 10 days, and the 90 % coverage rule are team-proposed. The tests assert the arithmetic, not that the
    thresholds are agronomically right. Phase 9's expert review is where that should be settled; until then
    every affected lineage row says "not expert-reviewed".
  - **Not run against real data.** S3 holds only smoke-test objects and every ClickHouse table is empty, so
    there is no POWER series yet. The tests use synthetic frames shaped like the documented contract. The first
    real pull is therefore still an open review step, and a mismatch between this contract and POWER's actual
    response is a live risk.
  - No golden test for SSURGO or for seasonal windows per field; both are separate tasks.
- **Evidence location:** `transform/indicators/climate.py`, `transform/indicators/tests/test_climate.py`.
  No output files: the module is pure functions, so its evidence is the test run.
- **Roadmap exit check met:** **partially — the DS2 half only.** The indicators exist with lineage rows, each
  stating its grid scale, and the golden-file test for a hand-computed indicator passes. They are **not** loaded
  and there is no Pandera schema, both of which are the DE's half of Phase 4 and depend on Phase 1 landing
  first. The tracker therefore shows Phase 4 split by role.
- **Roadmap tracker updated:** yes, 2026-11-14
