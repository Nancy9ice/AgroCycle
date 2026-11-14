# Validation: Marsden Farm management reproduction

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Applied N 74.5 / 56.6 / 40.8 (PRD targets) | `test_prd_targets` (parametrised over the three rotations), tolerance 0.05 | `data/out/marsden/management_summary.csv`, `reconciliation.csv` |
| 2. Herbicide 1.925 / 0.261 / 0.195 | `test_prd_targets`, `test_herbicide_matches_paper_text` | same |
| 3. Components split and sum to applied N | `test_manufactured_and_manure_split` | `management_summary.csv` |
| 4. All 12 PRD targets `MATCH`; every paper-text check classified | the reconciliation table written by the job, read in the results below | `reconciliation.csv` (20 rows) |
| 5. 2-yr manufactured-N gap stays visible | `test_manufactured_n_2yr_matches_paper_text` marked `xfail(strict=True)`, plus `test_2yr_gap_is_isolated_to_2011` | pytest output; `README.md` "One real discrepancy" |
| 6. Nine seasons per rotation, none dropped | `test_nine_seasons_per_rotation`, `test_real_tables_are_complete` | `management_by_year.csv` (27 rows) |
| 7. Reruns are byte-identical | `test_rerun_gives_identical_tables`, plus a manual md5 re-run check | md5 comparison recorded below |
| 8. Manifest mismatch or missing input aborts | `test_tampered_input_is_detected`, `test_raw_files_match_manifest` | pytest output |
| 9. `--strict` exits 1 on `UNRECONCILED` | hand-check of the exit code | recorded below |
| 10. No yield / profit / weed figure recomputed | review: the module computes only N and herbicide; paper figures appear in `README.md` with attribution | `README.md` |
| Extraction robustness | `test_missing_fertilizer_row_is_rejected`, `test_duplicate_fertilizer_row_is_rejected`, `test_negative_rate_is_rejected`, `test_missing_herbicide_year_is_not_treated_as_zero`, `test_unrecognised_phase_label_is_rejected`, `test_footnote_symbols_are_stripped_from_active_ingredients` | pytest output |
| Weighting method is correct | `test_equal_area_weighting_by_hand` (hand-computed case from Text S1) | pytest output |
| Lineage completeness (FR-12) | `test_every_indicator_has_a_complete_lineage_row` | `indicator_lineage.json` (4 rows) |

## Results

- **Date completed:** 2026-11-14
- **What was run:**
  - `python -m pytest transform/marsden -q` -> **24 passed, 1 xfailed** in 11.6 s
  - `python -m transform.marsden.marsden_repro` -> regenerated all five outputs and printed the reconciliation
  - determinism hand-check: md5 of `management_by_year.csv`, `management_summary.csv`, `reconciliation.csv` and
    `indicator_lineage.json` before and after a second run — all four unchanged (`run_manifest.json` carries a
    timestamp by design and is excluded)
  - `make check` **not run: it does not exist yet** (no Makefile in the repo)
- **Passed:** criteria 1-10 and all the extraction, weighting and lineage checks above. Nine-year values computed:
  manufactured N 74.500 / 16.704 / 10.917, manure N 0.000 / 39.852 / 29.889, applied N 74.500 / 56.556 / 40.806,
  herbicide 1.925 / 0.261 / 0.195 (2-yr / 3-yr / 4-yr). All 12 PRD s7.4 targets reconcile as `MATCH`. Reductions
  vs the 2-yr system: manufactured N 77.6 % and 85.3 %; herbicide 86.5 % and 89.8 %, pooled 88.2 % against the
  paper's reported 88 %.
- **Failed or skipped:**
  - **1 `UNRECONCILED` check, deliberately left open.** The paper's Results text gives 2-yr manufactured N as
    80 +/- 3 kg N/ha/yr; Table S3 weights to 74.5. The gap is isolated to 2011, where Table S3 gives maize 112 and
    soybean 0 (weighting to 56) while Fig. 1e plots the 2-yr point near 112. Reading 2011 as the maize phase alone
    gives 80.7, which matches the text. That is recorded as an `INFO` diagnostic, **not** applied as a correction;
    the cause (figure or text error, or a 2011 detail absent from the table) is unknown and only the authors could
    confirm it. The strict `xfail` keeps it visible.
  - `--strict` therefore exits 1 on the current data, as intended.
  - **Not done, and owed by others:** the Pandera schema over the two extracted tables (DE, shared module not yet
    created — checks are plain Python for now), copying the five raw files to S3, the ClickHouse load, and the
    `make check` wiring.
  - Raw inputs are not in git, so a fresh clone cannot run this until those files are restored from S3 or passed
    with `--raw DIR`.
  - The licence version on the article page is still unconfirmed; the manifest records what was read at retrieval.
- **Evidence location:** `transform/marsden/` (code, README, tracked manifest copy),
  `data/out/marsden/` (outputs, gitignored — regenerate with the command above),
  `data/raw/marsden/pone.0047149-supplement/2026-11-13/` (raw inputs, gitignored).
- **Roadmap exit check met:** **yes.** A test passes on 74.5 / 56.6 / 40.8 kg N/ha/yr applied N and
  1.925 / 0.261 / 0.195 kg ai/ha/yr herbicide, and yield claims are attributed to Davis et al. (2012) rather than
  recomputed. Note the wording change: the PRD's "total N" is **applied N (manufactured + manure)** and excludes
  biological N fixation. The DE half of Phase 6 (Pandera validation of the supplementary records) is still open.
- **Roadmap tracker updated:** yes, 2026-11-14
