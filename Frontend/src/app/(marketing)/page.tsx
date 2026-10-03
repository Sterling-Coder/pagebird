import Link from "next/link";
import { WatchDemoButton } from "@/components/WatchDemoButton";

const PRODUCTS = [
  {
    title: "Document / PDF",
    desc: "Translate InDesign IDML and PDF files with full layout preservation — fonts, columns, tables and page breaks stay exactly where they were.",
    href: "/platform/documents",
    live: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files with timing preserved. Every cue stays synced to its original frame.",
    href: "/platform/subtitles",
    live: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <rect x="2" y="4" width="20" height="16" rx="2" />
        <path d="M7 15h4M13 15h4M7 11h10" />
      </svg>
    ),
  },
  {
    title: "Image Translator",
    desc: "Detect and translate text embedded in images — signs, labels, infographics — and render it back in place.",
    href: "/platform/images",
    live: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <rect x="3" y="3" width="18" height="18" rx="2" />
        <circle cx="8.5" cy="8.5" r="1.5" />
        <path d="m21 15-5-5L5 21" />
      </svg>
    ),
  },
  {
    title: "Website Translator",
    desc: "Point at a live URL and get every page translated — navigation, footers, dynamic content included.",
    href: "/platform/websites",
    live: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <circle cx="12" cy="12" r="10" />
        <path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z" />
      </svg>
    ),
  },
  {
    title: "YouTube Subtitles",
    desc: "Paste a YouTube link. We pull the captions, translate them, and hand back a ready-to-upload SRT.",
    href: "/platform/youtube",
    live: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-6 w-6">
        <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.1c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-1.93 29 29 0 0 0 .46-5.42 29 29 0 0 0-.46-5.33z" />
        <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" />
      </svg>
    ),
  },
];

const FEATURES = [
  {
    title: "Layout preservation",
    desc: "Every font, column, table, footnote and page break lands exactly where it was.",
  },
  {
    title: "RTL mirroring",
    desc: "Arabic and Hebrew mirror the whole page — margins, gutters, bullets — not just text direction.",
  },
  {
    title: "OCR built in",
    desc: "Scanned PDFs get OCR, then a translated text layer rebuilt in position.",
  },
  {
    title: "Font substitution",
    desc: "No Japanese in your typeface? We pick a metrically compatible one, not a generic fallback.",
  },
  {
    title: "QA scoring",
    desc: "Every job gets a layout-integrity score. Catch reflow and overflow before it ships.",
  },
  {
    title: "Side-by-side review",
    desc: "Reviewers edit translations against the source page. Approved edits feed back in.",
  },
  {
    title: "Multi-engine translation",
    desc: "OpenAI and DeepL in consensus. Disagreements are flagged for human review.",
  },
  {
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including right-to-left scripts and CJK.",
  },
];

const FORMATS = [
  ".idml", ".pdf", ".ai", ".psd", ".eps",
  ".srt", ".vtt",
  ".docx", ".pptx", ".xlsx", ".html", ".xliff",
];

const STEPS = [
  {
    n: "01",
    title: "Upload",
    desc: "Drop an IDML, PDF, or subtitle file. We read the layout tree, not a flattened text dump.",
  },
  {
    n: "02",
    title: "Pick a language",
    desc: "Choose from 40+ targets. Attach a glossary to lock terms that must never be translated.",
  },
  {
    n: "03",
    title: "Download",
    desc: "Same extension, same styles, same page count. Open it and keep editing as if nothing happened.",
  },
];

