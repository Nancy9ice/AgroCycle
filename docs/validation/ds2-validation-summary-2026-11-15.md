# AgroCycle validation summary

**Date:** 15 November 2026 · **Author:** DS2 · **Rules version:** `2026-11-15.2` ·
**Engine run:** `ds2-validation-f577400f9329` · **Indicator run:** `ds2-indicators-7c2b6c30601c`

What was tested, what the result was, what it does not establish, and what was not tested at all. Every
figure below is recomputed from the loaded database or a committed artefact; the command or query is given so
any of it can be checked.

**The test set is 45 team-drawn demonstration polygons in two Iowa counties.** Results are reported as counts.
They are indicative, not statistically strong. No percentage of accuracy, no significance claim, and
field-years are not treated as independent samples, because pixels within a field are correlated and the same
field appears in eleven seasons.

> **Superseded in part (added when the READMEs were updated).** This is DS2's record as written on 15 November
> for rules version `2026-11-15.2`, and it is kept as written. Two things have changed since:
>
> - The climate rule `applicability_climate_distance_gdd` (300 degree-days), listed in section 2 as never firing,
>   was **withdrawn**, and two machinery rules for Strategy C were added. The rules version is now
>   `2026-11-15.5`, with 14 applicability rules.
> - The sweep now gives **26 worth exploring and 19 abstaining** with every constraint stated, and **26
>   qualified comparisons and 19 abstentions** with no manure or nothing stated. Six of the 14 rules never fire.
>   The tables in section 1 (27 and 18) and the list in section 2 describe the earlier version.
>
> Re-run `uv run python -m engine.sweep` for the current figures. The validation matrix
> (`engine/tests/test_validation_matrix.py`) has not yet been signed off by DS1 or the backend engineer.

---

## 1. The decision engine over the whole test set

`uv run python -m engine.sweep` · loaded as `engine_test_set` (135 rows = 45 fields × 3 scenarios)

| Constraint scenario | Worth exploring | Qualified comparison | Abstention |
|---|---:|---:|---:|
| Every constraint stated | 27 | 0 | 18 |
| No manure | 0 | 27 | 18 |
| Nothing stated | 0 | 27 | 18 |

**This is the intended behaviour, and the abstentions are the correct answer.** The 18 are the fields whose
crop history is not a maize–soybean rotation (11 continuous corn, 6 pasture-hay, 1 mixed, from
`crop_rotation`). Every Marsden comparison is measured against a two-year maize–soybean baseline, so for
those fields the engine declines rather than answering.

The scenarios matter more than any single row. Run once with every constraint stated, the engine looks as
though it always says yes. Withhold manure — a fact many farmers would not volunteer — and all 27 drop to a
qualified comparison, because the nitrogen comparison depends on manure the diversified systems received.
That the result moves with the evidence is the thing being demonstrated.

**What this does not establish.** Nothing here shows the engine is *right*. It shows it is consistent,
deterministic and that its outputs follow its documented rules. Whether the rules themselves are good
agronomy is unreviewed — see section 5.

## 2. Which rules actually fire

Five of fourteen applicability rules fire on this test set. **Nine never fire.** A rule that never fires is
either a guardrail for input this test set does not contain, or a threshold that is wrong, and the difference
matters.

| Never fires | Why |
|---|---|
| `applicability_climate_distance_gdd` | threshold 300 degree-days; the largest difference measured is **43**. Untested, and the band may be far too wide. |
| `applicability_outside_demo_counties` | every field is in Story or Boone by construction. Guardrail for input we do not have. |
| `applicability_crop_history_unknown` | CDL classified every field. Guardrail. |
| `applicability_climate_unknown` | POWER returned a complete series for every field. Guardrail. |
| `applicability_indicator_coverage` | no indicator came back `unknown`. See section 4. |
| `applicability_forage_outlet_strategy_c`, `applicability_oat_outlet_strategy_b`, `applicability_machinery_small_grain` | fire only when a farmer answers "no"; the sweep's scenarios cover stated-yes and unstated. |

Two rules were **withdrawn** on 15 November rather than left in: `applicability_alfalfa_drainage` fired on all
27 in-domain fields, so it separated nothing while looking like a finding, and `applicability_oat_season_length`
could never fire (threshold 120 frost-free days against a measured minimum of 159). Both rested on crop claims
no source was found for. The drainage data is still shown to the farmer; what was removed is our inference
from it.

## 3. The Marsden reproduction

`marsden_reconciliation` (20 checks) · `uv run pytest transform/marsden -q` (44 tests, 1 strict xfail)

