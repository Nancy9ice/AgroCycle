# Plan: Validation page ("How we checked this")

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 14 (UI side) and the PRD §16 gate: "limitations and evidence types are disclosed", "stakeholder engagement is documented or the gap is explicitly acknowledged"

## Goal

A public page that says, for each part of AgroCycle, what has been checked, by what kind of check, and what has not. It exists so a judge, adviser or farmer can see how far to trust each part, including the gaps. It is the product's own evidence-type honesty applied to the product itself.

## Approach

- **Nine rows, the PRD §11 components.** Field geometry, CDL crop history, HLS, soil, climate indicators, Marsden calculations, applicability rules, decision engine, user review.
- **Four kinds of evidence, kept apart** (PRD §11 closing paragraph): internal tests, agreement with another source, independent reference validation, expert review. Each row shows all four as done, partly or not done, so "tested" is never read as "validated".
- **Content is typed data, written from the repo's own records.** Every claim is taken from a spec's `validation.md` or the roadmap tracker as of 2026-11-14 and names that source. Nothing is invented and nothing is rounded up. The page shows the date and says it is a snapshot.
- **Counts are derived from the rows**, not typed, so the summary strip cannot disagree with the table.
- **The failure stays visible.** The Marsden reconciliation has one result that does not match the paper (2-year manufactured N, 80 in the text, 74.5 from Table S3). It gets its own callout.
- Server component, no client JS. A footer link and a link from the comparison's limits section reach it.

## Files, tables and endpoints

- `web/src/features/validation/` (`content.ts`, `content.test.ts`, `validation-screen.tsx`).
- `web/src/app/validation/page.tsx`; `routes.ts` already has `validation`.
- Footer and comparison limits: a link each.
- No endpoints.

## Steps (in order)

1. Spec and tracker.
2. Content and tests.
3. Screen and page; links.
4. `npm run check`; browser checks at 360, 390, 768, 1280 px.

## Dependencies and interfaces with other roles

- **DS1, DS2, DE, BE:** each owns rows. When a check is done (confusion matrix, expert review, real-data runs), update `content.ts` and the date. A row must not move to "done" without a spec result that says so.
- **Farmer reviewer:** reads the wording.

## Risks and open questions

- The page is a hand-maintained snapshot and will go stale; the date is on the page and the README says to update it with the tracker.
- Test counts are as recorded in each spec and may differ from a fresh run; the page says "as recorded".
