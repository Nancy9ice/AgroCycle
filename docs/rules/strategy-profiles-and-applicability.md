# AgroCycle strategy profiles and applicability rules

**Rules version:** 2026-11-14.1  
**Role:** DS2, roadmap Phase 9  
**Review status: NOT EXPERT-REVIEWED.** Every rule below is a conservative team-proposed guardrail, not a universal agronomic threshold (PRD 7.6).

> This file is **generated** from `engine/rules/strategy_rules.py`. Edit the module, then run
> `python -m engine.rules.strategy_rules` from the repository root. A test fails if the two differ.

The Phase 10 decision engine evaluates these rules. This table decides nothing by itself.

## 1. Strategy profiles

### A — Existing system: Two-year maize-soybean

- **Phases:** maize, soybean
- **Why included:** The baseline the farmer already runs and the system every comparison is measured against.
- **Evidence anchor:** Two-year treatment of the Marsden Farm experiment, Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **Operational requirements:**
  - Equipment and markets already in place for maize and soybean
  - Nitrogen purchased as manufactured fertiliser

### B — Diversified option: Three-year maize-soybean-oat/red clover

- **Phases:** maize, soybean, oat_red_clover
- **Why included:** Adds a small-grain and a forage-legume phase, the shortest diversification the Marsden experiment tested.
- **Evidence anchor:** Three-year treatment of the Marsden Farm experiment, Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **Operational requirements:**
  - A use or buyer for oat grain and straw
  - Red clover establishment, usually frost-seeded into the small grain
  - Manure access: the Marsden three-year system received composted manure
  - Equipment and labour for small-grain harvest

### C — Diversified option: Four-year maize-soybean-oat/alfalfa-alfalfa

- **Phases:** maize, soybean, oat_alfalfa, alfalfa
- **Why included:** Adds a small grain and two years of a perennial forage legume, the longest rotation the Marsden experiment tested.
- **Evidence anchor:** Four-year treatment of the Marsden Farm experiment, Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **Operational requirements:**
  - A forage use or buyer for alfalfa across two years of the rotation
  - Alfalfa establishment, multiple cuts per season, and storage or handling for forage
  - Manure access: the Marsden four-year system received composted manure
  - Equipment and labour for small-grain and forage harvest
  - Commitment to keep a quarter of the land out of maize and soybean for two years at a time

## 2. Outcomes: what may and may not be said

An outcome marked **not claimable** must be reported as unknown / not assessed. It is listed so the engine has something explicit to return.

### applied_n_reduction — Lower applied nitrogen (manufactured plus manure)

- **Status:** claimable · evidence type: `experimental`
- **Source:** Davis et al. (2012) supplementary management records [S10]; reproduced in AgroCycle reproduction, transform/marsden (roadmap Phase 6)
- **May be said:** In the Marsden experiment, nine-year applied N averaged 74.5, 56.6 and 40.8 kg N/ha/yr for the two-, three- and four-year systems, and manufactured N alone was 74.5, 16.7 and 10.9. These are rotation-area-weighted averages from one site over nine seasons.
- **May not be said:** Not a prediction for another field, and not a reduction in total nitrogen input: manure supplied much of the diversified systems' nitrogen, and biological fixation is excluded from the figure altogether. Never call it 'total N'.

### herbicide_reduction — Lower herbicide active ingredient per hectare per year

- **Status:** claimable · evidence type: `experimental`
- **Source:** Davis et al. (2012) supplementary management records [S10]; reproduced in AgroCycle reproduction, transform/marsden (roadmap Phase 6)
- **May be said:** In the Marsden experiment, herbicide active ingredient averaged 1.925, 0.261 and 0.195 kg ai/ha/yr for the two-, three- and four-year systems, about 86-90 % lower in the diversified systems.
- **May not be said:** Mass of active ingredient is not toxicity, exposure or environmental risk. Insecticides applied in 2007-2009 are excluded. Not a prediction for another field.

### yield_parity — Maize and soybean yields matched or exceeded the two-year system

