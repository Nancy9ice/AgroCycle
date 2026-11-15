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

#### `POST /api/v1/fields/drawn`

Keeps a boundary the farmer drew, so they can carry on to a profile for it. Body: `{ "geometry": <Polygon>, "name": "North 80" }` (optional name). Only a single `Polygon` is accepted, with the same rules as `POST /fields` (1 to 1,000 ha, Story or Boone). A valid boundary is stored in `drawn_fields` and returned with `field_id: "drawn-…"`, `can_continue: true`, `can_compare: false` and all four sources `not_assessed`. An invalid one is not stored. Returns 429 if more than 300 boundaries were saved in the last hour, and 503 when the API has no database.

Nothing is pre-processed for a drawn boundary: its profile shows crop, soil and weather as `not_loaded`, and its comparison abstains and says which indicators are missing. It never shows another field's numbers as the farmer's.

#### `POST /api/v1/fields/{field_id}/crop-history`

The farmer's own crop for each of the last 11 seasons (2015 to 2025), oldest first, for a drawn boundary only: `{ "crops": ["corn", "soybeans", …] }` using `corn`, `soybeans`, `oats`, `alfalfa`, `pasture_hay`, `other`. All 11 are required (DS1's rules need them). The field's class comes from **DS1's classification rules** (`transform.crop_history.rules.classify_field`), the same ones the pre-processed fields go through. The answer shows in the profile labelled "Your own answers", evidence type `assumption`, never as CDL data. Even a rotation history does not make the comparison say "worth exploring": weather and soil are still missing, so it abstains.

#### `GET /api/v1/fields/{field_id}/detail`

One field with its boundary, class, area and centroid, for the map and pages. Works for demonstration and drawn fields (`role: "drawn"`).

##### Preparing weather and soil for a drawn boundary

A saved boundary has no weather or soil until someone runs the batch step. It reuses DS2's pipeline unchanged (NASA POWER at the centroid, USDA Soil Data Access for the polygon, `transform.indicators.runner`), so a drawn field is computed exactly like the demonstration fields. It is a batch step a person runs, not something the API does when a farmer clicks: the API reads curated data only, with no external call at request time.

```bash
uv run python -m transform.indicators.drawn                        # list saved boundaries still without weather and soil
uv run python -m transform.indicators.drawn --field drawn-ab12cd34 # fetch and compute; writes CSVs to data/out/drawn/, loads nothing
uv run python -m transform.indicators.drawn --field drawn-ab12cd34 --load    # also append that one field's rows
uv run python -m transform.indicators.drawn --boundary FILE.geojson --field-id drawn-test   # no database at all
```

The load is its own code on purpose. `field_indicators` and `soil_properties` are one partition each, so the standard loader would replace the **whole table** and wipe the demonstration fields, and it refuses any field not in `fields.geojson`. This appends rows for the one drawn id only, refuses a demonstration field, refuses a file with another field's rows, refuses a field that already has rows unless `--replace` (which deletes only that field's rows), and refuses indicators with no lineage row. The API picks the rows up within five minutes (its lookup cache).

Once prepared, the profile shows the weather of the grid cell the field sits in (about 50 km, shared with neighbouring fields) and soil averaged over the mapped units inside the boundary, and the comparison can complete. The crop history stays the farmer's own word.

#### `GET /api/v1/fields`

Lists all 45 pre-processed fields (id, county, role, class).

#### `GET /api/v1/fields/{field_id}`

Single field metadata.

#### `GET /api/v1/fields/{field_id}/profile`

Crop history, weather and soil for a field, each section with its data provenance.
A section with no data behind it returns `status: "not_loaded"` — no sample values are ever served.
`versions` records what produced the profile: `dataVersion`, `engineVersion`, `cropHistoryPeriod` and `cropHistorySource`.

#### `GET /api/v1/fields/{field_id}/season-summary`

