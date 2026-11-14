# Requirements: Web app scaffold and home page

## Covers
- **PRD requirements:** supports NFR-02 (explainability) and NFR-08 (usability); frames FR-11 (decision outcomes, including abstention) for the user. No FR is complete from this task alone.
- **Roadmap exit check satisfied:** partially. Phase 7's exit check ("the profile screen renders real crop-history, soil and climate data end to end") is not met by this task. This task delivers the app shell it depends on.

## Inputs
- PRD §1–§2 (decision question, strategies), §5.2 (user journey), §6.2 (evidence-type labels), §4.4 (what is out of scope).
- `specs/mission.md` principles.

## Outputs
- A running Next.js app in `web/` (`npm run dev`, `npm run build`).
- A home page at `/` with: header and footer, hero, decision statement, strategies A/B/C, five-step flow, the three possible outcomes and what the product will not claim, and the data sources with their evidence types.
- A placeholder at `/field`.

## Acceptance criteria
1. `npm run lint`, `npm run typecheck` and `npm run build` pass with no errors.
2. `/` renders with no console errors at 360 px, 768 px and 1280 px wide, with no horizontal scroll.
3. The three strategies on the page match PRD §2.2: A maize–soybean; B maize–soybean–oat + red clover; C maize–soybean–oat + alfalfa–alfalfa.
4. The page contains no computed numbers, yield, profit or outcome claims.
5. Each data source on the page shows its evidence type using the PRD §6.2 labels.
6. Primary call to action reaches `/field`; there are no dead links on the page.
7. The page is keyboard-navigable: skip link works, focus is visible, the mobile menu opens and closes without a mouse.
8. Text meets WCAG AA contrast.

## Evidence labels, scale and limitations to preserve
- Source cards state evidence type and scale (for example NASA POWER: model/reanalysis, grid about 50 km; CDL: classified output, 30 m, 10 m from 2024).
- The page states the Iowa pilot scope and that fields shown are demonstration polygons.

## Out of scope
Field selection, profile, priorities, comparison, plan and validation screens; API integration; map; charts; authentication; dark mode; the optional "Ask AgroCycle" explanation panel.
