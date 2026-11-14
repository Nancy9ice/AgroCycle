# Requirements: Deterministic decision engine

## Covers

- **PRD requirements:** FR-09 (compare strategies across dimensions supported by evidence, showing
  unavailable dimensions rather than omitting them), FR-10 (farmer constraints and their effect on
  feasibility), FR-11 (transparent comparison, qualified assessment or abstention, without forcing a
  ranking), FR-06 (data adequacy), FR-12 (traceability), NFR-01, NFR-02, NFR-03, NFR-05, NFR-06.
  Implements PRD 8.1 steps 6-9, 8.2, 8.3 and 8.5.
- **Roadmap exit check satisfied:** the DS half of "tests pass" for Phase 10. The `/compare` endpoint is BE's
  half and is not done.

## Inputs

Two frozen dataclasses, both pure data:

| `FieldProfile` | Type | Meaning |
|---|---|---|
| `field_id`, `boundary_source`, `crop_history_summary` | str | identity and provenance, carried into the result |
| `county` | str or `UNKNOWN` | from the field file |
| `crop_history_is_maize_soybean` | bool or `UNKNOWN` | maps onto the DE's `domain_note` value `"in-domain: maize-soybean rotation"` |
| `gdd_season_difference_vs_marsden` | float or `UNKNOWN` | degree-days C, from the climate indicators |
| `frost_free_days` | int or `UNKNOWN` | from `frost_window` |
| `dominant_drainage_class` | str or `UNKNOWN` | from the SSURGO class aggregation |
| `indicator_statuses` | mapping | `indicator_id` to `"ok"` or `"unknown"` |

| `FarmerConstraints` | Type |
|---|---|
| `manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor` | bool or `UNKNOWN` |
| `priorities` | tuple of str |

`UNKNOWN` is a singleton sentinel, distinct from `False` and from `None`, and raises on `bool()` so it cannot
be tested truthily by accident.

`REQUIRED_INDICATORS` — `gdd`, `precipitation_total`, `frost_window`, `om_r_0_30cm` — is the team-proposed set
that must be `"ok"` before any outcome is offered.

## Outputs

`assess(profile, constraints) -> Decision`:

| `Decision` field | Contents |
|---|---|
| `outcome` | one of `strategy_worth_exploring`, `qualified_comparison`, `abstention` |
| `outcome_reason` | why, naming the rules where relevant |
| `strategies` | three `StrategyAssessment`: feasibility `available` / `qualified` / `unavailable`, operational requirements, the findings that applied |
| `outcomes` | nine `OutcomeAssessment`: status `in_domain` / `qualified` / `abstained` / `out_of_domain` / `not_assessed`, evidence type, source, the statement when speakable, the caution always |
| `unknowns` | every unknown context key and missing required indicator |
| `constraints_recorded`, `priorities_recorded` | what the farmer said, echoed back |
| `rules_version`, `limitations` | the rule-table version and the standing limitations |

`Decision` carries **no score, no weight, no rank and no winner**.

## Acceptance criteria

Each is covered by a test in `engine/tests/test_decision.py`. The first four groups are the roadmap's
required categories.

1. **In domain:** a complete in-domain field with all constraints stated returns `strategy_worth_exploring`,
   all three strategies `available`, no unknowns, and the reason says it is not a recommendation.
2. **In domain:** each claimable outcome carries its evidence type, its source, a statement and a caution.
3. **Out of domain:** a field whose history is not maize-soybean returns `abstention`, names the rule, and
   marks every strategy `unavailable`.
4. **Out of domain, per outcome:** no manure access takes `applied_n_reduction` to `out_of_domain` with no
   statement, and leaves `herbicide_reduction` `in_domain` with its statement intact and no findings at all.
5. **Out of domain, per strategy:** no forage outlet makes strategy C `unavailable` while B stays
   `available`; a field outside Story and Boone is `qualified`, not excluded; poor drainage qualifies C
   without removing it.
6. **Missing data:** unstated manure access `abstains` that outcome rather than assuming; an unknown
   constraint is read as neither `False` nor `True`; a missing required indicator withholds every claimable
   outcome; an unknown climate distance qualifies; unknown crop history abstains.
7. **Abstention:** an empty profile abstains, lists at least eight unknowns, and still returns the full
   structure — three strategies, nine outcomes, limitations and the crop-history summary.
8. The three forbidden outcomes are `not_assessed` with no statement however good the field is, and
   `forage_supply` is not claimed even when there is a buyer.
9. The result contains no field whose name includes score, rank, winner, best, recommendation or weight;
   every strategy is returned even when unavailable.
10. Priorities are recorded but do not change the outcome, because acting on them without an explicit
    weighting would be the composite score PRD 8.5 forbids.
11. `UNKNOWN` raises on `bool()` and is a singleton; every `context_key` the table uses is supplied by
    `build_context`; a numeric rule given a non-numeric value raises; an unsupported operator raises.
12. The worst finding wins when several apply to one outcome; the engine is deterministic; fired rules come
    back in table order.

## Evidence labels, scale and limitations to preserve

- Each outcome's `evidence_type` and `source` come from the rule table unchanged: `experimental` for the
  reproduced Marsden figures, `published` for the paper's yield, net-return and weed findings.
- `caution` (what may not be said) is returned even when the outcome is withheld, so the caveat cannot be
  dropped by a consumer that only renders visible rows.
- `limitations` always carries the standing five: one site over nine seasons; POWER is a ~50 km grid; SSURGO
  is a mapped survey; every rule is unreviewed; no profitability is calculated.
- `not_assessed` and `abstained` must both render as "unknown / not assessed" in the UI.

## Out of scope

The `/compare` endpoint and JSON serialisation (BE), the constraints form (FE), acting on farmer priorities,
any weighting or ranking, the indicator computation itself, running the engine over the 45-field test set
(Phase 14), and expert review of the rules (Phase 9's open item).
