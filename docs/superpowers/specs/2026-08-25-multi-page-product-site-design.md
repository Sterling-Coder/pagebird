# Design: Docly multi-page product site

Date: 2026-08-25
Status: DRAFT

## Context

Docly currently exists as a single-page landing site (`/`) covering the
document-translation product only. The product has grown to include a
second surface (a browser extension), and the single page has become
overloaded (hero, handoff essay, live demo, how-it-works, formats,
accuracy, pricing, language grid, CTA, footer — all on one URL).

Backend/API for either product does not exist yet ("I have all the
backend, will provide later") — this site remains marketing-only,
static content, no real data fetching or auth. Any "Try it free" /
"Start a project" CTA stays a `#anchor` or `mailto:`-style placeholder
until a real backend is wired in; this spec does not include that
wiring.

## Goals

- Split the site into distinct pages so each product (Document
  Translator, Browser Extension) and Pricing have their own URL,
  answering "explain our product properly" and "we can also provide
  small things... create an extension."
- Turn Home into a hub: overview + teasers for both products, not a
  duplicate of the Document Translator page.
- Add a Company/About page for trust (new company, no track record
  yet — matters for a startup-mode product per the earlier office
  hours design doc).
- Reuse existing components; avoid rebuilding what already works.

## Non-goals

- No real backend integration, auth, or payment flow. All CTAs remain
  static links/anchors.
- No CMS/dynamic content system. Content is hardcoded in components,
  matching the existing pattern in this repo.
- No blog, docs/API reference page, or dynamic language/format data —
  out of scope for this round (flagged as future work, not built now).

## Site Map

Flat top-level routes under Next.js App Router (`src/app/`):

| Route          | Purpose                                                        |
|----------------|------------------------------------------------------------------|
| `/`            | Home — hub: hero, both products teased, trust/handoff essay, pricing preview, closing CTA |
| `/translator`  | Document Translator product page — demo, how-it-works, formats, accuracy, languages |
| `/extension`   | Browser Extension product page — own hero/demo-mock/how-it-works |
| `/pricing`     | Standalone pricing — existing pricing cards + FAQ + translator-vs-extension comparison |
| `/about`       | Company — mission, story, contact |

## Architecture

Each route is a Next.js page (`src/app/<route>/page.tsx`) composed from
section components in `src/components/`, following the existing
pattern established by `src/app/page.tsx`. No new framework, no new
dependency beyond what's already installed (Next.js, Tailwind,
Framer Motion).

### Component reallocation

Existing components move from Home into `/translator`, since their
content is translator-specific:
- `HandoffSection` (stays on Home — it's general "why Docly exists"
  framing, not translator-specific mechanics)
- `DemoSection` → `/translator`
- `HowItWorks` → `/translator`
- `FormatsStrip` → `/translator`
- `AccuracyBand` → `/translator`
- `LanguageGrid` → `/translator`

`PricingSection` becomes shared: a trimmed teaser version stays on
Home (top 3 cards, "See full pricing" link to `/pricing`), and the
full version (cards + FAQ + comparison table) lives at `/pricing`.
Rather than fork the component, `PricingSection` takes a `variant:
"teaser" | "full"` prop controlling whether FAQ/comparison render.

`Header` and `Footer` become shared across all pages (already are —
just need real nav links added now that multiple routes exist).

### New components

- `ProductTeaserGrid` (Home) — side-by-side cards for Document
  Translator and Browser Extension, each linking to its product page.
  Same bordered-offset-shadow visual language as `PricingCard`.
- `ExtensionHero`, `ExtensionDemo`, `ExtensionHowItWorks` (`/extension`)
  — new content, mirroring the structure of the translator's
  `Hero`/`DemoSection`/`HowItWorks` but for the browser-extension use
  case (translate any webpage/selected text in-browser, not upload a
  document).
- `PricingFAQ`, `PricingComparisonTable` (`/pricing`) — new, additive
  to existing `PricingSection`.
- `AboutHero`, `AboutStory`, `AboutContact` (`/about`) — new, simple
  content sections following the existing typographic system (bold
  uppercase sans headlines, mono labels, red accent).

### Navigation

`Header` gains real nav (currently masthead-only, no links, matched
pixel-for-pixel to a design reference that had none). New nav, still
within the masthead's 3-column grid:
- Left: `Vol. 01 · SaaS` (unchanged)
- Center: `The Docly Dispatch` masthead (links to `/`, unchanged)
- Right: replaces the static `Remote · 2026` text with a nav row:
  `Product ▾` (dropdown: Document Translator / Browser Extension) ·
  `Pricing` · `About`

Mobile: nav collapses behind a simple toggle (no existing mobile nav
pattern in this repo yet — new, minimal, consistent with the mono/
uppercase link style already used elsewhere).

### Data flow

None — fully static. No client-side fetching, no server actions. Content
lives as typed const arrays/objects inside each component file,
matching the existing pattern (`PLANS` in `PricingSection.tsx`,
`STEPS` in `HowItWorks.tsx`, etc).

### Error handling

- Standard Next.js 404 (`not-found.tsx`) for unmatched routes — not
  currently present in the repo, added as part of this work.
- No forms with real submission yet, so no server-side validation
  needed. Any placeholder "Talk to sales" / "Try it free" links point
  to `#demo`-style anchors or `mailto:` — no dead links.
- Broken internal links get caught by `next build`'s static generation
  (build fails if a `<Link>` target route doesn't exist) — the
  existing build-and-screenshot verification loop used throughout this
  project's history catches this.

### Testing / verification

- `next build` after each page is added — must stay clean (matches
  existing project practice throughout this session).
- Visual check per page in-browser (desktop + one mobile width) via
  the existing Chrome-automation verification pattern used earlier in
  this project — screenshot each new route, confirm layout doesn't
  break the established design system (paper/ink/red palette, mono
  labels, bordered-offset-shadow cards).
- Nav check: every link in the new Header nav resolves to a real page,
  every CTA resolves to either an in-page anchor or `mailto:`.

## Open Questions

- Extension product mechanics (translate selected text? full page?
  which browsers?) are not yet specified by the user — `/extension`
  content will use reasonable placeholder mechanics (mirroring the
  translator's "upload → translate → export" pattern as "select →
  translate → replace in-place") and should be revised once real
  extension scope is known.
- No real domain/hosting yet (per prior design doc,
  `aman-main-design-20260825-165755.md`) — this spec produces the
  site structure only; deployment is explicitly out of scope per
  user's "don't deploy for now" instruction.
