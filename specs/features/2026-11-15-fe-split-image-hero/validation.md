# Validation: Split-image hero

## Checks
- Inspect both supplied images and preserve left/right source order.
- Review desktop/mobile grid, text contrast overlays, font fallback, CTAs and navigation selectors.
- Typecheck, targeted lint, formatting, production build and whitespace check.

## Results
- **Completed:** 2026-11-15, FE.
- Downloaded and visually inspected both source photographs: left landscape 987 × 1480, right barn 987 × 1481. Saved optimized local WebP assets; source URLs in `sources.md`.
- Source review confirms equal columns on desktop, a single column below 768 px, left-to-right source order retained on mobile, and both images always present. Header behavior, CTAs and the section anchor are preserved.
- Added dedicated `hero.css` and removed obsolete single-image hero rules. Futura uses the local font with the documented fallback; no font file redistribution.
- Typecheck, targeted ESLint, changed-file formatting, whitespace checks and production build (190 pages) pass.
- Final CSS refinement removes the divider and gives both photos the same 24% green tint with 80% saturation. Tint pseudo-elements sit below text and controls. Formatting and whitespace checks rerun after this refinement; no repeat build for the CSS-only adjustment.
- No new browser walkthrough or screen-reader audit for this visual trial. Prior landing-page responsive/browser checks do not establish visual approval of the new hero. Existing product tests were not rerun for the markup and styling change.
- Roadmap visual task marked Done; broader Phase 7 data work unchanged.

## Footer and height refinement
Removed both photo footers, their divider lines, scroll prompt, credits and pilot metadata. Source URLs remain in `sources.md`, and pilot geography remains elsewhere on the landing page. Both panels now use a 95vh / 95svh minimum, retaining mobile stacking and allowing content to fit. Removed unused footer rules and source constants. Typecheck, targeted ESLint, formatting and whitespace checks pass. No repeat build or browser walkthrough for this small removal/style change.

## Compact white navigation
Landing header now uses the white surface at both initial and scrolled positions, with dark text, default green CTA and blue focus outlines. Desktop height is 64 px (previously 96 px); mobile height is 60 px (previously 80 px), retaining 44 px controls. Scroll-direction logic is unchanged. Removed redundant transparent/scrolled colour overrides. CSS formatting and whitespace checks pass; no repeated runtime checks for this CSS-only refinement.

## Fixed hero navigation and underline hovers
Header is fixed from initial render, including without JavaScript, and scroll-direction logic keeps it visible while the hero extends beneath it. Once outside the hero, downward hiding and upward revealing resume. Its bottom border and shadow are removed in the hero. Desktop and mobile navigation items underline on hover instead of filling their backgrounds. White surface, compact sizing, keyboard/menu protections and reduced motion are retained. Typecheck, targeted ESLint, formatting, whitespace checks and production build (190 generated pages) pass. Source review only; no repeated browser walkthrough for this follow-up.

## Corrected transparent-top / white-scroll-up navigation
Supersedes the preceding always-white, persistent-hero behavior. Initial hero navigation is absolute and transparent, using the photographs as its background with light text and no bottom border. After 80 px it becomes a white fixed bar: hidden when scrolling down and shown when scrolling up. Compact heights, underline hovers, keyboard/open-menu exceptions and reduced motion are retained. A one-off runtime check exercised the actual effect with scroll positions 0, 79, 81, 240, 220, 260 and 40, confirming top/down/up/return states including the floating-mode boundary. Typecheck, targeted lint, formatting and whitespace checks pass; no browser walkthrough or repeated build for this correction.

## Hero padding and 97vh height
Updated both photo panels to 97vh / 97svh and added 16 px top padding only to the transparent hero header. The floating white header resets top padding to zero. Source selectors, CSS formatting and whitespace checks pass; no repeated runtime checks for this spacing-only change.


