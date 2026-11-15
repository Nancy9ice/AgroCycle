# Plan: Compare endpoint and API skeleton

- **Role:** be (written by the frontend developer at the team's request, so the frontend can stop using its stand-in. The BE owner should review and take it over.)
- **Spec created:** 2026-11-15
- **Roadmap phase and task:** Phase 10, BE: `/compare` endpoint (and the FastAPI skeleton the rest of Phase 2/7/13 needs)

## Goal

A running FastAPI service that turns "this field plus these farmer answers" into DS2's `Decision`, built on the real data the team has produced. It is the contract the frontend already renders (`web/src/features/compare/types.ts`), so switching the web app from its TypeScript copy of the engine to this API changes one file.

## Approach

- **The API holds no policy.** It builds an `engine.decision.FieldProfile` and `FarmerConstraints`, calls `engine.decision.assess`, and serialises the result. Every rule, sentence and status is the engine's.
- **The server builds the profile, never the browser.** The request carries only the farmer's four answers (`true`, `false` or `null`) and the "high" priorities. County, crop history and indicator status come from the data. A client cannot send a profile value, so it cannot send a wrong one.
- **Unknown stays unknown end to end.** JSON `null` becomes the engine's `UNKNOWN` (the engine's own `FarmerConstraints.from_mapping`), and `UNKNOWN` goes back out as `null`.
- **A repository behind an interface.** `FieldRepository` has two implementations: files (the committed field data, plus DS2's indicator CSVs if `data/out/indicators/` exists) as the default, and ClickHouse (`fields`, `crop_rotation`). The ClickHouse one is tested against a fake client only; it has not been run against the live database. The `field_indicators` table does not exist in the schema yet, so it reports every indicator as unknown.
- **Indicator adapter, with its decisions written down.** DS2's runner and DS2's engine use different names and statuses. The adapter maps `frost_free_days` to the engine's `frost_window`, and treats a required indicator as `ok` only if every season row is `available` (a `partial` row is `unknown`). Both choices are conservative and are flagged for DS2.
- **Sample preview, off the record by default.** `sample_indicators: true` feeds the same sample values the web preview uses (120 degree-day difference, 150 frost-free days, all four indicators `ok`) and the response says `preview: true`. It is a demo affordance, switchable with `AGROCYCLE_ALLOW_SAMPLE_PREVIEW`.
- **Crop-history sentence:** ported from the frontend so API and web say the same thing for the same sequence; tested on the same cases.

## Files, tables and endpoints

- `api/` (`main.py`, `settings.py`, `schemas.py`, `serialise.py`, `facts.py`, `repository.py`, `profile.py`, `crop_summary.py`, `routes.py`, `tests/`).
- Endpoints: `GET /health`, `GET /fields`, `GET /fields/{field_id}`, `POST /fields/{field_id}/compare`. OpenAPI at `/openapi.json`, docs at `/docs`.
- `pyproject.toml` (fastapi, uvicorn; httpx in dev; `api` in testpaths), `Makefile` (`api`), `.env.example` (API settings).
- Reads: `data/fields/*`, optional `data/out/indicators/*.csv`, ClickHouse `fields` and `crop_rotation`.
- Not in this task: `GET /fields/{id}/profile`, `GET /evidence/marsden`, `GET /lineage/{id}`, `POST /fields`.

## Steps (in order)

1. Spec and tracker.
2. Crop summary, facts, repositories, profile adapter, with tests.
3. Schemas, serialisation, routes, app; endpoint tests.
4. Dependencies, Makefile, env example, README.
5. Run the suite and the server; call the endpoint; compare with the web port's output.

## Dependencies and interfaces with other roles

- **DS2:** indicator-name and status adapter (above); `frost_window` vs `frost_free_days`; whether `partial` should count as `ok`.
- **DE:** `field_indicators` table (not in `schema/` yet) for the ClickHouse repository; `crop_rotation` is read as is.
- **FE:** switch `getComparison` to `POST /fields/{id}/compare` (next PR); CORS origins are configurable.
- **uv:** `uv.lock` is not regenerated here (`uv` was not installed on this machine); run `uv lock` once.

## Risks and open questions

- The ClickHouse repository is unverified against the live database.
- The frontend and API each have a crop-history sentence until the profile endpoint exists; they are tested to agree.
- Strict `ok` rule may make every real field abstain if any season has a missing day. That is the honest result, and DS2 can relax it with a written reason.
