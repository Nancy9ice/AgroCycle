# Validation: Deterministic decision engine

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1-2. In domain | `test_a_complete_in_domain_field_is_worth_exploring`, `test_in_domain_outcomes_carry_their_evidence_and_their_caution`, `test_the_result_records_the_rules_version_and_the_standing_limitations` | pytest output |
| 3. Out of domain, whole comparison | `test_a_field_that_is_not_maize_soybean_is_out_of_domain` | pytest output |
| 4. Out of domain, per outcome | `test_no_manure_removes_the_nitrogen_outcome_only` | pytest output |
| 5. Out of domain, per strategy | `test_no_forage_outlet_removes_strategy_c_but_leaves_b`, `test_a_field_outside_the_demo_counties_is_qualified_not_excluded`, `test_poor_drainage_qualifies_strategy_c_without_removing_it` | pytest output |
| 6. Missing data | `test_unstated_manure_access_abstains_rather_than_assuming_either_way`, `test_an_unknown_constraint_is_not_read_as_no`, `test_an_unknown_constraint_is_not_read_as_yes_either`, `test_a_missing_required_indicator_withholds_every_outcome`, `test_an_unknown_climate_distance_qualifies_rather_than_passing`, `test_unknown_crop_history_abstains_rather_than_excluding` | pytest output |
| 7. Abstention | `test_an_empty_profile_abstains_and_says_what_is_missing`, `test_abstention_still_returns_the_full_structure` | pytest output |
| 8. Forbidden claims | `test_forbidden_outcomes_are_never_claimed_however_good_the_field_is` (parametrised over all three), `test_forage_supply_is_not_claimed_even_with_a_buyer` | pytest output |
| 9. No ranking or score | `test_the_decision_carries_no_score_and_no_winner`, `test_every_strategy_is_returned_even_when_one_is_unavailable` | pytest output |
| 10. Priorities recorded, not acted on | `test_priorities_are_recorded_but_do_not_change_the_outcome` | pytest output |
| 11. Evaluation mechanics | `test_unknown_has_no_truth_value`, `test_unknown_is_a_singleton`, `test_every_context_key_the_table_uses_is_supplied`, `test_numeric_rules_reject_a_non_numeric_value`, `test_an_unsupported_operator_raises` | pytest output |
| 12. Combination and determinism | `test_severity_ordering_takes_the_worst_finding`, `test_the_engine_is_deterministic`, `test_fired_rules_are_returned_in_table_order` | pytest output |

## Results

- **Date completed:** 2026-11-14
- **What was run:**
  - `python -m pytest engine/tests/test_decision.py -q` -> **31 passed**
  - `make check` equivalents on the merged branch: `ruff check .` -> **All checks passed!** (after fixing one
    import order and one implicit string concatenation it flagged); `transform.field_schema` -> **OK: 45
    fields valid**; `uv run pytest` -> **175 passed, 1 xfailed**
  - The full suite now collects everything: 18 DE, 34 climate, 31 soil, 24 Marsden (plus its documented
    strict `xfail`), 37 rules, 31 engine.
- **Passed:** all twelve criteria, including the four categories the roadmap requires. The two cases that
  matter most both hold: no manure takes the nitrogen comparison out of domain while the herbicide comparison
  keeps its statement and collects no findings at all (PRD 7.6), and an unknown constraint produces a
  different result from a stated "no" — `qualified` rather than `unavailable`.
- **Changed while building it:** the Phase 9 rule table had no rule for an **unstated** forage outlet, oat
  outlet or machinery access, so an unknown would have passed as available — exactly the "missing data read
  as favourable" failure PRD 8.5 forbids. I added three `is_unknown` rules and bumped `RULES_VERSION` to
  `2026-11-14.2` rather than special-casing it in the engine, because policy belongs in the table. The
  generated document was regenerated and the Phase 9 requirements updated from 13 rules to 16.
- **Failed or skipped:**
  - **Built without DS1, which Phase 10 assigns to both of us.** The deadline is tomorrow and BE and FE are
    blocked on the output shape, so I built it alone rather than waiting. The context keys and the `Decision`
    dataclass are what need joint review; if DS1 wants a different profile shape, that is rework.
  - **Never run on a real profile.** Every test constructs its own inputs, because no indicator data exists —
    S3 still held only smoke objects today. Phase 14 is where the engine meets the 45 fields, and it may show
    rules that never fire or always fire.
  - **Farmer priorities are recorded but do not affect anything.** PRD 8.5 says a strategy may be attractive
    for one objective and unsuitable for another, which argues for priorities shaping what is surfaced. Doing
    that without an explicit, justified weighting would be the composite score the PRD forbids, so it needs a
    design decision rather than code. Recorded as a gap, with a test asserting the current behaviour so the
    gap cannot close silently.
  - **`REQUIRED_INDICATORS` is a judgement call.** Four indicators, team-proposed. Too short and the engine
    speaks on thin data; too long and it abstains on everything.
  - **Severity ordering is a design choice**, not a derivation: `out_of_domain` beats `abstain_outcome`, so a
    field outside the domain reports as outside rather than as missing data. Defensible, not obvious, and
    worth a second opinion.
  - No expert review of the rules the engine evaluates; that remains Phase 9's open item.
- **Evidence location:** `engine/decision.py`, `engine/tests/test_decision.py`, and the regenerated
  `docs/rules/strategy-profiles-and-applicability.md`.
- **Roadmap exit check met:** **partially.** "Tests pass" is met — 31 covering in-domain, out-of-domain,
  missing-data and abstention. "The `/compare` endpoint returns the structured result" is BE's half and is not
  done; `assess(profile, constraints) -> Decision` is the contract they need.
- **Roadmap tracker updated:** yes, 2026-11-14
