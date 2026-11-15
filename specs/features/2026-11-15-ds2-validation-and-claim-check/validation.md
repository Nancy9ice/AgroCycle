# Validation: Validation summary and claim check

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Every figure reproducible | each section names the command or table it came from; figures recomputed from ClickHouse on the day | the summary's section 6; `engine_test_set`, `field_indicators`, `marsden_reconciliation` |
| 2. Counts not percentages; abstentions described as correct | read-through of section 1 | the summary |
| 3. Crop history stated as not validated | read-through of section 5; confirmed by reading `scripts/cdl_confusion_matrix.py` and the absent `data/out/phase3/` | the summary; DS1's spec folder |
| 4. Rules that never fire named with reasons | `uv run python -m engine.sweep` output, tabulated in section 2 | sweep output |
| 5. Zero `unknown` rows treated as a limitation | read-through of section 4 | `field_indicators` status query |
| 6. Constrained statistical language | read-through: no percentage of accuracy, no significance claim, field-years not treated as independent | the summary's preamble |
| 7. Feedback log and Iowa gap stated | read-through of section 5 | the summary |
| 8. Claim check covers every PRD section 16 item | item-by-item table with verdicts and owners | the claim check |
| 9. No forbidden outcome asserted | search both documents for soil carbon, erosion and nitrate leaching claims | both documents |
| 10. Versions and run ids named | header of each document | the summary header |

## Results

- **Date completed:** 2026-11-15
- **What was run:**
  - Queried the loaded database for every figure: `engine_test_set` (135 rows), `field_indicators` (4,410;
    4,390 available, 20 partial, 0 unknown), `indicator_lineage` (25, no orphan indicators),
    `marsden_management` (nine-year means 74.5 / 56.556 / 40.806 applied N and 1.925 / 0.261 / 0.195
    herbicide), `marsden_reconciliation` (17 MATCH, 1 WITHIN_SEM, 1 UNRECONCILED, 1 INFO), `crop_rotation`
    (27 rotation, 11 continuous corn, 6 pasture-hay, 1 mixed), `hls_ndvi` (9,663 rows over 45 fields),
    `hls_bare_windows` (127 over 42 fields), `data_sources` (10).
  - `uv run python -m engine.sweep` for the outcome spread and the rules that fire.
  - Read `scripts/cdl_confusion_matrix.py` and DS1's spec folder to establish what the CDL analysis does.
  - `uv run pytest -q --ignore=tests/live` -> 445 passed, 7 skipped, 1 xfailed.
- **Passed:** all ten criteria. The summary reports counts rather than percentages, describes the 18
  abstentions as the correct outcome, names the nine rules that never fire with a reason for each, and treats
  the complete indicator coverage as a limitation rather than a result.
- **Failed or skipped:**
  - **The feedback log does not exist**, so Phase 14's exit check is only half met. It needs F to walk the
    app, and the log must state that he is not an Iowa user. Not deliverable by me.
  - **The CDL analysis is not what the roadmap asked for and has not been run.** The script compares CDL with
    itself across years rather than against another classification, and `data/out/phase3/` is absent. I have
    not run or rewritten it, because it is DS1's and rewriting someone's analysis the night before a deadline
    is how a wrong number reaches a deck. Recorded as an open item with DS1 named.
  - **The PRISM/POWER sanity check** the roadmap lists for Phase 14 is not done; it is a P1 item and the
    POWER-versus-station comparison already bounds the rainfall question.
  - **No independent validation of reference ET** and no expert review of any threshold or rule; both carried
    forward from earlier phases.
- **Evidence location:** `docs/validation/ds2-validation-summary-2026-11-15.md`,
  `docs/validation/ds2-claim-check-2026-11-15.md`, and the tables named above.
- **Roadmap exit check met:** **partially.** Phase 14 asks for a validation summary **and** a feedback log;
  the summary exists, the log does not. Phase 15's claim check is delivered for the DS2 claims; the deck and
  the team-wide walk-through are not mine.
- **Roadmap tracker updated:** yes, 2026-11-15
