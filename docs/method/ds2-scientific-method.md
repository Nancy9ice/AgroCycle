# AgroCycle — scientific method

One page on how AgroCycle reaches a conclusion, what each number does and does not establish, and where it
refuses to answer. Written by DS2 for roadmap Phase 15. Every figure here is reproducible from the repository.

## 1. The question

> Given a field currently under a two-year maize–soybean rotation, what can available environmental, soil,
> crop and experimental evidence tell a farmer or adviser about **exploring** that system and two diversified
> alternatives — and what cannot be established?

The second half of that question carries equal weight. AgroCycle is decision support, not an agronomist: it
compares, qualifies or abstains, and it never ranks the strategies.

## 2. What is compared

| Strategy | Rotation |
|---|---|
| A | Two-year maize–soybean |
| B | Three-year maize–soybean–oat/red clover |
| C | Four-year maize–soybean–oat/alfalfa–alfalfa |

These are the systems of the Marsden Farm experiment (Davis et al. 2012, PLOS ONE 7(10): e47149). They are
comparison scenarios, not prescriptions, and not proof that the same outcomes occur on another field.

## 3. Evidence, and the label on every number

Sources differ in method, scale and strength, so they are never interchangeable. Every output carries one of:
`observed`, `derived`, `classified`, `survey`, `model_reanalysis`, `experimental`, `published`, `assumption`.

| What | Source | Label | Scale |
|---|---|---|---|
| Temperature, rainfall, GDD, frost, dry spells, reference ET | NASA POWER daily | `model_reanalysis` | ~0.5° × 0.625° grid cell, about 50 km — **not** a field measurement |
| Organic matter, texture, pH, available water, drainage, slope | SSURGO via Soil Data Access | `survey` | Mapped soil units — **not** a sample of this field |
| Crop history | USDA CDL | `classified` | 30 m classification, with its own error |
| Applied nitrogen, herbicide active ingredient | Marsden supplementary records, reproduced here | `experimental` | One research site, nine seasons |
| Yields, net returns, weed findings | Davis et al. 2012, attributed | `published` | Reported by the paper, not recomputed |

Two fields in the same POWER cell receive identical climate. That is a property of the data, stated plainly,
not a defect to smooth over.

## 4. What was reproduced, and the one gap

From the supplementary records, rebuilt with the equal-phase weighting of Text S1 (each land unit divided
equally among its crop phases; the nine-year value is the mean of the annual values):

| Rotation | Manufactured N | Manure N | **Applied N** | **Herbicide** |
|---|---:|---:|---:|---:|
| Two-year | 74.5 | 0.0 | **74.5** | **1.925** |
| Three-year | 16.7 | 39.9 | **56.6** | **0.261** |
| Four-year | 10.9 | 29.9 | **40.8** | **0.195** |

kg N/ha/yr and kg active ingredient/ha/yr. All twelve targets reconcile.

**Applied N, never "total N".** It is manufactured plus manure and **excludes biological nitrogen fixation**,
which the paper reports as substantial. Manure supplied most of the diversified systems' nitrogen, so the
reduction is not a reduction in nitrogen supplied to the crop.

**One documented disagreement.** The paper's text gives two-year manufactured N as 80 ± 3; Table S3 weights to
74.5. The gap isolates to 2011 and reading that year as the maize phase alone gives 80.7. We record the
diagnostic, do not apply it, and hold the disagreement open with a deliberately failing test so it cannot be
forgotten.

## 5. How missing data is treated

**Unknown is not neutral, and never favourable.** The rule runs through every layer:

- A null day lowers an indicator's valid-day count; it never counts as zero. A missing rainfall day **breaks**
  a dry spell rather than extending it, because an unknown day cannot be assumed dry.
- Every indicator reports `days_valid` / `days_expected`; below 90 % coverage it returns `unknown` with a
  reason rather than a number.
- A soil map unit with no area share makes the field value `unknown`. An equal split would invent a soil map.
- A component with no horizon data stays in its map unit's denominator, so a field that is partly a pond
  cannot report the organic matter of its dry part as the whole field's.
- An unanswered farmer question is neither yes nor no. "Not sure" about manure withholds the nitrogen
  comparison instead of assuming access.

## 6. From evidence to a conclusion

