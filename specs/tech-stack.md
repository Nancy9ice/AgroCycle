# AgroCycle — Tech Stack

Decisions made for the 2-day hackathon. Keep it boring and fast; deviate only with team agreement.

## Architecture at a glance

```
 Sources (HLS, POWER, CDL, SSURGO, Marsden, NAIP, NASS, AMS, PRISM, SMAP/GPM)
        │  ingestion jobs (Python)
        ▼
 S3  ── raw, immutable, original source metadata kept (raw/<source>/<version>/<retrieval-date>/)
        │  transform jobs (Python)
        ▼
 ClickHouse ── curated, transformed tables behind the app (indicators, profiles, evidence, lineage)
        │
        ▼
 FastAPI ── field profile, indicators, Marsden evidence, decision engine, provenance
        │  JSON (OpenAPI contract)
        ▼
 React + Vite ── map, profile, scenario comparison, constraints form, evidence/provenance panels
```

The app **reads only from ClickHouse** (transformed data). It never calls external data APIs at request time, so the demo cannot fail on a live service.

## Data layer

| Concern | Choice | Notes |
|---|---|---|
| Raw storage | **Amazon S3** | Store raw downloads untouched (GeoTIFF/COG, JSON, CSV, Marsden supplementary files). Layout `s3://<bucket>/raw/<source>/<product-version>/<retrieval-date>/`. Satisfies the "cache permitted source data" risk mitigation. |
| Serving store | **ClickHouse** | Final transformed data behind the app: indicators, crop history, soil, climate, vegetation time series, Marsden tables, evidence records, lineage. |
| Spatial formats | GeoParquet / COG for intermediates | Intermediates may live in S3 under `staging/`. |
| Provenance | Lineage table in ClickHouse | One row per derived indicator: source, version, URL, variables, resolution, retrieval date, formula, window, missing-data rule, limitation. |

### ClickHouse modelling guidance
- Use `MergeTree` tables, ordered by `(field_id, <time or indicator>)`.
- Keep a `data_sources` table and a `indicator_lineage` table, and link every indicator row to both.
- Store the evidence-type label as an `Enum` (observed, derived, classified, survey, model_reanalysis, experimental, published, assumption).
- Store valid-observation counts alongside every HLS-derived value.
- Spatial work (zonal stats over the field polygon, raster handling) happens in Python before load. ClickHouse holds the results, not rasters.

## Data processing (Python 3.11+)

| Purpose | Library |
|---|---|
| Vector / geometry | `geopandas`, `shapely`, `pyproj` |
| Raster / HLS | `rasterio`, `rioxarray`, `xarray`, `numpy` |
| STAC / HLS search | `pystac-client` (NASA CMR-STAC), `earthaccess` for Earthdata auth |
| Tabular | `pandas`, `pyarrow` |
| Climate | NASA POWER REST API via `requests` or `httpx` |
| Crop history | CDL via NASS CropScape / `CroplandCROS` API or downloaded annual rasters |
| Soil | SSURGO via USDA Soil Data Access (SDA) SQL service |
| S3 | `boto3` |
| ClickHouse | `clickhouse-connect` |
| Notebooks | Jupyter for exploration only. Anything the app depends on lives in versioned `.py` modules. |

Constraint: process **bounded subsets** (field bbox × a few seasons), not archives; development hardware is limited (NFR-04, NFR-07).

## Backend

| Concern | Choice |
|---|---|
| Framework | **FastAPI** + Uvicorn |
| Models / validation | Pydantic v2; the OpenAPI schema is the contract with the frontend |
| ClickHouse access | `clickhouse-connect` |
| Decision engine | Pure, deterministic Python module (no I/O, no LLM) with unit tests |
| Tests | `pytest` |
| Lint / format | `ruff` |
| Env / packaging | `uv` (or `pip` + `venv`); one `pyproject.toml`; secrets via `.env`, never committed |

Core endpoints (indicative):
- `POST /fields` validates the polygon and records boundary provenance (real vs demo)
- `GET /fields/{id}/profile` returns crop history, soil, climate and vegetation indicators
- `GET /evidence/marsden` returns reproduced management comparisons
- `POST /fields/{id}/compare` takes farmer constraints and priorities and returns strategies, trade-offs, applicability and the outcome (worth exploring / qualified comparison / abstention)
- `GET /lineage/{indicator_id}` returns the provenance for any output

The decision engine returns structured data with `evidence_type`, `scale`, `limitations` and `unknown` flags. It never returns free-form conclusions.

## Frontend

| Concern | Choice |
|---|---|
| Framework | **React + Vite + TypeScript** |
| Map | MapLibre GL JS (or Leaflet) with a field polygon draw/upload |
| Charts | Recharts or Plotly for timelines (rainfall, temperature, NDVI with valid-observation markers) |
| Data fetching | TanStack Query; types generated from the FastAPI OpenAPI schema |
| Styling | Tailwind CSS |
| Key components | Field selector, profile dashboard, scenario side-by-side, constraints form, evidence/provenance drawer, "unknown / not assessed" states |

Frontend develops against **mocked JSON that matches the OpenAPI contract** until the real API is up.

## Optional AI use

AI may only phrase explanations of already-computed, structured outputs. It must not generate evidence or conclusions. Not required for the MVP; skip it if time is short.

## Infrastructure and tooling

- Git repo with a monorepo layout: `/ingest`, `/transform`, `/api`, `/engine`, `/web`, `/specs`, `/docs`.
- `docker compose` for local ClickHouse; a shared S3 bucket for raw data.
- Deployment: local demo is acceptable. Optionally deploy the API and web on a single small host. The demo must run from ClickHouse + S3 data already loaded.
- Required secrets (kept out of git): NASA Earthdata credentials, AWS credentials, ClickHouse credentials.

