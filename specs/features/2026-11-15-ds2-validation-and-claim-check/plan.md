# Plan: Validation summary and claim check

- **Role:** ds2
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 14, DS2: run the decision engine over the whole test set and write the validation summary; Phase 15, DS2: check the claims AgroCycle makes against the evidence behind them

## Goal

Two documents that let a judge, an adviser or a teammate check what AgroCycle actually establishes: a
validation summary saying what was tested, what the result was and what remains untested, and a claim check
walking the PRD's Definition of Done and marking each item honestly.

## Approach

Everything in the summary is recomputed from the loaded database or from a committed artefact, not from
memory. Where a check was not done, the summary says so in the same voice as the checks that were, because a
validation summary that only lists successes is marketing.

The engine sweep already runs over all 45 fields under three constraint scenarios and its rows are loaded as
`engine_test_set`, so the summary cites the table rather than restating numbers. The first-pull review
covers POWER against the Marsden station record, and the Marsden reconciliation is in
`marsden_reconciliation`.

The claim check is a table: each PRD section 16 item, what supports it, and a verdict of met, partly met or
not met. The point is to find the claims we cannot support before a judge does.

## Files, tables and endpoints

Created:
- `docs/validation/ds2-validation-summary-2026-11-15.md`
- `docs/validation/ds2-claim-check-2026-11-15.md`

Reads, and does not change: `engine_test_set`, `field_indicators`, `indicator_lineage`,
`marsden_management`, `marsden_reconciliation`, `crop_rotation`, `hls_ndvi`, `hls_bare_windows`,
`data_sources`.

No code, no schema, no endpoint.

## Steps (in order)

1. Recompute the evidence from ClickHouse rather than quoting earlier runs.
2. Write the validation summary: what was tested, the result, and what the result does not establish.
3. List the untested parts as first-class entries, with why.
4. Walk PRD section 16 item by item for the claim check, and mark the ones we cannot support.
5. Note every claim that needs rewording before the deck, and who owns it.

## Dependencies and interfaces with other roles

- **DS1:** the roadmap asks for a CDL confusion matrix with correct terminology. `scripts/cdl_confusion_matrix.py`
  compares CDL with itself across years, which is an internal consistency check rather than agreement with
  another classification, and it has not been run: there is no `data/out/phase3/`. The crop-history
  classification is therefore unvalidated, which the summary has to say, and it affects a PRD section 16
  item. DS1 owns closing it or agreeing the wording.
- **F:** the feedback log needs the farmer to walk the app. He is Nigerian, not an Iowa user, so the log
  covers usability and general agronomic sense only, and the summary says that rather than implying wider
  review.
- **FE:** the validation page is in progress and has no content; this summary is the content.
- **BE:** `GET /validation/test-set` reads `engine_test_set`, the same rows this summary cites.

## Data size and subsets

None. Queries over tables of at most a few thousand rows.

## Risks and open questions

- **The test set is small and not independent.** 45 fields, 27 of them in domain, all team-drawn polygons in
  two counties. Counts, not percentages, and field-years are not independent samples.
- **The clean indicator coverage is itself a finding.** 4,390 of 4,410 indicator rows are `available` and
  none is `unknown`, so the missing-data paths that the engine depends on are exercised by tests and not by
  real data.
- The claim check may conclude that an item of the Definition of Done is not met. That is the point of doing
  it, and the answer is to reword the claim rather than to soften the check.