- **Status:** claimable · evidence type: `published`
- **Source:** Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **May be said:** The publication reports that maize and soybean yields in the diversified systems matched or exceeded the two-year system. This is attributed to the paper.
- **May not be said:** AgroCycle has not reproduced it: the retrieved supplement holds no plot-level yield tables. Do not present it as an AgroCycle finding or imply a yield outcome for another field.

### profitability_parity — No significant difference in net returns between systems

- **Status:** claimable · evidence type: `published`
- **Source:** Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **May be said:** The publication reports no significant difference in net returns between the systems, under its own price and cost assumptions.
- **May not be said:** Not a profitability calculation for this farm. PRD 9 forbids computing profitability without suitable yield, input-cost, machinery, labour, transport and price data with explicit assumptions, and none of that is present.

### weed_suppression — Weed suppression in the diversified systems

- **Status:** claimable · evidence type: `published`
- **Source:** Davis et al. (2012), PLOS ONE 7(10): e47149 [S09]
- **May be said:** The publication reports its own weed findings, which are attributed to it and not recomputed.
- **May not be said:** The reproduced records cover herbicide applied, not weed populations or weed pressure. Do not infer weed control on another field.

### soil_carbon_change — Soil carbon gain

- **Status:** **NOT claimable** · evidence type: `none`
- **Source:** none
- **May be said:** Nothing. Report as unknown / not assessed.
- **May not be said:** PRD 7.4 and 4.4: the retrieved management records do not demonstrate soil-carbon gains, and no AgroCycle data source measures soil carbon on a field.

### erosion_reduction — Measured erosion reduction

- **Status:** **NOT claimable** · evidence type: `none`
- **Source:** none
- **May be said:** Nothing. Report as unknown / not assessed.
- **May not be said:** PRD 7.4: not demonstrated by the retrieved records. Erosion susceptibility is a conditional P1 item and needs a defensible method before anything is shown.

### nitrate_leaching_reduction — Measured nitrate-leaching reduction

- **Status:** **NOT claimable** · evidence type: `none`
- **Source:** none
- **May be said:** Nothing. Report as unknown / not assessed.
- **May not be said:** PRD 7.4: not demonstrated by the retrieved records. Lower applied nitrogen is an input difference, not a measured leaching outcome.

### forage_supply — Forage produced for on-farm use or sale

- **Status:** **NOT claimable** · evidence type: `none`
- **Source:** none
- **May be said:** Nothing quantitative. That the four-year system includes two alfalfa years is a property of the rotation definition, not an evidenced forage yield.
- **May not be said:** No forage yield, quality or feed value is available from any AgroCycle source. See the research_needed crop claims.

## 3. Crop characteristics

1 of 8 claims are sourced. The rest are marked **research needed** and must not be shown as explanations until a citable source exists (PRD 7.5). They are listed rather than omitted so the gap is visible.

### Sourced

| Claim id | Crop | Claim | Evidence | Source | Note |
|---|---|---|---|---|---|
| marsden_manure_to_diversified | red_clover, alfalfa | The Marsden three- and four-year systems received composted manure, so their nitrogen comparison depends on manure being available. | `experimental` | Davis et al. (2012) supplementary management records [S10]; reproduced in AgroCycle reproduction, transform/marsden (roadmap Phase 6) | Manure N is total N in composted manure, not plant-available N. Text S1 places the application on the clover and alfalfa phases. |

### Research needed

