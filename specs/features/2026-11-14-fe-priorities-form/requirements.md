# Requirements: Priorities and constraints form (step 3)

## Covers

- **PRD requirements:** FR-10 (capture priorities and constraints and show how each affects feasibility), FR-06 (missing inputs identified), §9 (market and operational feasibility), NFR-08.
- **Roadmap exit check satisfied:** partly. Phase 11's exit check ("the full core journey works for the demo field") also needs the comparison UI.

## Inputs

- `docs/rules/strategy-profiles-and-applicability.md` (context keys, outcome effects).
- User answers.

## Outputs

- `/fields/[fieldId]/priorities` for all 45 demo fields.
- URL query with the answers, for example `?manure=no&soil=high`.
- `toEngineContext(answers)` returning `{ manure_access, forage_use_or_buyer, oat_use_or_buyer, small_grain_equipment_or_contractor }`, each `true`, `false` or `null`.
- `/fields/[fieldId]/compare?...` placeholder.

## Acceptance criteria

1. The form has 5 priorities (low, medium, high) and 7 constraints, 12 questions in all, every one optional.
2. Each constraint says why it is asked. The four that the rules read are tagged "Used in the comparison"; the other three are tagged "Recorded for your adviser".
3. `toEngineContext` maps: yes, some, have, can hire and the "own animals or can sell hay" answers to `true`; no, none and neither to `false`; "not sure" and unanswered to `null`. Unit tests cover every question and every option.
4. Answers are stored in the URL; opening a URL restores them. Unknown keys, unknown values and repeated keys are ignored. Tests cover each.
5. Answering, changing and clearing an answer works with mouse and keyboard; a cleared question shows as unanswered.
6. The summary shows "Answered so far: X of 12" and says unanswered questions appear as "not provided". It lists how the answers are used without claiming effects that do not exist.
7. "Compare strategies" carries the answers to the compare placeholder, which lists each question with its answer or "Not provided".
8. The page makes no yield, profit or outcome claims and shows no single score.
9. `npm run check` passes; no horizontal scroll at 360, 390, 768 and 1280 px; console is clean.

## Evidence labels, scale and limitations to preserve

- Answers are `assumption / user input` (PRD §6.2). They are never presented as measured.
- Unknown is kept as unknown: skipped and "not sure" both become `null`.

## Out of scope

The comparison UI, engine calls, saving answers on a server, free-text notes, accounts, translation.
