# DS1 Source Requirements Sheet

**From:** DS1 (Hannah)
**Date:** 2026-11-14
**For:** Data Engineer (DE)
**Edited by DE, 2026-11-14 (agreed with DS1):** CDL is 30 m for all years, with 2024 and 2025 marked as resampled. See "What to download" and the test checks in Part 1.

This document tells you exactly what data to download for the two sources that DS1 owns: **CDL** (crop maps) and **HLS** (satellite imagery).

---

# Part 1: CDL (Cropland Data Layer)

## What we need

Download the Cropland Data Layer (USDA's annual crop map) for all our fields in Story and Boone County, Iowa. Every year available, from 2008 to 2025.

## What to download

| Detail | Answer |
|---|---|
| Product | USDA NASS Cropland Data Layer (CDL) |
| Where to get it | [CropScape - NASS CDL Program](https://nassgeodata.gmu.edu/CropScape/) - go to the "Download" section or use the WCS API |
| What years | 2008 through 2025 (all available) |
| Which area | Our field polygons in Story and Boone Counties, Iowa |
| Format to deliver | Clipped GeoTIFF - one file per field per year |
| Important: | The native resolution changes in 2024 (30 m to 10 m), but we use the **resampled 30 m product for all years**, because 10 m could not be obtained from the website exports (agreed with DS1, 2026-11-14). Record the resolution and "resampled from 10 m" for 2024 and 2025 in the manifest. |

## Where to put it

**CDL main page:** [https://www.nass.usda.gov/Research_and_Science/Cropland/](https://www.nass.usda.gov/Research_and_Science/Cropland/)

**S3 path for clipped files:**
```
s3://<bucket>/raw/CDL/v1.0/2026-11-14/<field_id>/CDL_<year>_<field_id>.tif
```

Example: `s3://<bucket>/raw/CDL/v1.0/2026-11-14/field_primary/CDL_2023_field_primary.tif`

## Steps to follow

1. Go to [CropScape](https://nassgeodata.gmu.edu/CropScape/) and download the full Iowa CDL GeoTIFF for each year (2008-2025).
2. Clip each raster to the exact shape of each field polygon (cookie-cutter style).
3. Save the clipped files to S3 using the naming convention above.
4. Write a manifest for every file (see template below).
5. First, do a test: Clip just the primary demo field x 1 year (e.g. 2023). Show me the output. I will verify it. Then do all fields x all years.

## Manifest template (save as JSON beside each file)

```json
{
  "source": "USDA NASS CDL",
  "year": 2023,
  "resolution_meters": 30,
  "field_id": "field_primary",
  "crs": "EPSG:5070",
  "retrieval_date": "2026-11-14",
  "sha256": "abc123...",
  "file_size_bytes": 12345,
  "licence": "USDA - public domain"
}
```

## How I will check the test file

1. Open it - confirm it is a valid GeoTIFF.
2. Check it covers the right area (Story/Boone County).
3. Confirm resolution is recorded correctly (30 m for all years; 2024 and 2025 marked as resampled from the native 10 m).
4. The dominant crop class should be maize or soybeans (since we selected a typical rotation field).
5. Confirm no-data pixels (value = 0) are excluded from the pixel counts.

If all pass, proceed with the full extraction.


---

# Part 2: HLS (Harmonized Landsat and Sentinel-2)

## What we need

Download satellite imagery (HLS) over our fields in Story and Boone County, Iowa. We need 3 recent years, only the growing season, only the bands we need, with clouds removed.

## What to download

We need **surface reflectance** data (not the pre-computed Vegetation Indices). We will compute NDVI ourselves later.

| Detail | Answer |
|---|---|
| Product | NASA HLS - **L30 v2.0** (Landsat) + **S30 v2.0** (Sentinel-2) - both 30 m resolution |
| Where to get it | Search via **Earthdata Search**: |
|  | -> [HLS L30 v2.0](https://search.earthdata.nasa.gov/search?q=C2021957657-LPCLOUD) ✅ Get this |
|  | -> [HLS S30 v2.0](https://search.earthdata.nasa.gov/search?q=C2021957295-LPCLOUD) ✅ Get this |
|  | -> [HLS L30 VI](https://search.earthdata.nasa.gov/search?q=C3246892554-LPCLOUD) ❌ Skip (pre-computed NDVI - we will do it ourselves) |
|  | -> [HLS S30 VI](https://search.earthdata.nasa.gov/search?q=C3246894861-LPCLOUD) ❌ Skip (same reason) |
| Access | You need an **Earthdata Login** (free) - sign up at [urs.earthdata.nasa.gov](https://urs.earthdata.nasa.gov) |
| API tooling | Use `earthaccess` (Python) for authentication, `pystac-client` to search CMR-STAC |
| What years | 2023, 2024, 2025 - that is 3 years |
| What season | April 1 to October 31 each year (Iowa growing season) |
| Which area | Our field polygons + 500 m buffer around each field |
| Reference site | [HLS Data Access and Tools](https://hls.gsfc.nasa.gov/data-access-and-tools/) - for documentation |

### Which bands to download

| Band name | L30 band | S30 band | Why we need it |
|---|---|---|---|
| Red | B04 | B04 | For NDVI calculation |
| Near-Infrared (NIR) | B05 | B08 | For NDVI calculation |
| Shortwave Infrared (SWIR1) | B06 | B11 | For detecting bare soil vs residue |
| Fmask (quality) | included | included | Tells us which pixels have clouds/shadows |

Only these 4 - do not download all the other bands.

## Cloud removal (important)

Satellite images have clouds. We need to remove them so we do not mistake cloudy pixels for bare soil.

| Fmask value | Meaning | Keep or remove? |
|---|---|---|
| 0 | Clear sky | Keep ✅ |
| 1 | Water | Remove ❌ |
| 2 | Cloud shadow | Remove ❌ |
| 3 | Snow | Remove ❌ |
| 4+ | Cloud | Remove ❌ |

Deliver the masked bands (clouds removed, set to NaN) AND the raw Fmask band so we can verify.

## Where to put it

```
s3://<bucket>/raw/HLS/<L30|S30>/v2.0/2026-11-14/<tile>/<date>/<band>.tif
```

Example: `s3://<bucket>/raw/HLS/L30/v2.0/2026-11-14/T15TUN/20230615/B04.tif`

Format: Cloud-Optimised GeoTIFF (COG) - one file per band per satellite pass.

## Steps to follow

1. Sign up for an Earthdata Login (if you do not have one).
2. Search Earthdata for HLS L30 v2.0 and S30 v2.0 granules intersecting our field areas (April-October, 2023-2025).
3. Filter - only download bands: Red, NIR, SWIR1, and Fmask.
4. Apply the Fmask quality mask (remove cloud, shadow, snow, water).
5. Save as COG files to S3 with the naming convention above.
6. Write a manifest for every file.
7. First, do a small test: Fetch just the primary demo field x 1 growing season (e.g. April-Oct 2023). I will verify. Then do all fields x all years.

Tip: HLS data is hosted in AWS `us-west-2`. If your extraction runs there, you will avoid slow cross-region transfers.

## Manifest template (save as JSON beside each file)

```json
{
  "source": "HLS L30 v2.0",
  "granule": "HLS.L30.T15TUN.20230615T...",
  "bands": ["B04", "B05", "B06", "Fmask"],
  "field_area": "Story/Boone Counties, Iowa",
  "crs": "EPSG:32615",
  "retrieval_date": "2026-11-14",
  "sha256": "abc123...",
  "file_size_bytes": 1234567,
  "licence": "NASA Earthdata - free for public use with registration"
}
```

## How I will check the test file

1. Open it - confirm it is a valid COG.
2. Check CRS matches UTM zone 15N (EPSG:32615).
3. Confirm the area covers our field polygon.
4. Check date is within April-October window.
5. Confirm Fmask was applied - no clouds or shadows left in the data.
6. Check reflectance values make sense (Red ~0.02-0.30, NIR ~0.05-0.90).
7. Confirm no file is all-empty (all-NaN).

If all pass, proceed with full extraction.


## Note

In Phase 5, I will test whether HLS adds anything useful beyond what CDL already tells us. If it does not, we might drop HLS from the project.