| Status | Count |
|---|---:|
| MATCH | 17 |
| WITHIN_SEM | 1 |
| UNRECONCILED | 1 |
| INFO | 1 |

As loaded in `marsden_management`, the nine-year means are applied N **74.5 / 56.556 / 40.806** kg N/ha/yr and
herbicide **1.925 / 0.261 / 0.195** kg ai/ha/yr for the two-, three- and four-year systems. All twelve PRD
targets match.

**The one unreconciled check is deliberate and open.** The paper's text gives two-year manufactured N as
80 ± 3; Table S3 weights to 74.5. The gap isolates to 2011, and reading that year as the maize phase alone
gives 80.7. We record the diagnostic, do not apply it, and hold a strict `xfail` so the disagreement cannot be
forgotten. The cause is unknown and only the authors could settle it.

**What this does not establish.** That the Marsden results apply to any field in the test set. It establishes
that our arithmetic reproduces their records.

## 4. Indicator coverage

`field_indicators` — 4,410 rows, 45 fields, 18 indicators (9 climate × 11 seasons, 9 soil)

| Status | Rows |
|---|---:|
| available | 4,390 |
| partial | 20 |
| unknown | 0 |

Every indicator in use has a lineage row: a left join of `field_indicators` to `indicator_lineage` returns no
orphan. `indicator_lineage` holds 25 records; `data_sources` holds 10.

The 20 partial rows are five fields where SSURGO coverage is genuinely short (96.72 % to 99.52 % of mapped
area or depth), and each row states its own coverage.

**Zero `unknown` rows is a limitation, not a triumph.** The missing-data behaviour the whole design rests on —
null never counting as zero, a missing day breaking a dry spell, an absent area share refusing to be
weighted — is exercised by **unit tests, not by this data**. The POWER and SSURGO pulls were complete. So the
abstention paths are verified in principle and unexercised in practice, and a future field with real gaps is
untested territory.

## 5. What has not been validated

Stated as plainly as the sections above, because a summary that lists only successes is not a validation.

**The crop-history classification is not validated.** The roadmap asks for a CDL confusion matrix with correct
terminology. `scripts/cdl_confusion_matrix.py` compares CDL **with itself across years** — year-to-year
consistency — which is an internal consistency check, not agreement with an independent classification, and
certainly not accuracy. It has also not been run: there is no `data/out/phase3/`. The 45 field classes
therefore rest on documented, versioned rules that have been self-reviewed and never checked against anything
external. This matters because the classification decides which 18 fields the engine declines to answer for.
**Owner: DS1.**

**No applicability rule, indicator threshold or depth interval has been reviewed by an agronomist.** GDD base
and cap, the 30 °C heat day, the 10-day dry spell, the 0–30 cm and 0–100 cm intervals, the 90 % coverage rule,
every rule in the table: all team-proposed. The table says so on every row.

**Reference evapotranspiration is not independently validated.** Implemented from the published FAO-56
equations and physically sensible, never checked against a worked example. Its radiation input comes from a
1-degree grid, making it our least local indicator.

**POWER rainfall runs about 11 % low** against the Marsden station record for 2003–2011 (−92 mm per season,
lower in 7 of 9 years; temperature agreed within 1 °C in 8 of 9 years). Dry spells computed from it are more
likely overstated than understated. Full comparison in `docs/sources/ds2-first-pull-review-2026-11-14.md`.

**There is no farmer feedback log yet, and no Iowa stakeholder feedback at all.** The farmer reviewer is
Nigerian, not an Iowa user; his feedback will cover usability and general agronomic sense and must be labelled
as such. **No adoption claim and no local-impact claim is supported by anything in this project.**

**Seven of eight crop characteristics remain unsourced.** Nitrogen fixation, living cover, rooting and soil
structure, forage value, alfalfa drainage sensitivity, the oat season window and rotation effects on disease
and pest pressure are all marked "research needed". Only the manure dependence of the diversified systems is
sourced.

**The test set is not independent of its own design.** The 45 polygons were drawn by the team from uniform CDL
blocks, so the fields are cleaner than real farm boundaries, and the in-domain and out-of-domain split was
chosen rather than sampled.

## 6. How to re-run any of this

```
uv run python -m transform.indicators.runner     # indicators from the raw pulls
uv run python -m engine.sweep                    # engine over all 45 fields
uv run python -m engine.load_test_set --yes      # load the audit
uv run pytest -q --ignore=tests/live             # 445 tests
```

`tests/live` needs a ClickHouse user with `DROP TABLE`; without it those tests fail on teardown and leave
scratch tables behind.
