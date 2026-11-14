# Plan: Raw data into S3

- **Role:** de
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 1, DE: S3 layout, manifest and checksum tooling, and extraction of all P0 sources into `raw/`

## Goal
Every P0 source (CDL, SSURGO, NASA POWER, Marsden files, a bounded HLS sample) sits in S3 as untouched raw files, each with a manifest and a verified checksum, plus a one-field, one-season sample for dev and tests.

## Approach
- Shared tooling first, then one small extractor per source. Source specifics (variables, bands, years, queries, what a correct file looks like) come from the sheets in `docs/source_requirements/`, not from this plan.
- **Raw means as returned.** Phase 1 stores service responses and downloads verbatim. Fill-value conversion, masks, area shares and tables are Phase 3 to 5 work. DS2 agreed this for POWER, SSURGO and Marsden.
- Subset before download, per source: POWER by field centroid, SSURGO by field polygon, CDL by county clip, HLS by field bbox plus buffer. Subset and size budget are recorded in each manifest.
- Raw files are immutable. The upload tool refuses to write a key that already exists, and the IAM user cannot delete, so each source is dry-run first.
- Layout is the tech-stack one in lowercase, `raw/<source>/<product-version>/<retrieval-date>/`, with one manifest per file. The retrieval date is the day of the pull.
- Marsden is downloaded by the DE from Europe PMC, not copied from `ds2_marsden/` (confirmed with DS2).

## Files, tables and endpoints
- Done: `ingest/manifest.py`, `ingest/s3_store.py`, `ingest/subset.py`, `ingest/checks.py`, `ingest/cdl.py`, `ingest/run.py`, `scripts/smoke_ingest.py`, and their tests
- To build: `ingest/power.py`, `ingest/ssurgo.py`, `ingest/marsden.py`, `ingest/hls.py`
- `data/sample/`: the one-field, one-season sample (small files only)
- New dependencies as needed (for example `pystac-client`, `earthaccess`, `httpx`), added with `uv add` and listed in the PR
- S3 objects: `raw/<source>/...` (nothing else; `smoke/` stays for smoke tests)

## Steps (in order)
1. **Claim the task.** Done: Phase 1 DE row is In progress.
2. **Tooling.** Done: manifest, no-overwrite S3 store with checksum verification, subset module, file checks, tests, and a real-bucket smoke test.
3. **CDL.** Dry run done for the 22 clips and 22 class tables (2015-2025, confirmed by DS1). Ready to upload with `python -m ingest.run cdl --execute`. DS1 reviews the upload.
4. **Marsden.** Download the 7 supplement files as one ZIP from Europe PMC, store the ZIP and the extracted files with manifests. DS2 reviews.
5. **POWER.** One raw JSON per unique grid cell (centroids of the 45 fields plus the Marsden site), 1991-2025. First pull is the Marsden site for 2003-2011; DS2 reviews it before the full run.
6. **SSURGO.** Raw Soil Data Access responses (steps A to D) per field polygon. First pull is `primary-001`; DS2 reviews it before the full run.
7. **HLS sample.** Per-field windowed COG reads with a 500 m buffer, April to October, 2023-2025. L30: B04, B05, B06, Fmask. S30: B04, B8A, B11, Fmask. Original bands stored unmasked; DS1 masks in Phase 5. DS1 reviews the first pull (`primary-001`, 2023).
8. **Dev sample.** Build the one-field, one-season sample from `primary-001` into `data/sample/`.
9. **Close.** Fill in `validation.md`, update the tracker row.

## Dependencies and interfaces with other roles
- **DS1 sheet (CDL, HLS):** questions answered. DS1's updated sheet is in the repo; the remaining differences are listed in `requirements.md`.
- **DS2 sheet (POWER, SSURGO, Marsden):** all questions answered; DS2 reviews each first pull.
- **Phase 0 (Done):** `data/fields/fields.geojson`, `common/config.py`, the S3 bucket.
- **Downstream:** Phases 2 to 6 read from `raw/` using the manifests and layout defined here. A change to the layout must be announced to DS1, DS2 and BE.
- **Credentials:** NASA Earthdata (HLS) goes in the local `.env`.

## Data size and subsets
Proposed caps, adjusted to the sheets:

| Source | Subset | Cap |
|---|---|---|
| CDL | county clips and class tables (44 files, 39.6 MB for 2015-2025) | 100 MB (a 2008-2025 window would be about 63 MB) |
| SSURGO | per field polygon, tabular JSON | 200 MB |
| POWER | a few unique grid cells, daily, 7 variables, 1991-2025 | 100 MB |
| Marsden | 7 supplement files, one ZIP (about 4.2 MB) | 50 MB |
| HLS | field windows plus 500 m buffer, 4 bands, 3 seasons | 3 GB |

## Risks and open questions
- The IAM user cannot delete S3 objects, so a bad upload stays. Dry run and the no-overwrite check mitigate this.
- HLS needs an Earthdata login, and the data sits in `us-west-2`, so pulls from a laptop are slow. Windowed reads keep this workable. Whole tiles would be far over budget.
- USDA services have been unreliable (the CDL clip service timed out; the CroplandCROS download link fails). The same may happen for SSURGO.
- PMC and PLOS block scripted downloads. Europe PMC works but is slow. The paper PDF is optional.
- DS2 did not verify the SSURGO main query (`STIntersection`) live. The first pull tests it; the fallback query is known to work.