## Floating-header visibility bug fix
- Replaced the shared 8 px direction threshold: downward movement now hides the white bar immediately, while cumulative upward movement of 8 px reveals it. Entering the first 80 px resets to the transparent, absolute hero navigation.
- Removed the transform transition that could flash a newly fixed white bar during downward scrolling. Hiding is immediate (`visibility`, opacity and off-screen transform); only upward reveal animates.
- Replaced the broad `:focus-within` exemption with `:has(:focus-visible)`, so clicking a navigation link with a pointer no longer pins the white header open. Keyboard-visible focus and open mobile menus remain protected.
- Corrected reduced-motion specificity so the header reveal animation is disabled too.
- The actual effect passed 13 runtime regression states, including threshold crossing, cumulative upward movement, a one-pixel downward reversal, return to top and another downward pass. Typecheck, targeted ESLint, formatting, whitespace checks and production build (190 pages) pass.
- Native Chrome screenshot confirmed the transparent hero navigation at the top after clicking its logo. Further scroll verification could not finish because the native browser surface returned `noWindowsAvailable` and then reported user interaction; no claim of a completed browser scroll walkthrough.
- Roadmap returned to Done on 2026-11-15.

## Mobile image composition
Below 768 px, one 97vh / 97svh hero contains two equal-height image rows; panel minimum heights reset to zero instead of each taking 97vh. A 44rem content-safe minimum prevents clipping on short screens. Main copy spans both image halves, uses compact mobile spacing and a shared darker overlay for contrast. The secondary caption uses `display: none` on mobile; desktop remains unchanged. Source review, CSS formatting and whitespace checks pass. No repeated browser walkthrough or test suite for this CSS-only layout refinement.


## Strict navigation modes and compact mobile controls
- Replaced separate background/visibility flags with `top`, `hidden` and `floating`. CSS assigns a white background only to `floating`; hidden mode unconditionally hides the header, with no focus/open-menu CSS exceptions.
- Any downward scroll, downward wheel input or downward touch gesture hides the floating bar. Mobile menus close when hiding or selecting a link. Synchronizing position at downward input prevents an already queued upward frame from restoring it.
- Transparent top navigation remains the only navigation in the first 80 px; upward movement reveals the white floating mode after 8 px.
- Nav gutters: 16 px desktop/tablet, 12 px mobile. Mobile transparent-nav top padding: 8 px. Hamburger: 36 × 36 px, square corners, 4 px padding.
- Added five persistent regression tests for initialization, downward traversal from the hero, cumulative upward reveal, one-pixel downward reversals, top reset and resize behavior. All 14 files / 231 tests pass.
- One-off checks exercised the actual effect with wheel/touch listeners, open-menu closure and the pending-frame race. They pass. Typecheck, targeted ESLint, formatting, whitespace checks and production build (190 pages) pass.
- No new browser scroll walkthrough: the native browser was in use on another task, so it was left untouched. This follow-up supersedes earlier focus/menu exceptions described above.
- Roadmap returned to Done on 2026-11-15.

## Single-image trial
`Hero` now defaults to `layout="single"`, rendering only the first supplied Unsplash photograph at full width. Its responsive sizes are `100vw`; copy remains overlaid across one 97vh image on mobile rather than spanning two rows. The second photo/caption is not rendered in this mode. `layout="split"` retains the previous design for easy comparison. Typecheck, targeted ESLint, formatting and whitespace checks pass. No repeated build/browser pass for this reversible visual trial.

## Second-image centered trial
Single-image mode now defaults to the second supplied photograph (the barn), with centered heading, description, eyebrow, assurance and CTA group. Balanced vertical padding and a consistent tint preserve readability; mobile spacing is reduced to avoid crowding. `image="first"` and `layout="split"` retain comparison choices. Typecheck, targeted ESLint, formatting and whitespace checks pass. No repeated browser/build pass for this reversible visual trial.

## NASA logo and fuller introduction
Added the official NASA insignia through a reusable `.ts` image component before the challenge label, replacing the decorative dot. The adjacent text supplies the name, so the logo is decorative to screen readers. Expanded the description with environmental data, local crop/soil context, research evidence, farmer priorities and trade-offs. Centered text measure increased to 44rem. Single-image mobile height now grows naturally for the longer text while retaining its 97vh minimum, preventing clipping. Official SVG source recorded in `sources.md`; independent-project disclosure retained. Typecheck, targeted ESLint, formatting and whitespace checks pass. No new browser walkthrough or repeated test/build run for this asset/copy refinement.
