# Responsive

Every screen, designed. Content-driven breakpoints. Written mobile-first, finished desktop-first-class: neither end is an afterthought.

## The width ladder (every build, no exceptions)

Render and look at the page at **320, 375, 414, 768, 1024, 1280, 1440 and 1920 px**. Screenshot each one and read the screenshot. A class-name grep or a build exit code does not count as looking.

| Band | Widths | What the layout must do |
|---|---|---|
| Phone | 320 to 480 | One focused column. Secondary panels become a drawer, a tab or a sheet, never deleted. Tap targets at least 44 px. |
| Tablet | 481 to 1023 | Two columns where the content earns it. Side panel can collapse to a toggle. |
| Laptop | 1024 to 1439 | Use the width on purpose: persistent side panel, multi-column grids, a larger type scale. The primary content column keeps a readable measure; the rest of the screen is filled with real, useful structure. |
| Desktop | 1440 to 1919 | Same composition as laptop with more generous gutters and a roomier scale. No stretched phone layout, no centred strip floating in empty space. |
| Wide | 1920 and up | Cap the measure and the shell width, grow the margins, keep alignment on one axis. Nothing looks lost. |

"Responsive" means each band is composed, not that one layout is stretched or squeezed. Hiding a feature on a size is allowed only when a smaller equivalent exists (drawer for side panel). A page that is excellent at 375 and thin at 1440, or the reverse, is not done.

Desktop checks, in addition to the phone floor below:

- At 1280 and up, no more than about 40 percent of the viewport width is empty margin unless the page is deliberately a single-column reading page (Long Document, Letter).
- The above-the-fold at 1440 x 900 shows the product's real content, not just a header and an empty field.
- Line length stays between 45 and 80 characters for prose; chat bubbles, cards and panels get their own max widths.
- Type scale steps up with `clamp()` between bands instead of jumping.
- Hover and keyboard states exist on desktop; touch states exist on phone (`pointer: coarse`).

## Phone floor — non-negotiable at every width

Every Hallmark output must render flawlessly at **320 px, 375 px, 414 px, and 768 px**, and also hold at 1024 to 1920 (above). Eyeball each viewport before marking the output complete:

- No horizontal scroll (slop-test gate 34)
- No clickable text wrapping to two lines (gate 49)
- No image-bearing grid pushing the layout past viewport — use `minmax(0, 1fr)`, never bare `1fr`, on tracks containing images (gate 50)
- Root carries `overflow-x: clip` on both `html` and `body` — never `hidden` (gate 34)
- Display headers wrap inside long words via `overflow-wrap: anywhere; min-width: 0` (gate 51)
- Section heads collapse to one column on mobile across every theme variant — per-theme overrides need a matching mobile rule (gate 52)
- No scroll-jump on radio-tab clicks — radios in normal flow OR JS guard with `focus({ preventScroll: true })` (gate 53)

This is a hard floor, not a wish list. A page that fails any of these on any of those four widths is not done. The slop-test gates listed run automatically — keep this checklist near the screen while building.

## Principles

- Base styles are for the smallest viewport. `min-width` media queries add as you go up. Never `max-width` as the primary direction.
- Breakpoints are where the *content* breaks, not where a device sits. If the headline reflows awkwardly at 720px, that's a breakpoint — regardless of what the Tailwind defaults say.
- Use `pointer` and `hover` media queries instead of width to detect *interaction capability*.

## Breakpoints

Three or four, content-driven. As a default:

```css
@media (min-width: 40rem) { /* ~640px — tablet, small laptop */ }
@media (min-width: 60rem) { /* ~960px — desktop baseline */ }
@media (min-width: 90rem) { /* ~1440px — wide */ }
```

Use `rem` so the breakpoints respect the user's font size.

## Fluid scaling

Prefer `clamp()` for sizes that change continuously; use media queries for layouts that change discretely.

```css
h1 { font-size: clamp(2.5rem, 4vw + 1rem, 6rem); }
.container { padding-inline: clamp(1rem, 4vw, 4rem); }
```

## Pointer and hover queries

```css
@media (hover: hover) and (pointer: fine) {
  .card:hover { transform: translateY(-2px); }
}
@media (pointer: coarse) {
  .btn { min-height: 48px; }
}
```

Never build a mouse-hover interaction that has no touch equivalent.

## Clickable text — never wraps

Buttons, primary nav links, footer links, tab labels, breadcrumbs, and CTAs must read as **single-line affordances at every viewport between 320 px and 1920 px**. A button or nav link wrapping to two lines looks broken — visitors read it as a styling error, not as intentional. The shortest fix is almost always to shorten the label.

```css
/* Affordances are single-line — let the parent reflow, not the label. */
.btn,
.nav__link,
.foot__link,
.cta {
  white-space: nowrap;
}
```

```css
/* When the row can't fit, collapse the row, not the labels. */
@media (max-width: 40rem) {
  .nav__rail { display: none; }      /* desktop nav hides */
  .nav__sheet-toggle { display: grid; } /* mobile menu shows */
}
```

**Order of fixes**, when something does wrap:

1. **Shorten the label.** *"Get started free"* → *"Start free"*. *"Read the documentation"* → *"Read docs"*. *"Schedule a demo"* → *"Book demo"*. Most CTA labels are 30–40 % longer than they need to be.
2. **`white-space: nowrap`** on the affordance, let the parent flex/grid reflow.
3. **`hidden=until-found`** the lowest-priority nav item at narrow widths (it remains in DOM for find-in-page and SEO).
4. **Collapse the nav** into a sheet / off-canvas / disclosure menu below a content-driven breakpoint.

**Never:** let a primary CTA or top-level nav link wrap. Long footer-link labels can wrap *only* in a footer column where wrapping is part of the column's rhythm — not in the inline footer link strip (Ft2).

This is gate **49** in [`slop-test.md`](slop-test.md). Audit any output that ships interactive affordances and confirm none wrap at the breakpoints listed above.

## Viewport units

- Use `dvh` / `svh` / `lvh` instead of `vh` for heights that interact with mobile chrome.
- Never `width: 100vw`. Use `width: 100%` with padding; `100vw` includes the scrollbar on desktop and causes overflow.

## Safe areas

For iOS notch / Android navigation bars:

```html
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
```

```css
body {
  padding-inline: max(1rem, env(safe-area-inset-left));
  padding-bottom: max(1rem, env(safe-area-inset-bottom));
}
```

## Tables on small screens

Tables of data that won't fit: collapse to cards. Use `display: block` on `<tr>` and `data-label` attributes keyed from `<th>`, rendered via `::before`. Or, the better option: redesign the data for small screens — tables are rarely the right mobile representation.

## Images

- `srcset` with width descriptors for responsive sizing.
- `<picture>` for art direction (different crop at different widths).
- `loading="lazy"` on anything below the fold.
- `width` and `height` attributes on every image, always, to avoid CLS.

## Internationalisation

- Reserve 30–40% extra horizontal space for German, Russian, and Finnish translations.
- Use logical properties: `margin-inline-start`, `padding-block`, `border-inline-end`. Not `margin-left` etc. RTL comes for free.
- Don't hard-code language-specific punctuation or date formats.

## Bans

- Desktop-first media queries (`max-width: 768px` as the primary direction).
- `vh` on full-height layouts (use `dvh`).
- `100vw` widths.
- Device-sniffing UA strings instead of feature queries.
- Hover-only interactions.
- Ignoring `prefers-color-scheme` when the app claims to support dark mode.
- Fixed pixel breakpoints that don't respect `rem`.
- Tables of 10+ columns on mobile without a redesign.
