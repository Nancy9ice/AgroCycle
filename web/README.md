# AgroCycle web

Next.js frontend for AgroCycle. See the repo `PRD.md` and `specs/` for what the product must do and why.

## Run

Needs Node 20+ and npm.

```bash
cd web
npm install
npm run dev        # http://localhost:3004
npm run check      # lint + typecheck + format check + tests + production build
npm test           # unit tests (geometry validation, demo-field data)
```

From the repo root: `make web-setup` and `make web-check`.

> This is Next.js 16. Its conventions differ from older versions; read the bundled docs in
> `node_modules/next/dist/docs/` before using data fetching or caching APIs.

## Structure

```
src/
  app/                 Routes only. Keep pages thin; compose from features.
  features/<name>/     Page sections and logic for one feature (e.g. home).
  components/
    ui/                Generic primitives (Button, Container, Section).
    layout/            Site header and footer.
    brand/             Logo link and wordmark.
    icons/             Reusable SVG icons and the custom logo mark.
    illustrations/     Reusable SVG artwork, including the field patchwork.
    evidence/          Evidence-type badge, reused on every screen that shows an output.
    rotation/          Rotation ribbon, reused by home, compare and plan.
  features/priorities/ Priorities form: question set, URL codec, and `toEngineContext` (the facts DS2's rules read).
  features/profile/    Field profile: the `FieldProfile` contract (`types.ts`), data layer, drawer.
  domain/              Shared product vocabulary: strategies A/B/C, evidence types (PRD §2.2, §6.2).
  lib/                 Helpers: cn, routes, site metadata.
```

## Icons and illustrations

Import SVG components instead of putting SVG markup in screens or layouts:

```tsx
import { CheckIcon } from "@/components/icons/check-icon";
import { FieldPatchwork } from "@/components/illustrations/field-patchwork";

<CheckIcon className="size-4 text-forest-600" />;
<FieldPatchwork className="h-auto w-full" />;
```

Icons accept standard SVG props and are decorative by default; give their parent button or
link an accessible name. The field illustration has its own image label and unique pattern
IDs for each instance. The favicon stays in `src/app/icon.svg` for Next.js metadata.

Icon modules use `.ts` with React `createElement` rather than JSX. Use Lucide when the icon
matches the intended design; if it does not, create a custom `.ts` icon in `components/icons/`.

## Field data

The field screen reads the demo polygons committed by the data team (`data/fields/`,
`data/reference/`). Next.js cannot import files from outside `web/`, so
`npm run sync:data` copies the columns the UI needs into
`src/features/field/data/*.generated.json`. Re-run it when those source files change; never edit
the generated files.

## Profile data

Crop history and soil are real (from the same synced files). Weather and satellite greenness are
**sample values** (`features/profile/data/sample-environment.ts`), labelled as such in the UI, until
the pipeline and API exist. `src/features/profile/types.ts` is the proposed API contract.

## Talking to the API

Set `AGROCYCLE_API_URL` (see `.env.example`, copy to `.env.local`) and the comparison and the adviser brief
call the API's `POST /fields/{id}/compare` from the server, and the profile page calls `GET /fields/{id}/profile` (it is then rendered per request, so it always reflects the latest data). Unset, they use the TypeScript copy of the engine,
so the app works with no backend. A failing API shows an error screen, not a guessed result. The API is in
`../api` (`make api`).

## Comparison (step 4)

`/fields/[id]/compare` renders DS2's `Decision` (`engine/decision.py`). Until BE ships `POST /compare`,
`features/compare/evaluate.ts` is a TypeScript port of the engine, and `npm run sync:engine` (needs
Python 3) re-exports the rule table and a parity fixture from the real engine; `npm test` fails if the
port drifts. No field has computed indicators yet, so the real result is abstention; `?preview=sample`
shows the other outcomes with clearly labelled sample values.

## Adviser summary (step 5)

`/fields/[id]/plan` is a printable one-page brief built from the same `Decision`: result, options,
answers, questions to ask (derived in `features/plan/expert-questions.ts`) and evidence sources. The
browser's print dialog saves it as a PDF; the header, footer and buttons are hidden in print.

## Validation page

`/validation` is a hand-written, dated snapshot (`features/validation/content.ts`) of what has been
checked and by which of four kinds of check. Update it, and `SNAPSHOT_DATE`, when a spec records a new
result; a row moves to "done" only when a spec says so.

## Map

The map uses MapLibre GL with Esri World Imagery (attribution is shown on the map; check Esri's
terms before any public deployment). MapLibre's Web Worker is copied to the git-ignored
`public/vendor/maplibre/` by `scripts/copy-maplibre-worker.mjs`, which runs on install, dev and build.

## Conventions

- **Design tokens** live in `src/app/globals.css` (`@theme`). Use semantic classes (`bg-paper`,
  `text-ink-soft`, `text-forest-700`), never raw hex values in components.
- **Routes** come from `src/lib/routes.ts`. Do not hard-code paths.
- **Domain data** (strategies, evidence types) lives in `src/domain` so every screen shares one
  source of truth. Evidence-type ids match the API/ClickHouse enum.
- **Server Components by default.** Add `"use client"` only for real interactivity.
- **Colour is never the only signal.** Crop colours always sit next to a text label.
- **Honesty rules apply to UI copy:** no yield, profit or outcome claims; unknown is shown as
  unknown, never as neutral or favourable (see `specs/mission.md`).
- **No computed numbers without a source.** Until the API is live, screens read typed mock JSON
  that matches the API contract, clearly labelled as sample data.
