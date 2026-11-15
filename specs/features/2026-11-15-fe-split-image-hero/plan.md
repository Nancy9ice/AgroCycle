# Plan: Split-image hero

- **Role:** FE
- **Date:** 2026-11-15
- **Roadmap task:** Phase 7, FE: split-image hero exploration

Use the two user-provided Unsplash photographs, first on the left and second on the right, stacked below 768 px. Keep copy/CTAs over the first panel, photography visible on the second, and retain the scroll-aware navigation. Save optimized local images and source URLs. Interpret “Futuru” as Futura: use the installed font through a home-page CSS stack, with a sans-serif fallback rather than redistributing a system font. Keep the hero in its own component and stylesheet. Existing data and other application screens are unchanged.

Validate typecheck, targeted lint, formatting and production compilation; inspect responsive CSS and image dimensions. Keep the previous generated asset for the closing section.

## Image blending refinement
Remove the center gap and apply a shared 24% translucent green wash over both photographs, with restrained desaturation. The tint sits below the content so text and controls retain their contrast.

## Footer and height refinement
Remove the bottom divider/footer from both photo panels, including the scroll link, photo credits and pilot metadata. Keep image source URLs in `sources.md`. Target 95vh (95svh on supporting browsers) per image panel while allowing content to fit on small screens.

## Navigation appearance refinement
Use a solid white landing navigation at the top and while scrolling. Reduce its height to 64 px on desktop and 60 px on mobile, with dark links, a green CTA and visible focus indicators. Keep scroll-direction behavior intact.

## Hero navigation refinement
Keep the landing header fixed from initial render and visible throughout the hero. Below the hero retain directional hiding/revealing. Remove its bottom border/shadow over the hero; use underline hovers for desktop/mobile navigation links. White background and compact heights stay unchanged.

## Corrected navigation modes
User clarified that the initial hero navigation must be transparent over the photographs, not a persistent white bar. Use an absolute transparent header at the top; after 80 px of scrolling it becomes a fixed white floating header, hidden on downward scroll and revealed on upward scroll. Retain compact heights, underline hovers, no bottom border, keyboard/menu protections and reduced motion. This supersedes the preceding white/always-visible hero navigation refinements.

## Final spacing adjustment
Use 97vh / 97svh photo panels and add 16 px top padding to the transparent hero navigation only. White floating navigation keeps its compact sizing and zero extra top padding.

## Scroll visibility correction
Hide the floating header immediately on any downward movement, require a small cumulative upward movement before revealing it, and reset to the transparent original navigation near the top. Use a reveal-only animation so changing absolute/fixed positioning cannot flash a white bar while scrolling down. Pointer focus must not pin it open; retain keyboard-visible focus and open-menu protection. Verify actual browser scrolling and focus where available.

## Mobile image composition
Fit the two stacked mobile photographs into one hero, each occupying half its height. Let the main copy span the shared backdrop and hide the secondary right-panel caption below 768 px. Keep a 97vh / 97svh target with a small content-safe minimum on short screens; desktop composition stays unchanged.

## Strict navigation states and compact mobile controls
Replace independent visibility/background attributes with atomic top/hidden/floating states. Apply a white surface only in floating mode. Remove all CSS focus/menu exceptions that can override downward hiding; close the mobile menu on downward movement and on link selection. Also hide on downward wheel/touch intent. Add regression coverage for state transitions. Reduce nav horizontal gutters to 16 px (12 px mobile), hero-nav mobile top padding to 8 px, and hamburger to a 36 px square with 4 px padding.

## Single-image trial
Default the hero to only the first Unsplash image across the full width, retaining 97vh sizing, copy, tint and navigation. Keep a `layout="split"` component option for easy comparison with the previous design. Preserve both local assets and the split CSS.

## Second-image centered trial
Default the single-image hero to the second supplied photograph and center its main copy/CTAs. Keep the first-photo and split options for comparison, retain 97vh sizing and navigation, and use a readable tint over the lighter barn photograph.

## NASA label and fuller hero introduction
Place an official NASA SVG asset before the challenge label through a reusable `.ts` component, keeping the adjacent text as its accessible label. Expand the hero description with field context, rotation trade-offs and practical farm priorities, with no predicted outcome claims. Give the centered introduction a wider measure. Preserve the independent-project disclosure.
