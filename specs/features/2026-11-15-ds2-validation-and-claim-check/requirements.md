# Requirements: Validation summary and claim check

## Covers

- **PRD requirements:** FR-06 (data adequacy), FR-12 (traceability), NFR-01 (reproducibility), NFR-02
  (explainability), NFR-03 (auditability), NFR-05 (missing data must not create misleading outputs), and
  PRD section 16 (Definition of Done) in full.
- **Roadmap exit check satisfied:** Phase 14 — "a validation summary and a feedback log exist" — for the
  summary half. The feedback log needs F and is not delivered here. Phase 15 — "every claim is evidenced" —
  for the DS2 claims.

## Inputs

Recomputed from the loaded database, not quoted from earlier runs:

| Source | Used for |
|---|---|
| `engine_test_set` (135 rows) | the engine's behaviour over 45 fields × 3 constraint scenarios |
| `field_indicators` (4,410) | indicator coverage and status spread |
| `indicator_lineage` (25) | that every indicator in use has provenance |
| `marsden_management`, `marsden_reconciliation` | the reproduction and its reconciliation statuses |
| `crop_rotation` (45) | the in-domain and out-of-domain split |
| `hls_ndvi`, `hls_bare_windows` | DS1's vegetation coverage |
| `docs/sources/ds2-first-pull-review-2026-11-14.md` | POWER against the Marsden station record |
| `engine/sweep.py` | which applicability rules fire and which never do |
| PRD section 16 | the Definition of Done checklist |

## Outputs

**`docs/validation/ds2-validation-summary-2026-11-15.md`** — what was tested, what the result was, what the
result does not establish, and what remains untested. Written so a reader can re-run every figure.

**`docs/validation/ds2-claim-check-2026-11-15.md`** — one row per PRD section 16 item: the claim, what
supports it, a verdict of **met**, **partly met** or **not met**, and the action where it is not met.

## Acceptance criteria

1. Every figure in the summary is reproducible by a stated command or query, and none is quoted from memory.
2. The engine result is reported as counts over 45 fields, never as a percentage or an accuracy, and the 18
   abstentions are described as the correct outcome rather than as failures.
3. The summary states that **the crop-history classification is not validated**: the script that exists
   compares CDL with itself across years, which is internal consistency, not agreement with another
   classification, and it has not been run.
4. The summary reports that 9 of 14 applicability rules never fire on this test set, names them, and says for
   each whether that is a guardrail for absent input or a threshold that may be wrong.
5. The summary reports that no indicator row came back `unknown`, and treats that as a limitation — the
   missing-data paths are exercised by tests, not by data.
6. Statistical language is constrained: counts not percentages, "indicative, not statistically strong", no
   significance claims, and field-years are not treated as independent samples.
7. The absence of the farmer feedback log and of any Iowa stakeholder feedback is stated plainly, with no
   adoption or local-impact claim anywhere.
8. The claim check covers every PRD section 16 item with a verdict and, where not met, a named action and
   owner.
9. Nothing in either document asserts an outcome the rule table marks `claimable=False`.
10. Both documents name the rules version and the run ids they describe, so a reader can tell if they are
    stale.

## Evidence labels, scale and limitations to preserve

- Marsden figures are `experimental`, one site, nine seasons; the yield and profit figures are `published`
  and attributed, not reproduced.
- Climate indicators are `model_reanalysis` on a ~50 km grid; soil is `survey` over mapped units; neither is
  a field measurement.
- The POWER precipitation shortfall against the station record (about 11 %) must appear, because it bounds
  what the rainfall and dry-spell indicators can support.
- Reference ET remains not independently validated.
- No applicability rule is expert-reviewed.

## Out of scope

The farmer feedback log itself (needs F), running or rewriting DS1's CDL analysis (DS1 owns it), the PRISM
comparison (P1), the slide deck, and any change to the engine or the rule table — if the claim check finds an
unsupported claim, this task records it and names the owner rather than silently changing behaviour.
