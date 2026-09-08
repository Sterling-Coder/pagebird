# Docly Multi-Page Product Site Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split the single-page Docly site into five routes (`/`, `/translator`, `/extension`, `/pricing`, `/about`) so each product and pricing get their own URL, with Home acting as a hub that teases both products instead of duplicating the translator's content.

**Architecture:** Next.js 16 App Router, file-based routing under `src/app/`. Shared `Header`/`Footer` move into `src/app/layout.tsx` so every route gets them for free. All content is hardcoded typed data in component files — no CMS, no data fetching, no backend calls. Visual system (paper/ink/red palette, bold-uppercase-sans headlines, mono uppercase labels, bordered offset-shadow cards) is already established and must be reused, not reinvented.

**Tech Stack:** Next.js 16 (Turbopack), React 19, TypeScript, Tailwind CSS v4, Framer Motion. No new dependencies.

**Spec:** `docs/superpowers/specs/2026-08-25-multi-page-product-site-design.md`

## Global Constraints

- No real backend integration, auth, or payment flow — every CTA is a static `#anchor` or `mailto:` link (per spec Non-goals).
- No CMS or dynamic content system — content lives as typed const arrays/objects inside component files, matching the existing pattern (`PLANS` in `PricingSection.tsx`, `STEPS` in `HowItWorks.tsx`).
- No new npm dependencies beyond what's already installed.
- Reuse existing design tokens only: colors `bg-paper`, `bg-paper-dim`, `text-ink`, `text-ink-soft`, `text-muted`, `border-rule`, `bg-red`/`text-red`; typography `font-black uppercase` for headlines, `font-mono uppercase tracking-widest` for labels/eyebrows/CTAs. No new colors, no new fonts.
- `next build` must stay clean after every task — no task ends with a broken build.
- Every task must leave the site in a working, deployable-if-it-were-deployed state (per "don't deploy for now" — still must build clean, just not pushed anywhere).

---

### Task 1: Move Header/Footer into root layout

**Files:**
- Modify: `src/app/layout.tsx`
- Modify: `src/app/page.tsx`

**Interfaces:**
- Consumes: existing `Header` (`src/components/Header.tsx`), `Footer` (`src/components/Footer.tsx`) — no signature changes.
- Produces: every future page under `src/app/*/page.tsx` gets `Header`/`Footer` automatically via the root layout; page files only need to render their own `<main>` content.

This is a refactor extracted from the spec's "Header and Footer become shared across all pages" note — currently every page would otherwise need to import and render them individually. Doing this first means every later task only writes page-specific content.

- [ ] **Step 1: Read current layout and Home page**

Read `src/app/layout.tsx` and `src/app/page.tsx` in full before editing (already done in this session — confirm no drift by re-reading if this task runs in a fresh session).

- [ ] **Step 2: Move Header/Footer rendering into layout.tsx**

Edit `src/app/layout.tsx` — add the imports and wrap `{children}`:

```tsx
import type { Metadata } from "next";
import { Inter, IBM_Plex_Mono } from "next/font/google";
import "./globals.css";
import { Header } from "@/components/Header";
import { Footer } from "@/components/Footer";

const inter = Inter({
  variable: "--font-body",
  subsets: ["latin"],
  weight: ["400", "500", "600", "800", "900"],
});

const plexMono = IBM_Plex_Mono({
  variable: "--font-mono",
  subsets: ["latin"],
  weight: ["400", "500"],
});

export const metadata: Metadata = {
  title: "Docly — Translate any document without breaking the layout",
  description:
    "Docly translates DOC, PDF, INDD and IDML files into 30+ languages at 95% accuracy — text, images and layout, all preserved.",
};

export default function RootLayout({ children }: LayoutProps<"/">) {
  return (
    <html
      lang="en"
      className={`${inter.variable} ${plexMono.variable} h-full antialiased`}
    >
      <body className="min-h-full flex flex-col bg-paper text-ink font-body">
        <Header />
        <main className="flex-1">{children}</main>
        <Footer />
      </body>
    </html>
  );
}
```

- [ ] **Step 3: Remove Header/Footer/main wrapper from Home page**

Edit `src/app/page.tsx` — remove the `Header`, `Footer` imports and the `<Header />`/`<main>`/`<Footer />` wrapper (layout now provides them), keep only the section components as a fragment:

