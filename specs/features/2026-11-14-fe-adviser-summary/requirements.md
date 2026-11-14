# Requirements: Adviser summary (step 5)

## Covers

- **PRD requirements:** FR-11, FR-12 (traceability), NFR-02, NFR-08. PRD 5.2 step 8 and 8.4 (required decision output: field and boundary source, crop history, strategies, farmer constraints, outcome, assumptions, limitations).
- **Roadmap exit check satisfied:** with step 4, the full core journey works for the demo field (Phase 11 exit check), apart from the API call and real indicators.

## Inputs

`/fields/[fieldId]/plan?<answers>[&preview=sample]`; the `Decision` from `getComparison`; the rule table.

## Outputs

A one-page summary for each of the 45 demo fields, printable.

## Acceptance criteria

1. The page shows: field name, county, boundary source (demonstration polygon or real); crop history sentence; the outcome in words with the engine's reason; the three options with their feasibility and reasons; all 12 questions with the answer or "Not provided"; the questions for the adviser; the evidence list; the limitations and rules version.
2. It says "summary" or "brief", never "plan to follow" or "recommendation", and shows no score, ranking or winner.
3. Questions for the adviser include one per fired rule (using the engine's sentence), one per research-needed crop claim, and the standing questions. Every unanswered farmer question appears as a question.
4. With `?preview=sample` a sample-values banner is at the top; without it, if the outcome is abstention the page says why in the result block.
5. The evidence list shows each claimable outcome's evidence type and source from the rule table, unchanged.
6. "Print this page" opens the print dialog; in print the header, footer, step bar and buttons are hidden and no content is cut off.
7. Links: back to the comparison and to the answers keep the answers and preview flag.
8. `expert-questions.ts` is unit tested; `npm run check` passes; no horizontal scroll at 360, 390, 768, 1280 px; console clean.

## Evidence labels, scale and limitations to preserve

Answers are user input (`assumption`). Evidence types and sources are the rule table's. Sample values are labelled wherever they influence the result.

## Out of scope

PDF generation, saving or emailing, accounts, dates and signatures, translating.