| Claim id | Crop | Claim | What is needed |
|---|---|---|---|
| legume_biological_fixation | red_clover, alfalfa | Legumes may contribute biologically fixed nitrogen under suitable conditions. | PRD 7.5 names this as an example of a potential mechanism, not a measured outcome for a field. No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. The magnitude depends on species, establishment, management, soil and climate, and the Marsden applied-N figures exclude fixation entirely. |
| living_cover_bare_periods | oat, red_clover, alfalfa | A small grain or forage phase may provide living cover during otherwise bare periods. | Listed in PRD 7.5 as a potential mechanism. No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. DS1's bare-field windows (Phase 5) could show cover timing for a field, but that is an observation of this field, not evidence that the rotation causes it. |
| rooting_depth_soil_structure | alfalfa | Deeper or different rooting patterns may affect soil structure. | Listed in PRD 7.5 as a potential mechanism. No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. |
| forage_feed_value | alfalfa, oat | Forage crops may provide feed value. | Listed in PRD 7.5 as a potential mechanism. No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. No forage yield or quality figure is available from any AgroCycle source. |
| alfalfa_drainage_sensitivity | alfalfa | Alfalfa is sensitive to poor drainage and waterlogging. | No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. Rule applicability_alfalfa_drainage depends on this claim: if no source is found, withdraw that rule rather than relying on it. |
| oat_season_window | oat | Oat needs an early-spring planting window and matures mid-season. | No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. Rule applicability_oat_season_length depends on this claim: if no source is found, withdraw that rule rather than relying on it. |
| rotation_disease_pest_effects | maize, soybean, oat, red_clover, alfalfa | Rotation length may affect disease and pest pressure. | No agronomic source retrieved yet. Needs a citable source (for example Iowa State University Extension agronomy guidance or peer-reviewed Iowa rotation literature) before this is shown as an explanation. Until sourced, the disease and pest dimension of the comparison is reported as not assessed rather than left blank. |

## 4. Outcome-specific applicability rules

Applicability is assessed **per outcome**, never per strategy: lack of manure access limits the manure-dependent nitrogen comparison but does not invalidate the herbicide comparison (PRD 7.6). `all_outcomes` means the rule applies to the whole comparison.

Effects: `in_domain`, `qualified` (show it, with the reason), `out_of_domain` (do not offer it), `abstain_outcome` (withhold pending data).