```tsx
import { Hero } from "@/components/Hero";
import { HandoffSection } from "@/components/HandoffSection";
import { DemoSection } from "@/components/DemoSection";
import { HowItWorks } from "@/components/HowItWorks";
import { FormatsStrip } from "@/components/FormatsStrip";
import { AccuracyBand } from "@/components/AccuracyBand";
import { PricingSection } from "@/components/PricingSection";
import { LanguageGrid } from "@/components/LanguageGrid";
import { CTABand } from "@/components/CTABand";

export default function Home() {
  return (
    <>
      <Hero />
      <HandoffSection />
      <DemoSection />
      <HowItWorks />
      <FormatsStrip />
      <AccuracyBand />
      <PricingSection />
      <LanguageGrid />
      <CTABand />
    </>
  );
}
```

- [ ] **Step 4: Build and verify**

Run: `npx next build`
Expected: compiles clean, no errors. Home page still renders Header/Footer (now via layout) plus all existing sections.

- [ ] **Step 5: Visual check**

Start dev server (`npx next dev -p 3210` if not already running), screenshot `/` — confirm it looks identical to before this task (Header masthead + all sections + Footer, unchanged visually).

- [ ] **Step 6: Commit**

```bash
git add src/app/layout.tsx src/app/page.tsx
git commit -m "refactor: move Header/Footer into root layout

Shared across all routes now that the site is becoming multi-page."
```

---

### Task 2: Add 404 page

**Files:**
- Create: `src/app/not-found.tsx`

**Interfaces:**
- Consumes: nothing new.
- Produces: nothing consumed by later tasks — standalone.

- [ ] **Step 1: Write the not-found page**

Create `src/app/not-found.tsx`:

```tsx
import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-32 text-center sm:px-8">
      <span className="font-mono text-[11px] uppercase tracking-widest text-red">
        404
      </span>
      <h1 className="mt-3 text-4xl font-black uppercase tracking-tight sm:text-5xl">
        This page didn&apos;t make it through translation.
      </h1>
      <p className="mx-auto mt-4 max-w-md text-ink-soft">
        The page you&apos;re looking for doesn&apos;t exist. It might have moved.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
      >
        Back to home →
      </Link>
    </div>
  );
}
```

- [ ] **Step 2: Build and verify**

Run: `npx next build`
Expected: compiles clean, `/_not-found` route listed in the build output.

- [ ] **Step 3: Visual check**

Navigate to `http://localhost:3210/this-route-does-not-exist` in the browser, screenshot — confirm the 404 page renders with Header/Footer (from layout) and the message above.

- [ ] **Step 4: Commit**

```bash
git add src/app/not-found.tsx
git commit -m "feat: add 404 page"
```

---

### Task 3: Create /translator page

**Files:**
- Create: `src/app/translator/page.tsx`

**Interfaces:**
- Consumes: existing `Hero`, `DemoSection`, `HowItWorks`, `FormatsStrip`, `AccuracyBand`, `LanguageGrid`, `CTABand` components — no changes to any of them in this task.
- Produces: `/translator` route, referenced by `ProductTeaserGrid` (Task 7) and `Header` nav (Task 8).

Home still renders its own copies of these same components at this point in the plan (removed from Home in Task 7) — this task is purely additive, no risk of breaking Home.

- [ ] **Step 1: Write the translator page**

Create `src/app/translator/page.tsx`:

```tsx
import { Hero } from "@/components/Hero";
import { DemoSection } from "@/components/DemoSection";
import { HowItWorks } from "@/components/HowItWorks";
import { FormatsStrip } from "@/components/FormatsStrip";
import { AccuracyBand } from "@/components/AccuracyBand";
import { LanguageGrid } from "@/components/LanguageGrid";
import { CTABand } from "@/components/CTABand";

export default function TranslatorPage() {
  return (
    <>
      <Hero />
      <DemoSection />
      <HowItWorks />
      <FormatsStrip />
      <AccuracyBand />
      <LanguageGrid />
      <CTABand />
    </>
  );
}
```

- [ ] **Step 2: Build and verify**

Run: `npx next build`
Expected: compiles clean, `/translator` listed as a static route.

- [ ] **Step 3: Visual check**

