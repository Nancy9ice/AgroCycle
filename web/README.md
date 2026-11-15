# AgroCycle web

The user interface for AgroCycle: a Next.js app that takes a farmer through choosing a field, reading what is known about it, saying what matters on their farm, comparing three rotation strategies, and producing a brief for an adviser.

This document explains how the interface is organised and how it talks to the API. For the service itself, see [`../api/README.md`](../api/README.md). For what the product must do and why, see the repo's [`PRD.md`](../PRD.md) and `specs/`.

## Contents

- [1. Overview](#1-overview)
- [2. Application structure](#2-application-structure)
  - [Pages](#pages)
  - [Code layout](#code-layout)
  - [Features and what each is responsible for](#features-and-what-each-is-responsible-for)
  - [State management](#state-management)
- [3. User journey](#3-user-journey)
  - [1. Field selection (`/field`)](#1-field-selection-field)
  - [2. Field profile (`/fields/{id}/profile`)](#2-field-profile-fieldsidprofile)
  - [3. Farmer priorities and constraints (`/fields/{id}/priorities`)](#3-farmer-priorities-and-constraints-fieldsidpriorities)
  - [4. Strategy comparison (`/fields/{id}/compare`)](#4-strategy-comparison-fieldsidcompare)
  - [5. Evidence and trade-offs](#5-evidence-and-trade-offs)
  - [6. Adviser brief (`/fields/{id}/plan`)](#6-adviser-brief-fieldsidplan)
- [4. API integration](#4-api-integration)
  - [4.1 Base URL](#41-base-url)
  - [4.2 Endpoints consumed](#42-endpoints-consumed)
  - [4.3 Loading, empty and error states](#43-loading-empty-and-error-states)
  - [4.4 With and without the API](#44-with-and-without-the-api)
  - [Data synced into the app](#data-synced-into-the-app)
- [5. Configuration](#5-configuration)
  - [Environment variables](#environment-variables)
  - [Map](#map)
- [6. Local development](#6-local-development)
  - [Prerequisites](#prerequisites)
  - [Install](#install)
  - [Run](#run)
  - [Tests and build](#tests-and-build)
  - [Docker](#docker)
- [7. Troubleshooting](#7-troubleshooting)
- [8. Conventions](#8-conventions)

---

## 1. Overview

The app is for farmers in Story and Boone counties, Iowa. It does not recommend a rotation. It lays out the evidence for three strategies, says what kind of evidence each claim rests on, and says plainly what it cannot tell. Anything unknown is shown as unknown.

It is a Next.js 16 app (React 19, Tailwind 4, MapLibre GL) that renders mostly on the server. The browser never calls the API directly; the Next.js server does (see [API integration](#4-api-integration)).

The main journey is five steps, shown in a progress bar on every step:

```
Field  ->  Profile  ->  Priorities  ->  Compare  ->  Plan
/field     /fields/{id}/  /fields/{id}/  /fields/{id}/  /fields/{id}/
           profile        priorities     compare        plan
```

Two more pages sit outside the journey: the home page (`/`) and `/validation`, a dated record of what has and has not been checked.

The app also runs **with no API at all**. If `AGROCYCLE_API_URL` is unset it falls back to local stand-ins, clearly labelled, so the interface can be developed without a backend (see [4.4](#44-with-and-without-the-api)).

---

## 2. Application structure

### Pages

Routes live in `src/app/` and stay thin: they read params, call a data function, and render a feature screen.

| Route | File | Renders |
|---|---|---|
| `/` | `app/page.tsx` | Home sections from `features/home/` |
| `/field` | `app/field/page.tsx` | `FieldEntry` (step 1) |
| `/fields/[fieldId]/profile` | `app/fields/[fieldId]/profile/page.tsx` | `ProfileScreen` (step 2) |
| `/fields/[fieldId]/priorities` | `.../priorities/page.tsx` | `PrioritiesForm` (step 3) |
| `/fields/[fieldId]/compare` | `.../compare/page.tsx` | `CompareScreen` (step 4) |
| `/fields/[fieldId]/plan` | `.../plan/page.tsx` | `PlanScreen` (step 5) |
| `/validation` | `app/validation/page.tsx` | `ValidationScreen`: the hand-written snapshot, plus a live audit section read from the API |
| `/field-imagery/[fieldId]` and `.../image` | `app/field-imagery/` | Route handlers that pass the API's aerial-photo answer and picture to the browser |

`app/fields/[fieldId]/error.tsx` is the error screen for every field page (step 2 to 5).

### Code layout

```
src/
  app/                 Routes only. Keep pages thin; compose from features.
  features/<name>/     One folder per feature: screen, components, data layer, tests.
  components/
    ui/                Generic primitives (Button, Container, Section)
    layout/            Site header and footer, the five-step progress bar
    brand/             Logo
    evidence/          Evidence-type badge, shown wherever an output appears
    rotation/          Rotation ribbon (home, compare, plan)
  domain/              Shared vocabulary: strategies A/B/C, evidence types, crops
  lib/                 api.ts (server-side API client), routes.ts, plain-words.ts, cn, site metadata
scripts/               Data and engine sync, MapLibre worker copy, screenshot capture
```

### Features and what each is responsible for

| Feature | Responsibility |
|---|---|
| `field/` | Step 1. The map, the demo-field list, drawing your own boundary, browser-side boundary checks, the aerial-photo toggle. `data/load.ts` loads the demo fields and county outlines (from the API, or from the synced files when there is no API); every page that needs a field goes through it. |
| `profile/` | Step 2. The `FieldProfile` contract (`types.ts`), fetching and validating the API's answer (`api-client.ts`), the local stand-in (`get-field-profile.ts`), and the four sections with their provenance drawers. |
| `priorities/` | Step 3. The question set (`questions.ts`), the URL codec for answers, and `toEngineContext`, which turns answers into the facts the engine reads. |
| `compare/` | Step 4. Fetching the decision (`get-comparison.ts`, `api-client.ts`), rewording engine text into plain language, and the outcome, strategy, evidence and open-question components. Also holds the TypeScript copy of the engine. |
| `plan/` | Step 5. The printable adviser brief and the questions-to-ask logic. |
| `ask/` | "Ask about these results": the panel and the server actions that call the API's ask endpoints. Used on profile and compare. |
| `validation/` | The hand-written validation snapshot, and the "engine on our test fields" audit read from the API (`get-test-set.ts`). |
| `home/` | Home page sections and copy. |

### State management

There is no global store and no client-side data-fetching library. State lives in three places:

| State | Where | Why |
|---|---|---|
| Selected field, entry mode | URL (`?field=primary-001`, `?mode=demo`), via `use-selected-field.ts` and `field-entry.tsx` | Shareable, survives reload |
| Farmer's answers | URL query (`?manure=no&soil=high`), encoded and parsed by `answers-codec.ts`; held in React state while the form is open (`use-answers.ts`) and written back with `history.replaceState` | A result can be shared or bookmarked. Parsing keeps only known questions with known values, so a hand-edited URL cannot inject anything |
| Preview mode | URL (`?preview=sample`) | Same reason |
| Profile detail level (Simple or Detailed) | React context (`profile-ui.tsx`) | Per-visit display preference only |
| Draft boundary, location lookup | Component state in `add-your-field.tsx` | Stays in the browser |
| Aerial-photo availability | Hook with an in-memory per-field cache (`use-field-imagery.ts`) | Avoids refetching when switching fields |
| Ask panel result | `useActionState` on a server action | The question and answer are not kept anywhere in the browser |

Server data (profile, comparison) is fetched in server components and handed to screens as props. Pages that read the URL do so inside `Suspense` so the page shell can show immediately.

---

## 3. User journey

### 1. Field selection (`/field`)

Two tabs, chosen by `?mode=`:

- **My field.** Find the field on a satellite map (or use the phone's location), tap its corners, and check the boundary. The boundary and the position stay in the browser. Checks run in `features/field/geometry.ts`: closed ring, enough points, valid coordinates, no self-crossing, inside Story or Boone County, within one county. A valid boundary ends in an honest "not yet": the API can validate a boundary but does not yet prepare data for one, so the app never shows another field's numbers as the farmer's. It offers the demo fields instead.
- **Try a demo field.** A map and list of the 45 practice fields (not real farms), filterable by county. The fields and county outlines come from the API when it is configured. `primary-001` is the default. Selecting a field updates the URL and a summary panel. Fields outside the rotation class show an edge-case note on later steps.

If the field has an aerial photo, a toggle appears on the map (see [4.2](#42-endpoints-consumed)).

### 2. Field profile (`/fields/{id}/profile`)

What is known about the field, in four sections, each labelled for what it is and where it came from:

- **Crop history** by year (USDA's satellite crop map, 2015 to 2025)
- **Climate** (growing-season rain, heat, dry spells and similar)
- **Vegetation** (how green the field looks through the year, from satellite)
- **Soil** (the surveyed soil type and measures)

An availability strip summarises which sections have data. Each card has a provenance drawer (what it is, source, precision, gaps), and a **Simple/Detailed** toggle adds the technical lines. A section with nothing behind it renders as "not loaded" (`NotLoaded`), never as a zero or a placeholder. An "Ask about these results" panel answers questions about the profile.

### 3. Farmer priorities and constraints (`/fields/{id}/priorities`)

Twelve questions, all optional (`features/priorities/questions.ts`):

- **Five priorities** (soil, water, inputs, income, forage), each low, medium or high.
- **Seven practical questions** (manure, a use or buyer for hay and for oats, grain and hay equipment, storage, labour).

Skipping a question means "don't know", which the engine treats as unknown, never as yes or no. Four constraint questions feed the engine (`manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor`); the rest are captured for the adviser brief and tagged as such, so the form never implies an effect that does not exist. Answers go into the URL and travel to the next steps.

### 4. Strategy comparison (`/fields/{id}/compare`)

The engine's decision for the field, shown as:

1. A banner with the single outcome: *worth exploring*, *qualified comparison* or *abstention*, and the reason.
2. The three strategies side by side (A: two-year, B: three-year, C: four-year), in rotation order and never ranked.
3. How the farmer's priorities line up with what the evidence covers.

All engine text is reworded into farmer language by `lib/plain-words.ts` before display. Ids and statuses are left as the engine sent them.

### 5. Evidence and trade-offs

Also on the compare page, below the strategies: **"What the evidence says, one outcome at a time."** Each outcome card carries an evidence-type badge, the claim (with the Marsden Farm trial figures where the engine makes one), what it cannot tell you, and whether it applies to this farm. Outcomes that cannot be assessed are shown, not hidden. Then **Still open** (what would change the answer, and which of it only the farmer can supply), **The limits of this comparison**, and the ask panel.

`?preview=sample` swaps in labelled sample indicator values so the other outcomes can be seen. A banner says the result is not the field's own.

### 6. Adviser brief (`/fields/{id}/plan`)

A one-page printable summary built from the same decision: the outcome, the options, the farmer's answers, questions to take to an adviser (`plan/expert-questions.ts`), and the evidence sources. The print button opens the browser's print dialog, which can save as PDF; the header, footer and buttons are hidden in print.

---

## 4. API integration

### 4.1 Base URL

`AGROCYCLE_API_URL` sets the API address. `lib/api.ts` accepts it with or without the `/api/v1` suffix and adds it if missing, so `http://localhost:8000` and `http://localhost:8000/api/v1` are equivalent.

The variable is **server-only** (not `NEXT_PUBLIC_`). The Next.js server calls the API; the browser calls only the Next.js server. That is why the API's CORS list does not matter for this app, and why aerial photos go through the `/field-imagery` route handlers instead of straight to the API.

All calls use `callApi` in `lib/api.ts`: no caching (`cache: "no-store"`), a 10-second timeout by default (60 seconds for ask, 20 seconds for the photo), JSON in and out.

### 4.2 Endpoints consumed

| Screen | Request | Made by | Notes |
|---|---|---|---|
| Field, Profile, Priorities, Compare, Plan | `GET /fields/demo` and `GET /meta/pilot-area` | Server components, `loadFieldData` / `loadField` | The 45 demo fields (geometry, area, class, notes) and the county outlines. Read once per request. These pages render per request, so an unknown field id is decided by the API's list |
| Profile | `GET /fields/{id}/profile` | Server component, `getFieldProfile` | The page renders per request so it always reflects the latest data |
| Validation | `GET /validation/test-set` | Server component, `getTestSet` | The live "engine on our test fields" audit. A 503 means no audit is loaded yet |
| Compare, Plan | `POST /fields/{id}/compare` | Server component, `getComparison` | Body is the four answers (`manure_access`, `forage_use_or_buyer`, `oat_use_or_buyer`, `small_grain_equipment_or_contractor`, each true, false or null), `priorities`, and `sample_indicators` (the preview flag). The profile is not sent; the API builds it |
| Compare | `POST /analyses/{analysis_id}/ask` | Server action, `askAnalysis` | Panel appears only when the compare response carried an `analysis_id` |
| Profile | `POST /fields/{id}/ask` | Server action, `askField` | |
| Field (map) | `GET /fields/{id}/imagery` | Browser, via `GET /field-imagery/{id}` | Whether there is a photo, its date and bounds |
| Field (map) | `GET /fields/{id}/imagery/image.png` | Browser, via `GET /field-imagery/{id}/image` | Passed through unchanged, cached for an hour |

The compare and plan pages each run their own comparison on every visit, so each visit stores a new analysis on the API.

**Not consumed.** The question set, the evidence figures and the boundary checks live in the web app (typed in or synced, see [Data synced into the app](#data-synced-into-the-app)). The app does not call `GET /fields`, `POST /fields`, `GET /meta/constraint-options`, `GET /analyses/{id}`, the timeseries, sources, indicators, lineage or Marsden endpoints. It also does not yet send the compare request's optional `context` block or show the response's `persistence` fields.

Every response the app reads is checked before use (`isFieldProfile`, `isCompareResponse`, `parseImagery`). An answer that does not look right is an error or, for photos, "no photo", never a guess.

### 4.3 Loading, empty and error states

**Loading**

| Where | What shows |
|---|---|
| Field, profile and priorities pages | A pulsing grey block while the page resolves |
| Compare | "Comparing the options…" |
| Plan | "Preparing the summary…" |
| Ask panel | The submit control is pending while the server action runs |
| Aerial photo | The toggle stays hidden until the check finishes |

**Empty or unknown**

| Situation | What shows |
|---|---|
| Field id not in the field list, or the API says 404 | The Next.js 404 page |
| Validation audit not available | A grey notice in the audit section, with the reason: not connected to the data service, not loaded yet (503), or unreachable. The rest of the page still renders |
| Unknown `?field=` on the field page | A notice, then the primary demo field is selected |
| A profile section the API has no data for (`not_loaded`) | A dashed "not loaded" chip. The availability strip says which |
| No aerial photo | The toggle is hidden |
| A question the farmer skipped | Treated as unknown and listed under "Still open" |
| Ask question the context cannot answer | The answer is marked refused and says why |

**Errors**

| Situation | What shows |
|---|---|
| API unreachable, timeout, non-404 error status, unexpected body | `ServiceError`. Profile, compare and plan show the error screen: "We could not load this screen. … We have not shown a result, because a guess would be worse than none." with **Try again** and **Add or choose a field** |
| API down on the field page (`/field`) | There is no custom error screen on this route, so Next.js's default error page shows. Only the step 2 to 5 pages have the friendly one |
| Ask fails | The panel shows the error text; the page stays usable |
| Aerial photo check fails | The toggle is hidden and the map says why. This differs from "no photo" on purpose |
| Photo fails to load | A 404 (none) or 502 (service problem) from the route handler |

The rule across the app is that a failing service is visible. It is never papered over with a made-up result.

### 4.4 With and without the API

| | `AGROCYCLE_API_URL` set | Unset |
|---|---|---|
| Fields and county outlines | From the API (`/fields/demo`, `/meta/pilot-area`) | From the synced files in `features/field/data/` |
| Profile | From the API. Missing sections are `not_loaded` | Built locally: crop history and soil are real (synced files); climate and greenness are **labelled sample values** |
| Compare, Plan | The API runs the engine | A TypeScript copy of the engine (`features/compare/evaluate.ts`) runs in the app |
| Ask | Calls the API | Says AI explanations are not available in this environment |
| Aerial photos | From the API | None |
| Validation audit | From the API (`/validation/test-set`) | A notice that the site is not connected |

The TypeScript engine is not hand-maintained. `npm run sync:engine` regenerates its rule table and a parity fixture from the Python engine, and `npm test` fails if the port stops matching (`engine-parity.test.ts`). If you change `engine/`, re-run the sync and commit the generated files.

### Data synced into the app

Next.js cannot import files from outside `web/`, so some repo data is copied in as generated JSON. Never edit these by hand. With the API configured, the demo fields and county outlines come from the API instead, so the field JSON is the **no-API fallback** (and the source of the primary field id and the profile stand-in).

| Command | Reads | Writes |
|---|---|---|
| `npm run sync:data` | `data/fields/`, `data/reference/` | `src/features/field/data/*.generated.json`, `src/features/profile/data/profile-source.generated.json` |
| `npm run sync:engine` (needs Python 3) | `engine/` | `src/features/compare/data/rules.generated.json`, `engine-parity.generated.json` |

Re-run the relevant command whenever its source changes.

---

## 5. Configuration

### Environment variables

| Variable | Default | Purpose |
|---|---|---|
| `AGROCYCLE_API_URL` | unset | Address of the API, for example `http://localhost:8000`. Unset means local stand-ins. Server-side only |
| `PORT` | `3004` in Docker | Port for the production server |
| `HOSTNAME` | `0.0.0.0` in Docker | Bind address for the production server |

There are no API keys and no `NEXT_PUBLIC_` variables. Copy `.env.example` to `.env.local` to set the API address for local development. Do not commit `.env.local`.

`AGROCYCLE_API_URL` is read when the server handles a request, not at build time, so one image works in any environment. Set it at runtime. In Docker Compose it is `http://api:8000` (the API's service name on the shared network).

### Map

- **Library:** MapLibre GL.
- **Basemap:** Esri World Imagery raster tiles (`server.arcgisonline.com`), no token needed. Attribution is shown on the map. Check Esri's terms before any public deployment.
- **Worker:** MapLibre runs geometry in a Web Worker that bundlers do not emit. `scripts/copy-maplibre-worker.mjs` copies it into `public/vendor/maplibre/` (git-ignored). It runs automatically on install, dev and build, so you should not need to run it yourself.
- **Overlays:** field polygons and county outlines come from the synced JSON; the aerial photo overlay uses the bounds the API returns.
- **Network:** the map needs internet access for tiles, and the build needs it for Google Fonts.

---

## 6. Local development

### Prerequisites

- Node.js 20 or newer (Docker uses 20, CI uses 22)
- npm or pnpm. Both lockfiles are committed; Docker and CI install with pnpm 10, and the Makefile uses npm
- Python 3 only for `npm run sync:engine`
- The API is optional (see [4.4](#44-with-and-without-the-api))

> This is Next.js 16 and its conventions differ from older versions. Read the bundled docs in `node_modules/next/dist/docs/` before using data-fetching or caching APIs (`AGENTS.md` says the same).

### Install

```bash
cd web
npm install        # also copies the MapLibre worker
```

From the repo root: `make web-setup`.

### Run

```bash
npm run dev        # http://localhost:3004, works with no API
```

To use the API, start it from the repo root (`make api`, port 8000), then point the web app at it:

```bash
# web/.env.local
AGROCYCLE_API_URL=http://localhost:8000
```

Restart `npm run dev` after changing the file.

### Tests and build

| Command | What it does |
|---|---|
| `npm test` | Unit tests (Vitest): geometry checks, answer codec, API response checks, engine parity, plain words, validation content |
| `npm run typecheck` | `tsc --noEmit` |
| `npm run lint` | ESLint |
| `npm run format` / `format:check` | Prettier write or check |
| `npm run build` | Production build (standalone output) |
| `npm run start` | Serve the production build on port 3004 |
| `npm run check` | Lint, typecheck, format check, tests and build, in that order |
| `npm run screenshots -- <url> <dir>` | Capture the demo screenshots from a running app (needs Chrome; see `docs/demo/README.md`) |

From the repo root: `make web-check`. CI runs `typecheck` and `test` on every pull request.

### Docker

```bash
docker compose up --build -d web      # from the repo root; also starts the API it depends on
```

---

## 7. Troubleshooting

**The map is blank or grey, or the console mentions a worker**
`public/vendor/maplibre/` is missing or stale. Run `node scripts/copy-maplibre-worker.mjs` (or reinstall). Also check you are online: the basemap tiles come from Esri.

**Weather and greenness say "sample", the compare page runs without the API, or Ask says it is unavailable**
`AGROCYCLE_API_URL` is not set in the server's environment. Set it in `.env.local` and restart `npm run dev`. In production, set it on the running container, not at build time.

**"We could not load this screen"**
The API did not answer, answered with an error, or sent a body the app did not recognise. Check that the API is running and that `AGROCYCLE_API_URL` points at it (`curl $AGROCYCLE_API_URL/api/v1/health`). In Docker, use `http://api:8000`, not `localhost`. Check the API logs for the request.

**Connection refused to `localhost:8000` from inside Docker**
Inside a container `localhost` is the container itself. Use the API's service name.

**A field page returns 404**
The field id is not one of the 45 in the field list (the API's, or the synced files when there is no API), or the API returned 404 for it. If the data team added fields and you are running without the API, run `npm run sync:data`.

**The validation page says the test-field results are not shown**
The notice gives the reason. "Not connected" means `AGROCYCLE_API_URL` is unset; "not loaded yet" means the API answered 503 because no audit is in `engine_test_set`; "could not be reached" means the API is down.

**Changes to field data or the engine do not appear (without the API)**
The generated JSON is stale. Run `npm run sync:data` or `npm run sync:engine`, then restart the dev server.

**`engine-parity` tests fail**
The TypeScript engine no longer matches `engine/decision.py`. Run `npm run sync:engine` to regenerate the fixture, then fix `evaluate.ts` if it still fails. Do not edit the generated files.

**Profile shows "not loaded" for climate or soil**
Expected when the API has no indicators for that field. This is the API's honest answer, not an app fault. See the API README for loading data.

**No aerial photo toggle**
Either the field has no photo, or the check failed. If it failed, the map says why. Photos need the API in ClickHouse mode with S3 configured.

**Ask panel is missing on the compare page**
It appears only when the compare response included an `analysis_id`. Without the API, comparisons are computed locally and are not stored.

**The answers in the URL reset or are ignored**
Unknown question ids or option values are dropped on purpose. Use the values defined in `features/priorities/questions.ts`.

**`npm run build` fails fetching fonts**
The build downloads Google Fonts. It needs network access.

**`npm install` and `pnpm install` disagree on versions**
Both `package-lock.json` and `pnpm-lock.yaml` are tracked. Docker and CI use pnpm; if you change dependencies, update both.

---

## 8. Conventions

- **Design tokens** live in `src/app/globals.css` (`@theme`). Use semantic classes (`bg-paper`, `text-ink-soft`, `text-forest-700`), never raw hex values in components.
- **Routes** come from `src/lib/routes.ts`. Do not hard-code paths.
- **Domain data** (strategies, evidence types) lives in `src/domain` so every screen shares one source of truth. Evidence-type ids match the API and ClickHouse enum.
- **Server components by default.** Add `"use client"` only for real interactivity.
- **Colour is never the only signal.** Crop colours always sit next to a text label.
- **Honesty rules apply to UI copy.** No yield, profit or outcome claims. Unknown is shown as unknown, never as neutral or favourable (see `specs/mission.md`).
- **No computed numbers without a source.** Anything that is not real data is labelled as sample.
- **`/validation` is hand-written.** `features/validation/content.ts` is a dated snapshot of what has been checked, sorted into four kinds that must never be merged: our own tests, comparison with another source, an independent reference, and expert review. Update it, and `SNAPSHOT_DATE`, when a spec records a new result. A row moves to "done" only when a spec says so.
