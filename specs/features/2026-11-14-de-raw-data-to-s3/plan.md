# Plan: Raw data into S3

- **Role:** de
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 1, DE: S3 layout, manifest and checksum tooling, and extraction of all P0 sources into `raw/`

## Goal
Every P0 source (CDL, SSURGO, NASA POWER, Marsden files, a bounded HLS sample) sits in S3 as untouched raw files, each with a manifest and a verified checksum, plus a one-field, one-season sample for dev and tests.

## Approach
- Shared tooling first, then one small extractor per source, each started when its source requirements sheet is in the repo.
- Subset before download, per source: POWER by field centroid, SSURGO by field bbox plus buffer, CDL by county clip, HLS by field bbox plus buffer. Subset and size budget are recorded before each pull.
- Raw files are immutable. The upload tool refuses to write a key that already exists.
- The CDL clips already downloaded (Story and Boone, 2015-2025, 30 m, resampled for 2024-2025) are uploaded as the CDL raw data. They are replaced only if DS1's sheet asks for something different.
- Source specifics (bands, variables, years, masks, what a correct file looks like) come from the DS sheets, not from this plan.

## Files, tables and endpoints
- `ingest/manifest.py`: build, write and read manifests, SHA-256
- `ingest/s3_store.py`: upload to `raw/<source>/<product-version>/<retrieval-date>/`, no overwrite, checksum verification
- `ingest/subset.py`: per-field bbox, buffer, centroid and union from `data/fields/fields.geojson`; size-budget check
- `ingest/checks.py`: file opens, bbox, CRS and date range match the request
- `ingest/cdl.py`, `ingest/ssurgo.py`, `ingest/power.py`, `ingest/marsden.py`, `ingest/hls.py`: one extractor each
- `ingest/run.py`: `python -m ingest.run <source>`
- `data/sample/`: the one-field, one-season sample (small files only)
- `tests/test_manifest.py`, `tests/test_s3_store.py`, `tests/test_subset.py`, `tests/test_checks.py`
- New dependencies as needed (for example `pystac-client`, `earthaccess`, `httpx`), added with `uv add` and listed in the PR
- S3 objects: `raw/<source>/...` (nothing else; `smoke/` stays for smoke tests)

## Steps (in order)
1. **Claim the task.** Set the Phase 1 DE row to In progress.
2. **Tooling.** Manifest module, S3 store with no-overwrite and checksum verification, subset module, open-checks, with tests on small local files and a fake S3 client.
3. **Subsets and budgets.** From the 45 fields, write each source's subset and size budget to a `subset.json` that goes into every manifest.
4. **CDL.** Upload the existing 22 clips with manifests (website export, resampled 30 m for 2024-2025). DS1 reviews the first upload.
5. **SSURGO and POWER.** Extract as the DS2 sheets specify. DS2 reviews each first pull.
6. **Marsden.** Download the supplementary files, upload with manifests. DS2 reviews.
7. **HLS sample.** Search by tile, date and cloud cover, fetch only the sheet's bands, windowed COG reads, bounded to the primary and test fields over 2 to 3 seasons. DS1 reviews.
8. **Dev sample.** Build the one-field, one-season sample from `primary-001` into `data/sample/`.
9. **Close.** Fill in `validation.md`, update the tracker row.

## Dependencies and interfaces with other roles
- **DS1 and DS2 sheets:** CDL and HLS (DS1), POWER, SSURGO and Marsden (DS2). Steps 5 to 7 wait for their sheet. The sheets are being added to the repo; where they live is theirs to confirm.
- **Phase 0 (Done):** `data/fields/fields.geojson`, `common/config.py`, the S3 bucket.
- **Downstream:** Phase 2 and Phases 3 to 6 read from `raw/` using the manifests and layout defined here. A change to the layout must be announced to DS1, DS2 and BE.
- **Credentials:** NASA Earthdata (HLS) goes in the local `.env`.

## Data size and subsets
Proposed caps, to be adjusted against the sheets:

| Source | Subset | Cap |
|---|---|---|
| CDL | county clips, 22 files | 100 MB (existing files are about 38 MB) |
| SSURGO | field bbox plus buffer, tabular | 200 MB |
| POWER | field centroids, daily | 100 MB |
| Marsden | supplementary files | 50 MB |
| HLS | field bbox plus buffer, sheet's bands, 2-3 seasons | 3 GB |

## Risks and open questions
- The IAM user cannot delete S3 objects, and raw files are immutable, so a bad upload stays. A dry-run flag and the no-overwrite check mitigate this.
- HLS needs an Earthdata login, and the data sits in `us-west-2`, so pulls from a laptop are slow. Bounded windows keep this workable.
- The USDA services have been unreliable (the CDL clip service timed out and the CroplandCROS download failed). The same may happen for other sources.
- Marsden file formats and the POWER and SSURGO fields are unknown until the sheets are in.
- The CDL years or source in the DS1 sheet may differ from the clips already downloaded.