Screenshot `http://localhost:3210/translator` — confirm it matches the current Home page's translator content (hero through CTA band), since it's the same components.

- [ ] **Step 4: Commit**

```bash
git add src/app/translator/page.tsx
git commit -m "feat: add standalone /translator product page"
```

---

### Task 4: Pricing variant prop + FAQ + comparison table + /pricing page

**Files:**
- Modify: `src/components/PricingSection.tsx`
- Create: `src/components/PricingFAQ.tsx`
- Create: `src/components/PricingComparisonTable.tsx`
- Create: `src/app/pricing/page.tsx`

**Interfaces:**
- Produces: `PricingSection({ variant }: { variant?: "teaser" | "full" })` — `variant` defaults to `"full"` so the existing call site on Home (`<PricingSection />`, no props) keeps rendering exactly as before until Task 7 explicitly passes `variant="teaser"`.
- Produces: `/pricing` route, referenced by `Header` nav (Task 8) and `Footer`/`CTABand` links where relevant.

- [ ] **Step 1: Add variant prop to PricingSection**

Edit `src/components/PricingSection.tsx` — change the exported function signature and wrap the "See full pricing" affordance. Replace the final `export function PricingSection` block with:

```tsx
type PricingSectionProps = {
  variant?: "teaser" | "full";
};

export function PricingSection({ variant = "full" }: PricingSectionProps) {
  return (
    <section id="pricing" className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-12 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Pricing
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Pay for pages. Not for seats.
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            No per-user licenses. Pricing follows document volume, the way
            translation cost already works for your team.
          </p>
        </div>

        <div className="grid gap-10 pt-2 sm:grid-cols-3 sm:gap-8">
          {PLANS.map((plan) => (
            <PricingCard key={plan.name} plan={plan} />
          ))}
        </div>

        {variant === "teaser" ? (
          <div className="mt-10">
            <a
              href="/pricing"
              className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
            >
              See full pricing, FAQ and plan comparison →
            </a>
          </div>
        ) : null}
      </div>
    </section>
  );
}
```

(The `type Row`, `type Plan`, `PLANS` const, and `PricingCard` function above it stay unchanged — only the final exported function changes.)

- [ ] **Step 2: Write PricingFAQ**

Create `src/components/PricingFAQ.tsx`:

```tsx
type Question = { q: string; a: string };

const QUESTIONS: Question[] = [
  {
    q: "How is a \"page\" counted?",
    a: "One page of source content, regardless of word count. A two-column INDD spread counts as one page per side.",
  },
  {
    q: "What happens if I go over my included pages?",
    a: "Overage bills at the same per-page rate as the Pay as you go plan — no surprise tiers, no throttling.",
  },
  {
    q: "Can I mix formats in one plan?",
    a: "Yes. DOC, PDF, INDD and IDML all draw from the same page allowance.",
  },
  {
    q: "Is there a free trial?",
    a: "Your first document is free on every plan, including Pay as you go.",
  },
  {
    q: "Do you offer refunds?",
    a: "If a translated document comes back with broken layout, that page doesn't count against your allowance and isn't billed.",
  },
];

export function PricingFAQ() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            FAQ
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Questions people actually ask.
          </h2>
        </div>
        <div className="divide-y divide-rule border-t border-rule">
          {QUESTIONS.map((item) => (
            <div key={item.q} className="grid gap-2 py-6 sm:grid-cols-[minmax(0,320px)_1fr] sm:gap-8">
              <h3 className="font-black uppercase text-base">{item.q}</h3>
              <p className="text-sm leading-relaxed text-ink-soft">{item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Write PricingComparisonTable**

Create `src/components/PricingComparisonTable.tsx`:

```tsx
type Row = { label: string; translator: string; extension: string };

const ROWS: Row[] = [
  { label: "Billing unit", translator: "Per page", extension: "Per seat / mo" },
  { label: "Formats", translator: "DOC, PDF, INDD, IDML", extension: "Any webpage, selected text" },
  { label: "Starting price", translator: "$0.08 / page", extension: "$8 / seat / mo" },
  { label: "Team plan", translator: "$149 / mo, 2,000 pages", extension: "$49 / mo, 5 seats" },
  { label: "Free tier", translator: "First document free", extension: "First 50 translations free" },
];

