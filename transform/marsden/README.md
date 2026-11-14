# Marsden reproduction (DS2, roadmap Phase 6)

Rebuilds the nine-year, rotation-level management summaries from the supplementary records of
Davis et al. (2012), *PLOS ONE* 7(10): e47149, and reconciles them with the PRD targets and the paper's own text.
Evidence type for every output: `experimental` (summary of experimental records from one site).

## Run

All commands run from the repository root.

```
pip install -r transform/marsden/requirements.txt
python -m transform.marsden.marsden_repro            # writes data/out/marsden/*, prints the reconciliation
python -m transform.marsden.marsden_repro --strict   # exit 1 if any check is UNRECONCILED
python -m pytest transform/marsden -q                # 24 pass, 1 expected failure (documented gap below)
```

Raw inputs are not in git (development rules s6). The script reads `data/raw/marsden/pone.0047149-supplement/2026-11-13/`
by default and verifies every file against `transform/marsden/manifests/2026-11-13.json` before it runs, so a
fresh clone needs those five files restored from S3 (or `--raw DIR`) first.

## Result (kg/ha/yr, 2003-2011, equal-area weighted)

| Rotation | Manufactured N | Manure N | Applied N | Herbicide (kg ai) |
|---|---:|---:|---:|---:|
| 2-yr | 74.50 | 0.00 | **74.5** | **1.925** |
| 3-yr | 16.70 | 39.85 | **56.6** | **0.261** |
| 4-yr | 10.92 | 29.89 | **40.8** | **0.195** |

All 12 PRD targets match. Reductions vs 2-yr: manufactured N 77.6% (3-yr) and 85.3% (4-yr); herbicide 86.5% and 89.8%
(pooled 88.2%, the paper reports 88%).

Method (Text S1): each land unit is split into equal portions per phase (2, 3 or 4). Annual value = sum over phases / number
of phases; the nine-year value is the mean of the nine annual values. Phases with no herbicide (small grain, forage legumes)
count as zero.

## One real discrepancy with the paper

The paper's text reports manufactured N of **80 +/- 3 / 16 +/- 3 / 11 +/- 2** kg N/ha/yr. Our values agree for the 3-yr and 4-yr
systems and for all herbicide figures, but the 2-yr system is **74.5, not 80**.

* The gap is isolated to **2011**. Table S3 gives maize 112 + soybean 0, which weights to 56. Fig. 1e plots the 2-yr point
  for 2011 at about 112 (read by eye). The other eight years agree with Fig. 1e.
* Treating 2011 as the maize phase alone gives a 2-yr mean of 80.7, matching the paper. This is a diagnostic, not a
  correction. The cause (figure or text error, or a 2011 detail not in the table) is unknown; the authors could confirm.
* The test `test_manufactured_n_2yr_matches_paper_text` is marked `xfail(strict=True)` so the gap stays visible and the
  note is revisited if it ever closes.

## Suggested wording changes to the PRD / demo

1. Say **"applied N (manufactured + manure)"**, not "total N". It excludes biological N fixation by red clover and alfalfa,
   which the paper says was substantial.
2. Cite both: Table S3 gives 74.5 for the 2-yr system, the paper's text gives 80 (difference traced to 2011).
   With the paper's figures the manufactured-N reductions are about 80% and 86%; with Table S3 they are 78% and 85%.
3. Keep yield, profit and weed claims attributed to the paper. The supplement has no plot-level yields. Paper means (2003-2011):
   maize 12.3 / 12.7 / 12.9 Mg/ha, soybean 3.4 / 3.8 / 3.8 Mg/ha, harvested mass 7.9 / 8.5 / 8.6 Mg/ha (2-yr / 3-yr / 4-yr).
   Net returns showed no significant difference between systems.

## Limitations

Single research site (Marsden Farm, Boone Co.), nine seasons, treatment-level table values (not plot-level records).
Manure N is total N in composted manure, not plant-available N. Herbicide is mass of active ingredient, not toxicity;
insecticides (2007-2009) are excluded. Table S3 lists manure on the maize row although Text S1 says it went on clover/alfalfa
in October (no effect on the averages). Not a field-level prediction and no soil-carbon, erosion or nitrate claims.

## Handoff to the DE

* `data/raw/marsden/pone.0047149-supplement/2026-11-13/` follows the `raw/<source>/<version>/<date>/` layout and is gitignored. `MANIFEST.json` (tracked copy: `transform/marsden/manifests/2026-11-13.json`)
  has URL, version, SHA-256, size and licence per file (retrieval date is the date the files reached DS2; confirm the
  licence version on the article page).
* `data/out/marsden/management_by_year.csv`, `management_summary.csv` -> ClickHouse (tables for Marsden evidence).
* `data/out/marsden/indicator_lineage.json` -> `indicator_lineage` (four rows, one per derived indicator).
* `data/out/marsden/reconciliation.csv` -> evidence / validation record. `data/out/marsden/run_manifest.json` -> run manifest (script and input checksums).
* Inputs are verified against the manifest before every run; a mismatch aborts.
* Not yet done: Pandera schema (checks are plain Python for now), `make check` wiring.
