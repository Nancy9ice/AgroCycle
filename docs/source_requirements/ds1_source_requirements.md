# DS1 Source Requirements Sheet

**From:** DS1 (Hannah)
**Date:** 2026-11-14 (updated)
**For:** Data Engineer (DE)

This document tells you exactly what data to download for the two sources that DS1 owns: CDL (crop maps) and HLS (satellite imagery).

---

# Part 1: CDL (Cropland Data Layer)

## What we need

Download the Cropland Data Layer (USDA's annual crop map) for Story and Boone County, Iowa. Years 2015 to 2025.

## What to download

| Detail | Answer |
|---|---|
| Product | USDA NASS Cropland Data Layer (CDL) |
| Where to get it | [CropScape - NASS CDL Program](https://nassgeodata.gmu.edu/CropScape/) |
| What years | **2015 to 2025** (11 years - matches the field selection window) |
| Which area | Story County and Boone County, Iowa (one GeoTIFF per county per year) |
| Format to deliver | One GeoTIFF per county per year (22 files total: 2 counties x 11 years). Field-level clipping will happen in Phase 3. |
| Resolution | All years at 30 m. Record resolution in the manifest. |
| Important | The field IDs used in the project are `primary-001` and `test-001` through `test-044`. |

## Where to put it

```
s3://<bucket>/raw/cdl/v1.0/<retrieval-date>/cdl_<year>_<county>.tif
```

Example: `s3://<bucket>/raw/cdl/v1.0/2026-11-15/cdl_2023_story.tif`

Write a manifest JSON beside each file (see template below).

## Steps to follow

1. Download the CDL GeoTIFF for each year (2015-2025).
2. Clip to Story County boundary and Boone County boundary separately.
3. Save the county-level GeoTIFFs to S3.
4. Write a manifest for every file.
5. First, do a test: Download and clip 1 county x 1 year. Show me. I will verify. Then do all years.

## Manifest template

```json
{
  "source": "USDA NASS CDL",
  "year": 2023,
  "resolution_meters": 30,
  "county": "Story",
  "crs": "EPSG:5070",
  "retrieval_date": "2026-11-15",
  "sha256": "abc123...",
  "file_size_bytes": 12345,
  "licence": "USDA - public domain"
}
```

## How I will check the test file

1. Open it - confirm it is a valid GeoTIFF.
2. Check it covers the right county.
3. Confirm resolution is recorded (30 m).
4. Check that pixel values are in the expected CDL range.

If all pass, proceed with full extraction.

## Size estimate

Very tiny - no storage concerns.

---

# Part 2: HLS (Harmonized Landsat and Sentinel-2)

## What we need

Download satellite imagery (HLS) over our fields in Story and Boone County, Iowa. Years 2023-2025, growing season only (April-October).

## What to download

We need **surface reflectance** data. We will compute NDVI ourselves later.

| Detail | Answer |
|---|---|
| Product | NASA HLS - **L30 v2.0** (Landsat) + **S30 v2.0** (Sentinel-2) |
| Where to get it | [Earthdata Search](https://search.earthdata.nasa.gov/) - see links below |
| Access | Earthdata Login required (free at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov)) |
| API tooling | `earthaccess` for auth, `pystac-client` for CMR-STAC search |
| What years | 2023, 2024, 2025 |
| What season | April 1 to October 31 each year (Iowa growing season) |
| Which area | Per-field windowed clips with 500 m buffer, or one merged bbox over all fields |
| Tiles | T15TVG (covers all 45 fields), T15TUG (overlaps 6 fields) |
| Bands to get | See table below |

### Links for Earthdata Search

| Product | Get/Skip |
|---|---|
| [HLS L30 v2.0](https://search.earthdata.nasa.gov/search?q=C2021957657-LPCLOUD) | ✅ Get this |
| [HLS S30 v2.0](https://search.earthdata.nasa.gov/search?q=C2021957295-LPCLOUD) | ✅ Get this |
| [HLS L30 VI](https://search.earthdata.nasa.gov/search?q=C3246892554-LPCLOUD) | ❌ Skip (pre-computed NDVI) |
| [HLS S30 VI](https://search.earthdata.nasa.gov/search?q=C3246894861-LPCLOUD) | ❌ Skip (pre-computed NDVI) |

### Which bands to download

| Band name | L30 band | S30 band | Why we need it |
|---|---|---|---|
| Red | B04 | B04 | For NDVI calculation |
| Near-Infrared (NIR) | B05 | **B8A** | For NDVI calculation. Use B8A (narrow NIR) for S30, not B08. This keeps NDVI consistent between L30 and S30. |
| Shortwave Infrared (SWIR1) | B06 | B11 | For detecting bare soil vs residue |
| Fmask (quality) | included | included | Bit-flag layer for cloud, shadow, snow, water detection |

## Fmask quality mask (bit-flags, not simple values)

**Corrected by DE, 2026-11-14,** from the HLS v2.0 User Guide, section 6.4, Table 9. The original table here had every bit shifted.

The HLS v2.0 Fmask layer is a **bit-packed uint8** layer. Each bit is a separate flag:

| Bit | Meaning | Action |
|---|---|---|
| Bit 0 | Cirrus (reserved, not used in v2.0) | Ignore |
| Bit 1 | Cloud | Remove (discard pixels where bit 1 = 1) |
| Bit 2 | Adjacent to cloud/shadow (5-pixel dilation) | Remove |
| Bit 3 | Cloud shadow | Remove |
| Bit 4 | Snow / ice | Remove |
| Bit 5 | Water | Remove |
| Bits 6-7 | Aerosol level (00 climatology, 10 low, 01 medium, 11 high) | Ignore for masking |

**Keep only pixels where bits 1-5 are all 0:** `Fmask & 0b00111110 == 0`.

**Masking will happen in Phase 5** (DS1's task), not during extraction. Store the raw bands and raw Fmask band as-is in S3.

## Where to put it

```
s3://<bucket>/raw/hls/<l30|s30>/v2.0/<retrieval-date>/<field_id>/<date>/<band>.tif
```

Example: `s3://<bucket>/raw/hls/l30/v2.0/2026-11-15/primary-001/20230615/b04.tif`

Format: Cloud-Optimised GeoTIFF (COG) - one file per band per date per field.

Delivery option (choose one):
- **Per-field windowed clips** with 500 m buffer (preferred - keeps data small)
- **One merged clip** over all field bounding boxes (alternative)

## Steps to follow

1. Sign up for an Earthdata Login (if you do not have one).
2. Search Earthdata for HLS L30 v2.0 and S30 v2.0 granules intersecting our field areas (April-October, 2023-2025).
3. Filter - only download bands: Red, NIR (B8A for S30), SWIR1, and Fmask.
4. Clip to per-field windows with 500 m buffer (or merged bbox).
5. Save as COG files to S3. **Do not apply the Fmask mask** - store raw bands and raw Fmask.
6. Write a manifest for every file.
7. First, do a small test: Fetch just primary-001 x 1 growing season (e.g. April-Oct 2023). I will verify.

Tip: HLS data is hosted in AWS us-west-2. Running extraction there will be faster.

## Manifest template

```json
{
  "source": "HLS L30 v2.0",
  "granule": "HLS.L30.T15TVG.20230615T...",
  "bands": ["B04", "B05", "B06", "Fmask"],
  "field_id": "primary-001",
  "crs": "EPSG:32615",
  "retrieval_date": "2026-11-15",
  "sha256": "abc123...",
  "file_size_bytes": 1234567,
  "licence": "NASA Earthdata - free for public use with registration"
}
```

## How I will check the test file

1. Open it - confirm it is a valid COG.
2. Check CRS matches UTM zone 15N (EPSG:32615).
3. Confirm the area covers the field polygon.
4. Check date is within April-October window.
5. Confirm Fmask band is present and is uint8 type.
6. Check reflectance values make sense (Red ~0.02-0.30, NIR ~0.05-0.90).
7. Confirm no file is all-empty.

If all pass, proceed with full extraction.

## Size estimate

| Item | Size |
|---|---|
| Dev sample (primary-001 x 1 season) | ~50 MB |
| All fields x 3 years | ~5-15 GB |

## Note

In Phase 5, I will test whether HLS adds anything useful beyond what CDL already tells us. If it does not, we might drop HLS. So for now, just get the raw data.