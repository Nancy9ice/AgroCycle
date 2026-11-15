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

**The API is the authoritative decision engine.** Set `AGROCYCLE_API_URL` (see `.env.example`, copy to `.env.local`) and the comparison and the adviser brief call the API's `POST /fields/{id}/compare` from the server, and the profile page calls `GET /fields/{id}/profile` (it is then rendered per request, so it always reflects the latest data). A failing API shows an error screen, not a guessed result. The API is in `../api` (`make api`).

**The offline fallback.** Without `AGROCYCLE_API_URL` the web app answers from `features/compare/evaluate.ts`, a TypeScript copy of `engine/decision.py`, so it runs with no backend. It is a fallback, not a second engine:

- It is labelled. `getComparison` returns `provenance.source` (`"api"` or `"offline_fallback"`); the compare screen shows a banner and the adviser brief names the engine when the copy answered.
- It sees less. It has no weather, no drainage and only sample indicators, so for the same field it does not give the API's answer. Never use it for a real field.
- It is off in production. `next start` and the web image refuse to answer without an API unless `AGROCYCLE_ALLOW_OFFLINE_ENGINE=true`.
- It cannot drift quietly. `npm run sync:engine` re-exports the rule table and a 567-case parity fixture from the real engine; `engine-parity.test.ts` requires the copy to reproduce it, and the API's `api/tests/test_web_export_is_current.py` fails if the committed export differs from the engine in any way. Change `engine/`, run `npm run sync:engine`, commit the result.

## Comparison (step 4)

`/fields/[id]/compare` renders DS2's `Decision` (`engine/decision.py`) from the API, with the offline fallback described above. `npm run sync:engine` (needs Python 3) re-exports the rule table and the parity fixture. Where the real indicators are not computed the result is abstention; `?preview=sample` shows the other outcomes with clearly labelled sample values.

**Evidence hierarchy.** Evidence is not all alike, so the screen sorts it by whose land it is about (`domain/evidence.ts`, `evidenceLayers`; filed by `features/compare/evidence-ledger.ts`): (1) looked up for your field, (2) worked out from those, (3) from the soil survey, (4) from the Marsden experiment, (5) published and not reproduced by AgroCycle, (6) assumed or unknown. The ledger sits in the open on the compare screen, each outcome card says which layer it belongs to, and values the sample preview substitutes are marked "sample", never "used". A new outcome needs no change here: its layer follows from the `evidence_type` the engine sends.

## Adviser summary (step 5)

`/fields/[id]/plan` is a printable brief built from the same `Decision` and the field profile. It carries: field identity and demonstration-field status; crop-history period and source; the evidence ledger; the three strategies with what each needs; the farmer's priorities and constraints (marking the four the rules read); outcomes not shown and why; questions for local expert review (`features/plan/expert-questions.ts`); and the engine, rules version, data version and data sources. It says on the page that it is not a prescription or a farm-management plan. The browser's print dialog saves it as a PDF; the header, footer and buttons are hidden in print.

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
