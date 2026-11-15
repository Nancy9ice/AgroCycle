# AgroCycle API

The backend service for AgroCycle. It is a FastAPI application that serves field data, runs the rotation decision engine on request, stores the results, and answers questions about them.

This document describes the API as a service: how it is built, what it exposes, where its data comes from, and how to run and debug it. For what AgroCycle is and why, see the [root README](../README.md) and the [PRD](../PRD.md).

**Interactive reference** (served by the running API): `/docs` (Swagger UI), `/redoc` (ReDoc), `/openapi.json`. In production these are at `https://agrocycle.praxicraft.com/redoc` and `/docs`.

## Contents

- [1. Overview](#1-overview)
- [2. Architecture](#2-architecture)
  - [Components](#components)
  - [Request and response flow](#request-and-response-flow)
  - [Mounting](#mounting)
  - [External dependencies](#external-dependencies)
  - [Errors](#errors)
- [3. API endpoints](#3-api-endpoints)
  - [Health](#health)
  - [Fields and profiles](#fields-and-profiles)
  - [Validating a boundary](#validating-a-boundary)
  - [Comparing strategies](#comparing-strategies)
  - [Evidence and rules](#evidence-and-rules)
  - [Validation audit](#validation-audit)
  - [Plan the switch](#plan-the-switch)
  - [Ask](#ask)
  - [Aerial photo](#aerial-photo)
  - [Feedback](#feedback)
- [4. Data access](#4-data-access)
  - [ClickHouse integration](#clickhouse-integration)
  - [Caching](#caching)
  - [Persistence and failure behaviour](#persistence-and-failure-behaviour)
- [5. Configuration](#5-configuration)
  - [Variables](#variables)
  - [Secrets and credentials](#secrets-and-credentials)
  - [Local versus deployed](#local-versus-deployed)
- [6. Local development](#6-local-development)
  - [Prerequisites](#prerequisites)
  - [Install](#install)
  - [Run](#run)
  - [Test](#test)
- [7. Troubleshooting](#7-troubleshooting)

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
  routes/          One router per domain: meta, fields, imagery, compare, methods, ask, test_set, feedback
  schemas/         Pydantic request and response models, split the same way
  core/            Logic with no database access: profile building, geometry validation, demo-field
                   assembly, test-set audit, ask context and Claude call, imagery rendering, serialisation
  db/              Data access: FieldRepository protocol, FileRepository, ClickHouseRepository,
                   imagery source, in-process caches, constraint options
  tests/           pytest
common/            Shared with the pipeline: config.py (clients), migrate.py (schema runner)
engine/            The decision engine and its rules
schema/            Numbered ClickHouse migrations (*.sql)
```

Put new code in `routes/`, `schemas/`, `core/` or `db/`. The top level of `api/` holds only the app wiring (`main.py`, `settings.py`, `deps.py`, `logging_config.py`) and two read-only check scripts (`check_clickhouse.py`, `check_imagery.py`).

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
  -> repository.store_analysis                  (a failure is reported in `persistence`, not raised)
  -> CompareResponse
```

### Mounting

Every endpoint is under `/api/v1` and nowhere else; an unversioned path such as `/fields` is a 404. Only the docs (`/docs`, `/redoc`, `/openapi.json`) are served at the root.

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
| 503 | `service_unavailable` | Photo index or chip unreadable; stored analysis unparseable; no test-set audit loaded |
| 403 | `error` | `sample_indicators: true` while previews are disabled |
| 500 | (not enveloped) | An unexpected exception, such as a failed ClickHouse query. Logged with traceback; look it up by `X-Request-ID` |

---

## 3. API endpoints

All paths below are relative to `/api/v1`.

| Method | Path | Purpose |
|---|---|---|
| GET | `/health` | Status, data source, rules version, ClickHouse reachability |
| GET | `/meta/constraint-options` | The farmer questions the compare form must render |
| GET | `/meta/pilot-area` | The Story and Boone county outlines, for drawing the map |
| GET | `/fields/demo` | The pre-processed fields with boundary geometry, area, class and notes |
| POST | `/fields` | Validate a drawn polygon, or select a demo field |
| POST | `/fields/drawn` | Keep a boundary the farmer drew |
| POST | `/fields/{field_id}/crop-history` | The farmer's own crop for each of the last 11 seasons, for a drawn boundary |
| GET | `/fields` | List fields (id, county, role, class) |
| GET | `/fields/{field_id}` | One field's metadata |
| GET | `/fields/{field_id}/detail` | One field with boundary, class, area and centroid; demonstration or drawn |
| GET | `/fields/{field_id}/profile` | Crop history, climate, vegetation and soil, each with provenance |
| GET | `/fields/{field_id}/timeseries` | Climate or NDVI series |
| GET | `/fields/{field_id}/season-summary` | Per-season weather stress summary, 2015 to 2025 |
| GET | `/fields/{field_id}/cover-calendar` | Observed cover by month from satellite images and bare windows |
| GET | `/fields/{field_id}/imagery` | Whether an aerial photo exists, when it was flown, where it sits |
| GET | `/fields/{field_id}/imagery/image.png` | The photo |
| POST | `/fields/{field_id}/compare` | Run the comparison |
| GET | `/analyses/{analysis_id}` | Fetch a stored comparison |
| GET | `/evidence/marsden` | Marsden Farm management means the engine's claims rest on |
| GET | `/evidence/rules` | The engine's rule register: rules, crop claims, outcomes, strategies |
| GET | `/sources` | Data sources with citation and coverage |
| GET | `/indicators` | Glossary of indicators |
| GET | `/lineage/{indicator_id}` | Full provenance for one indicator |
| GET | `/strategies/{strategy_id}/transition` | Year-by-year sequence for switching to strategy B or C |
| GET | `/validation/test-set` | The "How we tested this" audit of the engine on the test fields |
| POST | `/fields/{field_id}/ask` | Question about a field's profile |
| POST | `/analyses/{analysis_id}/ask` | Question about a stored comparison |
| POST | `/feedback` | Save one piece of feedback from a farmer, adviser or researcher |

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

`GET /fields/{id}/profile` returns one object with four sections, `cropHistory`, `climate`, `vegetation` and `soil`, each `{ "status": "available" | "not_loaded", "data": ..., "provenance": ... }`. A section with nothing behind it is `not_loaded`; the API never fills it with sample values. A `versions` object records what produced the profile: `dataVersion`, `engineVersion`, `cropHistoryPeriod` and `cropHistorySource`. Profile keys are camelCase; most other responses are snake_case.

`GET /fields/demo` returns each demonstration field with its geometry, `area_ha`, `centroid` (`[longitude, latitude]`), `field_class` (DS1's classification: `rotation`, `continuous_corn`, `pasture_hay` or `mixed`) and plain-language `domain_note`, `provenance` and `cover_detail`. The web app builds its map and field list from this.

`GET /meta/pilot-area` returns the Story and Boone county outlines and a one-line description of the pilot area.

**`POST /api/v1/fields/drawn`**

Keeps a boundary the farmer drew, so they can carry on to a profile for it. Body: `{ "geometry": <Polygon>, "name": "North 80" }` (optional name). Only a single `Polygon` is accepted, with the same rules as `POST /fields` (1 to 1,000 ha, Story or Boone). A valid boundary is stored in `drawn_fields` and returned with `field_id: "drawn-…"`, `can_continue: true`, `can_compare: false` and all four sources `not_assessed`. An invalid one is not stored. Returns 429 if more than 300 boundaries were saved in the last hour, and 503 when the API has no database.

Nothing is pre-processed for a drawn boundary: its profile shows crop, soil and weather as `not_loaded`, and its comparison abstains and says which indicators are missing. It never shows another field's numbers as the farmer's.

**`POST /api/v1/fields/{field_id}/crop-history`**

The farmer's own crop for each of the last 11 seasons (2015 to 2025), oldest first, for a drawn boundary only: `{ "crops": ["corn", "soybeans", …] }` using `corn`, `soybeans`, `oats`, `alfalfa`, `pasture_hay`, `other`. All 11 are required (DS1's rules need them). The field's class comes from **DS1's classification rules** (`transform.crop_history.rules.classify_field`), the same ones the pre-processed fields go through. The answer shows in the profile labelled "Your own answers", evidence type `assumption`, never as CDL data. Even a rotation history does not make the comparison say "worth exploring": weather and soil are still missing, so it abstains.

**`GET /api/v1/fields/{field_id}/detail`**

One field with its boundary, class, area and centroid, for the map and pages. Works for demonstration and drawn fields (`role: "drawn"`).

**Preparing weather and soil for a drawn boundary.**

A saved boundary has no weather or soil until someone runs the batch step. It reuses DS2's pipeline unchanged (NASA POWER at the centroid, USDA Soil Data Access for the polygon, `transform.indicators.runner`), so a drawn field is computed exactly like the demonstration fields. It is a batch step a person runs, not something the API does when a farmer clicks: the API reads curated data only, with no external call at request time.

```bash
uv run python -m transform.indicators.drawn                        # list saved boundaries still without weather and soil
uv run python -m transform.indicators.drawn --field drawn-ab12cd34 # fetch and compute; writes CSVs to data/out/drawn/, loads nothing
uv run python -m transform.indicators.drawn --field drawn-ab12cd34 --load    # also append that one field's rows
uv run python -m transform.indicators.drawn --boundary FILE.geojson --field-id drawn-test   # no database at all
```

The load is its own code on purpose. `field_indicators` and `soil_properties` are one partition each, so the standard loader would replace the **whole table** and wipe the demonstration fields, and it refuses any field not in `fields.geojson`. This appends rows for the one drawn id only, refuses a demonstration field, refuses a file with another field's rows, refuses a field that already has rows unless `--replace` (which deletes only that field's rows), and refuses indicators with no lineage row. The API picks the rows up within five minutes (its lookup cache).

Once prepared, the profile shows the weather of the grid cell the field sits in (about 50 km, shared with neighbouring fields) and soil averaged over the mapped units inside the boundary, and the comparison can complete. The crop history stays the farmer's own word.

`GET /fields/{id}/timeseries` takes `kind` (`climate` or `ndvi`, default `climate`), `from` (default `2015-01-01`), `to` (default `2024-12-31`) and `max_points` (10 to 3650, default 365). Climate series are bucketed to stay under `max_points`. In file mode both kinds return an empty `points` list.

`GET /fields/{id}/season-summary` is the season stress summary: for every season on record (2015 to 2025) the very hot days (30 °C or more), the longest dry run, dry spells of 10 or more days, season rain, growing degree days, mean temperature and reference evapotranspiration, each from DS2's `field_indicators` with its lineage limitation. Each indicator gives the per-season values plus the highest and lowest season (earliest if tied), so a screen can say "73 hot days in 2021 against 9 in 2019".

- There are seven indicators: very hot days, longest dry run, dry spells, season rain, growing degree days, season mean temperature, and reference evapotranspiration (grass-surface demand, not any crop's water use). Each carries a `threshold` record read from DS2's `season_stress_thresholds` table: what it counts, the line it is counted against ("none" for a mean or a total), its unit, `evidence_basis` and `review`. The review caveat follows that table, so it says "No agronomist has reviewed them" only while that is true; an empty table is not a review.
- A season with too little data is `value: null` with its `unknown_reason`. It is never read as zero and never counts toward the highest or lowest.
- **It is not a crop-phase stress test.** It counts past weather over the whole season and says nothing about when in the season it happened, because the Marsden records give no planting or growth-stage timing. The `caveats` say so, along with: grid-scale weather (about 50 km, not a field measurement), team-proposed thresholds not reviewed by an agronomist, and POWER rainfall running about 11 % low against the station record.
- It returns 200 with `indicators: []` when no weather is loaded for the field, and 404 for an unknown field.

**`GET /api/v1/fields/{field_id}/cover-calendar`**

The F3 cover calendar, **observed only**: what satellite images (NASA HLS NDVI) and DS1's bare windows say about cover on this field, month by month, for each year that has images (2023 to 2025, April to October). Each month is one of:

- `bare`: at least two usable images that month (at least half the field clear of cloud) and at least half the month's days inside a bare window.
- `likely_bare`: inside a bare window but with no usable image that month, so it is inferred between images (a winter window crosses months with no image at all).
- `green`: at least two usable images and not bare. This says there is green cover, not which crop.
- `unknown`: too few usable images to say. Never guessed as bare or green.

Also returns each bare window with `seen_in_images` (false when it crosses a month with no usable image), the legend, and caveats. A bare window is 14 or more days with NDVI under 0.3, which is the team's own threshold. 404 when the field has no images.

**Not built: expected cover for the three-year and four-year rotations.** The spec's F3 also asks for B and C expected cover, but the cover claims for oats, red clover and alfalfa are marked "research needed" and no source gives their timing, so anything shown would be invented. The endpoint says so in its caveats.

### Validating a boundary

`POST /fields` takes either `{ "demo_field_id": "primary-001" }` or `{ "geometry": <GeoJSON>, "name": "...", "boundary_source": "drawn" }`. It always returns 200 with a `valid` flag; read `errors` rather than the status code.

A drawn polygon is checked in this order: parseable and non-self-intersecting, at most 2,000 vertices, between 1 and 1,000 ha (area computed in UTM 15N), and intersecting Story or Boone County, Iowa. Error codes: `invalid_geometry`, `too_many_vertices`, `too_small`, `too_large`, `outside_pilot_area`.

A drawn boundary is **validated, not analysed**: only the 45 demonstration fields have pre-processed data. A valid drawn polygon gets a throwaway `drawn-xxxxxxxx` id, `is_preprocessed: false`, `can_compare: false`, `not_assessed` coverage for every source, and a plain-language `message` to show the user. It is not stored, so comparing it or fetching its profile is a 404. A demo field returns `can_compare: true`.

### Comparing strategies

```bash
curl -X POST http://localhost:8000/api/v1/fields/primary-001/compare \
  -H 'Content-Type: application/json' \
  -d '{
    "manure_access": false,
    "forage_use_or_buyer": null,
    "oat_use_or_buyer": true,
    "small_grain_equipment_or_contractor": null,
    "priority_levels": { "soil": "high", "water": "medium", "inputs": "low" }
  }'
```

Request fields:

| Field | Type | Notes |
|---|---|---|
| `manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor` | `true`, `false` or `null` | `null` or omitted means unknown and is never read as `false`. Strict: `"yes"` or `1` is a 422, not coerced |
| `priority_levels` | object, ids `soil`, `water`, `inputs`, `income`, `forage`; levels `low`, `medium`, `high` | The farmer's answer for each priority. Shapes the order the outcomes are shown in, never the result (see below) |
| `priorities` | list of the same ids | Older form; each id means `high`. Where both name a priority, `priority_levels` wins |
| `context` | object, optional | Context-only answers: `hay_equipment_or_contractor` (true, false or null), `storage_space` (true, false or null), `extra_labour` (`little`, `some`, `plenty` or null). Stored and shown to the AI and the adviser, but **no rule reads them, so they never change the outcome** |
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
  "context_recorded": { "hay_equipment_or_contractor": null, "storage_space": null, "extra_labour": null },
  "context_note": "Hay equipment, storage space and extra labour are recorded for you and your adviser. They do not change the result, because no rule uses them yet.",
  "analysis_id": "a_3f9c21",
  "created_at": "2026-11-15T10:42:11.402913+00:00",
  "engine_version": "2026-11-15.2",
  "data_version": "20261101-001",
  "persistence": "stored",
  "persistence_warning": null
}
```

`outcome` is one of `strategy_worth_exploring`, `qualified_comparison`, `abstention`. Strategies are `A`, `B`, `C` with `feasibility` of `available`, `qualified` or `unavailable`.

The response also carries `emphasis`, the engine's [`emphasise()`](../engine/README.md) applied to the finished decision: `outcome_order` (every outcome id, the priority ones first), `highlighted`, `gaps_for_priorities` (plain words for what we cannot answer, one per priority used, in the order of `priorities_used`) and `note`. **It never changes the result.** The outcome, its reason and the strategies are identical with or without priorities, nothing is hidden, `low` promotes nothing, and there is no score, rank, winner or weight. Show the gaps, not only the reordering: someone who picks soil is told we do not measure soil carbon.

`persistence` says whether the result was kept, and clients should show `persistence_warning` when it is not `stored`:

| `persistence` | Meaning |
|---|---|
| `stored` | Saved in ClickHouse; `GET /analyses/{id}` and the ask endpoint will find it |
| `temporary` | Held in memory only (file mode); lost on restart |
| `failed` | Saving failed, so the share link will not open later. The comparison itself is still correct |

A storage failure never fails the comparison.

`GET /analyses/{analysis_id}` returns the same payload as it was when stored.

### Evidence and rules

`GET /evidence/marsden` returns the nine-year management means from the Marsden Farm experiment (Davis et al. 2012), which underpin the engine's nitrogen and herbicide claims.

`GET /evidence/rules` returns the engine's rule register, read from `engine_rules`, `engine_crop_claims`, `engine_outcomes` and `engine_strategies` (the tables `python -m engine.load_rules` fills; see the [engine README](../engine/README.md#2-architecture-and-responsibilities)). It reads the newest `rules_version` and returns 503 if nothing is loaded.

- `rules[]`: each applicability rule with its `context_key`, `operator`, `value`, `effect`, `evidence_basis` (`team_proposed` or `experimental_context`) and `review` (`not_expert_reviewed` or `expert_reviewed`).
- `crop_claims[]`: the evidence register. `status` is `sourced` or `research_needed`; the engine makes no claim from a `research_needed` one.
- `outcomes[]`: what each outcome may claim (`claimable: false` means it is always "not assessed"), with its caution. `strategies[]`: the three rotations, their phases and operational requirements.
- `summary` counts rules by basis and review, and claims by status. `matches_engine` is false when the loaded version differs from the running engine's. `caveats` is generated from the counts, so it says "no rule has been reviewed by an agronomist" for as long as that is true.
- This is the rule table, **not** a crop-phase stress test. The switch sequence is its own endpoint, [`/strategies/{id}/transition`](#plan-the-switch).

### Validation audit

`GET /validation/test-set` returns the "How we tested this" audit: for each test field, the engine's outcome against the expected outcome, plus outcome counts and a CDL agreement summary. It reads the newest run in the `engine_test_set` table and answers 503 if no audit has been loaded.

- `fields[]` has `field_id`, `role`, `county`, `sequence_summary`, `expected_outcome`, `engine_outcome` (from the scenario `every_constraint_stated`), `match`, and the outcome under every scenario.
- **Expectations are DS2's, from the validation matrix, and there are few on purpose.** `engine_test_set` carries `expected_outcome` and `expected_review_state` on the rows that match a matrix case (four of 135 today: `primary-001` with every constraint and without manure, `test-022`, `test-027`). Everything else is blank, and a blank is **no expectation, not a failure**: `expected_outcome` and `match` are `null`. Nothing is derived from a field's crop class or the selection label, because the engine reads those labels and the comparison would be circular. Every expectation says its `expected_review_state` (all `awaiting_review` today), so it is not presented as a benchmark until it is reviewed.
- `expectations` summarises it: `cases_total`, `cases_with_expectation`, `cases_matching`, `fields_with_expectation`, `awaiting_review`, `reviewed` and a plain `note`. Each scenario in a field's `scenarios` carries its own `expected_outcome`, `expected_review_state` and `match`.
- DS1's `scenario = 'expected'` rows (run `ds1_handover`) are never read as an engine run or as expectations: they are the 27/18 class split, which predates the `test-022` decision and would show a false failure. The engine results are the newest run that has real scenarios; with none the endpoint answers 503 rather than an empty 200.
- `cdl_agreement` compares the selection label with DS1's classification of the same CDL history. It is agreement with another classification, not accuracy, and it is not independent.
- `caveats` repeats these limits in plain words so a client can show them next to the numbers.

### Plan the switch

`GET /strategies/{strategy_id}/transition` returns the year-by-year sequence for switching from the two-year rotation to strategy `B` or `C` (`A` is the system already run, so it answers 404). It reads DS2's `engine_transition_steps` table (newest `rules_version`) and answers 503 when the table is not loaded. An optional `analysis_id` (a saved comparison) adds `readiness`: which of the farmer's own answers bear on which step, as `yes`, `no` or `not_answered`. A skipped answer is never read as no.

- Step `year` 0 is the manure; 1 and up are the rotation's years. Each step has `action`, `needs`, `timing_note`, `evidence_basis` (`experimental`, `team_proposed` or `assumption`) and `source`.
- **Almost every `timing_established` is false.** DS2 found no planting date, phase window or establishment guidance in the Marsden paper or its supplement; the only sourced timing is that composted manure was applied in October. Show "not established", never a guess. Needs marked `team_proposed` are read from the rotation definition and are not reviewed by an agronomist.
- `shows_past_weather` marks the steps where the field's season-by-season weather (`/season-summary`) bears on them: counts over whole seasons, not tied to a crop stage.

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

These are prompt constraints, not guarantees: the model is asked to stay inside the context, cite ids and never rank, and the checks above catch some failures but not all. Describe the feature as "AI phrases results the engine computed", never as "no AI" and never as "AI analyses your field". Clients that show these answers must label the panel **"AI explanation of AgroCycle's computed results"**, so users can tell it apart from the engine's own output.

When a comparison carries `context_recorded` answers, the model is told they were recorded for the adviser and did not affect the result.

Ask never returns an error status for an AI-side failure. A missing `ANTHROPIC_API_KEY`, a timeout, a rate limit or an upstream error all return **200** with `refused: true` and a one-line `answer` saying what happened. Only a missing field or analysis (404) or an unparseable stored analysis (503) uses the error envelope.

### Aerial photo

`GET /fields/{id}/imagery` returns `available: false` when there is no photo, or `available: true` with `year`, `tiles` (one flight date per source tile), `resolution_m`, `bounds`, `evidence_type`, `attribution` and a `note` stating it is one day's photo and not a crop map. `image.png` returns the picture, or 404 when there is none.

Photos exist only in ClickHouse mode with S3 configured. The chip is verified against the checksum in `naip_tiles` and reprojected to longitude and latitude. A missing, unreadable or checksum-mismatched chip is a 503; it is never replaced with a blank image.

### Feedback

`POST /feedback` saves one piece of feedback and returns a `feedback_id`. It takes `role` (`farmer`, `adviser`, `researcher` or `other`), `usefulness` and `clarity` as whole numbers from 1 to 5 (strict: `"4"` is refused, not converted), and optional `farming_context`, `what_was_missing` and `would_use`. Contact details are kept only when the person ticked consent. Unknown fields are rejected.

The answer includes a note that feedback from outside Iowa helps judge how clear the app is, not whether its Iowa agronomy is right, and the feedback log keeps the two apart. Nothing is read back out through the API. More than 200 submissions in an hour are refused with 429, since a burst that size is spam, not people.

---

## 4. Data access

All routes talk to a `FieldRepository` (`db/repository.py`), chosen once at startup by `AGROCYCLE_DATA_SOURCE`. Routes never build SQL.

| | `files` (default) | `clickhouse` |
|---|---|---|
| Fields | `data/fields/field_selection_notes.csv` and `fields.geojson` | `fields` joined to `crop_rotation` |
| Indicators and soil | `field_indicators.csv` and `soil_properties.csv` from `AGROCYCLE_INDICATORS_DIR` (default `data/out/indicators`), if present | `field_indicators`, `soil_properties` |
| Lineage, sources, Marsden means | Empty (`/lineage/{id}` is 404, `/sources` is `[]`) | `indicator_lineage`, `data_sources`, `marsden_management` |
| Time series | Empty | `climate_points` and `climate_daily`; `hls_ndvi` |
| Test-set audit | None (`/validation/test-set` is 503) | `engine_test_set` (newest run) |
| Rule register | None (`/evidence/rules` is 503) | `engine_rules`, `engine_crop_claims`, `engine_outcomes`, `engine_strategies` (newest `rules_version`) |
| Aerial photos | None | `naip_tiles` plus chips in S3 |
| Stored analyses | In memory: lost on restart, not shared between workers; `persistence` is `temporary` | `analyses` table; `persistence` is `stored` |
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

- Client: `clickhouse-connect` over HTTP(S), built by `common/config.py`. Queries use bound parameters (`{field_id:String}`), not string formatting. The API runs requests in a thread pool and shares one client, so it builds it with `threadsafe=True`, which drops the server session; with a session, two simultaneous queries fail with "concurrent queries within the same session". The loaders keep the default.
- Schema: numbered files in `schema/`, applied by `python -m common.migrate` (or `make migrate`; safe to rerun). The API writes to two tables: `analyses` (007) and `ask_log` (008). Run migrations before starting the API against a new database; in Docker Compose the `migrate` service does this first.
- `data_version` is read once and cached for the process lifetime. After a data load, restart the API so `data_version` and the `ETag` change.
- Field and analysis ids are matched exactly; there is no fuzzy lookup.

### Caching

The database is remote (about 0.2 s a query), so reads that change only when the pipeline reloads are cached in the process:

- **Repository reads** (field list and single fields, indicator facts, Marsden means, lineage, sources, demo fields, aerial-photo index rows) are cached for 5 minutes, up to 256 entries in all per repository. Simultaneous first requests for the same key run one query; failures are not cached.
- **Rendered aerial photos** are cached (64 at most, oldest out first), keyed by the chip's checksum, so each chip is fetched from S3 and rendered once and a replaced chip is never served stale.
- **HTTP**: every 200 `GET` carries `Cache-Control: public, max-age=3600` and an `ETag` equal to `data_version`.

Stored analyses, the ask log and the test-set audit are not cached. After loading new data, restart the API to pick it up straight away; otherwise it appears within 5 minutes (plus any client-side hour).

### Persistence and failure behaviour

Some failures are deliberately not allowed to break the request. Know which:

| Operation | If it fails |
|---|---|
| Storing an analysis after compare | The comparison still returns, with `persistence: "failed"` and a `persistence_warning`; the error is logged. `GET /analyses/{id}` and `/ask` on that `analysis_id` will 404 |
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
Repository reads are cached in the process for 5 minutes, `data_version` for the process lifetime, and `GET` responses carry `Cache-Control: max-age=3600`. See [Caching](#caching). Restart the API after a load and hard-refresh the client.

**`GET /analyses/{id}` or `/ask` returns 404 right after a compare**
Check `persistence` in the compare response: `failed` means storing the analysis failed (the response carries a `persistence_warning`), and `temporary` means file mode, where analyses are lost on restart. For `failed`, look in the log for the compare request's `X-Request-ID` and confirm migration `007_analyses.sql` has been applied.

**`/validation/test-set` returns 503**
No audit has been loaded into `engine_test_set` yet, or the table could not be read (the message says which). File mode never has one.

**A request to `/fields` or `/health` without `/api/v1` returns 404**
Only the versioned paths exist; the unversioned mount was removed. Use `/api/v1/...`.

**ClickHouse errors about "concurrent queries within the same session"**
Something built the API's shared client without `threadsafe=True`. Use `build_clickhouse_client` / `build_repository` in `settings.py`, which do.

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
