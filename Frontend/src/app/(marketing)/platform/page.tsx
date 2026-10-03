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

      {/* Bento grid — same pattern as landing page */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="mb-12">
            <div className="flex items-center gap-3 mb-4">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">All products</span>
            </div>
            <h2 className="font-pb-mono text-4xl font-bold text-pb-text" style={{ letterSpacing: "-0.02em" }}>
              Five ways to translate.
            </h2>
          </div>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">

            {/* 01 Documents / PDF — large, spans 2 cols */}
            <Link href="/platform/documents" className="group relative col-span-1 overflow-hidden md:col-span-2" style={{
              background: "linear-gradient(135deg, #2a1408 0%, #1a0c06 100%)",
              border: "1px solid rgba(224,138,111,0.15)",
              borderRadius: "12px",
              minHeight: "280px",
            }}>
              <div className="pointer-events-none absolute inset-0 opacity-20 transition-opacity group-hover:opacity-30" style={{
                background: "radial-gradient(ellipse 60% 80% at 80% 50%, #e08a6f, transparent)",
              }} />
              <div className="relative flex h-full flex-col justify-between p-8">
                <div className="flex items-start justify-between">
                  <div>
                    <span className="font-pb-mono text-[10px] text-pb-text-muted">01</span>
                    <h3 className="mt-1 text-[22px] font-bold text-white">Document / PDF</h3>
                    <p className="mt-2 max-w-xs text-[13px] leading-relaxed text-white/50">
                      Translate InDesign IDML and PDF files. Every font, column and page break stays exactly where it was.
                    </p>
                  </div>
                  <span className="font-pb-mono rounded-full border border-emerald-500/40 bg-emerald-900/30 px-3 py-1 text-[9px] font-bold tracking-widest text-emerald-400 uppercase">Live</span>
                </div>
                <div className="mt-6 grid grid-cols-2 gap-2 opacity-60 transition-opacity group-hover:opacity-90">
                  <div className="rounded-md bg-black/40 p-4">
                    <div className="font-pb-mono mb-2 text-[8px] text-white/30 uppercase">English</div>
                    <div className="space-y-1.5">
                      <div className="h-1.5 w-[80%] rounded bg-white/20" />
                      <div className="h-1.5 w-[95%] rounded bg-white/20" />
                      <div className="h-1.5 w-[60%] rounded bg-white/20" />
                      <div className="mt-2 h-8 w-full rounded bg-white/10" />
                    </div>
                  </div>
                  <div className="rounded-md p-4" style={{ background: "rgba(245,240,230,0.08)" }}>
                    <div className="font-pb-mono mb-2 text-[8px] text-white/30 uppercase">中文</div>
                    <div className="space-y-1.5">
                      <div className="h-1.5 w-[70%] rounded bg-pb-accent/30" />
                      <div className="h-1.5 w-[88%] rounded bg-pb-accent/30" />
                      <div className="h-1.5 w-[55%] rounded bg-pb-accent/30" />
                      <div className="mt-2 h-8 w-full rounded bg-pb-accent/15" />
                    </div>
                  </div>
                </div>
              </div>
              <span className="absolute bottom-6 right-6 font-pb-mono text-[11px] text-white/20 transition-colors group-hover:text-pb-accent">→</span>
            </Link>

            {/* 02 SRT / VTT */}
            <Link href="/platform/subtitles" className="group relative overflow-hidden" style={{
              background: "linear-gradient(135deg, #120a28 0%, #0a0818 100%)",
              border: "1px solid rgba(139,111,191,0.15)",
              borderRadius: "12px",
              minHeight: "280px",
            }}>
              <div className="pointer-events-none absolute inset-0 opacity-20 transition-opacity group-hover:opacity-35" style={{
                background: "radial-gradient(ellipse 80% 80% at 50% 0%, #8b6fbf, transparent)",
              }} />
              <div className="relative flex h-full flex-col justify-between p-7">
                <div>
                  <div className="flex items-start justify-between">
                    <span className="font-pb-mono text-[10px] text-pb-text-muted">02</span>
                    <span className="font-pb-mono rounded-full border border-white/10 px-2.5 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">Soon</span>
                  </div>
                  <h3 className="mt-2 text-[19px] font-bold text-white">SRT / VTT Subtitles</h3>
                  <p className="mt-2 text-[12px] leading-relaxed text-white/50">Every cue stays synced to its original timecode.</p>
                </div>
                <div className="mt-4 rounded-lg bg-black/40 p-4 opacity-60 transition-opacity group-hover:opacity-90" style={{ fontFamily: "monospace" }}>
                  <div className="text-[10px] text-purple-400/70">00:00:01,000 → 00:00:04,000</div>
                  <div className="mt-1 text-[11px] text-white/60">The document stays</div>
                  <div className="mt-2 text-[10px] text-purple-400/70">00:00:04,500 → 00:00:07,000</div>
                  <div className="mt-1 text-[11px] text-white/40">Le document reste...</div>
                </div>
              </div>
              <span className="absolute bottom-5 right-5 font-pb-mono text-[11px] text-white/20 transition-colors group-hover:text-[#8b6fbf]">→</span>
            </Link>

            {/* 03 Image Translator */}
            <Link href="/platform/images" className="group relative overflow-hidden" style={{
              background: "linear-gradient(135deg, #081814 0%, #050e0c 100%)",
              border: "1px solid rgba(74,158,138,0.15)",
              borderRadius: "12px",
              minHeight: "220px",
            }}>
              <div className="pointer-events-none absolute inset-0 opacity-20 transition-opacity group-hover:opacity-35" style={{
                background: "radial-gradient(ellipse 80% 80% at 50% 100%, #4a9e8a, transparent)",
              }} />
              <div className="relative flex h-full flex-col justify-between p-7">
                <div>
                  <div className="flex items-start justify-between">
                    <span className="font-pb-mono text-[10px] text-pb-text-muted">03</span>
                    <span className="font-pb-mono rounded-full border border-white/10 px-2.5 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">Soon</span>
                  </div>
                  <h3 className="mt-2 text-[19px] font-bold text-white">Image Translator</h3>
                  <p className="mt-2 text-[12px] leading-relaxed text-white/50">Text in images, translated in place.</p>
                </div>
                <div className="mt-4 flex gap-2 opacity-60 transition-opacity group-hover:opacity-90">
                  <div className="flex-1 rounded border border-red-500/30 bg-black/40 p-3 text-center">
                    <div className="text-[10px] font-bold text-white/70">OPEN DAILY</div>
                    <div className="text-[9px] text-white/40">9AM – 5PM</div>
                  </div>
                  <span className="self-center text-[#4a9e8a] text-sm">→</span>
                  <div className="flex-1 rounded border border-teal-500/30 bg-black/40 p-3 text-center">
                    <div className="text-[10px] font-bold text-teal-300/70">مفتوح يومياً</div>
                    <div className="text-[9px] text-white/40">٩ص – ٥م</div>
                  </div>
                </div>
              </div>
              <span className="absolute bottom-5 right-5 font-pb-mono text-[11px] text-white/20 transition-colors group-hover:text-[#4a9e8a]">→</span>
            </Link>

            {/* 04 Website Translator */}
            <Link href="/platform/websites" className="group relative overflow-hidden" style={{
              background: "linear-gradient(135deg, #081408 0%, #050c05 100%)",
              border: "1px solid rgba(90,158,90,0.15)",
              borderRadius: "12px",
              minHeight: "220px",
            }}>
              <div className="pointer-events-none absolute inset-0 opacity-20 transition-opacity group-hover:opacity-35" style={{
                background: "radial-gradient(ellipse 80% 80% at 0% 50%, #5a9e5a, transparent)",
              }} />
              <div className="relative flex h-full flex-col justify-between p-7">
                <div>
                  <div className="flex items-start justify-between">
                    <span className="font-pb-mono text-[10px] text-pb-text-muted">04</span>
                    <span className="font-pb-mono rounded-full border border-white/10 px-2.5 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">Soon</span>
                  </div>
                  <h3 className="mt-2 text-[19px] font-bold text-white">Website Translator</h3>
                  <p className="mt-2 text-[12px] leading-relaxed text-white/50">Entire site, every page, automatically.</p>
                </div>
                <div className="mt-4 space-y-1.5 opacity-60 transition-opacity group-hover:opacity-90">
                  {[["yoursite.com/about", "yoursite.com/fr/about"], ["yoursite.com/pricing", "yoursite.com/de/pricing"]].map(([src, dst]) => (
                    <div key={src} className="flex items-center gap-2 font-pb-mono text-[10px]">
                      <span className="text-white/30">{src}</span>
                      <span className="text-[#5a9e5a]">→</span>
                      <span className="text-[#5a9e5a]/70">{dst}</span>
                    </div>
                  ))}
                </div>
              </div>
              <span className="absolute bottom-5 right-5 font-pb-mono text-[11px] text-white/20 transition-colors group-hover:text-[#5a9e5a]">→</span>
            </Link>

            {/* 05 YouTube Subtitles */}
            <Link href="/platform/youtube" className="group relative overflow-hidden" style={{
              background: "linear-gradient(135deg, #180808 0%, #0e0606 100%)",
              border: "1px solid rgba(201,64,64,0.15)",
              borderRadius: "12px",
              minHeight: "220px",
            }}>
              <div className="pointer-events-none absolute inset-0 opacity-20 transition-opacity group-hover:opacity-35" style={{
                background: "radial-gradient(ellipse 80% 80% at 100% 50%, #c94040, transparent)",
              }} />
              <div className="relative flex h-full flex-col justify-between p-7">
                <div>
                  <div className="flex items-start justify-between">
                    <span className="font-pb-mono text-[10px] text-pb-text-muted">05</span>
                    <span className="font-pb-mono rounded-full border border-white/10 px-2.5 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">Soon</span>
                  </div>
                  <h3 className="mt-2 text-[19px] font-bold text-white">YouTube Subtitles</h3>
                  <p className="mt-2 text-[12px] leading-relaxed text-white/50">Paste a URL. Get translated SRT back.</p>
                </div>
                <div className="mt-4 rounded-lg bg-black/50 px-3 py-2 opacity-60 transition-opacity group-hover:opacity-90">
                  <div className="font-pb-mono text-[9px] text-white/30 truncate">youtube.com/watch?v=dQw4w9WgXcQ</div>
                  <div className="mt-2 flex gap-2">
                    {["ZH", "FR", "DE", "ES", "JA"].map((l) => (
                      <span key={l} className="font-pb-mono rounded bg-red-900/40 px-1.5 py-0.5 text-[8px] text-red-400/70">{l}</span>
                    ))}
                  </div>
                </div>
              </div>
              <span className="absolute bottom-5 right-5 font-pb-mono text-[11px] text-white/20 transition-colors group-hover:text-[#c94040]">→</span>
            </Link>

          </div>
        </div>
      </section>

      {/* AI Engine section */}
      <section className="pb-glass-section" style={{ background: "#0a0908" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">The Engine</span>
          </div>
          <h2 className="pb-stencil mb-4" style={{ fontSize: "clamp(2rem, 3.5vw, 3rem)" }}>Two engines. One consensus.</h2>
          <p className="mb-16 max-w-xl text-[15px] leading-relaxed text-pb-text-secondary">
            OpenAI and DeepL translate every segment independently. When they agree, the output ships. When they disagree, the segment is flagged for human review.
          </p>

          {/* Pipeline visual */}
          <div className="flex items-center justify-center gap-0 overflow-x-auto">
            {/* Input */}
            <div className="flex flex-col items-center gap-2 shrink-0">
              <div style={{ background: "rgba(255,255,255,0.06)", border: "1px solid rgba(255,255,255,0.1)", borderRadius: "8px", padding: "12px 20px", fontSize: "13px", color: "rgba(240,236,227,0.7)", fontFamily: "monospace" }}>
                Your segment
              </div>
            </div>

            <div style={{ width: "40px", height: "1px", background: "rgba(255,255,255,0.15)" }} />

            {/* Split */}
            <div className="flex flex-col items-center gap-3 shrink-0">
              <div style={{ background: "rgba(224,138,111,0.15)", border: "1px solid rgba(224,138,111,0.3)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", fontWeight: 700, color: "#e08a6f", fontFamily: "monospace" }}>
                OpenAI GPT
              </div>
              <div style={{ background: "rgba(74,112,224,0.15)", border: "1px solid rgba(74,112,224,0.3)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", fontWeight: 700, color: "#4a70e0", fontFamily: "monospace" }}>
                DeepL Neural
              </div>
            </div>

            <div className="flex flex-col gap-3 shrink-0" style={{ width: "40px" }}>
              <div style={{ height: "1px", background: "rgba(224,138,111,0.4)" }} />
              <div style={{ height: "1px", background: "rgba(74,112,224,0.4)" }} />
            </div>

            {/* Consensus */}
            <div className="flex flex-col items-center gap-3 shrink-0">
              <div style={{ background: "rgba(74,158,90,0.15)", border: "1px solid rgba(74,158,90,0.3)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", fontWeight: 700, color: "#4a9e5a", fontFamily: "monospace" }}>
                ✓ Agreement
              </div>
              <div style={{ background: "rgba(224,138,111,0.1)", border: "1px solid rgba(224,138,111,0.25)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", fontWeight: 700, color: "#e08a6f", fontFamily: "monospace" }}>
                ⚠ Flagged
              </div>
            </div>

            <div className="flex flex-col gap-3 shrink-0" style={{ width: "40px" }}>
              <div style={{ height: "1px", background: "rgba(74,158,90,0.4)" }} />
              <div style={{ height: "1px", background: "rgba(201,64,64,0.4)" }} />
            </div>

            {/* Output */}
            <div className="flex flex-col items-center gap-3 shrink-0">
              <div style={{ background: "rgba(74,158,90,0.12)", border: "1px solid rgba(74,158,90,0.2)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", color: "#4a9e5a", fontFamily: "monospace" }}>
                Ships to output
              </div>
              <div style={{ background: "rgba(201,64,64,0.12)", border: "1px solid rgba(201,64,64,0.2)", borderRadius: "8px", padding: "10px 16px", fontSize: "12px", color: "#c94040", fontFamily: "monospace" }}>
                Review queue
              </div>
            </div>
          </div>

          {/* Stats */}
          <div className="mt-16 grid grid-cols-3 gap-0" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            {[
              { n: "40+", label: "Languages" },
              { n: "2", label: "AI engines in consensus" },
              { n: "100%", label: "Segment-level accuracy check" },
            ].map((s, i) => (
              <div key={s.label} className="py-8" style={{ borderRight: i < 2 ? "1px solid rgba(255,255,255,0.06)" : "none", paddingLeft: i > 0 ? "32px" : "0", paddingRight: i < 2 ? "32px" : "0" }}>
                <div className="pb-stencil" style={{ fontSize: "2.5rem" }}>{s.n}</div>
                <div style={{ fontSize: "13px", color: "rgba(240,236,227,0.45)", marginTop: "6px" }}>{s.label}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Integrations */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Integrations</span>
          </div>
          <h2 className="pb-stencil mb-4" style={{ fontSize: "clamp(2rem, 3.5vw, 3rem)" }}>Works everywhere<br />you work.</h2>
          <p className="mb-14 max-w-xl text-[15px] leading-relaxed text-pb-text-secondary">
            Pagebirdy reads and writes the same formats your tools already use. No export step, no conversion, no new workflow to learn.
          </p>

          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">
            {[
              { name: "Adobe InDesign", desc: "Open translated IDML directly. No re-linking.", soon: false, color: "#e08a6f" },
              { name: "Adobe Illustrator", desc: "Translated .ai files ready to edit.", soon: false, color: "#e08a6f" },
              { name: "Adobe Photoshop", desc: "Text layers translated in place.", soon: false, color: "#e08a6f" },
              { name: "YouTube Studio", desc: "Upload translated SRT directly to your video.", soon: false, color: "#c94040" },
              { name: "Premiere Pro", desc: "Import .srt caption tracks into your timeline.", soon: false, color: "#4a70e0" },
              { name: "WordPress", desc: "Paste translated HTML into any page builder.", soon: false, color: "#5a9e5a" },
              { name: "Figma", desc: "Export frames, translate, re-import.", soon: true, color: "#8b6fbf" },
              { name: "Notion", desc: "Translate docs and pages.", soon: true, color: "#4a9e8a" },
              { name: "Slack", desc: "Trigger translations from your workspace.", soon: true, color: "#4a70e0" },
            ].map((item) => (
              <div key={item.name} className="flex flex-col gap-2 p-5" style={{
                background: "rgba(255,255,255,0.03)",
                border: "1px solid rgba(255,255,255,0.07)",
                borderLeft: `3px solid ${item.soon ? "rgba(255,255,255,0.1)" : item.color + "60"}`,
                borderRadius: "8px",
                opacity: item.soon ? 0.55 : 1,
              }}>
                <div className="flex items-center justify-between">
                  <span style={{ fontSize: "14px", fontWeight: 700, color: item.soon ? "rgba(240,236,227,0.5)" : "#f0ece3" }}>{item.name}</span>
                  {item.soon && <span className="font-pb-mono text-[8px] tracking-widest text-pb-text-muted uppercase" style={{ border: "1px solid rgba(255,255,255,0.1)", padding: "2px 6px", borderRadius: "4px" }}>Soon</span>}
                </div>
                <p style={{ fontSize: "12px", color: "rgba(240,236,227,0.38)", lineHeight: 1.5 }}>{item.desc}</p>
              </div>
            ))}
          </div>
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