The F2 season stress summary: for every season on record (2015 to 2025) the very hot days (30 °C or more), the longest dry run, dry spells of 10 or more days, season rain and growing degree days, each from DS2's `field_indicators` with its lineage limitation. Each indicator gives the per-season values plus the highest and lowest season (earliest if tied), so a screen can say "73 hot days in 2021 against 9 in 2019".

- A season with too little data is `value: null` with its `unknown_reason`; it is never read as zero and never counts toward the highest or lowest.
- **Not a crop-phase stress test.** It counts past weather over the whole season and says nothing about when in the season it happened, because the Marsden records give no planting or growth-stage timing. The `caveats` say so, along with: grid-scale weather (about 50 km, not a field measurement), thresholds are team-proposed and not reviewed by an agronomist, and POWER rainfall runs about 11 % low against the station record.
- Returns 200 with `indicators: []` when no weather is loaded for the field, and 404 for an unknown field.

#### `GET /api/v1/fields/{field_id}/cover-calendar`

The F3 cover calendar, **observed only**: what satellite images (NASA HLS NDVI) and DS1's bare windows say about cover on this field, month by month, for each year that has images (2023 to 2025, April to October). Each month is one of:

- `bare`: at least two usable images that month (at least half the field clear of cloud) and at least half the month's days inside a bare window.
- `likely_bare`: inside a bare window but with no usable image that month, so it is inferred between images (a winter window crosses months with no image at all).
- `green`: at least two usable images and not bare. This says there is green cover, not which crop.
- `unknown`: too few usable images to say. Never guessed as bare or green.

Also returns each bare window with `seen_in_images` (false when it crosses a month with no usable image), the legend, and caveats. A bare window is 14 or more days with NDVI under 0.3, which is the team's own threshold. 404 when the field has no images.

**Not built: expected cover for the three-year and four-year rotations.** The spec's F3 also asks for B and C expected cover, but the cover claims for oats, red clover and alfalfa are marked "research needed" and no source gives their timing, so anything shown would be invented. The endpoint says so in its caveats.

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
- `priority_levels` (`{"soil": "high", "water": "medium", "inputs": "low", ...}`, ids `soil`, `water`, `inputs`, `income`, `forage`; levels `low`, `medium`, `high`) is the farmer's answer for each priority, straight from the form. The response's `emphasis` is DS2's `engine.emphasis` applied to the finished decision: `outcome_order` (every outcome id, priority ones first), `highlighted`, `gaps_for_priorities` (plain words for what we cannot answer, one per priority used, in the order of `priorities_used`) and `note`. **It never changes the result**: the outcome, its reason and the strategies are identical with or without priorities, nothing is hidden, `low` promotes nothing, and there is no score, rank, winner or weight. Show the gaps, not only the reordering: someone who picks soil is told we do not measure soil carbon. The older `priorities` list still works and means `high`; where both name a priority, `priority_levels` wins.
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
- **Expectations are DS2's, from the validation matrix, and there are few on purpose.** `engine_test_set` carries `expected_outcome` and `expected_review_state` on the rows that match a matrix case (four of 135 today: `primary-001` with every constraint and without manure, `test-022`, `test-027`). Everything else is blank, and a blank is **no expectation, not a failure**: `expected_outcome` and `match` are `null`. Nothing is derived from a field's crop class or the selection label, because the engine reads those labels and the comparison would be circular. Every expectation says its `expected_review_state` (all `awaiting_review` today), so it is not presented as a benchmark until it is reviewed.
- `expectations` summarises it: `cases_total`, `cases_with_expectation`, `cases_matching`, `fields_with_expectation`, `awaiting_review`, `reviewed`, and a plain `note`. Each scenario in a field's `scenarios` carries its own `expected_outcome`, `expected_review_state` and `match`.
- DS1's `scenario = 'expected'` rows (run `ds1_handover`) are never read as an engine run or as expectations: they are the 27/18 class split, which predates the `test-022` decision and would show a false failure. The engine results are the newest run that has real scenarios; with none the endpoint answers 503 rather than an empty 200.
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

