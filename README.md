# AgroCycle

Environmental and agricultural crop-rotation decision-support tool, built for the **NASA Space Apps Challenge 2026** challenge *"Field Shift: Adapting Farms with NASA Data"*.

AgroCycle helps farmers and agricultural advisers explore alternative crop-rotation strategies by connecting NASA Earth observations with local soil and crop information, experimental evidence and farmer priorities. It shows benefits, trade-offs, uncertainties and evidence gaps, and it can return a qualified comparison or abstain when the evidence is not strong enough.

> **Status:** planning stage. The product requirements and the project "constitution" are written. No application code exists yet.

## Pilot scope

- **Geography:** Story and Boone Counties, Iowa, USA.
- **Strategies compared:** (A) existing 2-year maize–soybean; (B) 3-year with oat and red clover; (C) 4-year with oat and alfalfa.
- **Fields:** one primary demo field plus a test set of about 30–50 fields. All are team-drawn **demonstration polygons**, not real farm boundaries.
- **MVP:** P0 + P1 capabilities (see `PRD.md` §4).
- **Submission format:** a 7-slide deck, with real screenshots from the working app.

## Documents

| File | Purpose |
|---|---|
| [`PRD.md`](PRD.md) | Full product requirements, evidence rules, validation plan and source register |
| [`specs/mission.md`](specs/mission.md) | Mission, scope, principles and team roles |
| [`specs/tech-stack.md`](specs/tech-stack.md) | Architecture, tools, data-integrity and large-data optimisation rules |
| [`specs/roadmap.md`](specs/roadmap.md) | Implementation order in very small phases, with owners, exit checks and the **progress tracker** |
| [`specs/development-rules.md`](specs/development-rules.md) | **Read before contributing:** role and phase clarification, feature specs, status updates, git workflow |
| [`specs/features/`](specs/features/) | One spec folder per implemented phase task (`YYYY-MM-DD-role-feature-name`), with templates in `_template/` |

## Planned architecture

```
Sources (HLS, POWER, CDL, SSURGO, Marsden, ...)
   -> Python ingestion -> S3 (raw, immutable)
   -> Python transforms -> ClickHouse (curated tables behind the app)
   -> FastAPI (profile, evidence, decision engine, provenance)
   -> React + Vite (map, profile, scenario comparison)
```

The app reads only from ClickHouse, so it never depends on live data services.

## Planned repository layout

```
specs/      project constitution (mission, tech stack, roadmap)
ingest/     extraction jobs, one per source
transform/  cleaning, features, ClickHouse loads (SQL and Python)
engine/     deterministic decision engine
api/        FastAPI service
web/        React + Vite frontend
data/fields/  field polygons (GeoJSON) tracked in git; other data is not
docs/       diagrams and write-ups
```

These folders do not exist yet.

## Principles

- Decision support, not an autonomous agronomist.
- Deterministic, traceable calculations. AI may explain outputs but never invent evidence.
- Every output states its evidence type, scale and limitations. Unknown is never treated as neutral.
- No claims of yield, profit or measured soil outcomes, and no claims of adoption without evidence.

## Data and secrets

- Large and raw data live in S3, not in git. See `.gitignore`.
- Credentials (NASA Earthdata, AWS, ClickHouse) go in a local `.env` file that is never committed. Provide a `.env.example` with variable names only.

## Team

Data engineer, two data scientists, backend engineer, frontend engineer and a farmer. Roles are detailed in [`specs/mission.md`](specs/mission.md).

## Getting started

Setup instructions will be added once the first code lands (Phase 0 in the roadmap).

## License

To be decided. Check the licence and access conditions of each data source before redistributing any data.
