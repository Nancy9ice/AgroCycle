# AgroCycle API

FastAPI backend for the AgroCycle crop-rotation decision-support tool (NASA Space Apps 2026).

The API turns "this field + what the farmer told us" into one of three outcomes — *worth exploring*, *qualified comparison*, or *abstention* — with the evidence behind each. It never scores, ranks, or recommends.

**Interactive docs:** `/docs` (Swagger UI) · `/redoc` (ReDoc) · `/openapi.json`

---

## Quick start (local, no Docker)

```bash
# 1. Copy and fill in credentials
cp .env.example .env   # then edit .env

# 2. Install dependencies (uv required: https://docs.astral.sh/uv/)
uv sync

# 3. Run migrations (needs CLICKHOUSE_* in .env)
uv run python -m common.migrate

# 4. Start the API
uv run uvicorn api.main:app --reload --port 8000
```

The API is now at `http://localhost:8000`.
ReDoc reference: `http://localhost:8000/redoc`

To run against committed file data instead of ClickHouse, set `AGROCYCLE_DATA_SOURCE=files` in `.env` — no database needed.

---

## Environment variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `CLICKHOUSE_HOST` | yes (clickhouse mode) | — | ClickHouse server IP or hostname |
| `CLICKHOUSE_PORT` | no | `8123` | HTTP port |
| `CLICKHOUSE_USER` | yes | — | Database user |
| `CLICKHOUSE_PASSWORD` | yes | — | Database password |
| `CLICKHOUSE_DATABASE` | no | `agrocycle` | Target database |
| `CLICKHOUSE_SECURE` | no | `false` | Use HTTPS (`true`/`false`) |
| `AWS_ACCESS_KEY_ID` | yes (S3 loads) | — | AWS key for the raw-data bucket |
| `AWS_SECRET_ACCESS_KEY` | yes (S3 loads) | — | AWS secret |
| `AWS_REGION` | no | `us-east-1` | AWS region |
| `S3_BUCKET` | no | `agrocycle-fieldshift-2026-data` | Raw-data bucket |
| `ANTHROPIC_API_KEY` | no | — | Enables the F1 AI chat (`/ask`). If absent, `/ask` endpoints return 503 gracefully |
| `AGROCYCLE_DATA_SOURCE` | no | `files` | `files` or `clickhouse` |
| `AGROCYCLE_CORS_ORIGINS` | no | `http://localhost:3004` | Comma-separated allowed origins |
| `AGROCYCLE_ALLOW_SAMPLE_PREVIEW` | no | `true` | Let `sample_indicators: true` bypass missing data (demo only) |
| `AGROCYCLE_INDICATORS_DIR` | no | `data/out/indicators` | Where DS2's field indicator CSVs live |

---

## Running with Docker Compose

```bash
# First time: copy and fill in .env
cp .env.example .env

# Build images, run migrations, start services
docker compose up --build -d

# View logs
docker compose logs -f api
docker compose logs -f migrate
```

Migrations run automatically in the `migrate` service before the `api` service starts.
The app is available at `https://agrocycle.praxicraft.com` in production.
ReDoc reference: `https://agrocycle.praxicraft.com/redoc`

---

## API reference

All endpoints live under `/api/v1`. Every response includes `data_version` (the latest ClickHouse `load_id`). GET 200 responses include `ETag` and `Cache-Control: public, max-age=3600`.

### Errors

All errors share one shape:

```json
{
  "error": {
    "code": "not_found",
    "message": "No field with id 'primary-999'.",
    "details": {}
  }
}
```

| Code | HTTP status |
|---|---|
| `not_found` | 404 |
| `validation_error` | 422 |
| `service_unavailable` | 503 |

---

### Meta

#### `GET /api/v1/health`

Returns API status, data source, rules version and ClickHouse reachability.

```bash
curl http://localhost:8000/api/v1/health
```

```json
{
  "status": "ok",
  "data_source": "clickhouse",
  "rules_version": "2026-11-01",
  "clickhouse": true,
  "data_version": "20261101-001"
}
```

#### `GET /api/v1/meta/constraint-options`

Returns the farmer-survey questions the UI must render in the compare form.

---

### Fields

#### `GET /api/v1/fields/demo`

Lists the pre-processed demonstration fields with their boundary geometry and area.

#### `POST /api/v1/fields`

Validates a GeoJSON polygon (drawn by the farmer) or selects a demo field.

