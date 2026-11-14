# AgroCycle web

Next.js frontend for AgroCycle. See the repo `PRD.md` and `specs/` for what the product must do and why.

## Run

Needs Node 20+ and npm.

```bash
cd web
npm install
npm run dev        # http://localhost:3004
npm run check      # lint + typecheck + format check + production build
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
    brand/             Logo.
    evidence/          Evidence-type badge, reused on every screen that shows an output.
    rotation/          Rotation ribbon, reused by home, compare and plan.
  domain/              Shared product vocabulary: strategies A/B/C, evidence types (PRD §2.2, §6.2).
  lib/                 Helpers: cn, routes, site metadata.
```

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
