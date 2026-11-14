# Validation: Strategy profiles, crop characteristics and outcome-specific applicability rules

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Three complete profiles, manure declared | `test_three_strategies_match_the_prd_comparison`, `test_every_profile_is_complete`, `test_both_diversified_options_declare_the_manure_requirement` | pytest output; document section 1 |
| 2. Forbidden outcomes present and closed | `test_forbidden_outcomes_are_present_and_closed` | pytest output; document section 2 |
| 3. Claimable outcomes sourced and correctly typed | `test_claimable_outcomes_name_an_evidence_type_and_a_source`, `test_reproduced_outcomes_are_experimental_and_published_ones_are_not`, `test_every_outcome_says_what_may_not_be_said` | pytest output |
| 4. Crop claims sourced or research needed | `test_every_crop_claim_is_either_sourced_or_marked_research_needed`, `test_unsourced_claims_say_what_kind_of_source_is_needed`, `test_the_only_sourced_claim_is_the_one_marsden_supports` | pytest output; document section 3 |
| 5. Rules structurally valid and unique | `test_every_rule_is_structurally_valid`, `test_rule_ids_are_unique`, `test_unknown_conditions_carry_no_value` | pytest output |
| 6. No rule claims expert review | `test_no_rule_claims_to_be_expert_reviewed` | pytest output |
| 7. Manure rules touch only the nitrogen outcome | `test_manure_rules_do_not_touch_the_herbicide_outcome` | pytest output |
| 8. No rule on a forbidden outcome | `test_no_rule_applies_to_a_forbidden_outcome` | pytest output |
| 9. Missing data never favourable | `test_missing_data_abstains_rather_than_being_read_as_favourable` | pytest output |
| 10. Rules on unsourced claims qualify only, and say so | `test_rules_resting_on_unsourced_claims_say_so_and_name_the_claim` | pytest output |
| 11. The weakest rule admits it | `test_the_weakest_rule_admits_it` | pytest output |
| 12. Operational rules: only one removes an option | `test_operational_rules_cite_the_feasibility_requirement`, `test_only_the_forage_outlet_rule_removes_an_option_on_operational_grounds` | pytest output |
| 13. Vocabularies match the PRD and the mission | `test_decision_outcomes_are_exactly_the_three_the_prd_permits`, `test_evidence_types_match_the_mission_label_set`, `test_rule_targets_cover_every_outcome_plus_the_comparison_wide_targets` | pytest output |
| 14. Document current, complete and deterministic | `test_the_committed_document_matches_the_table`, `test_the_document_leads_with_the_review_status`, `test_the_document_lists_every_rule_and_claim`, `test_the_document_states_its_own_weaknesses`, `test_rendering_is_deterministic`, `test_write_document_round_trips`, `test_each_profile_reaches_the_document` | pytest output; the committed document |
| Also: other claims cite the paper correctly | `test_applied_nitrogen_outcome_refuses_the_phrase_total_n`, `test_herbicide_outcome_separates_mass_from_toxicity`, `test_profitability_is_not_computed_by_agrocycle` | pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:**
  - `python -m pytest engine -q` -> **37 passed**
  - `python -m pytest engine transform -q` -> **126 passed, 1 xfailed** across the whole of my work on this
    branch (37 rules, 31 soil, 34 climate, 24 Marsden plus its documented strict `xfail`)
  - `python -m engine.rules.strategy_rules` -> regenerated the document; byte-identical to the committed copy
  - `ruff check` with the DE branch's settings -> **All checks passed!**, after parenthesising 13 implicit
    string concatenations in the renderer that it flagged (`ISC004`). The document was regenerated afterwards
    and diffed byte-for-byte against the pre-fix copy to confirm the change was behaviour-preserving.
  - `make check` **not run:** the Makefile is on the DE's branch. `testpaths` there will now need `engine` as
    well as `transform`.
- **Passed:** all fourteen acceptance criteria. The table holds 3 strategy profiles, 9 outcomes (3 of them
  explicitly not claimable), 8 crop claims and 13 applicability rules, versioned `2026-11-14.1`, with the
  reviewable document generated from it.
- **Failed or skipped — read this section before using the table:**
  - **Nothing here is expert-reviewed.** Every rule is a team-proposed guardrail. A test enforces that no rule
    can claim otherwise, which protects the honesty of the label but does not make the rules right. The
    roadmap asks for an Iowa-knowledgeable adviser; none has been approached. Until then the table should be
    presented as a proposal, not as agronomy.
  - **Seven of the eight crop claims are unsourced.** Only the manure dependence of the diversified systems is
    supported, by the Marsden supplement and our own reproduction. The potential mechanisms the PRD lists —
    biological nitrogen fixation, living cover, rooting and soil structure, forage feed value — plus alfalfa
    drainage sensitivity, the oat season window and rotation effects on disease and pest pressure are all
    marked `research_needed`, because no agronomic literature was available and I will not manufacture
    citations. The practical effect is that the "why this crop" explanation in the demo will be thin. That is
    the honest state of the evidence, not an omission to be filled in later without sources.
  - **Two rules rest on unsourced claims.** `applicability_alfalfa_drainage` and
    `applicability_oat_season_length` depend on `alfalfa_drainage_sensitivity` and `oat_season_window`. They
    are recorded so the questions are visible and reviewable, they may only *qualify* a comparison, and each
    rationale says it must be **withdrawn** if no source is found. A test enforces all three of those
    properties. They should not survive to the demo unsourced.
  - **`applicability_climate_distance_gdd` is the weakest rule in the table** and says so in its own
    rationale. There is no published basis for the 300 degree-day band; it is wide and only qualifies the
    comparison. If an expert rejects one rule, expect it to be this one.
  - **One condition per rule.** Interactions cannot be expressed. If review shows that, say, drainage matters
    only when there is no tile drainage, Phase 10 needs a richer form than this table provides.
  - **Not validated against a field.** No rule has been run over the 45-field test set, because the profile
    indicators it reads do not exist yet. That is Phase 14's job and it may show rules that never fire or
    always fire.
  - The `context_key` names are my proposal and have not been agreed with DS1, who will write the evaluator
    with me in Phase 10.
- **Evidence location:** `engine/rules/strategy_rules.py`,
  `engine/rules/tests/test_strategy_rules.py`, `docs/rules/strategy-profiles-and-applicability.md`.
- **Roadmap exit check met:** **yes.** The rule table is written, versioned (`2026-11-14.1`) and reviewable as
  a generated document that a non-programmer can read, with its own weaknesses stated in it. The expert review
  the phase also asks for has **not** happened, and the table is labelled accordingly throughout.
- **Roadmap tracker updated:** yes, 2026-11-14
