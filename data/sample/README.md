# Dev sample: primary-001, 2023

A small sample (about 0.4 MB) of every Phase 1 source for one field and one season, for development and tests. Nobody needs S3 access to use it.

It is **derived from the raw pulls in S3**, not raw data itself. `sample_manifest.json` lists every file, the S3 object it came from (`derived_from`), that object's SHA-256, the sample's own SHA-256, and how it was cut. Raw data is only ever read from S3.

| Folder | Content | How it was cut |
|---|---|---|
| `primary-001/cdl/` | CDL 2015-2025, 30 m, EPSG:5070 | Story County clip cut to the field plus 500 m |
| `primary-001/hls/l30`, `hls/s30` | 4 fully clear scenes each (April to September 2023), one file per band | Copied unchanged: unmasked, unscaled (reflectance scale 0.0001, fill -9999; Fmask fill 255) |
| `primary-001/power/` | NASA POWER daily, 7 variables, 2023 | The 1991-2025 response cut to 2023, header otherwise unchanged |
| `primary-001/ssurgo/` | Soil Data Access steps A to D | Copied unchanged |

Things to know:
- The field polygon is in `data/fields/fields.geojson`.
- Scale: CDL and HLS are 30 m, POWER is a grid cell of about 50 km, SSURGO is mapped soil units. None is a field measurement.
- HLS Fmask: mask with `Fmask & 0b00111110 == 0` (bits 1 to 5, from the HLS v2.0 User Guide, Table 9).
- Rebuild (DE only, needs the local pull folders): `uv run python -m scripts.build_dev_sample`.