## Testing and validation tooling

- `pytest` for the decision engine (in-domain, out-of-domain, abstention cases) and Marsden reconciliation (74.5 / 56.6 / 40.8 kg N/ha/yr; herbicide 1.925 / 0.261 / 0.195).
- CDL validation reports a confusion matrix and class-wise metrics, with correct terminology (agreement with another classification ≠ independent validation).
- HLS: report valid-date counts and gap summaries; compare against the CDL baseline to decide whether HLS stays.

## Data integrity

No dbt and no Great Expectations. Integrity is enforced with lightweight Python checks at each layer, and a failed check stops the load.

### 1. Ingestion (raw → S3)
- Write a **manifest** beside every raw file: source URL, product and version, retrieval date, SHA-256 checksum, size and licence (PRD §6.1).
- Verify the checksum after upload. Raw files are immutable and never overwritten.
- Confirm the file opens, its bounding box covers the field, and its CRS and date range match the request.

### 2. Transform (Python, before loading)
- **Pandera** (or Pydantic) schemas on every DataFrame: column types, units, allowed ranges (e.g. NDVI in [−1, 1], precipitation ≥ 0), enum values and required non-null fields. Validate before every ClickHouse load and fail loudly.
- **Geometry checks** (shapely): polygon is valid and non-empty, lies within Story or Boone County, and is flagged real or demo.
- **Domain checks:**
  - HLS: valid-observation counts are always present. Periods with too few valid observations are labelled `unknown`, never classified.
  - CDL: product version and resolution recorded, including the 30 m → 10 m change from 2024.
  - POWER: fill values (e.g. −999) converted to null, and gaps in the daily series reported.

### 3. ClickHouse
- Typed columns, `Enum` for evidence type, `LowCardinality` where it fits.
- Plain `MergeTree` tables (not `ReplacingMergeTree`: it dedups only at merge time and needs `FINAL` to read correctly, which is costly on huge data). Make loads idempotent at the partition level: load each batch into a staging table with the same schema, then `ALTER TABLE … REPLACE PARTITION … FROM <staging>`, so reruns swap the partition atomically and cannot create duplicates. Partition so a reload maps onto whole partitions (e.g. by year).
- Add a `load_id` column linked to the run manifest so every row traces to the run that wrote it.
- Use `AggregatingMergeTree` or materialized views only for pre-aggregated tables, where they genuinely help.
- Post-load SQL assertions run by a script: row counts match the staged file, no nulls in key columns, no duplicate `(field_id, indicator, date)` keys, and no indicator row without a matching `indicator_lineage` row.

### 4. Reproducibility
- Pinned dependencies (`uv.lock`) and a **run manifest** per pipeline run: code git SHA, input checksums and config.
- Loads are idempotent. Running the pipeline twice on the same raw files must give identical table hashes, and this is tested.

### 5. Scientific correctness (`pytest`)
- Marsden reconciliation to the known values (total N 74.5 / 56.6 / 40.8; herbicide 1.925 / 0.261 / 0.195).
- Golden-file tests for selected indicators (e.g. growing degree days for one season, computed by hand).
- Decision-engine cases: in-domain, out-of-domain, missing data and abstention.

### 6. Gate
- One command (`make check`) runs the schema checks, post-load assertions and `pytest`. It must pass before loading to ClickHouse and before the demo. Add it as a pre-commit hook or CI step if time allows.

## Large-data optimisation

Rule: **shrink data as early as possible; everything downstream reads small, pre-aggregated tables.**

- **Subset before download.** Fix a size budget and the subset (field bbox + buffer, growing-season windows, a few seasons). For HLS, filter by tile, date and cloud cover in the STAC query, fetch only needed bands (red, NIR, SWIR, `Fmask`), and use windowed COG reads (`/vsicurl/`) instead of whole tiles. Request CDL, SSURGO and POWER by bbox or point, never statewide. Keep a one-field, one-season sample for dev and tests. The budget scales with the field count: one primary demo field plus a test set of ~30–50 fields in Story/Boone, stored as GeoJSON with `field_id`, `role` (`primary`/`test`) and boundary provenance.
- **Store features, not pixels.** Compute zonal stats per field per date (mean/median NDVI, valid and total pixel counts) at transform time and load only those rows into ClickHouse. Full rasters stay in S3.
- **Compute lazily and in parallel.** Use `xarray`/`dask` chunks (e.g. 512×512), threads for I/O, processes for CPU work, `float32`, and one field at a time. Make jobs resumable per scene (skip if the output exists).
- **Formats.** COG for rasters; Parquet/GeoParquet (zstd) for tables and vectors. Partition S3 paths by source/year. Run heavy HLS extraction in AWS `us-west-2` (where HLS is hosted) to avoid slow transfers.
- **ClickHouse.** Batch inserts only (never row-by-row), bulk-loading from Parquet in S3. `ORDER BY (field_id, indicator, date)` with a coarse `PARTITION BY`. Compact types (`Float32`, `LowCardinality`, avoid `Nullable`) and codecs (`Delta`/`ZSTD`). Serve the API from pre-aggregated tables or materialized views, and check queries with `EXPLAIN`.
- **API and frontend.** Paginate with hard `LIMIT`s, downsample long time series for charts, and cache stable responses (the data is read-only at demo time). Use tiled COG or vector tiles for map layers; never ship raw GeoTIFFs or large GeoJSON to the browser.
- **Keep it honest.** Re-run golden-file and Marsden tests after any performance change, keep valid-observation counts through subsetting and downsampling, and record the subset in the lineage and manifest.

## Explicit non-choices

PostGIS, Streamlit, Next.js, dbt, Great Expectations, a live-API-at-request-time design, and ML yield models are out for the hackathon.