**Request body:**
```json
{ "demo_field_id": "primary-001" }
```
or
```json
{ "geometry": { "type": "Polygon", "coordinates": [[[...]]] } }
```

Polygon rules: valid GeoJSON, ≤ 2 000 vertices, 1–1 000 ha, intersects Story or Boone County Iowa.

A drawn boundary is **validated, not analysed**: only the 45 demonstration fields have pre-processed data. For a valid drawn
polygon the response has `can_compare: false`, `is_preprocessed: false`, every `coverage` entry `not_assessed`, and a
plain-language `message` to show the user. Comparing it returns 404. Demo fields return `can_compare: true`.

#### `GET /api/v1/fields`

Lists all 45 pre-processed fields (id, county, role, class).

#### `GET /api/v1/fields/{field_id}`

Single field metadata.

#### `GET /api/v1/fields/{field_id}/profile`

Crop history, weather and soil for a field, each section with its data provenance.
A section with no data behind it returns `status: "not_loaded"` — no sample values are ever served.
`versions` records what produced the profile: `dataVersion`, `engineVersion`, `cropHistoryPeriod` and `cropHistorySource`.

#### `GET /api/v1/fields/{field_id}/timeseries`

Climate or NDVI time-series for a field.

| Query param | Default | Description |
|---|---|---|
| `kind` | `climate` | `climate` or `ndvi` |
| `from` | `2015-01-01` | Start date (YYYY-MM-DD) |
| `to` | `2024-12-31` | End date |
| `max_points` | `365` | Cap on returned points (10–3650) |

---

### Compare

#### `POST /api/v1/fields/{field_id}/compare`

Runs the rotation comparison. Returns one outcome with its evidence.

**Request body:**
```json
{
  "manure_access": false,
  "forage_use_or_buyer": null,
  "oat_use_or_buyer": true,
  "small_grain_equipment_or_contractor": null,
  "priorities": ["soil", "water"],
  "sample_indicators": false
}
```

- Each answer is `true`, `false`, or `null`. `null` means unknown — never read as `false`.
- `sample_indicators: true` is a demo affordance; response marks `"preview": true`.
- The response carries `analysis_id` for later retrieval and AI questions.
- `context` (`hay_equipment_or_contractor`, `storage_space`, `extra_labour`) is **context-only**: stored, echoed as `context_recorded` and given to the AI and adviser views, but no rule reads it, so it never changes the outcome. `context_note` says so in plain words. DS2 and FE decide if any of these becomes a rule.
- `persistence` says whether the result was kept: `stored` (retrievable), `temporary` (in memory only, lost on restart; file mode) or
  `failed` (not saved, the share link will not work). When it is not `stored`, `persistence_warning` holds text to show the user.
  A storage failure never fails the comparison itself.

#### `GET /api/v1/analyses/{analysis_id}`

Retrieves a stored comparison result by its `analysis_id`.

---

### Validation (F5)

#### `GET /api/v1/validation/test-set`

The "How we tested this" audit: engine outcome vs expected for each test field, outcome counts and a CDL agreement summary.
Reads DS's `engine_test_set` table (newest run). Returns 503 if no audit has been loaded.

- `fields[]`: `field_id`, `role`, `county`, `sequence_summary`, `expected_outcome`, `engine_outcome` (scenario `every_constraint_stated`), `match`, and the outcome under every scenario.
- **Expected outcome is derived**, not recorded by DS: rotation fields should reach a comparison, every other class should abstain, from the team's field-selection labels. It is a soft check, not ground truth.
- `cdl_agreement` compares the selection label with DS1's classification of the same CDL history. It is agreement with another classification, not accuracy, and not independent.

### Evidence

#### `GET /api/v1/evidence/marsden`

Returns the nine-year management means from the Marsden Farm experiment (Davis et al. 2012), which underpins the engine's N-input and herbicide claims.

---

#### `GET /api/v1/evidence/rules`

The engine's rule register, read from DS2's `engine_rules`, `engine_crop_claims`, `engine_outcomes` and `engine_strategies` tables (newest `rules_version`). Returns 503 if nothing is loaded.

