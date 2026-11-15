# Validation: Landing-page design

## Checks
- Frontend lint, typecheck, existing tests, production build and changed-file formatting.
- Local browser at 360, 768 and 1440 px: screenshots, overflow, navigation, reveals, reduced motion and no-JavaScript content.
- Source/diff review: separate section files, `.ts` icons, strategies, evidence labels, disclosures and image provenance.

## Results
- **Completed:** 2026-11-15, FE.
- **Passed:** Typecheck; lint (no errors; existing unused `contextType` warning in `features/ask/ask-panel.tsx:20`); 13 test files / 226 tests; changed-file formatting; `git diff --check`; production build with 190 generated pages.
- **Browser:** Native Chrome via CUA, existing local server on port 3004. Inspected screenshots at 360 × 800, 768 × 800 and 1440 × 800, plus the original desktop window. Hero image, typography, cards, workflow, outcome rows and evidence layout render; no horizontal overflow observed. Mobile menu and section anchors work; primary CTA reaches `/field`.
- **Motion:** Normal scrolling shows staggered reveals. Emulated reduced motion keeps content static and visible. Disabled JavaScript and reloaded: landing-page text/evidence remain visible and the field CTA still navigates. Reset emulation and closed the separate test window.
- **Source review:** Seven separate section files, custom `.ts` icons, unchanged strategy/evidence data and disclosures. Header changes are scoped to the home page.
- **Final refinement:** Desktop gutters reduced from 6vw / max 96 px to 3vw / max 48 px, across header, sections and footer. Mobile/tablet padding unchanged. Increased section-number contrast and preserved mobile-menu focus visibility. Final CSS formatting passed; no repeated browser pass for the spacing adjustment.
- **Image:** Local optimized WebP, 361,286 bytes. Exact prompt and provenance in `image-provenance.md`.
- **Limits:** Visual/source review, not a full screen-reader or automated accessibility audit. Browser host integration was unavailable; native Chrome was used. Evidence is retained in this conversation.
- **Roadmap:** This visual maintenance task is Done; broader Phase 7 data/profile work unchanged.


## Scroll-navigation follow-up
- Added `components/layout/scroll-header.tsx` as the client shell around the existing server-rendered navigation.
- Landing header stays visible near the top, reveals after 8 px of upward movement, and hides on downward movement below 128 px. Its scrolled surface is opaque enough for legible dark links over all sections.
- CSS keeps the header visible when focus is inside it or the mobile menu is open. Reduced motion disables the slide transition. No-JavaScript retains the original top navigation; non-home pages retain their sticky header.
- Typecheck, targeted ESLint, changed-file formatting, whitespace checks and production build (190 pages) pass. Existing product tests were already green; no new tests or repeated browser walkthrough for this small follow-up. State thresholds and accessibility selectors reviewed in source.
- Roadmap returned to Done on 2026-11-15.
