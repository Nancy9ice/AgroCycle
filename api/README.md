# AgroCycle API

The backend service for AgroCycle. It is a FastAPI application that serves field data, runs the rotation decision engine on request, stores the results, and answers questions about them.

This document describes the API as a service: how it is built, what it exposes, where its data comes from, and how to run and debug it. For what AgroCycle is and why, see the [root README](../README.md) and the [PRD](../PRD.md).

**Interactive reference** (served by the running API): `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json`. In production these are at `https://agrocycle.praxicraft.com/redoc` and `/docs`.

## Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [API endpoints](#3-api-endpoints)
4. [Data access](#4-data-access)
5. [Configuration](#5-configuration)
6. [Local development](#6-local-development)
7. [Troubleshooting](#7-troubleshooting)

---

## 1. Overview

The API has four jobs:

- **Serve field data.** List the 45 pre-processed fields, return a field's profile (crop history, weather, soil, each with its provenance), time series and aerial photo, and validate a polygon a user draws.
- **Run the comparison.** Take a field and the farmer's answers, build the field's indicator facts, call the decision engine (`engine/`), and return one of three outcomes: `strategy_worth_exploring`, `qualified_comparison` or `abstention`. There is no score, ranking or winner anywhere in the response.
- **Store and replay results.** Each comparison gets an `analysis_id` and is stored, so it can be fetched again and asked about.
- **Answer questions about stored results.** The ask endpoints call the Claude API with only the stored result or field profile as context, and log every exchange.

It sits between three things:

| Neighbour | Relationship |
|---|---|
| **Frontend** (`web/`, Next.js) | The only client in production. The Next.js server calls the API using `AGROCYCLE_API_URL`; the browser does not call it directly. |
| **Data store** (ClickHouse, plus S3 for aerial photos) | Source of indicators, lineage, sources and photos; destination for stored analyses and the ask log. A file-backed mode runs without either. |
| **Decision engine** (`engine/`) | A pure Python package imported in-process. The API builds its inputs and serialises its output; it does not change its rules. |

There is no authentication. All endpoints are public and read-mostly; the only writes are the analysis store and the ask log.

---

## 2. Architecture

### Components

```
api/
  main.py          App factory (create_app), middleware, exception handlers, /redoc
  settings.py      Settings from environment; builds the repository, ClickHouse client, imagery source
  deps.py          FastAPI dependencies: repository, settings, data_version
  logging_config.py  JSON log formatter
  routes/          One router per domain: meta, fields, imagery, compare, methods, ask
  schemas/         Pydantic request and response models, split the same way
  core/            Logic with no database access: profile building, geometry validation,
                   ask context and Claude call, imagery rendering, serialisation
  db/              Data access: FieldRepository protocol, FileRepository, ClickHouseRepository,
                   imagery source, constraint options
  tests/           pytest
common/            Shared with the pipeline: config.py (clients), migrate.py (schema runner)
engine/            The decision engine and its rules
schema/            Numbered ClickHouse migrations (*.sql)
```

Put new code in `routes/`, `schemas/`, `core/` or `db/`. Top-level modules such as `api/ask.py`, `api/routes.py` and `api/facts.py` are older layouts kept for compatibility; do not add to them.

`create_app(settings, repository, imagery)` accepts all three as arguments, which is how tests run the API against fake or file data without a database.

### Request and response flow

1. **CORS** admits the origins in `AGROCYCLE_CORS_ORIGINS` (methods `GET` and `POST`, header `Content-Type` only).
2. **Request logging** assigns a 12-character `X-Request-ID` and writes one JSON log line with method, path, status and duration. `/health` is not logged.
3. **ETag middleware** adds `ETag: "<data_version>"` and `Cache-Control: public, max-age=3600` to every `GET` that returns 200.
4. **The route** receives the repository, settings and data version through dependencies. Request bodies are validated by Pydantic models that forbid unknown fields.
5. **The handler** reads from the repository, calls `core/` and, for compare, the engine.
6. **Exception handlers** turn errors into the shared envelope (below).

A comparison, end to end:

```
POST /fields/{id}/compare
  -> validate body (strict booleans; null means "not answered")
  -> repository.get_field + get_indicators      (ClickHouse or files)
  -> core.profile.build_profile                 (facts the engine needs)
  -> engine.decision.assess(profile, constraints)
  -> assign analysis_id, stamp engine_version and data_version
  -> repository.store_analysis                  (best effort)
  -> CompareResponse
```

### Mounting

The router is mounted at `/api/v1` and also at the root (`/fields`, `/health`, ...) for callers that predate versioning. Use `/api/v1`. `/docs`, `/redoc` and `/openapi.json` are served at the root only.

### External dependencies

| Dependency | Used for | If unavailable |
|---|---|---|
| ClickHouse | Indicators, fields, lineage, sources, time series, stored analyses, ask log | `data_source=files`: runs without it. `clickhouse`: startup fails if it cannot connect |
| S3 (raw-data bucket) | Aerial photo chips (`/imagery`) | API starts; photos report as unavailable |
| Anthropic API | `/ask` endpoints | Endpoints return 200 with `refused: true` and an explanatory answer |
| Committed files under `data/` | Field polygons, field notes, county boundaries | API will not start without `data/fields/` |

### Errors

Every error the API raises itself uses one envelope:

```json
{ "error": { "code": "not_found", "message": "No field with id 'nope'.", "details": {} } }
```

| HTTP | `code` | Typical cause |
|---|---|---|
| 404 | `not_found` | Unknown field, analysis or indicator id |
| 422 | `validation_error` | Body or query fails validation; `details.errors` holds Pydantic's list |
| 503 | `service_unavailable` | Photo index or chip unreadable; stored analysis unparseable |
| 403 | `error` | `sample_indicators: true` while previews are disabled |
| 500 | (not enveloped) | An unexpected exception, such as a failed ClickHouse query. Logged with traceback; look it up by `X-Request-ID` |

---

## 3. API endpoints

All paths below are relative to `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status, data source, rules version, ClickHouse reachability |
| GET | `/meta/constraint-options` | The farmer questions the compare form must render |
| GET | `/fields/demo` | The pre-processed fields with boundary geometry and area |
| POST | `/fields` | Validate a drawn polygon, or select a demo field |
| GET | `/fields` | List fields (id, county, role, class) |
| GET | `/fields/{field_id}` | One field's metadata |
| GET | `/fields/{field_id}/profile` | Crop history, climate, vegetation and soil, each with provenance |
| GET | `/fields/{field_id}/timeseries` | Climate or NDVI series |
| GET | `/fields/{field_id}/imagery` | Whether an aerial photo exists, when it was flown, where it sits |
| GET | `/fields/{field_id}/imagery/image.png` | The photo |
| POST | `/fields/{field_id}/compare` | Run the comparison |
| GET | `/analyses/{analysis_id}` | Fetch a stored comparison |
| GET | `/evidence/marsden` | Marsden Farm management means the engine's claims rest on |
| GET | `/sources` | Data sources with citation and coverage |
| GET | `/indicators` | Glossary of indicators |
| GET | `/lineage/{indicator_id}` | Full provenance for one indicator |
| POST | `/fields/{field_id}/ask` | Question about a field's profile |
| POST | `/analyses/{analysis_id}/ask` | Question about a stored comparison |

### Health

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "data_source": "files",
  "rules_version": "2026-11-15.2",
  "clickhouse": false,
  "data_version": "files"
}
```

`status` is `degraded` (still HTTP 200) when the API is in ClickHouse mode and `SELECT 1` fails. In file mode `clickhouse` is always `false` and `status` is `ok`.

### Fields and profiles

`GET /fields` returns 45 entries:

```json
{ "field_id": "primary-001", "county": "Story", "boundary_source": "demo", "role": "primary", "field_class": "rotation" }
```

`GET /fields/{id}/profile` returns one object with four sections, `cropHistory`, `climate`, `vegetation` and `soil`, each `{ "status": "available" | "not_loaded", "data": ..., "provenance": ... }`. A section with nothing behind it is `not_loaded`; the API never fills it with sample values. Profile keys are camelCase; most other responses are snake_case.

`GET /fields/{id}/timeseries` takes `kind` (`climate` or `ndvi`, default `climate`), `from` (default `2015-01-01`), `to` (default `2024-12-31`) and `max_points` (10 to 3650, default 365). Climate series are bucketed to stay under `max_points`. In file mode both kinds return an empty `points` list.

### Validating a boundary

`POST /fields` takes either `{ "demo_field_id": "primary-001" }` or `{ "geometry": <GeoJSON>, "name": "...", "boundary_source": "drawn" }`. It always returns 200 with a `valid` flag; read `errors` rather than the status code.

A drawn polygon is checked in this order: parseable and non-self-intersecting, at most 2,000 vertices, between 1 and 1,000 ha (area computed in UTM 15N), and intersecting Story or Boone County, Iowa. Error codes: `invalid_geometry`, `too_many_vertices`, `too_small`, `too_large`, `outside_pilot_area`.

A valid drawn polygon gets a throwaway `drawn-xxxxxxxx` id, `is_preprocessed: false` and `not_assessed` coverage for every source. It is not stored, and no other endpoint can serve data for it.

### Comparing strategies

```bash
curl -X POST http://localhost:8000/api/v1/fields/primary-001/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "manure_access": false,
    "forage_use_or_buyer": null,
    "oat_use_or_buyer": true,
    "small_grain_equipment_or_contractor": null,
    "priorities": ["soil", "water"]
  }'
```

Request fields:

| Field | Type | Notes |
|---|---|---|
| `manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor` | `true`, `false` or `null` | `null` or omitted means unknown and is never read as `false`. Strict: `"yes"` or `1` is a 422, not coerced |
| `priorities` | list of `soil`, `water`, `inputs`, `income`, `forage` | Priorities marked high |
| `sample_indicators` | boolean, default `false` | Demo only. Pretends the four required indicators are known. The response carries `preview: true` |

Response (trimmed):

```json
{
  "field": { "field_id": "primary-001", "county": "Story", "boundary_source": "demo", "role": "primary", "field_class": "rotation" },
  "decision": {
    "field_id": "primary-001",
    "crop_history_summary": "Corn and soybeans alternate every year, 2015 to 2025: ...",
    "outcome": "qualified_comparison",
    "outcome_reason": "the strategies can be compared but not separated: 1 of 5 claimable outcomes were withheld",
    "strategies": [
      { "strategy_id": "B", "label": "Diversified option", "rotation": "Three-year maize-soybean-oat/red clover",
        "feasibility": "qualified", "operational_requirements": ["..."],
        "findings": [{ "rule_id": "applicability_machinery_unknown", "effect": "qualified", "...": "..." }] }
    ],
    "outcomes": ["..."],
    "unknowns": ["..."],
    "constraints_recorded": { "manure_access": false, "...": "..." },
    "priorities_recorded": ["soil", "water"],
    "rules_version": "2026-11-15.2",
    "limitations": ["..."]
  },
  "preview": false,
  "analysis_id": "a_3f9c21",
  "created_at": "2026-11-15T10:42:11.402913+00:00",
  "engine_version": "2026-11-15.2",
  "data_version": "20261101-001"
}
```

`outcome` is one of `strategy_worth_exploring`, `qualified_comparison`, `abstention`. Strategies are `A`, `B`, `C` with `feasibility` of `available`, `qualified` or `unavailable`.

`GET /analyses/{analysis_id}` returns the same payload as it was when stored.

### Ask

```bash
curl -X POST http://localhost:8000/api/v1/analyses/a_3f9c21/ask \
  -H 'Content-Type: application/json' \
  -d '{ "question": "Why is the 3-year rotation qualified?", "audience": "farmer" }'
```

`question` is 1 to 1,000 characters. `audience` is `farmer` (plain language, 2 to 4 sentences) or `adviser` (technical, up to 6). Unknown fields are rejected.

```json
{
  "answer": "...",
  "citations": ["gdd", "om_r_0_30cm"],
  "refused": false,
  "model": "claude-opus-4-7",
  "log_id": "ask_7a3c1b2d"
}
```

How it stays grounded:

- The model receives only the stored analysis (or field record and indicator facts) plus the indicator lineage rows. It is told to use nothing else and to refuse questions about yield, profit, other regions or other farms (`refused: true`).
- It is forced to answer through a single `provide_answer` tool call, so the response is structured.
- `citations` are filtered to indicator ids actually present in the context.
- Banned phrasing (for example "recommended", "best option", "guaranteed") is replaced before the answer is returned.
- Requests time out after 45 seconds.

Clients that show these answers must label the panel **"AI explanation of AgroCycle's computed results"**, so users can tell it apart from the engine's own output.

Ask never returns an error status for an AI-side failure. A missing `ANTHROPIC_API_KEY`, a timeout, a rate limit or an upstream error all return **200** with `refused: true` and a one-line `answer` saying what happened. Only a missing field or analysis (404) or an unparseable stored analysis (503) uses the error envelope.

### Aerial photo

`GET /fields/{id}/imagery` returns `available: false` when there is no photo, or `available: true` with `year`, `tiles` (one flight date per source tile), `resolution_m`, `bounds`, `evidence_type`, `attribution` and a `note` stating it is one day's photo and not a crop map. `image.png` returns the picture, or 404 when there is none.

Photos exist only in ClickHouse mode with S3 configured. The chip is verified against the checksum in `naip_tiles` and reprojected to longitude and latitude. A missing, unreadable or checksum-mismatched chip is a 503; it is never replaced with a blank image.

---

## 4. Data access

All routes talk to a `FieldRepository` (`db/repository.py`), chosen once at startup by `AGROCYCLE_DATA_SOURCE`. Routes never build SQL.

| | `files` (default) | `clickhouse` |
|---|---|---|
| Fields | `data/fields/field_selection_notes.csv` and `fields.geojson` | `fields` joined to `crop_rotation` |
| Indicators and soil | `field_indicators.csv` and `soil_properties.csv` from `AGROCYCLE_INDICATORS_DIR` (default `data/out/indicators`), if present | `field_indicators`, `soil_properties` |
| Lineage, sources, Marsden means | Empty (`/lineage/{id}` is 404, `/sources` is `[]`) | `indicator_lineage`, `data_sources`, `marsden_management` |
| Time series | Empty | `climate_points` and `climate_daily`; `hls_ndvi` |
| Aerial photos | None | `naip_tiles` plus chips in S3 |
| Stored analyses | In memory: lost on restart, not shared between workers | `analyses` table |
| Ask log | In memory | `ask_log` table |
| `data_version` | `files` | Latest `load_id` in `field_indicators` |

Both modes turn indicator rows into engine facts through the same function (`facts_from_rows`), so the rules are identical:

- An indicator is `ok` only if **every** season row is `available`. A `partial` or missing season makes it `unknown`, which pushes the engine toward abstention.
- Weather means use only seasons that are `available`, have a value and state their dates; the response reports `seasons_used` of `seasons_total`.
- Soil values that are `unknown` or empty are omitted, never shown as zero. `partial` values are kept with their coverage note.
- DS2's `frost_free_days` is the engine's `frost_window`.
- Field class `rotation` is the in-domain class. A field with no class is unknown, never treated as out of domain.

Two things are read from committed files even in ClickHouse mode: the crop sequence and soil series (from `field_selection_notes.csv`, because the table's crop codes differ from the web app's) and the demo polygons (`data/fields/fields.geojson`). Drawn-polygon validation reads `data/reference/story_boone_counties.geojson`.

### ClickHouse integration

- Client: `clickhouse-connect` over HTTP(S), built by `common/config.py`. Queries use bound parameters (`{field_id:String}`), not string formatting.
- Schema: numbered files in `schema/`, applied by `python -m common.migrate` (or `make migrate`; safe to rerun). The API writes to two tables: `analyses` (007) and `ask_log` (008). Run migrations before starting the API against a new database; in Docker Compose the `migrate` service does this first.
- `data_version` is read once and cached for the process lifetime. After a data load, restart the API so `data_version` and the `ETag` change.
- Field and analysis ids are matched exactly; there is no fuzzy lookup.

### Persistence and failure behaviour

Some failures are deliberately swallowed so that a secondary write cannot break a primary read. Know which:

| Operation | If it fails |
|---|---|
| Storing an analysis after compare | Ignored. The response still carries an `analysis_id`, but `GET /analyses/{id}` and `/ask` on it will 404 |
| Writing the ask log | Ignored. The answer is still returned |
| `hls_ndvi` table missing | `timeseries?kind=ndvi` returns an empty list |
| Reading `data_version` at startup | `unknown`; the API still starts |
| Aerial-photo index query | 503 |
| Any other ClickHouse query on a request | Unhandled, so HTTP 500 and a traceback in the log |
| ClickHouse unreachable at startup (`clickhouse` mode) | The process exits with the connection error |
| ClickHouse unreachable later | `/health` reports `degraded`; data routes 500 |

---

## 5. Configuration

Settings come from environment variables. `.env.example` lists them; copy it to `.env` and fill it in. **Never commit `.env`.**

### Variables

| Variable | Needed for | Default | Notes |
|---|---|---|---|
| `AGROCYCLE_DATA_SOURCE` | Choosing the repository | `files` | `files` or `clickhouse`; anything else aborts startup |
| `AGROCYCLE_CORS_ORIGINS` | Browser access | `http://localhost:3004` | Comma-separated origins |
| `AGROCYCLE_ALLOW_SAMPLE_PREVIEW` | `sample_indicators` | `true` | Set `false` to make `sample_indicators: true` a 403 |
| `AGROCYCLE_INDICATORS_DIR` | File mode | `data/out/indicators` | Where `field_indicators.csv` and `soil_properties.csv` live |
| `CLICKHOUSE_HOST` | `clickhouse` mode | none (required) | |
| `CLICKHOUSE_PORT` | `clickhouse` mode | none (required) | HTTP(S) port, for example 8123 or 8443 |
| `CLICKHOUSE_USER` | `clickhouse` mode | none (required) | |
| `CLICKHOUSE_PASSWORD` | `clickhouse` mode | empty | |
| `CLICKHOUSE_DATABASE` | `clickhouse` mode | `agrocycle` | |
| `CLICKHOUSE_SECURE` | `clickhouse` mode | `true` | HTTPS. Set `false` for a plain-HTTP server |
| `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`, `S3_BUCKET` | Aerial photos | none (all required together) | If any is missing, photos are silently disabled |
| `ANTHROPIC_API_KEY` | `/ask` | none | Not in `.env.example`. Read at call time |

`EARTHDATA_*` and `NASS_API_KEY` in `.env.example` belong to the ingest pipeline; the API does not use them.

### Secrets and credentials

- The secrets are the ClickHouse password, the AWS key pair and `ANTHROPIC_API_KEY`. None is logged or returned by any endpoint.
- Locally they live in `.env` (git-ignored). In Docker Compose, `env_file: .env` passes them into the containers.
- Teammates without S3 access do not need it: tests and the file-backed API skip everything that needs it.

### Local versus deployed

| | Local | Deployed (Docker Compose) |
|---|---|---|
| Data source | `files` unless you export `clickhouse` | `clickhouse`, set in `docker-compose.yml` |
| CORS | `http://localhost:3004` | `https://agrocycle.praxicraft.com` |
| Process | `uvicorn --reload`, one worker | `uvicorn` with 2 workers, port 8000 inside the container |
| Migrations | Run by hand | `migrate` service runs first; `api` waits for it |
| Routing | Direct on port 8000 | Traefik forwards `/api/`, `/docs`, `/redoc`, `/openapi.json` on `agrocycle.praxicraft.com` to the API; no host ports are published |
| Health check | Manual | Compose polls `/api/v1/health` every 30 seconds |

**Where `.env` is read.** The API reads the `AGROCYCLE_*` variables from the process environment when it starts. `.env` is only loaded later, when the ClickHouse or S3 client is first built (`common/config.py`). So a plain `uvicorn` run will not see `AGROCYCLE_DATA_SOURCE=clickhouse` written only in `.env`. Either export it in the shell, or have uv load the file: `uv run --env-file .env uvicorn api.main:app --reload --port 8000`. Docker Compose is unaffected because it injects the environment itself.

---

## 6. Local development

### Prerequisites

- Python 3.11 or newer (CI and the Docker image use 3.12)
- [uv](https://docs.astral.sh/uv/)
- Optional: ClickHouse credentials for `clickhouse` mode, AWS credentials for photos, an Anthropic key for `/ask`
- Optional: Docker, to run the full stack

### Install

```bash
uv sync          # also installs the dev group (pytest, ruff, httpx)
cp .env.example .env
```

### Run

File mode needs no credentials:

```bash
make api
# same as: uv run uvicorn api.main:app --reload --port 8000
```

The API is at `http://localhost:8000`, with the reference at `/docs` and `/redoc`. In file mode, indicator-backed sections of a profile read as `not_loaded` unless DS2's indicator CSVs exist under `data/out/indicators`.

Against ClickHouse (after setting the `CLICKHOUSE_*` variables, see [Configuration](#5-configuration)):

```bash
make migrate
AGROCYCLE_DATA_SOURCE=clickhouse uv run uvicorn api.main:app --reload --port 8000
```

Sanity-check what the API will read for one field, without running the engine:

```bash
uv run python -m api.check_clickhouse primary-001
uv run python -m api.check_imagery primary-001 primary-001.png   # aerial photo, read-only
```

Full stack with Docker:

```bash
docker compose up --build -d
docker compose logs -f api
```

### Test

```bash
uv run pytest api/ -q
```

Tests run against the committed field data through FastAPI's `TestClient`; no database, S3 or API key is needed. Checks that need live ClickHouse or S3 skip themselves when credentials are absent. To make sure none run, blank them: `CLICKHOUSE_HOST="" AWS_ACCESS_KEY_ID="" uv run pytest api/ -q`.

Before pushing, `make check` runs lint, field-file validation, the SQL-versus-schema check and the whole test suite, as CI does (`ruff check .` then `pytest`).

---

## 7. Troubleshooting

**The API exits on startup with `Missing required setting: CLICKHOUSE_...`**
`AGROCYCLE_DATA_SOURCE` is `clickhouse` but a required `CLICKHOUSE_*` variable is not set. `CLICKHOUSE_PORT` has no default. Or switch to `files`.

**`AGROCYCLE_DATA_SOURCE must be 'files' or 'clickhouse'`**
The value is misspelled or has stray whitespace or quotes.

**My `.env` values are ignored**
See [Where `.env` is read](#5-configuration). Export the variable in the shell or use `uv run --env-file .env`.

**ClickHouse connection errors: timeout, SSL or "connection refused"**
Check `CLICKHOUSE_PORT` matches the protocol: `CLICKHOUSE_SECURE` defaults to `true`, so a plain-HTTP port such as 8123 needs `CLICKHOUSE_SECURE=false`. Then run `uv run python -m api.check_clickhouse primary-001`.

**`/health` says `degraded` or `"clickhouse": false`**
In `clickhouse` mode, `SELECT 1` failed: the server is down, unreachable or rejecting credentials. In `files` mode `clickhouse: false` is normal.

**`data_version` is `unknown`**
The startup query for the latest `load_id` returned nothing or failed (empty `field_indicators`, or ClickHouse not reachable at that moment). Fix the cause and restart; the value is cached.

**Responses look stale after a data load**
`GET` responses carry `Cache-Control: max-age=3600`, and `data_version` is cached per process. Restart the API after a load and hard-refresh the client.

**`GET /analyses/{id}` or `/ask` returns 404 right after a compare**
Storing the analysis failed silently (see [failure behaviour](#persistence-and-failure-behaviour)) or, in file mode, the process restarted. Check the log for the compare request's `X-Request-ID`, and confirm migration `007_analyses.sql` has been applied.

**`/ask` returns `refused: true` with "The AI assistant is not configured"**
`ANTHROPIC_API_KEY` is not in the server's environment. This is a 200, not a 503. If it says the service is busy, slow or unavailable, the call to Anthropic failed; retry. Questions the context cannot answer (yield, profit, other farms) are also refused by design.

**Profile sections say `not_loaded`, or `/sources`, `/lineage/...` and time series are empty**
Expected in file mode without DS2's indicator CSVs, and for lineage, sources and time series in file mode generally. Use `clickhouse` mode, or confirm the CSVs are in `AGROCYCLE_INDICATORS_DIR`.

**`/fields/{id}/imagery` says `available: false`**
Photos need ClickHouse mode, all four AWS variables, and a row for that field in `naip_tiles`. Missing AWS settings do not raise an error; they just disable photos.

**`/imagery/image.png` returns 503**
The chip is missing in S3, unreadable, or its checksum does not match `naip_tiles`. The message says which. `uv run python -m api.check_imagery <field_id> out.png` reproduces it.

**`POST .../compare` returns 422 for an answer like `"yes"` or `1`**
Answers are strict booleans: `true`, `false` or `null`. Unknown fields in the body are also rejected.

**`POST .../compare` returns 403**
`sample_indicators: true` was sent while `AGROCYCLE_ALLOW_SAMPLE_PREVIEW=false`.

**Browser requests fail with a CORS error**
The page's origin is not in `AGROCYCLE_CORS_ORIGINS` (exact match, scheme and port included). Only `GET` and `POST` and the `Content-Type` header are allowed.

**HTTP 500 with a plain body, not the error envelope**
An unexpected exception. Logs are one JSON object per line; find the `X-Request-ID` from the response header and read its `traceback` field:

```bash
docker compose logs api | grep '<request id>'
```

**Tests try to contact ClickHouse or S3**
Blank the credentials for the run: `CLICKHOUSE_HOST="" AWS_ACCESS_KEY_ID="" uv run pytest api/ -q`.
