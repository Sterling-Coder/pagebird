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
  },
  {
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files with timing preserved. Every cue stays synced to its original timecode.",
    href: "/platform/subtitles",
    live: false,
  },
  {
    title: "Image Translator",
    desc: "Detect and translate text embedded in images — signs, labels, infographics — and render it back in place.",
    href: "/platform/images",
    live: false,
  },
  {
    title: "Website Translator",
    desc: "Point at a live URL and get every page translated — navigation, footers, dynamic content included.",
    href: "/platform/websites",
    live: false,
  },
  {
    title: "YouTube Subtitles",
    desc: "Paste a YouTube link. We pull the captions, translate them, and hand back a ready-to-upload SRT.",
    href: "/platform/youtube",
    live: false,
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
      <section className="relative overflow-hidden" style={{
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
        minHeight: "50vh",
      }}>
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(90deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 80px)",
        }} />
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(180deg, transparent 0px, transparent 2px, rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 3px)",
        }} />
        <div className="relative mx-auto max-w-[1100px] px-8 pt-28 pb-16 lg:px-14 lg:pt-36 lg:pb-24">
          <div className="pb-enter-label flex items-center gap-3 mb-8">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              Platform
            </span>
          </div>
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-end">
            <h1 className="pb-enter pb-stencil" style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}>
              Five products.<br />One platform.
            </h1>
            <p className="pb-enter pb-enter-delay-1 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Documents, subtitles, images, websites and YouTube captions — all
              translated with their original layout intact, in 40+ languages.
            </p>
          </div>
        </div>
      </section>

      {/* Product list — editorial rows */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-24">
          {PRODUCTS.map((p, i) => (
            <Link
              key={p.href}
              href={p.href}
              className="group flex items-center justify-between py-7 transition-all hover:px-4"
              style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <div className="flex items-center gap-6 lg:gap-10">
                <span className="font-pb-mono text-[13px]" style={{ color: "rgba(240,236,227,0.3)" }}>
                  0{i + 1}
                </span>
                <div>
                  <div className="flex items-center gap-4">
                    <h3 className="text-[20px] font-bold text-pb-text lg:text-[24px]">{p.title}</h3>
                    {p.live ? (
                      <span className="font-pb-mono hidden rounded-full border border-emerald-500/30 bg-emerald-900/20 px-2.5 py-0.5 text-[9px] font-bold tracking-widest text-emerald-400 uppercase sm:inline">Live</span>
                    ) : (
                      <span className="font-pb-mono hidden rounded-full border border-white/10 px-2.5 py-0.5 text-[9px] font-bold tracking-widest text-pb-text-muted uppercase sm:inline">Soon</span>
                    )}
                  </div>
                  <p className="mt-1 max-w-xl text-[14px] leading-relaxed text-pb-text-muted">{p.desc}</p>
                </div>
              </div>
              <span className="font-pb-mono shrink-0 text-[13px] text-pb-text-muted transition-colors group-hover:text-pb-text">→</span>
            </Link>
          ))}
        </div>
      </section>

      {/* Capabilities strip */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-12 lg:px-14">
          <span className="font-pb-mono mb-6 block text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
            Shared capabilities across every product
          </span>
          <div className="flex flex-wrap gap-2">
            {CAPABILITIES.map((c) => (
              <span
                key={c}
                className="font-pb-mono border border-white/[0.07] px-4 py-1.5 text-[12px] text-pb-text-secondary"
              >
                {c}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: "#e08a6f" }}>
        <div className="mx-auto flex max-w-[1100px] flex-col items-start justify-between gap-8 px-8 py-16 md:flex-row md:items-center lg:px-14 lg:py-20">
          <h2 className="font-pb-mono text-3xl font-bold text-pb-bg md:text-4xl" style={{ letterSpacing: "-0.02em" }}>
            Start translating — no credit card, no catch.
          </h2>
          <Link
            href="/login"
            className="font-pb-mono shrink-0 border-2 border-pb-bg bg-pb-bg px-8 py-3 text-[12px] font-bold tracking-widest text-pb-accent uppercase transition-all hover:bg-transparent hover:text-pb-bg"
          >
            Translate free →
          </Link>
        </div>
      </section>
    </>
  );
}
