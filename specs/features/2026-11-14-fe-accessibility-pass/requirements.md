# Requirements: Accessibility and keyboard pass

## Covers

PRD NFR-08 (usability), §16 (limitations disclosed). Not a conformance claim.

## Acceptance criteria

1. Axe (WCAG 2.0/2.1 A and AA) reports no serious or critical violations on the pages and states listed in the plan; any remaining minor or incomplete item is listed with the reason.
2. Every stop in the keyboard walk has an accessible name and a visible focus indicator.
3. The skip link is the first stop and moves focus to the main content.
4. Radio groups on the priorities form work with arrow keys and Tab moves between groups, not between options.
5. The provenance drawer opens from the keyboard, keeps focus inside, closes with Escape and returns focus to the opening button.
6. The map is not a keyboard trap, and the field list offers every field.
7. `npm run check` passes after fixes.
8. The results state plainly that no real screen reader was used.

## Out of scope

Screen-reader testing with real assistive technology, translation, user testing with disabled people.