- `rules[]`: each applicability rule with its `context_key`, `operator`, `value`, `effect`, `evidence_basis` (`team_proposed` or `experimental_context`) and `review` (`not_expert_reviewed` or `expert_reviewed`).
- `crop_claims[]`: the evidence register. `status` is `sourced` or `research_needed`; the engine makes no claim from a `research_needed` one.
- `outcomes[]`: what each outcome may claim (`claimable: false` means it is always "not assessed"), with its caution. `strategies[]`: the three rotations, their phases and operational requirements.
- `summary` counts rules by basis and review, and claims by status. `matches_engine` is false when the loaded version differs from the running engine's. `caveats` is generated from the counts, so it says "no rule has been reviewed by an agronomist" for as long as that is true.
- This is the rule table, **not** the F2 stress test or the F6 transition plan. Those need crop-phase windows, thresholds and transition steps that DS2 has not provided.

### Methods

#### `GET /api/v1/sources`

All data sources used (CDL, NASA POWER, SSURGO, HLS) with citation and coverage details.

#### `GET /api/v1/indicators`

Glossary of all indicators (id, name, unit, source, lineage explanation, evidence type).

#### `GET /api/v1/lineage/{indicator_id}`

Full provenance record for one indicator: source, grid scale, missing-data handling, limitations, and the literature it rests on.

---

### F1 — Ask AgroCycle (AI chat)

Requires `ANTHROPIC_API_KEY` in `.env`. If absent, these endpoints return `503`.

The model is given only the stored analysis or field profile, and its prompt tells it to cite indicator ids, refuse out-of-scope questions and never rank strategies. That is a prompt constraint, not a guarantee. Say "AI phrases results the engine computed", never "no AI" and never "AI analyses your field". The UI should label this panel **"AI explanation of AgroCycle's computed results"**.

#### `POST /api/v1/analyses/{analysis_id}/ask`

Ask a question about a stored comparison result.

**Request:**
```json
{ "question": "Why did the 4-year rotation get a qualified result?", "audience": "farmer" }
```

`audience` is `farmer` (plain language) or `adviser` (technical). Default: `farmer`.

**Response:**
```json
{
  "refused": false,
  "answer": "The 4-year rotation got a qualified result because...",
  "citations": ["gdd", "om_r_0_30cm"],
  "model": "claude-opus-4-7",
  "log_id": "ask_7a3c1b2d"
}
```

#### `POST /api/v1/fields/{field_id}/ask`

Ask a question about a field's environmental profile (before running a comparison). Same request/response shape.

---

## Folder layout

```
api/
  core/          # Business logic: profile builder, AI chat, serialiser, geometry validator
  db/            # Data access: repository protocol + FileRepository + ClickHouseRepository
  routes/        # FastAPI routers split by domain (fields, compare, methods, ask, meta)
  schemas/       # Pydantic request/response models split by domain
  tests/         # Pytest tests
  deps.py        # Shared FastAPI dependencies
  main.py        # App factory
  settings.py    # Settings from environment variables
```

---

## Running tests

```bash
# All tests (live ClickHouse/S3 checks skip when credentials are absent)
uv run pytest api/ -x -q

# Skip live checks explicitly
CLICKHOUSE_HOST="" uv run pytest api/ -x -q
```

---

## Checking the live ClickHouse path

```bash
uv run python -m api.check_clickhouse primary-001
```

Prints the field record, indicator statuses, weather means and drainage class — a quick sanity check without touching the compare engine.

---

## Data sources

| `AGROCYCLE_DATA_SOURCE` | Reads | Needs credentials |
|---|---|---|
| `files` (default) | Committed field data + DS2 indicator CSVs from `data/out/indicators/` | No |
| `clickhouse` | DE-loaded ClickHouse tables (`fields`, `crop_rotation`, `field_indicators`, `soil_properties`) | Yes |

Both paths produce identical indicator facts through the same `facts_from_rows` function.

## Mapping decisions

- DS2's `frost_free_days` → engine's `frost_window`.
- An indicator is `ok` only if **every** season row is `available`; a `partial` or missing season makes it `unknown`.
- Field class `rotation` is the in-domain class; a field with no class is unknown, never out of domain.

## Aerial photo (NAIP)

`GET /fields/{id}/imagery` says whether a field has an aerial photo, when it was flown (one date per source tile), its resolution and where the picture sits. `GET /fields/{id}/imagery/image.png` is the picture. They read DE's `naip_tiles` index and the chip in S3 (needs the AWS settings; without them, or in file mode, the answer is "no photo"). The chip is checked against the checksum in the index and warped from UTM to longitude/latitude; colours are unchanged. A chip that is missing, unreadable or does not match its checksum is a 503, never a blank picture. It is reference imagery from one day, not crop ground truth.

Check it against the real data (read-only):

```bash
uv run python -m api.check_imagery primary-001 primary-001.png
```

