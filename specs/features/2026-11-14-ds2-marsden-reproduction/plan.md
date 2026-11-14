# Plan: Marsden Farm management reproduction

- **Role:** ds2
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 6, DS2: reproduce the rotation-area-weighted nine-year management averages from the Marsden supplementary records and reconcile them with the paper

## Goal

Rebuild the 2-yr / 3-yr / 4-yr rotation management summaries (manufactured N, manure N, applied N, herbicide
active ingredient) from the supplementary records of Davis et al. (2012), PLOS ONE 7(10): e47149, so the
Marsden evidence shown in the app is a reproduced figure with a lineage record, not a number copied from a PRD.

## Approach

Parse Table S3 (fertiliser N by year and crop phase) and Table S4 (herbicide active ingredient by year, crop and
rotation) out of the supplementary `.docx` files with `python-docx`, then apply the weighting documented in
Text S1: each land unit is divided into equal portions per crop phase (2, 3 or 4), so a rotation's annual value is
the sum over phases divided by the number of phases, and the nine-year value is the mean of 2003-2011. Phases with
no herbicide application (small grain, forage legumes) contribute zero.

Every computed value is checked twice: against the PRD targets, and against the numbers in the paper's own Results
text. Disagreements are reported as reconciliation rows rather than tuned away, and the single real disagreement
(2-yr manufactured N) is kept visible as a strict `xfail`.

Raw inputs are verified against a SHA-256 manifest before every run; a mismatch aborts.

## Files, tables and endpoints

Created:
- `transform/marsden/marsden_repro.py` — the reproduction job (pure computation plus CSV/JSON writes; no network, no DB)
- `transform/marsden/tests/test_marsden_repro.py` — 24 tests plus 1 strict `xfail`
- `transform/marsden/README.md` — method, result, the documented discrepancy, limitations, DE handoff
- `transform/marsden/manifests/2026-11-13.json` — tracked copy of the raw-input manifest (URL, version, SHA-256, size, licence per file)
- `transform/marsden/requirements.txt` — `python-docx`, `pandas`, `pytest` (to fold into the root `pyproject.toml` when the DE creates it)
- `docs/sources/ds2-power-ssurgo-marsden.md` — the DS2 source requirements sheet (POWER, SSURGO, Marsden)

Outputs, written to `data/out/marsden/` (gitignored; regenerable):
- `management_by_year.csv`, `management_summary.csv` — for the DE to load into ClickHouse
- `indicator_lineage.json` — four rows, one per derived indicator, for `indicator_lineage`
- `reconciliation.csv` — the evidence / validation record
- `run_manifest.json` — script and input checksums, interpreter and platform

Raw inputs live at `data/raw/marsden/pone.0047149-supplement/2026-11-13/` and are **not** committed
(development rules s6); they are restored from S3 or passed with `--raw DIR`.

No endpoints and no ClickHouse DDL in this task.

## Steps (in order)

1. Retrieve the article PDF and supplementary files; write `MANIFEST.json` with URL, version, SHA-256, size and licence.
2. Extract Table S3 and Table S4 into tidy DataFrames.
3. Apply the Text S1 equal-phase weighting; compute annual and nine-year values per rotation.
4. Reconcile against the PRD targets and the paper's Results text; classify each check MATCH / WITHIN_SEM / UNRECONCILED / INFO.
5. Isolate the 2-yr manufactured-N gap to a single year and record the diagnostic without correcting the data.
6. Write the lineage, reconciliation and run manifest; add tests covering every target and the manifest check.
7. Write the handoff notes for the DE.

## Dependencies and interfaces with other roles

- **Upstream:** none. This task reads only the supplementary files, so it did not wait on Phase 2 or 3.
- **DE (Phase 6, "DE validates"):** owes a Pandera schema over the two extracted tables; the checks here are plain
  Python for now. The DE also owns copying the five raw files to S3 at
  `raw/marsden/pone.0047149-supplement/2026-11-13/` and loading the two CSVs plus the lineage rows into ClickHouse.
  Column names, types and units are fixed by `requirements.md` and should not change without telling BE.
- **BE:** `GET /evidence/marsden` reads the loaded tables, not this module. If the engine needs the numbers in
  process instead, import `transform.marsden.marsden_repro`.
- **Everyone:** `make check` does not exist yet, so this module is not wired into it.

## Data size and subsets

Not relevant: five files, 753 KB in total, one research site, nine seasons. Nothing is downloaded at run time.

## Risks and open questions

- The paper's Results text reports 2-yr manufactured N as 80 +/- 3 kg N/ha/yr; Table S3 weights to 74.5. The gap is
  isolated to 2011 and its cause is unknown (see `README.md`). Kept as a strict `xfail`, not corrected.
- Table S3 lists manure on the maize row although Text S1 says it was applied to clover/alfalfa in October. No effect
  on the averages, but it means the by-year table is a treatment-level record, not a field operation log.
- The licence version on the article page still needs confirming; the manifest records what was read at retrieval.
- Parsing depends on the `.docx` table structure. If PLOS re-issues the supplement, the manifest check fails loudly
  rather than silently producing different numbers.
