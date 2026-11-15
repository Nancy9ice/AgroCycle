# Requirements: Split-image hero

Supports NFR-06 (maintainability) and NFR-08 (usability).

1. Use the supplied photographs in their specified order; render two equal columns on desktop and one column below 768 px, without hiding either image.
2. Keep one accessible H1, readable overlays, field/demo CTAs and scroll-navigation behavior. Pilot scope remains in the other landing sections and site footer.
3. Use Futura for landing-page display/body typography, including navigation/footer. Fall back to a sans-serif on systems without Futura; do not copy the licensed system font into the repository.
4. Keep section composition tidy with a dedicated hero stylesheet. Preserve other section content and application data.
5. Record source URLs in the spec, without claiming photography depicts the Iowa pilot.
6. Typecheck, targeted lint, formatting and production build pass; record verification limits.

7. Images touch without a divider and share a translucent green treatment to unify their colours. Text and links remain above the tint.

8. Neither photo has a bottom divider/footer; panels target 97vh with a stable-viewport equivalent, growing only if their content needs space.

9. Landing navigation is 64 px tall on desktop / 60 px on mobile. At the top it is transparent over the photographs with light text; after scrolling it uses a white floating surface with dark text, shown on upward scroll and hidden on downward scroll.

10. The initial transparent hero navigation is absolute rather than always fixed. There is no bottom border. Navigation-item hovers use underlines instead of background fills; focus/open-menu protections remain.

11. Transparent hero navigation has 16 px top padding; floating white navigation has no extra top padding.

12. A pointer-clicked navigation link cannot pin the floating header open. Any downward movement hides it immediately without a positioning-transition flash; returning to the first 80 px restores only the transparent top navigation.

13. Below 768 px, both mobile photographs occupy equal halves of one hero rather than separate full-screen panels. Main copy spans both halves with a readable overlay, and the secondary caption is hidden. Desktop remains unchanged.

14. Use one atomic navigation mode: top is transparent/absolute, hidden cannot display the white bar, floating is white/fixed and only follows upward scrolling. Focus/menu CSS cannot override downward hiding. Close mobile menus on downscroll/link selection.
15. Navigation gutters are 16 px desktop/tablet and 12 px mobile. Mobile hero-nav top padding is 8 px; hamburger is 36 px square, zero corner radius and 4 px padding.
