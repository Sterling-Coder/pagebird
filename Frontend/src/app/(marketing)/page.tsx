import Link from "next/link";
import { WatchDemoButton } from "@/components/WatchDemoButton";

const PRODUCTS = [
  {
    n: "01",
    title: "Document / PDF",
    desc: "Translate InDesign IDML and PDF files. Every font, column, table and page break lands exactly where it was.",
    href: "/platform/documents",
    live: true,
    color: "#e08a6f",
    tag: "IDML · PDF",
  },
  {
    n: "02",
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files with every cue staying synced to its original timecode.",
    href: "/platform/subtitles",
    live: false,
    color: "#8b6fbf",
    tag: "SRT · VTT",
  },
  {
    n: "03",
    title: "Image Translator",
    desc: "Detect and translate text embedded in images — signs, labels, infographics — rendered back in place.",
    href: "/platform/images",
    live: false,
    color: "#4a9e8a",
    tag: "AI · PSD · PNG",
  },
  {
    n: "04",
    title: "Website Translator",
    desc: "Point at a live URL and get every page translated — navigation, footers, dynamic content included.",
    href: "/platform/websites",
    live: false,
    color: "#5a9e5a",
    tag: "HTML · CSS",
  },
  {
    n: "05",
    title: "YouTube Subtitles",
    desc: "Paste a YouTube link. We pull the captions, translate them, hand back a ready-to-upload SRT.",
    href: "/platform/youtube",
    live: false,
    color: "#c94040",
    tag: "YouTube · SRT",
  },
];

const FEATURES = [
  { title: "Layout preservation", desc: "Every font, column, table and page break lands exactly where it was." },
  { title: "RTL mirroring", desc: "Arabic and Hebrew mirror the whole page — margins, gutters, bullets." },
  { title: "OCR built in", desc: "Scanned PDFs get OCR, then a translated text layer rebuilt in position." },
  { title: "Font substitution", desc: "No Japanese in your typeface? Metrically compatible, not a generic fallback." },
  { title: "QA scoring", desc: "Every job gets a layout-integrity score. Catch reflow before it ships." },
  { title: "Side-by-side review", desc: "Reviewers edit translations against the source. Edits feed back in." },
  { title: "Multi-engine", desc: "OpenAI and DeepL in consensus. Disagreements flagged for human review." },
  { title: "40+ languages", desc: "From Afrikaans to Vietnamese, including RTL scripts and CJK." },
];

const FORMATS = [".idml", ".pdf", ".ai", ".psd", ".eps", ".srt", ".vtt", ".docx", ".pptx", ".xlsx", ".html"];