export default function Home() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <span className="font-pb-mono mb-6 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Layout-preserving document translation
          </span>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            document.
            <br />
            <span className="text-pb-text">Keep the design.</span>
          </h1>

          <div className="mt-8 flex max-w-4xl flex-col gap-8 lg:mt-12 lg:flex-row lg:items-start lg:justify-between">
            <p className="max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Pagebirdy translates InDesign, PDF, subtitles and more into 40+
              languages — and hands them back with every font, column, table and
              page break exactly where you left it.
            </p>
            <div className="flex shrink-0 items-center gap-4">
              <Link
                href="/login"
                className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
              >
                Translate free
              </Link>
              <WatchDemoButton />
            </div>
          </div>

          {/* Product mock — two cards side by side like giga.ai */}
          <div className="mt-16 grid grid-cols-1 gap-0 overflow-hidden rounded-xl border border-pb-border md:grid-cols-2 lg:mt-20">
            {/* Dark card — upload side */}
            <div className="flex flex-col justify-between bg-pb-bg p-8 md:p-10">
              <div>
                <span className="font-pb-mono text-[22px] text-pb-text-muted">product_magazine.idml</span>
                <div className="mt-6 space-y-3">
                  <div className="h-2 w-[88%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[96%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[70%] rounded-full bg-pb-border" />
                  <div className="mt-4 h-16 w-full rounded-lg bg-pb-bg-card" />
                  <div className="h-2 w-[92%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[64%] rounded-full bg-pb-border" />
                </div>
              </div>
              <div className="mt-8 border-t border-pb-border pt-5">
                <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                  Source · English
                </span>
              </div>
            </div>

            {/* Light/warm card — output side */}
            <div className="flex flex-col justify-between bg-[#f5f0e6] p-8 text-[#1a1914] md:p-10">
              <div>
                <span className="font-pb-mono text-[22px] text-[#a09a88]">product_magazine.zh.idml</span>
                <div className="mt-6 space-y-3">
                  <div className="h-2 w-[76%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[92%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[58%] rounded-full bg-[#d9d3c4]" />
                  <div className="mt-4 h-16 w-full rounded-lg bg-[#e8e2d4]" />
                  <div className="h-2 w-[84%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[50%] rounded-full bg-[#d9d3c4]" />
                </div>
              </div>
              <div className="mt-8 border-t border-[#d1cbbe] pt-5">
                <span className="font-pb-mono text-[11px] tracking-widest text-[#a09a88] uppercase">
                  Translated · Chinese
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── PRODUCTS ─── */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Products
          </span>
          <h2 className="font-pb-display max-w-xl text-4xl text-pb-text md:text-5xl">
            Five ways to translate.
          </h2>

          <div className="mt-14 grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {PRODUCTS.map((p) => (
              <Link
                key={p.href}
                href={p.href}
                className="pb-card-hover group flex flex-col gap-5 rounded-xl border border-pb-border bg-pb-bg-card p-7"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-11 w-11 items-center justify-center rounded-lg bg-pb-accent/10 text-pb-accent">
                    {p.icon}
                  </div>
                  {!p.live ? (
                    <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
                      Coming soon
                    </span>
                  ) : (
                    <span className="font-pb-mono rounded-full bg-emerald-900/30 px-3 py-1 text-[9px] font-bold tracking-widest text-emerald-400 uppercase">
                      Live
                    </span>
                  )}
                </div>
                <div>
                  <h3 className="text-[17px] font-bold text-pb-text">{p.title}</h3>
                  <p className="mt-2 text-[13.5px] leading-relaxed text-pb-text-muted">{p.desc}</p>
                </div>
                <span className="font-pb-mono mt-auto text-[11px] tracking-widest text-pb-accent uppercase opacity-0 transition-opacity group-hover:opacity-100">
                  Learn more →
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            How it works
          </span>
          <div className="flex flex-col justify-between gap-6 md:flex-row md:items-end">
            <h2 className="font-pb-display max-w-lg text-4xl text-pb-text md:text-5xl">
              Three steps. Zero cleanup.
            </h2>
            <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
              Upload → Translate → Download
            </span>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            {STEPS.map((s) => (
              <div
                key={s.n}
                className="group flex flex-col gap-5 rounded-xl border border-pb-border bg-pb-bg p-8"
              >
                <span className="font-pb-mono text-4xl font-bold text-pb-accent/30">{s.n}</span>
                <h3 className="text-xl font-bold text-pb-text">{s.title}</h3>
                <p className="text-[14px] leading-relaxed text-pb-text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Capabilities
          </span>
          <h2 className="font-pb-display max-w-2xl text-4xl text-pb-text md:text-5xl">
            Everything the file carried, carried across.
          </h2>

          <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-pb-border bg-pb-border md:grid-cols-2 lg:grid-cols-4">
            {FEATURES.map((f) => (
              <div key={f.title} className="flex flex-col gap-2.5 bg-pb-bg-card p-7">
                <h3 className="text-[15px] font-bold text-pb-text">{f.title}</h3>
                <p className="text-[13px] leading-relaxed text-pb-text-muted">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FORMATS ─── */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-pb-mono mr-4 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Formats
            </span>
            {FORMATS.map((f) => (
              <span
                key={f}
                className="font-pb-mono rounded-full border border-pb-border px-4 py-1.5 text-[12px] text-pb-text-secondary"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRICING ─── */}
      <section id="pricing" className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Pricing
          </span>
          <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
            <div>
              <h2 className="font-pb-display max-w-lg text-4xl text-pb-text md:text-5xl">
                Start free.
                <br />
                Scale when ready.
              </h2>
              <p className="mt-4 max-w-md text-[15px] leading-relaxed text-pb-text-muted">
                Your first documents are free. When you need more, talk to us — we price by
                volume, not per seat.
              </p>
            </div>
            <Link
              href="/contact"
              className="font-pb-mono inline-flex shrink-0 items-center rounded-full bg-pb-accent px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Book a call
            </Link>
          </div>

          <div className="mt-14 grid grid-cols-1 gap-4 md:grid-cols-3">
            <div className="rounded-xl border border-pb-border bg-pb-bg-card p-8">
              <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Free</span>
              <p className="mt-3 text-3xl font-bold text-pb-text">$0</p>
              <p className="mt-2 text-[13px] text-pb-text-muted">Try it out with your first documents.</p>
              <div className="mt-6 space-y-2.5 text-[13px] text-pb-text-secondary">
                <span className="block">— 5 pages free</span>
                <span className="block">— PDF + IDML</span>
                <span className="block">— All 40+ languages</span>
              </div>
              <Link
                href="/login"
                className="font-pb-mono mt-8 block rounded-full border border-pb-border py-2.5 text-center text-[11px] font-bold tracking-widest text-pb-text uppercase transition-colors hover:border-pb-text"
              >
                Get started
              </Link>
            </div>

            <div className="rounded-xl border border-pb-accent/30 bg-pb-bg-card p-8 shadow-[0_0_40px_rgba(224,138,111,0.08)]">
              <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-accent uppercase">Team</span>
              <p className="mt-3 text-3xl font-bold text-pb-text">Coming soon</p>
              <p className="mt-2 text-[13px] text-pb-text-muted">For teams shipping in several languages.</p>
              <div className="mt-6 space-y-2.5 text-[13px] text-pb-text-secondary">
                <span className="block">— Volume page packs</span>
                <span className="block">— All formats + subtitles</span>
                <span className="block">— Shared glossary</span>
                <span className="block">— Side-by-side review</span>
              </div>
              <span className="font-pb-mono mt-8 block cursor-not-allowed rounded-full bg-pb-accent/20 py-2.5 text-center text-[11px] font-bold tracking-widest text-pb-accent uppercase opacity-60">
                Coming soon
              </span>
            </div>

            <div className="rounded-xl border border-pb-border bg-pb-bg-card p-8">
              <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Enterprise</span>
              <p className="mt-3 text-3xl font-bold text-pb-text">Custom</p>
              <p className="mt-2 text-[13px] text-pb-text-muted">For regulated teams with volume and audit needs.</p>
              <div className="mt-6 space-y-2.5 text-[13px] text-pb-text-secondary">
                <span className="block">— Unlimited pages</span>
                <span className="block">— SSO + audit log</span>
                <span className="block">— Data residency</span>
              </div>
              <Link
                href="/contact"
                className="font-pb-mono mt-8 block rounded-full border border-pb-border py-2.5 text-center text-[11px] font-bold tracking-widest text-pb-text uppercase transition-colors hover:border-pb-text"
              >
                Book a call
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Send us the document you dread translating.
          </h2>
          <Link
            href="/login"
            className="font-pb-mono shrink-0 rounded-full bg-pb-bg px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-text uppercase transition-all hover:bg-pb-bg-raised"
          >
            Translate free →
          </Link>
        </div>
      </section>
    </>
  );
}