| Rule id | Outcome | Condition | Effect | Basis | Rationale |
|---|---|---|---|---|---|
| applicability_manure_access_applied_n | `applied_n_reduction` | The farmer has no access to manure. (`manure_access` equals `False`) | **out_of_domain** | experimental_context | Manure supplied 39.9 and 29.9 kg N/ha/yr of the three- and four-year systems' applied nitrogen. Without manure the diversified systems as tested at Marsden cannot be reproduced, so the applied nitrogen comparison does not transfer. |
| applicability_manure_unknown_applied_n | `applied_n_reduction` | Manure access has not been stated. (`manure_access` is_unknown `None`) | **abstain_outcome** | team_proposed | Missing data is not evidence of access (PRD 8.5). The outcome is withheld until the farmer says, rather than assumed either way. |
| applicability_crop_history_baseline | `all_outcomes` | The field's recent crop history is not a maize-soybean rotation. (`crop_history_is_maize_soybean` equals `False`) | **out_of_domain** | experimental_context | Every Marsden comparison is measured against a two-year maize-soybean baseline. A field in continuous maize, pasture or a non-rotation sequence is outside the experiment's domain, so the comparison is not offered for it. |
| applicability_crop_history_unknown | `all_outcomes` | Crop history could not be classified. (`crop_history_is_maize_soybean` is_unknown `None`) | **abstain_outcome** | team_proposed | A field whose CDL history is unavailable or low-confidence cannot be placed in or out of the domain, so the engine abstains rather than assuming the baseline. |
| applicability_outside_demo_counties | `all_outcomes` | The field lies outside Story or Boone County, Iowa. (`county` not_in `('Story', 'Boone')`) | **qualified** | team_proposed | The MVP's soil, climate and validation resources were assembled for these two counties (PRD 2.3). A field elsewhere is not excluded, but the comparison is qualified because the supporting context was not assembled for it. |
| applicability_climate_distance_gdd | `all_outcomes` | The field's growing-season GDD differs from the Marsden site by more than 300 degree-days C. (`gdd_season_difference_vs_marsden` gt `300.0`) | **qualified** | team_proposed | A field with a materially different heat accumulation may not support the same crop sequence. The band is deliberately wide and the effect is a qualification, not exclusion, because no published basis for a threshold was available. This is the weakest rule in the table. |
| applicability_climate_unknown | `all_outcomes` | The climate comparison with the Marsden site could not be computed. (`gdd_season_difference_vs_marsden` is_unknown `None`) | **qualified** | team_proposed | An unknown climate distance is not a close one. The comparison may still be shown, qualified, with the gap named. |
| applicability_alfalfa_drainage | `strategy_c_feasibility` | The field's dominant SSURGO drainage class is poorly or very poorly drained. (`dominant_drainage_class` in `('Very poorly drained', 'Poorly drained')`) | **qualified** | team_proposed | Depends on crop claim alfalfa_drainage_sensitivity, which is research_needed. The rule is recorded so the question is visible and reviewable; if no source is found it must be withdrawn rather than applied. SSURGO also does not record installed tile drainage, which could change the answer for a given field. |
| applicability_oat_season_length | `strategy_b_feasibility` | The field's frost-free window is shorter than 120 days. (`frost_free_days` lt `120`) | **qualified** | team_proposed | Depends on crop claim oat_season_window, which is research_needed. Recorded for review; withdraw if unsourced. The frost-free figure is a POWER grid value, not a field measurement. |
| applicability_forage_outlet_strategy_c | `strategy_c_feasibility` | There is no on-farm forage use and no buyer for alfalfa. (`forage_use_or_buyer` equals `False`) | **out_of_domain** | team_proposed | The four-year rotation grows alfalfa for two years of four. With no use and no buyer the rotation is not operationally available, whatever the environmental evidence says (PRD 9). |
| applicability_oat_outlet_strategy_b | `strategy_b_feasibility` | There is no on-farm use and no buyer for oat grain or straw. (`oat_use_or_buyer` equals `False`) | **qualified** | team_proposed | A single small-grain phase with no outlet is a real feasibility problem but a smaller commitment than two years of alfalfa, so it qualifies the option rather than removing it (PRD 9). |
| applicability_machinery_small_grain | `strategy_b_feasibility` | Neither small-grain equipment nor a contractor is available. (`small_grain_equipment_or_contractor` equals `False`) | **qualified** | team_proposed | Equipment and labour for small-grain harvest are an operational requirement of both diversified options and a first-class constraint, not explanatory text (PRD 9). |
| applicability_indicator_coverage | `all_outcomes` | One or more required profile indicators came back unknown. (`required_indicators_all_known` equals `False`) | **abstain_outcome** | team_proposed | PRD 8.5: missing data is never evidence of no risk or no benefit. An indicator that returned 'unknown' withholds the dimensions that depend on it instead of being read as neutral. |

## 5. Permitted decision outcomes (PRD 8.3)

| Outcome | When it is appropriate |
|---|---|
| `strategy_worth_exploring` | Evidence and the farmer's priorities make the option a reasonable candidate for further local evaluation. Not a prescription. |
| `qualified_comparison` | Evidence supports comparing strategies but is insufficient to identify a preferred option. |
| `abstention` | Evidence is missing, inadequate, contradictory, or outside the supported applicability domain. |

The engine must not force a ranking because a user expects one.

## 6. Known weaknesses of this table

- No rule has been reviewed by an agricultural expert. The roadmap asks for review by an Iowa-knowledgeable adviser; the farmer reviewer is Nigerian and can sanity-check practicality (machinery, labour, markets) but not Iowa agronomy.
- `applicability_climate_distance_gdd` has no published basis for its 300 degree-day band. It is wide and only qualifies the comparison, but it is a judgement.
- `applicability_alfalfa_drainage` and `applicability_oat_season_length` depend on crop claims that are research needed. If no source is found, withdraw those rules rather than applying them.
- A rule carries one condition, so interactions between conditions cannot be expressed. If review shows interactions matter, Phase 10 needs a richer form.
- Most crop characteristics are unsourced, so the "why this crop" explanation is thin by design rather than complete.