export default function Home() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section className="relative min-h-screen overflow-hidden" style={{
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
      }}>
        {/* Thick vertical bands — the giga.ai signature look */}
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(90deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 80px)",
        }} />
        {/* Subtle horizontal scan lines */}
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(180deg, transparent 0px, transparent 2px, rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 3px)",
        }} />

        <div className="relative mx-auto max-w-7xl px-6 pt-36 pb-20 lg:px-10 lg:pt-44 lg:pb-32">
          <div className="pb-enter flex items-center gap-3 mb-8">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              Layout-preserving translation
            </span>
          </div>

          <h1 className="pb-enter pb-enter-delay-1 font-pb-mono max-w-5xl" style={{
            fontSize: "clamp(3.5rem, 9vw, 8rem)",
            lineHeight: 0.92,
            letterSpacing: "-0.02em",
            color: "rgba(240,236,227,0.25)",
          }}>
            Translate the<br />
            <span style={{ color: "#f0ece3" }}>document.</span><br />
            Keep the design.
          </h1>

          <div className="pb-enter pb-enter-delay-2 mt-12 flex max-w-5xl flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <p className="max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Pagebirdy translates InDesign, PDF, subtitles and more into 40+ languages —
              and hands them back with every font, column, table and page break exactly
              where you left it.
            </p>
            <div className="flex shrink-0 items-center gap-5">
              <Link
                href="/login"
                className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
              >
                Translate free
              </Link>
              <WatchDemoButton />
            </div>
          </div>

          {/* Before / After mock */}
          <div className="pb-enter pb-enter-delay-3 mt-20 overflow-hidden border border-white/10" style={{ borderRadius: "2px" }}>
            <div className="grid grid-cols-2">
              {/* Source */}
              <div className="border-r border-white/10 bg-[#0e0d0b] p-8 lg:p-12">
                <div className="flex items-center justify-between mb-8">
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">Source · English</span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted/50">.idml</span>
                </div>
                <div className="space-y-3">
                  <div className="h-[3px] w-[88%] bg-white/10" />
                  <div className="h-[3px] w-[96%] bg-white/10" />
                  <div className="h-[3px] w-[70%] bg-white/10" />
                  <div className="mt-6 h-20 w-full bg-white/5" />
                  <div className="mt-6 h-[3px] w-[92%] bg-white/10" />
                  <div className="h-[3px] w-[64%] bg-white/10" />
                  <div className="h-[3px] w-[80%] bg-white/10" />
                </div>
              </div>
              {/* Output */}
              <div className="bg-[#f5f0e6] p-8 lg:p-12">
                <div className="flex items-center justify-between mb-8">
                  <span className="font-pb-mono text-[11px] tracking-widest text-[#a09a88] uppercase">Translated · Chinese</span>
                  <span className="font-pb-mono text-[10px] text-[#a09a88]/50">.zh.idml</span>
                </div>
                <div className="space-y-3">
                  <div className="h-[3px] w-[76%] bg-[#1a1914]/15" />
                  <div className="h-[3px] w-[88%] bg-[#1a1914]/15" />
                  <div className="h-[3px] w-[58%] bg-[#1a1914]/15" />
                  <div className="mt-6 h-20 w-full bg-[#1a1914]/8" />
                  <div className="mt-6 h-[3px] w-[82%] bg-[#1a1914]/15" />
                  <div className="h-[3px] w-[50%] bg-[#1a1914]/15" />
                  <div className="h-[3px] w-[72%] bg-[#1a1914]/15" />
                </div>
              </div>
            </div>
            <div className="border-t border-white/10 bg-pb-bg px-8 py-3 lg:px-12">
              <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                Identical layout · same page count · same styles
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── PRODUCTS ─── editorial list, no boxes */}
      <section className="bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="border-b border-white/[0.06] py-16 lg:py-20">
            <div className="flex items-center gap-3 mb-6">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
                Products
              </span>
            </div>
            <h2 className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl" style={{ letterSpacing: "-0.02em" }}>
              Five ways to translate.
            </h2>
          </div>

          {/* Full-width rows — no cards, no icons */}
          {PRODUCTS.map((p, i) => (
            <Link
              key={p.href}
              href={p.href}
              className="group flex items-center justify-between border-b border-white/[0.06] py-7 transition-all duration-200 hover:px-4 lg:py-9"
              style={{ "--product-color": p.color } as React.CSSProperties}
            >
              <div className="flex items-center gap-6 lg:gap-10">
                {/* Color bar */}
                <span
                  className="hidden h-12 w-1 shrink-0 transition-all duration-300 group-hover:h-16 lg:block"
                  style={{ background: p.color }}
                />
                <span className="font-pb-mono text-[13px] text-pb-text-muted">{p.n}</span>
                <div>
                  <div className="flex items-center gap-4">
                    <h3 className="text-[20px] font-bold text-pb-text transition-colors group-hover:text-pb-text lg:text-[24px]"
                        style={{ color: `color-mix(in srgb, ${p.color} 0%, #f0ece3 100%)` }}>
                      {p.title}
                    </h3>
                    {p.live ? (
                      <span className="font-pb-mono hidden rounded-full border border-emerald-500/30 bg-emerald-900/20 px-2.5 py-0.5 text-[9px] font-bold tracking-widest text-emerald-400 uppercase sm:inline">
                        Live
                      </span>
                    ) : (
                      <span className="font-pb-mono hidden rounded-full border border-white/10 px-2.5 py-0.5 text-[9px] font-bold tracking-widest text-pb-text-muted uppercase sm:inline">
                        Soon
                      </span>
                    )}
                  </div>
                  <p className="mt-1.5 max-w-xl text-[14px] leading-relaxed text-pb-text-muted">{p.desc}</p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-6">
                <span className="font-pb-mono hidden text-[11px] tracking-widest text-pb-text-muted uppercase lg:block">{p.tag}</span>
                <span className="font-pb-mono text-[13px] text-pb-text-muted transition-colors group-hover:text-pb-text">→</span>
              </div>
            </Link>
          ))}
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── full bleed numbered */}
      <section style={{ background: "#0e0d0b" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              How it works
            </span>
          </div>
          <h2 className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl lg:text-6xl" style={{ letterSpacing: "-0.02em" }}>
            Three steps.<br />Zero cleanup.
          </h2>

          <div className="mt-20 grid grid-cols-1 gap-0 md:grid-cols-3">
            {[
              { n: "01", title: "Upload", desc: "Drop an IDML, PDF, or subtitle file. We read the layout tree — not a flattened text dump." },
              { n: "02", title: "Pick a language", desc: "Choose from 40+ targets. Attach a glossary to lock terms that must never be translated." },
              { n: "03", title: "Download", desc: "Same extension, same styles, same page count. Open it and keep editing as if nothing happened." },
            ].map((s, i) => (
              <div key={s.n} className={`border-white/[0.06] py-10 ${i < 2 ? "md:border-r md:pr-10" : ""} ${i > 0 ? "md:pl-10" : ""} ${i < 2 ? "border-b md:border-b-0" : ""}`}>
                <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>
                  {s.n}
                </span>
                <h3 className="mt-4 text-[22px] font-bold text-pb-text">{s.title}</h3>
                <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CAPABILITIES ─── dark grid, no cards */}
      <section className="bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex flex-col justify-between gap-4 border-b border-white/[0.06] pb-12 md:flex-row md:items-end">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2 bg-pb-accent" />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
                  Capabilities
                </span>
              </div>
              <h2 className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl" style={{ letterSpacing: "-0.02em" }}>
                Everything the file<br />carried, carried across.
              </h2>
            </div>
            <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
              08 features
            </span>
          </div>

          <div className="mt-0 grid grid-cols-1 divide-y divide-white/[0.04] md:grid-cols-2 md:divide-y-0">
            {FEATURES.map((f, i) => (
              <div
                key={f.title}
                className={`flex gap-6 py-8 ${i % 2 === 0 ? "md:border-r md:border-white/[0.04] md:pr-12" : "md:pl-12"}`}
              >
                <span className="font-pb-mono mt-0.5 shrink-0 text-[11px] text-pb-accent/50">
                  {String(i + 1).padStart(2, "0")}
                </span>
                <div>
                  <h3 className="text-[15px] font-bold text-pb-text">{f.title}</h3>
                  <p className="mt-1 text-[13px] leading-relaxed text-pb-text-muted">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FORMATS ─── tight strip */}
      <section style={{ background: "#0e0d0b", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-pb-mono mr-6 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Formats
            </span>
            {FORMATS.map((f) => (
              <span key={f} className="font-pb-mono border border-white/[0.06] px-4 py-1.5 text-[12px] text-pb-text-muted">
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── PRICING ─── */}
      <section id="pricing" className="bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              Pricing
            </span>
          </div>
          <div className="flex flex-col justify-between gap-8 border-b border-white/[0.06] pb-16 md:flex-row md:items-end">
            <h2 className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl" style={{ letterSpacing: "-0.02em" }}>
              Start free.<br />Scale when ready.
            </h2>
            <Link
              href="/contact"
              className="font-pb-mono inline-flex shrink-0 items-center rounded-full bg-pb-accent px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Book a call
            </Link>
          </div>

          <div className="mt-0 grid grid-cols-1 divide-y divide-white/[0.06] md:grid-cols-3 md:divide-x md:divide-y-0">
            {[
              {
                tier: "FREE",
                price: "$0",
                tagline: "Try it out.",
                features: ["5 pages free", "PDF + IDML", "All 40+ languages"],
                cta: "Get started",
                href: "/login",
                accent: false,
              },
              {
                tier: "TEAM",
                price: "Coming soon",
                tagline: "For teams shipping in several languages.",
                features: ["Volume page packs", "All formats + subtitles", "Shared glossary", "Side-by-side review"],
                cta: "Coming soon",
                href: null,
                accent: true,
              },
              {
                tier: "ENTERPRISE",
                price: "Custom",
                tagline: "Volume, audit, and residency.",
                features: ["Unlimited pages", "SSO + audit log", "Data residency"],
                cta: "Book a call",
                href: "/contact",
                accent: false,
              },
            ].map((plan, i) => (
              <div key={plan.tier} className={`py-12 ${i > 0 ? "md:pl-12" : ""} ${i < 2 ? "md:pr-12" : ""}`}>
                <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">{plan.tier}</span>
                <p className="mt-4 text-[32px] font-bold text-pb-text">{plan.price}</p>
                <p className="mt-2 text-[13px] text-pb-text-muted">{plan.tagline}</p>
                <div className="mt-8 space-y-2.5">
                  {plan.features.map((f) => (
                    <span key={f} className="block text-[13px] text-pb-text-secondary">— {f}</span>
                  ))}
                </div>
                {plan.href ? (
                  <Link
                    href={plan.href}
                    className={`font-pb-mono mt-10 block border py-3 text-center text-[11px] font-bold tracking-widest uppercase transition-all ${
                      plan.accent
                        ? "border-pb-accent/40 text-pb-accent hover:bg-pb-accent hover:text-pb-bg"
                        : "border-white/[0.08] text-pb-text hover:border-pb-text"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                ) : (
                  <span className="font-pb-mono mt-10 block cursor-not-allowed border border-white/[0.04] py-3 text-center text-[11px] font-bold tracking-widest text-pb-text-muted uppercase opacity-50">
                    {plan.cta}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── full bleed accent */}
      <section style={{ background: "#e08a6f" }}>
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-10 lg:py-24">
          <h2 className="font-pb-mono max-w-2xl text-3xl font-bold text-pb-bg md:text-5xl" style={{ letterSpacing: "-0.02em" }}>
            Send us the document<br />you dread translating.
          </h2>
          <Link
            href="/login"
            className="font-pb-mono shrink-0 border-2 border-pb-bg bg-pb-bg px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-accent uppercase transition-all hover:bg-transparent hover:text-pb-bg"
          >
            Translate free →
          </Link>
        </div>
      </section>
    </>
  );
}
