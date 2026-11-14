# Plan: Strategy profiles, crop characteristics and outcome-specific applicability rules

- **Role:** ds2
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 9, DS2: define the three strategy profiles, crop characteristics with sources, and outcome-specific transferability rules

## Goal

A versioned, reviewable rule table that says, for each of the three rotation strategies and each outcome, what
the evidence supports, what it does not, and which field conditions take an outcome out of the domain where
Marsden evidence may be used at all. It is the input Phase 10's engine evaluates; it is not the engine.

## Approach

The rule table is a Python module of structured, frozen data — strategy profiles, crop-characteristic claims,
outcome evidence and applicability rules — and the reviewable document is **generated from it**, so the table
and the document cannot drift apart. A test regenerates the document and fails if the committed copy is stale.

Three decisions shape the content:

1. **Unsourced agronomy is marked, not written.** PRD 7.5 says that if suitable crop-characteristic sources are
   not identified, the explanation is a research requirement rather than an invented value. I have no agronomic
   literature to hand and will not manufacture citations, so every crop claim that Davis et al. (2012) and its
   supplement do not support carries `status: research_needed` and names the kind of source that would settle
   it. That is most of them, and the table says so plainly rather than looking complete.
2. **Applicability is per outcome, never per strategy.** PRD 7.6 is explicit: no manure access limits transfer
   of the manure-dependent nitrogen comparison but does not invalidate the herbicide comparison. Each rule
   therefore names one `outcome_id`, and a test asserts that no manure rule touches the herbicide outcome.
3. **Each condition is machine-readable.** A rule carries `context_key`, `operator` and `value` from fixed
   vocabularies, so Phase 10 implements it deterministically instead of re-reading prose. The rule table stays
   data; the evaluation is Phase 10's.

Outcomes the PRD forbids claiming — soil carbon, measured erosion, nitrate leaching — appear in the table as
first-class entries with `claimable: False`, so the engine has an explicit "not assessed" to return rather
than an absence that a later contributor might fill in.

## Files, tables and endpoints

Created:
- `engine/rules/strategy_rules.py` — the rule table, its vocabularies and the document renderer
- `engine/rules/tests/test_strategy_rules.py` — structural and honesty tests
- `engine/__init__.py`, `engine/rules/__init__.py`, `engine/rules/tests/__init__.py`
- `docs/rules/strategy-profiles-and-applicability.md` — generated, committed, reviewable by a non-programmer

No ClickHouse tables, no endpoints, no evaluator.

## Steps (in order)

1. Fix the vocabularies: evidence types from the mission principles, the PRD's three decision outcomes, the
   rule effects, and the condition operators.
2. Strategy profiles A, B and C from PRD 2.2, with phases, why each is included and what it requires
   operationally.
3. Outcome evidence: what Marsden supports (reproduced, experimental), what the paper reports but we did not
   reproduce (published), and what must never be claimed.
4. Crop-characteristic claims, each either sourced or `research_needed`.
5. Applicability rules, one outcome each, with machine-readable conditions and a rationale.
6. The renderer, then the generated document.
7. Tests, including that the committed document matches the table.

## Dependencies and interfaces with other roles

- **DS1, Phase 10:** this module is the engine's rule input. The contract is the four tables plus the
  vocabularies; the engine decides outcomes, this does not. Context keys must line up with the profile the API
  assembles, so the names here (`manure_access`, `crop_history_is_maize_soybean`, `gdd_season`, …) need
  agreeing before the engine is written.
- **BE:** `GET /lineage` and the comparison response should be able to cite `rule_id`, so the rules carry
  stable ids.
- **FE:** `research_needed` and `claimable: False` both have to render as "unknown / not assessed", not as a
  blank row.
- **F (farmer) and an Iowa-knowledgeable adviser:** every rule is `not_expert_reviewed` until reviewed. F can
  sanity-check practicality (machinery, labour, markets) but is not an Iowa agronomist, per the roadmap.
- **DE:** `testpaths` in `pyproject.toml` will now need `engine` as well as `transform`.

## Data size and subsets

None. Static tables, no data access.

## Risks and open questions

- **The rules are guardrails, not agronomy.** Every threshold is team-proposed. An expert may reject the
  thresholds, the direction of a rule, or the choice to have a rule at all.
- **Most crop characteristics are unsourced**, so the "why this crop" explanation will look thin in the demo.
  That is the honest state; filling it needs retrievable extension or peer-reviewed sources.
- **Climate-distance thresholds are the weakest part.** Deciding that a field is climatically close enough to
  Marsden for its evidence to transfer is a judgement with no published basis I can cite; the rule exists so
  the question is visible and reviewable, with wide bands and a `qualified` effect rather than exclusion.
- Alfalfa and oat suitability rules rest on drainage and season-length facts that are marked
  `research_needed`; if the research does not arrive, those rules should be withdrawn rather than relied on.
- The table cannot express an interaction between two conditions. If review shows interactions matter, Phase 10
  will need a richer form than one condition per rule.
