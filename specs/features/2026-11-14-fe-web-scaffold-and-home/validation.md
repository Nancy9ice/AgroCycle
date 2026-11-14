# Validation: Web app scaffold and home page

## Checks

| Requirement / criterion | How it will be verified | Evidence kept |
|---|---|---|
| 1. Lint, typecheck, build pass | `make web-check` | Command output pasted in Results |
| 2. Responsive, no console errors, no horizontal scroll | Open in a browser at 360, 768 and 1280 px; check the console | Screenshots, notes below |
| 3. Strategies match PRD §2.2 | Hand-check against the PRD | Note below |
| 4. No computed numbers or outcome claims | Read through the page copy | Note below |
| 5. Evidence types match PRD §6.2 | Hand-check labels against the PRD table | Note below |
| 6. No dead links | Click every link and anchor | Note below |
| 7. Keyboard use | Tab through the page, open and close the mobile menu | Note below |
| 8. Contrast | Check text and background token pairs | Note below |

## Results (fill in after implementation)

- **Date completed:** 2026-11-14 (implementation); manual checks below still open
- **What was run:** `npm run check` in `web/` (ESLint, `tsc --noEmit`, Prettier check, `next build`); layout measured at 360, 390 and 768 px through the Chrome DevTools protocol; screenshots at 1280 px and 390 px; link and anchor check by fetching the served HTML; contrast ratios computed for every text/background token pair.
- **Passed:**
  - 1: lint, typecheck, format and build all pass; `/`, `/field` and `/icon.svg` prerender as static.
  - 2 (partly): no horizontal overflow at 360, 390 and 768 px (document width equals viewport width, no element past the right edge).
  - 3: strategies A, B and C match PRD §2.2 (checked by reading `src/domain/strategies.ts`).
  - 4: the page has no computed numbers, yield or profit claims. The only figures are years in the rotations and scales taken from the PRD (30 m, 10 m from 2024, about 50 km grid, 2003–2011 trial).
  - 5: evidence labels use the PRD §6.2 types (derived, model/reanalysis, classified, survey, experimental).
  - 6: every in-page anchor (`#decision`, `#strategies`, `#how-it-works`, `#honesty`, `#evidence`, `#main`) has a matching element, and `/field` returns 200.
  - 8: all text/background pairs are at least 4.84:1 (lowest: harvest-700 on harvest-100); most are above 5.5:1.
- **Failed or skipped:**
  - 2: browser console errors were not inspected.
  - 7: keyboard use was not tested by hand. The skip link and mobile menu use native `<a>` and `<details>`/`<summary>` elements, and the menu was opened by script, not keyboard.
  - Bug found and fixed during checks: class conflicts (`inline-flex` vs `hidden`) showed the header button on phones; `cn` now merges Tailwind classes with `tailwind-merge`.
  - No automated UI tests yet.
- **Evidence location:** commands run in the session; screenshots were kept in the session scratchpad, not committed.
- **Roadmap exit check met:** not for Phase 7 as a whole (needs the profile screen on real data); this task covers the app shell and home page only.
- **Roadmap tracker updated:** 2026-11-14, left `In progress` until the manual checks (2 console, 7 keyboard) and a team review are done.