A versioned rule table (`docs/rules/strategy-profiles-and-applicability.md`) holds the strategy profiles, what
may and may not be said for each outcome, the crop claims, and 16 applicability rules. The engine evaluates
it; it decides nothing itself. Every conclusion names the rule that produced it.

**Applicability is assessed per outcome, never per strategy.** No access to manure takes the nitrogen
comparison out of domain and leaves the herbicide comparison untouched, because only one of them depends on
manure.

Three results are permitted, and no others:

| Outcome | When |
|---|---|
| Strategy worth exploring | A reasonable candidate for local evaluation. Not a prescription. |
| Qualified comparison | The strategies can be compared but not separated. |
| Abstention | Evidence missing, inadequate, contradictory, or outside the supported domain. |

**No composite score and no ranking.** Scoring would require weights whose components, evidence basis and
sensitivity we cannot justify, so farmer priorities are recorded and shown rather than weighted. A test
asserts the result cannot contain a field named score, rank, winner or recommendation.

## 7. What AgroCycle will not claim

- **Soil carbon, measured erosion, nitrate leaching.** No source measures them on a field. They appear in the
  rule table as outcomes that are explicitly *not claimable*, so the app returns "not assessed" rather than
  silence a later contributor might fill.
- **Profitability.** Not calculable without yield, input-cost, machinery, labour, transport and price data
  with explicit assumptions. The paper's own finding of no significant difference in net returns is shown,
  attributed.
- **Yields.** Reported by the paper, not reproduced: the supplement has no plot-level yield tables.
- **Mechanisms.** Seven of eight crop characteristics — nitrogen fixation, living cover, rooting and soil
  structure, forage value — are marked *research needed*, because no citable agronomic source was retrieved.
  They are listed rather than written, so the gap is visible.

## 8. How it is checked

- **201 automated tests**, one deliberately failing (the 2011 gap above).
- **Golden files computed by hand**: a five-day growing-degree-day season (36.0 °C-days) and a two-map-unit
  soil weighting chain (2.48 % organic matter).
- **Reproducibility**: raw inputs verified against SHA-256 manifests before every run; identical inputs give
  byte-identical outputs; Pandera schemas stop a drifted table before it is written.
- **Against independent data**: POWER was compared with the Marsden station record for 2003–2011. Temperature
  agreed within 1 °C in eight of nine years; **precipitation ran about 11 % low**, so POWER rainfall is not
  compared with station-based thresholds and dry spells are flagged as more likely overstated. That finding
  is recorded in the lineage of the affected indicators.

## 9. Known weaknesses

Stated here rather than discovered later.

1. **No agronomic expert has reviewed any threshold or rule.** GDD base and cap, the 30 °C heat day, the
   10-day dry spell, the 90 % coverage rule, every applicability rule: all team-proposed.
2. **Reference evapotranspiration is not independently validated.** Implemented from the published FAO-56
   equations and physically sensible, but never checked against a worked example. Its radiation input comes
   from a 1-degree grid, making it the least local indicator.
3. **Marsden is one site over nine seasons.** Applicability rules compare field context with experimental
   context, but transferability remains a judgement.
4. **Demo fields are team-drawn polygons**, not real farm boundaries, and are labelled `demo`.
5. **The farmer reviewer is Nigerian, not an Iowa user.** His feedback covers usability and general agronomic
   sense. We have no Iowa stakeholder feedback, and claim none.
6. **Two rules rest on unsourced claims** (alfalfa drainage sensitivity, oat season window). They may only
   qualify a comparison, and each says it must be withdrawn if no source is found.

## 10. Where to check any of this

| Claim | Where |
|---|---|
| Marsden reproduction | `transform/marsden/` — 44 tests, plus the Pandera schemas that gate the load |
| Climate indicators | `transform/indicators/climate.py` — 34 tests |
| Soil aggregation | `transform/indicators/soil.py` — 31 tests |
| Rule table | `docs/rules/strategy-profiles-and-applicability.md`, generated from `engine/rules/` — 37 tests |
| Decision engine | `engine/decision.py` — 37 tests |
| First-pull review | `docs/sources/ds2-first-pull-review-2026-11-14.md` |
| Provenance of every indicator | the `INDICATOR_LINEAGE` records, loaded into `indicator_lineage` |
