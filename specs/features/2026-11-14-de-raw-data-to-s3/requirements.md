# Requirements: Raw data into S3

## Covers
- **PRD requirements:** FR-02, FR-03, FR-04, FR-05, FR-07 (sources only), NFR-01, NFR-03, NFR-04, NFR-07
- **Roadmap exit check satisfied:** each source has its raw files in S3 with a manifest and a verified checksum.

## Scope and decisions
- In scope: S3 layout, manifest and checksum tooling, and raw extraction of CDL, SSURGO, NASA POWER, the Marsden supplementary files and a bounded HLS sample, plus the one-field, one-season dev sample.
- Subsets per source: POWER by field centroid, SSURGO by field bbox plus buffer, CDL by county clip, HLS by field bbox plus buffer.
- CDL: upload the existing clips as raw. Replace only if DS1's sheet requires something else.
- Each source starts only after its DS sheet is in the repo.

## Inputs
- `data/fields/fields.geojson` (45 fields, EPSG:4326)
- DS1 sheets (HLS, CDL) and DS2 sheets (POWER, SSURGO, Marsden)
- Existing CDL clips: 11 years (2015-2025) times 2 counties, EPSG:5070, 30 m
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
| `subset` | the subset requested (bbox or point, years or seasons, bands) |
| `evidence_type`, `scale` | project evidence label and spatial scale |
| `notes` | caveats, for example "resampled 30 m for 2024-2025" |

- `data/sample/`: the one-field (`primary-001`), one-season dev sample

## Acceptance criteria
1. Every raw file in S3 has a manifest, and the manifest's SHA-256 equals the hash of the object read back from S3.
2. Uploading to an existing key is refused, so raw files are never overwritten.
3. Each file opens, and its bbox covers the requested fields, its CRS matches and its date range matches the request.
4. Each source has a recorded subset and size budget, and the pulled size is within the budget.
5. The existing CDL clips are in S3 with manifests that state the website export route and the resampled 30 m for 2024-2025.
6. HLS records valid-observation counts and gaps, as the sheet specifies, so Phase 5 can compute denominators.
7. `data/sample/` exists, is small, and a test loads it.
8. A DS has reviewed the first pull of each source, and the review is recorded.
9. No secret, raw file or large data is committed.
10. `make check` passes.

## Evidence labels, scale and limitations to preserve
- CDL: classified output, 30 m, agreement with another classification. 2024-2025 are the resampled product, not native 10 m.
- SSURGO: survey information, map-unit scale. POWER: model/reanalysis, grid scale (not field). HLS: observed product, 30 m. Marsden: experimental record and published finding for one Iowa research setting.
- The manifest `notes` carry each limitation. No source is described as field-level measurement unless it is.

## Out of scope
Cleaning and loading into ClickHouse (Phase 2 onward), indicators and features (DS), the P1 sources (Phase 12), and the HLS-versus-CDL decision (Phase 5).
