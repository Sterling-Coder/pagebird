import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Platform — Pagebirdy",
  description:
    "Five products, one platform. Translate documents, subtitles, images, websites and YouTube captions — layout preserved.",
};

const PRODUCTS = [
  {
    title: "Document / PDF",
    desc: "Translate InDesign IDML and PDF files with full layout preservation — fonts, columns, tables and page breaks stay exactly where they were.",
    href: "/platform/documents",
    live: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
        <polyline points="14 2 14 8 20 8" />
        <line x1="16" y1="13" x2="8" y2="13" />
        <line x1="16" y1="17" x2="8" y2="17" />
      </svg>
    ),
  },
  {
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files with timing preserved. Every cue stays synced to its original timecode.",
    href: "/platform/subtitles",
    live: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
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
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
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
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
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
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-7 w-7">
        <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.1c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-1.93 29 29 0 0 0 .46-5.42 29 29 0 0 0-.46-5.33z" />
        <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" />
      </svg>
    ),
  },
];

const CAPABILITIES = [
  "Layout preservation",
  "RTL mirroring",
  "OCR built in",
  "Font substitution",
  "QA scoring",
  "Side-by-side review",
  "Multi-engine translation",
  "40+ languages",
];

export default function PlatformPage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <span className="font-pb-mono mb-6 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Platform
          </span>
          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Five products.
            <br />
            <span className="text-pb-text">One platform.</span>
          </h1>
          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Documents, subtitles, images, websites and YouTube captions — all
            translated with their original layout intact, in 40+ languages.
          </p>
        </div>
      </section>

      {/* Product grid */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
            {PRODUCTS.map((p) => (
              <Link
                key={p.href}
                href={p.href}
                className="pb-card-hover group flex flex-col gap-5 rounded-xl border border-pb-border bg-pb-bg-card p-8"
              >
                <div className="flex items-center justify-between">
                  <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-pb-accent/10 text-pb-accent">
                    {p.icon}
                  </div>
                  {p.live ? (
                    <span className="font-pb-mono rounded-full bg-emerald-900/30 px-3 py-1 text-[9px] font-bold tracking-widest text-emerald-400 uppercase">
                      Live
                    </span>
                  ) : (
                    <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
                      Coming soon
                    </span>
                  )}
                </div>
                <div>
                  <h3 className="text-lg font-bold text-pb-text">{p.title}</h3>
                  <p className="mt-2 text-[14px] leading-relaxed text-pb-text-muted">
                    {p.desc}
                  </p>
                </div>
                <span className="font-pb-mono mt-auto text-[11px] tracking-widest text-pb-accent uppercase opacity-0 transition-opacity group-hover:opacity-100">
                  Learn more →
                </span>
              </Link>
            ))}
          </div>
        </div>
      </section>

      {/* Capabilities strip */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-14 lg:px-10">
          <span className="font-pb-mono mb-6 block text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
            Shared capabilities across every product
          </span>
          <div className="flex flex-wrap gap-3">
            {CAPABILITIES.map((c) => (
              <span
                key={c}
                className="font-pb-mono rounded-full border border-pb-border px-5 py-2 text-[12px] text-pb-text-secondary"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Start translating — no credit card, no catch.
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
