# Requirements: Reusable SVG components

## Covers
- **PRD requirements:** supports NFR-08 (usability) through preserved accessible visual controls.
- **Roadmap exit check satisfied:** maintenance only; does not complete Phase 7's real-data profile requirement.

## Inputs and outputs
Existing inline SVG artwork becomes typed React components in `components/icons/` and `components/illustrations/`. Call sites import those components and supply their existing presentation props.

## Acceptance criteria
1. Screen, layout and brand composition files contain no inline SVG markup; the Next.js favicon stays at `app/icon.svg`.
2. Icons accept SVG props; decorative icons remain hidden from assistive technology and named controls retain their names.
3. Artwork geometry, colours, sizing, text and interactions remain unchanged, including the user's current hero and logo edits.
4. Repeated field illustrations use distinct pattern IDs, so they can coexist on a page.
5. Lint, typecheck, the existing test suite and production build pass; changed files pass formatting checks.
6. All icon modules use `.ts` without JSX. Use a custom `.ts` icon when Lucide does not match the required artwork.

## Evidence labels, scale and limitations to preserve
The field illustration remains explicitly illustrative; all evidence content and source limitations are unchanged.

## Out of scope
Landing-page redesign, new icon dependencies, data changes and favicon redesign.
