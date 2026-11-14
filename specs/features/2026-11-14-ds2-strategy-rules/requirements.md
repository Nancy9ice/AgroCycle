# Requirements: Strategy profiles, crop characteristics and outcome-specific applicability rules

## Covers

- **PRD requirements:** FR-08 (crop/rotation evidence: document relevant crop characteristics and the source
  and strength of evidence), FR-09 (strategy comparison across dimensions supported by evidence, showing
  unavailable dimensions rather than silently omitting them), FR-10 (farmer constraints and how each affects
  feasibility), FR-11 (transparent comparison, qualified assessment or abstention), FR-12 (traceability),
  NFR-02 (explainability), NFR-03 (auditability), NFR-05, NFR-06. Implements PRD 2.2, 7.5, 7.6, 8.2, 8.3,
  8.5 and 9.
- **Roadmap exit check satisfied:** "a rule table is written, versioned and reviewable."

## Inputs

No data. The content is drawn from documents already in the repository and from work already done:

| Source | Used for |
|---|---|
| PRD 2.2 | the three strategies and their rotations |
| PRD 7.4, 7.5, 7.6, 8.2, 8.3, 8.5, 9 | what may be claimed, the outcome vocabulary, the transferability requirement, the feasibility constraints |
| Davis et al. (2012), PLOS ONE 7(10): e47149 [S09] | published yield, net-return and weed findings, attributed |
| Its supplementary management records [S10] | the manure dependence of the diversified systems |
| `transform/marsden` (Phase 6) | the reproduced applied-N and herbicide figures |
| `specs/mission.md` | the evidence-type label set |

No agronomic literature was available, which is itself an input to the result: see criterion 4.

## Outputs

`engine/rules/strategy_rules.py`, four frozen-dataclass tables plus vocabularies and a renderer:

| Table | Contents |
|---|---|
| `STRATEGY_PROFILES` | 3 profiles: id, label, rotation, phases, why included, operational requirements, evidence anchor |
| `OUTCOME_EVIDENCE` | 9 outcomes: `claimable`, evidence type, source, what may be said, what may not be said |
| `CROP_CLAIMS` | 8 claims: `sourced` with a source and evidence type, or `research_needed` with what is needed |
| `APPLICABILITY_RULES` | 16 rules: `rule_id`, one `outcome_id`, a machine-readable condition, effect, rationale, evidence basis, review status |

Vocabularies: `EVIDENCE_TYPES`, `DECISION_OUTCOMES`, `RULE_EFFECTS`, `CLAIM_STATUSES`, `OPERATORS`,
`REVIEW_STATUSES`, `RULE_TARGETS`. A condition is `(context_key, operator, value)` so Phase 10 evaluates it
deterministically rather than re-reading prose.

`docs/rules/strategy-profiles-and-applicability.md` — generated from the module and committed, so a reviewer
who does not read Python can read the whole table, including a closing section on its own weaknesses.

`RULES_VERSION` (`2026-11-14.2`; three `is_unknown` rules for unstated operational constraints were added in Phase 10) versions the table and appears in the document.

## Acceptance criteria

Each is covered by a test in `engine/rules/tests/test_strategy_rules.py`.

1. Three strategy profiles, A/B/C, with 2, 3 and 4 phases, each complete, and both diversified options
   declaring the manure requirement in their operational requirements.
2. The three outcomes the PRD forbids — soil carbon, measured erosion, nitrate leaching — are **present** with
   `claimable=False`, no evidence type and no source, so the engine has an explicit "not assessed" to return.
3. Every claimable outcome names an evidence type from the mission label set and a source; the reproduced
   outcomes are `experimental` while yields and net returns are `published` and say they were not reproduced.
4. Every crop claim is either `sourced` with a source, or `research_needed` with no source and a note naming
   the kind of citable source required. Exactly one claim is sourced, because only the manure dependence is
   supported by Marsden; the other seven are open research.
5. Every applicability rule is structurally valid against the vocabularies, has a unique id, names exactly one
   target from `RULE_TARGETS`, and carries a rationale.
6. **No rule claims to be expert-reviewed.**
7. **Manure rules touch only the nitrogen outcome**, never the herbicide outcome (PRD 7.6).
8. No rule applies to a forbidden outcome.
9. Any `is_unknown` condition, and the indicator-coverage rule, resolve to `abstain_outcome` or `qualified`,
   never `in_domain` — missing data is never read as favourable (PRD 8.5).
10. A rule resting on a `research_needed` claim names that claim, says it must be withdrawn if unsourced, and
    may only **qualify** a comparison, never exclude an option.
11. The GDD climate-distance rule states that it has no published basis.
12. Only the forage-outlet rule removes an option on operational grounds; the other operational rules qualify.
13. `DECISION_OUTCOMES` is exactly the PRD's three outcomes, and `EVIDENCE_TYPES` is exactly the mission's
    eight labels.
14. The committed document is byte-identical to the rendered table, leads with the review status, lists every
    rule, claim and outcome, states its own weaknesses, and renders deterministically.

## Evidence labels, scale and limitations to preserve

- Reproduced Marsden figures are `experimental`, one site over nine seasons, not field-level predictions.
- Paper findings are `published` and attributed; AgroCycle did not reproduce them.
- Every rule is `not_expert_reviewed`. The roadmap wants review by an Iowa-knowledgeable adviser; the farmer
  reviewer is Nigerian and can sanity-check practicality but not Iowa agronomy, and that must be stated
  wherever the rules are presented.
- `research_needed` and `claimable=False` must both render as "unknown / not assessed", never as a blank row.
- The applied-nitrogen figure is applied N (manufactured plus manure) and excludes biological fixation. Never
  "total N".
- One condition per rule: interactions between conditions cannot be expressed in this form.

## Out of scope

The evaluator (Phase 10, DS2 with DS1), the `/compare` endpoint (BE), the constraints form (FE), the farmer's
own priorities and weightings, any composite score (PRD 8.5 forbids one without explicit components, weights
and sensitivity), profitability computation (PRD 9 forbids it on the data available), erosion susceptibility,
and retrieving the agronomic sources the seven open claims need.
