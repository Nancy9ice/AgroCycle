# Requirements: Raw data into S3

## Covers
- **PRD requirements:** FR-02, FR-03, FR-04, FR-05, FR-07 (sources only), NFR-01, NFR-03, NFR-04, NFR-07
- **Roadmap exit check satisfied:** each source has its raw files in S3 with a manifest and a verified checksum.

## Scope and decisions
- In scope: S3 layout, manifest and checksum tooling, and raw extraction of CDL, SSURGO, NASA POWER, the Marsden supplementary files and a bounded HLS sample, plus the one-field, one-season dev sample.
- Sheets: `docs/source_requirements/ds1_source_requirements.md` (CDL, HLS) and `ds2_source_requirements.md` (POWER, SSURGO, Marsden).
- **Decided (with DS1 or DS2):**
  - CDL is the resampled 30 m for all years, 2024-2025 marked as resampled (DS1). The sheet is edited to say so.
  - The DE downloads Marsden from Europe PMC. The sheet is edited to say so (DS2).
  - Phase 1 stores raw service responses verbatim. The sheet's cleaning rules (-999 to null, SSURGO area shares, `power_daily`, hard and soft checks) apply in Phase 4. Marsden cleaned tables and `indicator_lineage.json` are derived and stay out of `raw/` (DS2).
  - One manifest per file, in our format. The layout is lowercase `raw/<source>/<product-version>/<retrieval-date>/`.
- **Open with DS1** (the sheet and this spec disagree until answered):
  1. CDL years: sheet 2008-2025, held 2015-2025 (the fields were selected on 2015-2025).
  2. CDL deliverable: sheet wants one clip per field per year from statewide rasters (810 files); the spec uses one clip per county per year, with field clipping in Phase 3.
  3. Field ids in the sheet (`field_primary`) differ from the real ones (`primary-001`, `test-001` to `test-044`).
  4. HLS Fmask: the sheet's value table is wrong, as Fmask is a bit-flag layer. DS1 to rewrite the rule from the HLS v2.0 User Guide.
  5. HLS S30 NIR band: sheet says B08; B8A pairs with Landsat B05. DS1 to confirm.
  6. HLS masking: sheet asks for masked NaN bands; the roadmap masks in Phase 5, so raw keeps the original bands and the raw Fmask.
  7. HLS area: windowed clips per field (or one clip over all fields) instead of whole tiles. Tiles over the fields are `T15TVG` (all 45) and `T15TUG` (6).

## Inputs
- `data/fields/fields.geojson` (45 fields, EPSG:4326)
- The two sheets above
- Existing CDL clips: 2015-2025 for Story and Boone, EPSG:5070, 30 m, with class tables
- **POWER:** daily point API, `community=AG`, JSON, 1991-01-01 to 2025-12-31; points are the centroid of every field plus the Marsden site (42.0167 N, -93.7833 W); variables `T2M_MAX`, `T2M_MIN`, `T2M`, `PRECTOTCORR`, `RH2M`, `ALLSKY_SFC_SW_DWN`, `WS2M`; the same time standard everywhere
- **SSURGO:** Soil Data Access, per field polygon (WGS84 WKT), the sheet's steps A to D, with the fallback query if step A is rejected
- **Marsden:** the 7 supplement files of Davis et al. (2012) from Europe PMC (PMC3468434)
- Credentials from the local `.env`: AWS, NASA Earthdata

## Outputs
- Raw files at `s3://<bucket>/raw/<source>/<product-version>/<retrieval-date>/`
- A manifest beside every raw file (`<file>.manifest.json`):

| Field | Meaning |
|---|---|
| `source_url` | where the file came from (or the export route, for the CDL clips) |
| `product`, `version` | product name and version or release |
| `retrieval_date` | date pulled |
| `sha256`, `size_bytes` | checksum and size of the raw file |
| `licence` | licence or terms |
| `subset` | the subset requested (bbox, point or query, years, bands, field ids mapped to the file) |
| `evidence_type`, `scale` | project evidence label and spatial scale |
| `notes` | caveats, for example "resampled 30 m for 2024-2025" |

- `data/sample/`: the one-field (`primary-001`), one-season dev sample

## Acceptance criteria
1. Every raw file in S3 has a manifest, and the manifest's SHA-256 equals the hash of the object read back from S3.
2. Uploading to an existing key is refused, so raw files are never overwritten.
3. Each file opens, and its bbox covers the requested fields, its CRS matches and its date range matches the request.
4. Each source has a recorded subset and size budget, and the pulled size is within the budget.
5. The existing CDL clips and class tables are in S3 with manifests that state the website export route and the resampled 30 m for 2024-2025.
6. HLS records valid-observation counts and gaps, as the sheet specifies, so Phase 5 can compute denominators.
7. POWER: one raw JSON per unique grid cell, each covering 1991-2025 for every requested variable (12,784 days), fill values left as returned, the response header kept, and the field-to-cell mapping in the manifest.
8. SSURGO: raw responses for steps A to D for each field, with the full query in the manifest. Marsden: the ZIP and the 7 extracted files, none an HTML error page.
9. `data/sample/` exists, is small, and a test loads it.
10. DS2 has reviewed the first POWER pull (Marsden site, 2003-2011) and the first SSURGO pull (`primary-001`) before the full runs; DS1 has reviewed the first CDL and HLS pulls. Each review is recorded.
11. No secret, raw file or large data is committed.
12. `make check` passes.

## Evidence labels, scale and limitations to preserve
- CDL: classified output, 30 m, agreement with another classification. 2024-2025 are the resampled product, not native 10 m.
- SSURGO: survey information, map-unit scale. POWER: model/reanalysis, grid scale of about 50 km (two fields in one cell get identical climate). HLS: observed product, 30 m. Marsden: experimental record and published finding for one Iowa research setting.
- The manifest `notes` carry each limitation. No source is described as field-level measurement unless it is.

## Out of scope
Cleaning and loading into ClickHouse (Phase 2 onward), masks, fill-value conversion, area shares and indicators (DS and Phase 3 to 5), the P1 sources (Phase 12), and the HLS-versus-CDL decision (Phase 5).
