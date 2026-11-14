# Requirements: Marsden Farm management reproduction

## Covers

- **PRD requirements:** FR-07 (experimental evidence), FR-12 (traceability), NFR-01 (reproducibility),
  NFR-03 (auditability), NFR-05 (reliability: no silent misleading output). Supports PRD s7.4 and the
  demo checklist item "Marsden calculations are reproducible from retrieved source records" (PRD s13).
- **Roadmap exit check satisfied:** "a test passes on 74.5 / 56.6 / 40.8 kg N/ha/yr total N and
  1.925 / 0.261 / 0.195 kg/ha/yr herbicide; yield claims are attributed to the paper, not recomputed."

## Inputs

Davis, A.S., Hill, J.D., Chase, C.A., Johanns, A.M. and Liebman, M. (2012), PLOS ONE 7(10): e47149 [S09] and its
supplementary management records [S10]. Five files at `data/raw/marsden/pone.0047149-supplement/2026-11-13/`,
each with URL, version, SHA-256, size and licence in `MANIFEST.json` (tracked copy:
`transform/marsden/manifests/2026-11-13.json`):

| File | Content used | Units |
|---|---|---|
| `pone.0047149.s004.docx` | Table S3: manufactured-fertiliser N and composted-manure N by year and crop phase | kg N/ha |
| `pone.0047149.s005.docx` | Table S4: herbicide active ingredient by year, crop and rotation | kg ai/ha |
| `pone.0047149.s002.docx` | Table S1: site weather (reference for the DE's POWER first pull) | deg C, mm |
| `pone.0047149.s007.docx` | Text S1: the equal-phase weighting method | - |
| `pone.0047149.pdf` | Results text, Fig. 1e (reconciliation reference only) | - |

Coverage: 2003-2011, nine growing seasons, one site (Marsden Farm, Boone County, Iowa), three rotation treatments.

## Outputs

All under `data/out/marsden/` (gitignored, regenerable). Floats are rounded to 6 decimal places on write.

**`management_by_year.csv`** — one row per rotation-year (27 rows)

| Column | Type | Unit |
|---|---|---|
| `rotation` | enum `2-yr` / `3-yr` / `4-yr` | - |
| `year` | int | calendar year, 2003-2011 |
| `manufactured_n` | float | kg N/ha/yr, rotation-area weighted |
| `manure_n` | float | kg N/ha/yr, total N in composted manure, rotation-area weighted |
| `applied_n` | float | kg N/ha/yr, `manufactured_n + manure_n` |
| `herbicide` | float | kg active ingredient/ha/yr, rotation-area weighted |

**`management_summary.csv`** — one row per rotation (3 rows): the same four measures as the mean of the nine
annual values, plus `n_years` (int, must be 9).

**`indicator_lineage.json`** — four objects, one per derived indicator, each with `indicator_id`, `variables`,
`formula`, `unit`, `limitation`, `source`, `source_url`, `product_version`, `spatial_scale`, `temporal_window`,
`missing_data_rule`, `evidence_type`. Maps to the `indicator_lineage` table.

**`reconciliation.csv`** — one row per check, with `quantity`, `rotation`, `computed`, `reference`, `source`,
`rule`, `status` (`MATCH` / `WITHIN_SEM` / `UNRECONCILED` / `INFO`) and `note`.

**`run_manifest.json`** — script name and SHA-256, per-input SHA-256, timestamp, interpreter and platform.

## Acceptance criteria

1. Nine-year applied N is 74.5 / 56.6 / 40.8 kg N/ha/yr for the 2-yr / 3-yr / 4-yr rotations, each within half of
   the last published digit (0.05).
2. Nine-year herbicide is 1.925 / 0.261 / 0.195 kg ai/ha/yr, to the same tolerance.
3. Manufactured N and manure N components are reported separately and sum to applied N for every rotation-year.
4. All 12 PRD s7.4 targets reconcile as `MATCH`; every check against the paper's Results text is classified and
   written to `reconciliation.csv`.
5. The 2-yr manufactured-N disagreement with the paper's text (74.5 vs 80) is asserted by a strict `xfail` test,
   so closing it in future fails the suite and forces the note to be revisited.
6. `n_years` is 9 for every rotation; no rotation-year is silently dropped.
7. Running the job twice on the same raw inputs produces byte-identical CSV and lineage outputs.
8. A raw input whose SHA-256 does not match the manifest, or that is missing, aborts the run with a non-zero exit
   and no partial output.
9. `--strict` exits 1 while any check is `UNRECONCILED`.
10. No yield, profit or weed figure is recomputed; any that appear are attributed to the paper.

## Evidence labels, scale and limitations to preserve

- **Evidence type:** `experimental` for all four indicators — a derived summary of experimental records from one
  research site. The yield, profit and weed figures quoted in the README are `published`.
- **Scale:** one site (Marsden Farm, Boone County, Iowa), treatment-level (not plot-level), annual, 2003-2011.
  Not a field-level prediction and not transferable to another field without the applicability rules of Phase 9.
- **Limitations to carry into every downstream display:** single site and nine seasons; manure N is total N in
  composted manure, not plant-available N; herbicide is mass of active ingredient and says nothing about toxicity;
  insecticides (2007-2009) are excluded; Table S3 lists manure on the maize row although Text S1 places the
  application on clover/alfalfa in October; applied N excludes biological N fixation, which the paper reports as
  substantial, so the measure is "applied N", never "total N"; no soil-carbon, erosion or nitrate-leaching claim
  follows from these records.

## Out of scope

Plot-level yields (absent from the supplement), any statistical re-analysis of the experiment, Pandera schemas
(DE owns the shared module), ClickHouse DDL and loading, the `make check` wiring, the API endpoint, and the
applicability rules that decide whether this evidence may be shown for a given field.
