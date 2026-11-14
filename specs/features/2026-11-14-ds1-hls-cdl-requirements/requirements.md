# Requirements: HLS and CDL source requirements sheet

## Covers
- **PRD requirements:** FR-02 (Crop history — CDL), FR-04 (Vegetation and bare-field analysis — HLS), §6 Data Requirements and Evidence Status, §6.1 Data provenance requirements, §6.2 Evidence-type labels, §6.3 Known limitations
- **Roadmap exit check satisfied:** "each source has its raw files in S3 with a manifest and a verified checksum" (Phase 1 exit)

## Inputs

| Item | Source | Notes |
|---|---|---|
| Field polygons (GeoJSON) | Phase 0 output | `field_id`, `role` (primary/test), `boundary_source`, county, provenance |
| HLS product docs | [S03] https://hls.gsfc.nasa.gov/ | L30 (Landsat) and S30 (Sentinel-2) surface reflectance |
| CDL product docs | [S06] https://www.nass.usda.gov/Research_and_Science/Cropland/ | Annual crop classification rasters |
| NASA CMR-STAC API | For HLS discovery | Via `pystac-client` and `earthaccess` for auth |

## Outputs

Two requirements sheet documents placed at:

```
specs/features/2026-11-14-ds1-hls-cdl-requirements/hls-requirements-sheet.md
specs/features/2026-11-14-ds1-hls-cdl-requirements/cdl-requirements-sheet.md
```

These sheets must specify:

| Section | Details required |
|---|---|
| Product and version | Exact product name, version, provider |
| Access method | API endpoint, data URL pattern, authentication |
| Spatial subset | Per-field bbox + buffer (e.g. 500 m), or one merged bbox covering all fields |
| Temporal subset | Years, growing-season start/end, number of seasons |
| Bands / variables | Exactly which bands (HLS: red, NIR, SWIR1, Fmask; CDL: class layer only) |
| Quality masks | Which flags to apply, what to discard (HLS: cloud, cloud-shadow, snow, water; CDL: no-data/background) |
| Output format | COG, GeoTIFF, format specs |
| Delivery location | S3 path pattern: `s3://<bucket>/raw/<source>/<version>/<retrieval-date>/` |
| Size budget | Estimated MB/field for dev vs full set |
| Validation check | What the DS runs on first pull to confirm correctness |
| Manifest requirements | URL, version, retrieval date, SHA-256, size, licence |

## Acceptance criteria

Each must be testable by DE and DS1.

1. **Completeness:** Each sheet covers all 10 sections listed above.
2. **Clarity:** A competent DE (unfamiliar with NASA data) can implement the extraction from the sheets without asking the DS for clarification on bands, masks, or subsets.
3. **Size-budgeted:** Each sheet includes an explicit size budget per field and for the full test set, consistent with NFR-04 and NFR-07.
4. **Provenance-ready:** Each sheet specifies the manifest fields (URL, version, retrieval date, SHA-256, size, licence) that the DE must write beside every raw file.
5. **Validity check defined:** Each sheet specifies the one-file validation check the DS will run on first delivery (e.g. "open in rasterio, confirm CRS, bbox covers field, date range matches, no all-NaN rasters, quality mask discards expected pixels").

## Evidence labels, scale and limitations to preserve

- **HLS:** evidence type = `Observed / retrieved product`. Scale = 30 m. Limitations per §6.3: affected by cloud, shadow, quality gaps; crop-specific ID not validated at this stage.
- **CDL:** evidence type = `Classified output`. Scale = 30 m (2008–2023) / 10 m (2024+). Limitations per §6.3: classified product, not ground truth; resolution change in 2024 requires accounting.

## Out of scope

- Writing any extraction or processing code.
- Specifying HLS-derived features (NDVI, bare-field windows) — that is Phase 5.
- Specifying CDL-derived features (crop sequence, rotation flags) — that is Phase 3.
- POWER, SSURGO or Marsden sheets — those are DS2's task.