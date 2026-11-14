# Plan: Deterministic decision engine

- **Role:** ds2
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 10, DS2 (with DS1): a deterministic engine that takes the profile, evidence and farmer constraints and returns worth exploring / qualified comparison / abstention

## Goal

The piece BE and FE are both waiting on: a pure function that turns a field profile plus farmer constraints
into a structured comparison of the three strategies, with every conclusion traceable to a rule in the Phase 9
table and to the evidence behind it. It reaches an outcome or it abstains; it never ranks.

## Approach

All policy stays in `engine/rules/strategy_rules.py`; this module only evaluates it. Three steps:

1. **Build a context** from the profile and the constraints: one flat mapping whose keys are exactly the
   `context_key` values the rule table uses. Anything absent or unstated is `UNKNOWN`, a sentinel distinct from
   `False` and from `None`.
2. **Fire the rules.** A condition holds only when the value is known, except `is_unknown`, which holds only
   when it is not. So `manure_access equals False` never fires for a farmer who simply has not said — that
   case belongs to the `is_unknown` rule, which abstains instead of assuming.
3. **Combine the findings** by severity, per outcome and per strategy: `out_of_domain` beats `abstain_outcome`
   beats `qualified` beats `in_domain`. Findings targeting `all_outcomes` apply to every claimable outcome.

The overall result is one of the PRD's three outcomes and nothing else. There is no score, no weighting and no
winner field, because PRD 8.5 forbids a composite score without explicit components, weights and sensitivity,
and 8.4 forbids forcing a ranking.

Outcomes the table marks `claimable=False` are returned as `not_assessed` whatever the rules say, so the three
forbidden claims cannot reappear through the engine.

While writing the context builder I found three gaps in the Phase 9 table: unstated forage outlet, oat outlet
and machinery access had no rule, so an unknown would have passed as available. Rather than patch that in the
engine, I added three `is_unknown` rules to the table and bumped `RULES_VERSION` to `2026-11-14.2`. Policy
belongs in the table; this is what having one is for.

## Files, tables and endpoints

Created:
- `engine/decision.py` — the engine: context, evaluation, combination, the `Decision` result
- `engine/tests/test_decision.py` — the four roadmap categories plus the honesty cases
- `engine/tests/__init__.py`

Changed:
- `engine/rules/strategy_rules.py` — three new `is_unknown` rules, version `2026-11-14.2`
- `docs/rules/strategy-profiles-and-applicability.md` — regenerated
- the Phase 9 spec's requirements, which said 13 rules

No endpoints (BE wraps this), no I/O, no ClickHouse.

## Steps (in order)

1. `UNKNOWN` sentinel, `FieldProfile` and `FarmerConstraints` input types.
2. `build_context`, mapping profile and constraints onto the table's context keys.
3. `rule_applies`, honouring the known/unknown distinction for every operator.
4. Combination by severity, per outcome and per strategy.
5. The overall outcome and the reason for it.
6. Tests: in-domain, out-of-domain, missing data, abstention, plus the honesty cases.

## Dependencies and interfaces with other roles

- **DS1:** this is a joint task and I have built it alone, because the deadline is tomorrow and BE and FE are
  blocked on the output shape. The context keys and the `Decision` dataclass are the two things to review
  together; `crop_history_is_maize_soybean` maps onto the DE's existing `domain_note` value
  `"in-domain: maize-soybean rotation"`, so that one is already settled by the field file.
- **BE:** `assess(profile, constraints) -> Decision` is the whole contract. Serialise the dataclasses to JSON
  for `POST /fields/{id}/compare`. PRD 8.4 asks the response to also carry the indicators and the lineage,
  which the API assembles around this result rather than the engine returning them.
- **FE:** every outcome carries a `status` and a `caution`; `not_assessed` and `abstained` must render as
  "unknown / not assessed", never as an empty row or a zero.
- **DE:** no new dependency; `testpaths` already covers `engine`.

## Data size and subsets

None. Pure functions over small structures.

## Risks and open questions

- **Built without DS1.** The input shape may need changing after review. Everything is dataclasses with
  keyword arguments, so renaming a field is cheap, but a reshaped profile would be rework.
- **The required-indicator list is a judgement.** Which indicators must be known before a comparison is
  honest is team-proposed; I have kept it short and explicit.
- **Severity ordering is a design choice.** Making `out_of_domain` beat `abstain_outcome` means a field
  outside the domain reports as such rather than as missing data. Defensible, not obvious.
- The engine has never run on a real profile, because no indicator data exists yet. Phase 14 is where it meets
  the 45 fields, and that may expose rules that never fire or always fire.
- No farmer priorities yet: the PRD wants priorities to shape what is surfaced, and this version records them
  without acting on them. Acting on them without a weighting scheme would be the composite score the PRD
  forbids, so that needs a design decision first.