export function PricingComparisonTable() {
  return (
    <section className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Compare
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Translator vs. Extension
          </h2>
        </div>
        <div className="overflow-x-auto border border-rule">
          <table className="w-full min-w-[560px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-rule font-mono text-[11px] uppercase tracking-widest text-muted">
                <th className="px-4 py-3 font-normal">&nbsp;</th>
                <th className="px-4 py-3 font-normal">Document Translator</th>
                <th className="px-4 py-3 font-normal">Browser Extension</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row.label} className="border-b border-rule last:border-b-0">
                  <td className="px-4 py-3 font-black uppercase text-xs">{row.label}</td>
                  <td className="px-4 py-3 text-ink-soft">{row.translator}</td>
                  <td className="px-4 py-3 text-ink-soft">{row.extension}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Write the /pricing page**

Create `src/app/pricing/page.tsx`:

```tsx
import { PricingSection } from "@/components/PricingSection";
import { PricingComparisonTable } from "@/components/PricingComparisonTable";
import { PricingFAQ } from "@/components/PricingFAQ";
import { CTABand } from "@/components/CTABand";

export default function PricingPage() {
  return (
    <>
      <PricingSection variant="full" />
      <PricingComparisonTable />
      <PricingFAQ />
      <CTABand />
    </>
  );
}
```

- [ ] **Step 5: Build and verify**

Run: `npx next build`
Expected: compiles clean, `/pricing` listed as a static route. Home page (`/`) still renders `PricingSection` with the default `variant="full"` behavior (no "See full pricing" link) — confirms the prop default preserved existing behavior.

- [ ] **Step 6: Visual check**

Screenshot `http://localhost:3210/pricing` — confirm pricing cards, comparison table, and FAQ all render with the established visual system (bordered cards, dashed rows, mono labels). Screenshot `/` again — confirm Home's pricing section is unchanged (no "See full pricing" link visible, since Home still uses the default `variant="full"` until Task 7).

- [ ] **Step 7: Commit**

```bash
git add src/components/PricingSection.tsx src/components/PricingFAQ.tsx src/components/PricingComparisonTable.tsx src/app/pricing/page.tsx
git commit -m "feat: add standalone /pricing page with FAQ and comparison table"
```

---

### Task 5: Create /extension page

**Files:**
- Create: `src/components/ExtensionHero.tsx`
- Create: `src/components/ExtensionDemo.tsx`
- Create: `src/components/ExtensionHowItWorks.tsx`
- Create: `src/app/extension/page.tsx`

**Interfaces:**
- Produces: `/extension` route, referenced by `ProductTeaserGrid` (Task 7) and `Header` nav (Task 8).
- Placeholder mechanics per spec Open Questions: "select → translate → replace in-place" (mirrors the translator's upload→translate→export pattern), to be revised once real extension scope is known.

- [ ] **Step 1: Write ExtensionHero**

Create `src/components/ExtensionHero.tsx`:

```tsx
export function ExtensionHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly · Browser Extension
      </span>

      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-7xl lg:text-8xl">
        Select it.
        <br />
        <span className="text-red">Translate it in place.</span>
      </h1>

      <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
        Highlight any text on any page — an email, a ticket, a spec doc in
        your browser — and Docly replaces it with the translated version,
        right where it was. No copy-paste, no separate tab.
      </p>

      <div className="mt-10 flex flex-wrap items-center gap-4">
        <a
          href="#extension-demo"
          className="bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
        >
          Add to browser →
        </a>
        <a
          href="/translator"
          className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
        >
          Translating a document instead?
        </a>
      </div>
    </section>
  );
}
```

- [ ] **Step 2: Write ExtensionDemo**

Create `src/components/ExtensionDemo.tsx`:

```tsx
"use client";

import { useState } from "react";

const LANGUAGES = ["French", "German", "Japanese", "Spanish"];

type Status = "idle" | "translating" | "done";

export function ExtensionDemo() {
  const [status, setStatus] = useState<Status>("idle");
  const [language, setLanguage] = useState("French");

  function runDemo() {
    setStatus("translating");
    window.setTimeout(() => setStatus("done"), 900);
  }

  return (
    <section id="extension-demo" className="border-y border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Try it
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Highlight. Right-click. Done.
          </h2>
        </div>

        <div className="border border-rule bg-paper p-6">
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
            Sample page text
          </p>
          <p className="mt-3 text-base leading-relaxed text-ink-soft">
            {status === "done" ? (
              <span className="bg-red/10">
                {language === "French"
                  ? "Veuillez confirmer votre commande avant vendredi."
                  : language === "German"
                    ? "Bitte bestätigen Sie Ihre Bestellung bis Freitag."
                    : language === "Japanese"
                      ? "金曜日までにご注文の確認をお願いします。"
                      : "Por favor confirme su pedido antes del viernes."}
              </span>
            ) : (
              <span className="bg-red/10">
                Please confirm your order before Friday.
              </span>
            )}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => {
                  setLanguage(lang);
                  setStatus("idle");
                }}
                className={`border px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest transition-colors ${
                  language === lang
                    ? "border-ink bg-ink text-paper"
                    : "border-rule text-ink-soft hover:border-ink hover:text-ink"
                }`}
              >
                {lang}
              </button>
            ))}
            <button
              type="button"
              onClick={runDemo}
              disabled={status === "translating"}
              className="ml-auto bg-red px-6 py-2.5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === "translating" ? "Translating…" : "Translate selection"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Write ExtensionHowItWorks**

Create `src/components/ExtensionHowItWorks.tsx`:

```tsx
const STEPS = [
  {
    n: "01",
    title: "Install the extension",
    body: "Add Docly to Chrome, Firefox, or Edge in one click. No account needed to start.",
  },
  {
    n: "02",
    title: "Highlight any text",
    body: "Select text on any page — an inbox, a ticket, a doc in your browser.",
  },
  {
    n: "03",
    title: "Pick a language",
    body: "Right-click, choose a language from the menu that appears.",
  },
  {
    n: "04",
    title: "It's replaced in place",
    body: "The translated text swaps in where the original was — the page layout never moves.",
  },
];

export function ExtensionHowItWorks() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
      <div className="mb-12 max-w-xl">
        <span className="font-mono text-[11px] uppercase tracking-widest text-red">
          How it works
        </span>
        <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
          Four steps. Never leave the page.
        </h2>
      </div>
      <div className="grid gap-0 border-t border-rule sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step) => (
          <div key={step.n} className="border-b border-r border-rule px-1 py-8 pr-6 last:border-r-0 sm:px-6">
            <span className="font-mono text-sm text-red">{step.n}</span>
            <h3 className="mt-4 text-xl font-black uppercase">{step.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">
              {step.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Write the /extension page**

Create `src/app/extension/page.tsx`:

```tsx
import { ExtensionHero } from "@/components/ExtensionHero";
import { ExtensionDemo } from "@/components/ExtensionDemo";
import { ExtensionHowItWorks } from "@/components/ExtensionHowItWorks";
import { CTABand } from "@/components/CTABand";

export default function ExtensionPage() {
  return (
    <>
      <ExtensionHero />
      <ExtensionDemo />
      <ExtensionHowItWorks />
      <CTABand />
    </>
  );
}
```

- [ ] **Step 5: Build and verify**

Run: `npx next build`
Expected: compiles clean, `/extension` listed as a static route.

- [ ] **Step 6: Visual check**

Screenshot `http://localhost:3210/extension` — confirm hero, demo, how-it-works, and CTA band render correctly. Click a language button and "Translate selection" in the demo — confirm the sample text swaps language (mirrors the translator demo's interaction pattern).

- [ ] **Step 7: Commit**

```bash
git add src/components/ExtensionHero.tsx src/components/ExtensionDemo.tsx src/components/ExtensionHowItWorks.tsx src/app/extension/page.tsx
git commit -m "feat: add /extension product page"
```

---

### Task 6: Create /about page

**Files:**
- Create: `src/components/AboutHero.tsx`
- Create: `src/components/AboutStory.tsx`
- Create: `src/components/AboutContact.tsx`
- Create: `src/app/about/page.tsx`

**Interfaces:**
- Produces: `/about` route, referenced by `Header` nav (Task 8) and `Footer`.

- [ ] **Step 1: Write AboutHero**

Create `src/components/AboutHero.tsx`:

```tsx
export function AboutHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        About Docly
      </span>
      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-6xl lg:text-7xl">
        We got tired of watching
        <br />
        <span className="text-red">layouts break in translation.</span>
      </h1>
    </section>
  );
}
```

- [ ] **Step 2: Write AboutStory**

Create `src/components/AboutStory.tsx`:

```tsx
export function AboutStory() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="grid gap-10 sm:grid-cols-2 sm:gap-16">
          <div>
            <h2 className="text-2xl font-black uppercase tracking-tight">
              The problem
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-soft">
              Every team that translates documents ends up with the same
              three-person relay: a translator, a designer to rebuild the
              layout, and someone doing QA to catch what broke in between.
              The handoff is where quality and time both get lost.
            </p>
          </div>
          <div>
            <h2 className="text-2xl font-black uppercase tracking-tight">
              What we&apos;re building
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-soft">
              Docly reads a document&apos;s layout before it translates a
              single word, so text lands back in the frame it came from.
              One tool, one pass, no handoff. We&apos;re starting with
              document formats and expanding from there — a browser
              extension is next.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Write AboutContact**

Create `src/components/AboutContact.tsx`:

```tsx
export function AboutContact() {
  return (
    <section className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 text-center sm:px-8">
        <h2 className="text-3xl font-black uppercase tracking-tight sm:text-4xl">
          Want to talk to us directly?
        </h2>
        <p className="mx-auto mt-4 max-w-md text-ink-soft">
          If you&apos;re dealing with the translation handoff problem right
          now, we want to hear about it.
        </p>
        <a
          href="mailto:hello@docly.example"
          className="mt-8 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
        >
          hello@docly.example
        </a>
      </div>
    </section>
  );
}
```

- [ ] **Step 4: Write the /about page**

Create `src/app/about/page.tsx`:

```tsx
import { AboutHero } from "@/components/AboutHero";
import { AboutStory } from "@/components/AboutStory";
import { AboutContact } from "@/components/AboutContact";

export default function AboutPage() {
  return (
    <>
      <AboutHero />
      <AboutStory />
      <AboutContact />
    </>
  );
}
```

- [ ] **Step 5: Build and verify**

Run: `npx next build`
Expected: compiles clean, `/about` listed as a static route.

- [ ] **Step 6: Visual check**

Screenshot `http://localhost:3210/about` — confirm hero, two-column story, and contact band render correctly with the established visual system.

- [ ] **Step 7: Commit**

```bash
git add src/components/AboutHero.tsx src/components/AboutStory.tsx src/components/AboutContact.tsx src/app/about/page.tsx
git commit -m "feat: add /about page"
```

---

### Task 7: Turn Home into a hub

**Files:**
- Create: `src/components/HomeHero.tsx`
- Create: `src/components/ProductTeaserGrid.tsx`
- Modify: `src/app/page.tsx`

**Interfaces:**
- Consumes: `HandoffSection` (unchanged), `PricingSection({ variant: "teaser" })` from Task 4, `CTABand` (unchanged).
- Produces: Home (`/`) becomes the hub described in the spec — no longer duplicates `/translator`'s content.

All destination routes (`/translator`, `/extension`, `/pricing`) exist by this point (Tasks 3-5), so `ProductTeaserGrid` and the pricing teaser link can safely point to them.

- [ ] **Step 1: Write HomeHero**

Create `src/components/HomeHero.tsx`:

```tsx
export function HomeHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly
      </span>
      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-6xl lg:text-7xl">
        Translation that doesn&apos;t
        <br />
        <span className="text-red">touch the layout.</span>
      </h1>
      <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
        Two ways to use it: translate a whole document, or translate what
        you&apos;re looking at right now in your browser. Same accuracy,
        same layout-first approach, either way.
      </p>
    </section>
  );
}
```

- [ ] **Step 2: Write ProductTeaserGrid**

Create `src/components/ProductTeaserGrid.tsx`:

```tsx
type Product = {
  eyebrow: string;
  title: string;
  body: string;
  cta: string;
  href: string;
};

const PRODUCTS: Product[] = [
  {
    eyebrow: "Document Translator",
    title: "Upload a file. Get it back translated.",
    body: "DOC, PDF, INDD and IDML — 30+ languages, 95% accuracy, layout untouched.",
    cta: "See the translator",
    href: "/translator",
  },
  {
    eyebrow: "Browser Extension",
    title: "Highlight text. Translate it in place.",
    body: "Any webpage, any selection — replaced where it stood, no copy-paste.",
    cta: "See the extension",
    href: "/extension",
  },
];

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="relative">
      <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
      <a
        href={product.href}
        className="relative z-10 block border-2 border-ink bg-paper p-6 transition-opacity hover:opacity-90"
      >
        <p className="font-mono text-[11px] uppercase tracking-widest text-red">
          {product.eyebrow}
        </p>
        <h3 className="mt-3 text-2xl font-black uppercase tracking-tight">
          {product.title}
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          {product.body}
        </p>
        <p className="mt-6 font-mono text-[11px] uppercase tracking-widest">
          {product.cta} →
        </p>
      </a>
    </div>
  );
}

export function ProductTeaserGrid() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="grid gap-10 pt-2 sm:grid-cols-2 sm:gap-8">
          {PRODUCTS.map((product) => (
            <ProductCard key={product.href} product={product} />
          ))}
        </div>
      </div>
    </section>
  );
}
```

- [ ] **Step 3: Rewrite Home page**

Edit `src/app/page.tsx` — replace the entire file:

```tsx
import { HomeHero } from "@/components/HomeHero";
import { ProductTeaserGrid } from "@/components/ProductTeaserGrid";
import { HandoffSection } from "@/components/HandoffSection";
import { PricingSection } from "@/components/PricingSection";
import { CTABand } from "@/components/CTABand";

export default function Home() {
  return (
    <>
      <HomeHero />
      <ProductTeaserGrid />
      <HandoffSection />
      <PricingSection variant="teaser" />
      <CTABand />
    </>
  );
}
```

- [ ] **Step 4: Build and verify**

Run: `npx next build`
Expected: compiles clean. `Hero`, `DemoSection`, `HowItWorks`, `FormatsStrip`, `AccuracyBand`, `LanguageGrid` are no longer imported by Home (only by `/translator` from Task 3) — confirm no unused-import warnings.

- [ ] **Step 5: Visual check**

Screenshot `http://localhost:3210/` — confirm it now shows: HomeHero, the two-product teaser grid (each card linking out), HandoffSection, pricing teaser (3 cards + "See full pricing" link), CTABand. Click both product cards — confirm they land on `/translator` and `/extension`. Click "See full pricing" — confirm it lands on `/pricing`.

- [ ] **Step 6: Commit**

```bash
git add src/components/HomeHero.tsx src/components/ProductTeaserGrid.tsx src/app/page.tsx
git commit -m "feat: turn Home into a hub linking to /translator and /extension

Removes duplicate translator content from Home now that /translator
exists as its own page."
```

---

### Task 8: Real navigation in Header

**Files:**
- Modify: `src/components/Header.tsx`

**Interfaces:**
- Consumes: all four routes now exist (`/translator`, `/extension`, `/pricing`, `/about`) — safe to link to all of them.
- Produces: nothing consumed by later tasks — final task in the plan.

- [ ] **Step 1: Write the new Header with real nav**

Edit `src/components/Header.tsx` — replace the whole file:

```tsx
"use client";

import { useState } from "react";
import Link from "next/link";

export function Header() {
  const [productOpen, setProductOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);

  return (
    <>
      <div className="h-[3px] bg-ink" />
      <header className="relative border-b border-ink">
        <div className="mx-auto grid max-w-6xl grid-cols-3 items-center px-6 py-5 sm:px-8">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            Vol. 01 · SaaS
          </span>
          <Link
            href="/"
            className="justify-self-center text-center text-lg font-black uppercase tracking-tight sm:text-xl"
          >
            The Docly Dispatch
          </Link>

          <nav className="hidden justify-self-end items-center gap-6 font-mono text-[11px] uppercase tracking-widest sm:flex">
            <div
              className="relative"
              onMouseEnter={() => setProductOpen(true)}
              onMouseLeave={() => setProductOpen(false)}
            >
              <button
                type="button"
                className="text-ink-soft transition-colors hover:text-ink"
              >
                Product ▾
              </button>
              {productOpen ? (
                <div className="absolute right-0 top-full w-56 border border-ink bg-paper py-2 shadow-[4px_4px_0_rgba(0,0,0,1)]">
                  <Link
                    href="/translator"
                    className="block px-4 py-2 text-ink-soft hover:bg-paper-dim hover:text-ink"
                  >
                    Document Translator
                  </Link>
                  <Link
                    href="/extension"
                    className="block px-4 py-2 text-ink-soft hover:bg-paper-dim hover:text-ink"
                  >
                    Browser Extension
                  </Link>
                </div>
              ) : null}
            </div>
            <Link href="/pricing" className="text-ink-soft transition-colors hover:text-ink">
              Pricing
            </Link>
            <Link href="/about" className="text-ink-soft transition-colors hover:text-ink">
              About
            </Link>
          </nav>

          <button
            type="button"
            onClick={() => setMobileOpen((open) => !open)}
            className="justify-self-end font-mono text-[11px] uppercase tracking-widest text-ink-soft sm:hidden"
            aria-expanded={mobileOpen}
            aria-label="Toggle menu"
          >
            {mobileOpen ? "Close" : "Menu"}
          </button>
        </div>

        {mobileOpen ? (
          <nav className="flex flex-col gap-1 border-t border-rule px-6 py-4 font-mono text-[11px] uppercase tracking-widest sm:hidden">
            <Link href="/translator" className="py-2 text-ink-soft hover:text-ink">
              Document Translator
            </Link>
            <Link href="/extension" className="py-2 text-ink-soft hover:text-ink">
              Browser Extension
            </Link>
            <Link href="/pricing" className="py-2 text-ink-soft hover:text-ink">
              Pricing
            </Link>
            <Link href="/about" className="py-2 text-ink-soft hover:text-ink">
              About
            </Link>
          </nav>
        ) : null}
      </header>
    </>
  );
}
```

- [ ] **Step 2: Build and verify**

Run: `npx next build`
Expected: compiles clean. `Header` is now a client component (`"use client"`) — confirm this doesn't break static generation of any route (it won't; interactivity in a shared layout component is standard Next.js App Router usage).

- [ ] **Step 3: Visual check — desktop**

Screenshot `/` at desktop width. Hover "Product ▾" — confirm the dropdown appears with both product links. Click "Pricing" — lands on `/pricing`. Click "About" — lands on `/about`. Click the masthead — lands on `/`.

- [ ] **Step 4: Visual check — mobile**

Resize to a mobile width (or use `mcp__claude-in-chrome__resize_window` if available in the session), screenshot `/`. Confirm the desktop nav is hidden and a "Menu" toggle appears. Click it — confirm the mobile nav list appears with all four links, and toggles closed when clicked again.

- [ ] **Step 5: Full site nav check**

From each of the five pages (`/`, `/translator`, `/extension`, `/pricing`, `/about`), confirm the Header nav renders identically (it's shared via layout) and every link resolves to a real page — no 404s.

- [ ] **Step 6: Commit**

```bash
git add src/components/Header.tsx
git commit -m "feat: add real navigation to Header (Product dropdown, Pricing, About)

Replaces the static masthead-only header now that /translator,
/extension, /pricing, and /about all exist as real routes."
```

---

## Self-Review Notes

- **Spec coverage:** every spec section has a task — Context/Goals → Tasks 3-7 (page split), Non-goals respected (no backend/CMS/new deps anywhere above), Site Map → one task per route (2, 3, 4, 5, 6), Architecture/component reallocation → Task 7, Navigation → Task 8, Error handling → Task 2 (404) + build-catches-broken-links (every task's Step "Build and verify"), Testing/verification → every task ends with build + visual check.
- **Placeholder scan:** no TBD/TODO markers; every step has real, complete code, not a description of code.
- **Type consistency:** `PricingSection`'s `variant?: "teaser" | "full"` prop (Task 4) is the only new prop introduced across tasks, and it's used consistently — Home passes `variant="teaser"` (Task 7), `/pricing` passes `variant="full"` (Task 4 Step 4), the default `"full"` covers any call site that doesn't pass it. `href`/`eyebrow`/`title`/`body`/`cta` fields in `ProductTeaserGrid`'s `Product` type (Task 7) and `PricingComparisonTable`'s `Row` type (Task 4) are each used only within their own file — no cross-task name collisions to check.
