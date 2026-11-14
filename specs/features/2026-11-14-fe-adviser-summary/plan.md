# Plan: Adviser summary (step 5, "Plan")

- **Role:** fe
- **Spec created:** 2026-11-14
- **Roadmap phase and task:** Phase 11, FE (journey step 5; PRD 5.2 step 8: "identify questions requiring local expert review")

## Goal

End the journey with something a farmer can take to an adviser or extension agent: one printable page with the field, the result, the options, the answers given, the questions to ask, and the sources behind each claim. It is a brief for a conversation, not a plan to follow.

## Approach

- **Same `Decision` as step 4, no new logic.** The page calls `getComparison` with the same answers and renders the result again in a compact, print-first layout. Wording is "summary" and "brief", never "your plan", because the product is decision support, not prescription.
- **Questions for the adviser are derived, not written freehand.** A pure function (`expert-questions.ts`) turns each rule finding, each research-needed crop claim and the standing limitations into a question, with the engine's own sentence inside it. Unmapped rules still appear, so a new DS2 rule needs no UI change.
- **Traceability (FR-12):** an evidence list gives, for each claimable outcome, its evidence type and source from the rule table, plus the rules version.
- **Sample values never print unlabelled.** When `?preview=sample` is on, a banner at the top of the page says the result is not the field's; it prints with the page.
- **Print:** a client-side button calls `window.print()`; the site header, footer, step bar and buttons are hidden in print with `print:hidden`. No server storage, no PDF library, no account.
- Nothing is stored and no date is printed (pages are cached; a wrong date is worse than none).

## Files, tables and endpoints

- `web/src/features/plan/` (`expert-questions.ts` + test, `plan-screen.tsx`, `print-button.tsx`).
- `web/src/app/fields/[fieldId]/plan/page.tsx`; `routes.ts`: `planRoute` replaces the unused static `plan` route.
- Compare screen: a primary link to the summary.
- `print:hidden` on `SiteHeader`, `SiteFooter`, `FlowSteps`.
- No endpoints.

## Steps (in order)

1. Spec and tracker.
2. `expert-questions.ts` with tests.
3. Screen, print button, route.
4. Link from compare; print styles.
5. `npm run check`; browser check at 360, 390, 768, 1280 px, print emulation, abstention and preview.

## Dependencies and interfaces with other roles

- **DS2:** the question sentences embed `condition_text` and the crop-claim text unchanged.
- **BE:** none; reads the same `Decision`.
- **Farmer / adviser reviewer:** wording of the standing questions.

## Risks and open questions

- Browser print dialogs differ; verified with Chrome print emulation only (no PDF checked on paper).
- DS2 caution strings contain jargon (see step 4 validation); the evidence list shows only evidence type and source, not the cautions, to avoid printing that jargon.
