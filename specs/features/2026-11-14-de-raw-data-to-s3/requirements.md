# Requirements: Raw data into S3

## Covers
- **PRD requirements:** FR-02, FR-03, FR-04, FR-05, FR-07 (sources only), NFR-01, NFR-03, NFR-04, NFR-07
- **Roadmap exit check satisfied:** each source has its raw files in S3 with a manifest and a verified checksum.

## Scope and decisions
- In scope: S3 layout, manifest and checksum tooling, and raw extraction of CDL, SSURGO, NASA POWER, the Marsden supplementary files and a bounded HLS sample, plus the one-field, one-season dev sample.
- Sheets: `docs/source_requirements/ds1_source_requirements.md` (CDL, HLS) and `ds2_source_requirements.md` (POWER, SSURGO, Marsden).
- **Decided with DS2:**
  - The DE downloads Marsden from Europe PMC (sheet edited to say so).
  - Phase 1 stores raw service responses verbatim. The cleaning rules (-999 to null, SSURGO area shares, `power_daily`, hard and soft checks) apply in Phase 4. Marsden cleaned tables and `indicator_lineage.json` are derived and stay out of `raw/`.
- **Decided with DS2 (2026-11-14, reply relayed by the DE):** the full POWER and SSURGO runs may start. POWER is one request per field centroid plus the Marsden site (46 requests), with identical series grouped in Phase 4. `GWETROOT` and `GWETTOP` are not pulled, since nothing reads them.
- **Decided with DS1 (2026-11-14):**
  - CDL is the resampled 30 m for all years, 2024-2025 marked as resampled (sheet edited to say so).
  - CDL window is 2015-2025, so the clips already held are the ones to upload. One clip per county per year is the raw copy; DS1 does the per-field clipping in Phase 3, using the real field ids (`primary-001`, `test-001` to `test-044`).
  - HLS bands: Landsat B04, B05, B06; Sentinel-2 B04, B8A, B11; plus Fmask for both. The original bands are stored unmasked, and DS1 applies the mask (Phase 5), using the corrected bit-flag rule in DS1's updated sheet.
  - HLS area: per-field windowed clips with the 500 m buffer, not whole tiles. Tiles over the fields: `T15TVG` (all 45) and `T15TUG` (6).
- **Scope change (2026-11-14, project lead):** the HLS full run (45 fields, 2023-2025) is carried to Phase 5 so Phase 1 does not wait about two hours for it. Criteria 6 and 10 for HLS are met by the `primary-001` 2023 first pull only; the full run's own results are recorded in the Phase 5 spec.
- **Both:** one manifest per file in our format; lowercase layout `raw/<source>/<product-version>/<retrieval-date>/`, retrieval date being the day of the pull.
- **Decided by the DE, DS1 informed (2026-11-14):**
  - Fmask bit table corrected in our copy of the sheet from NASA's HLS v2.0 User Guide (Table 9): mask is bits 1-5, `Fmask & 0b00111110 == 0`. Her original in `specs/features/2026-11-14-ds1-hls-cdl-requirements/` is unchanged.
  - CDL keeps its original CropScape names (`CDL_<year>_<fips>.tif`) with the class table beside each file; the county is in the manifest; the retrieval date is the day of the pull.
  - HLS clips are plain windowed GeoTIFFs, not COGs: at about 58 x 56 pixels there is nothing to gain.
  - HLS stack names carry the sensing time, `<field>/<date>/T<hhmmss>_stack_<bands>.tif`, because a tile can have two scenes on one day (a real second overpass, found on 2025-04-10) and a date-only name would drop one.
  - HLS scene search asks for 50 results per page: 200 over the whole area returns a 502.
  - HLS tiles: `T15TVG` covers all 45 fields' windows, so the 344 `T15TUG` scenes found are not cut.
  - The HLS first pull (`primary-001`, 2023) stays one file per band, as her sheet says. The full run (45 fields, 3 years) is planned as one stacked file per field per date per sensor (Red, NIR, SWIR1, Fmask; band order in the manifest) to cut about 62,000 files to about 15,000, and reads each scene once for all fields.
  - Alfalfa (code 36) is not counted as pasture/hay in her Phase 3 rule. Not raised now; to settle when her Phase 3 code runs.
- **Open with DS1:** sign-off on the CDL and HLS first pulls, and whether to replace the 5 "mixed" fields that become continuous corn under her Phase 3 rules (default: replace unless she objects).
- HLS first pull size is 3.2 MB for 460 files (her estimate was 50 MB); all 45 fields over 3 years is about 430 MB.

## Inputs
- `data/fields/fields.geojson` (45 fields, EPSG:4326)
- The two sheets above
- Existing CDL clips: 2015-2025 for Story and Boone, EPSG:5070, 30 m, with class tables (the window DS1 confirmed)
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
