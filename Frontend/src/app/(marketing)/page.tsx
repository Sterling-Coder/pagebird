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
      <section className="relative overflow-hidden" style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
      }}>
        {/* Thick vertical bands */}
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(90deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 80px)",
        }} />
        {/* Horizontal scan lines */}
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(180deg, transparent 0px, transparent 2px, rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 3px)",
        }} />

        <div className="relative mx-auto max-w-[1100px] px-8 pt-28 pb-16 lg:px-14 lg:pt-32 lg:pb-24">

          {/* ── Two-column top: label+headline LEFT, description+CTA RIGHT ── */}
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-[55%_45%] lg:gap-0">
            {/* LEFT */}
            <div className="flex flex-col justify-end lg:pr-12">
              <div className="pb-enter-label mb-6 flex items-center gap-3">
                <span className="inline-block h-2 w-2 bg-pb-accent" />
                <span className="font-pb-mono text-[11px] font-bold tracking-[0.15em] text-pb-accent uppercase">
                  Layout-preserving translation
                </span>
              </div>

              <h1
                className="pb-enter pb-enter-delay-1 pb-stencil"
                style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)", lineHeight: 1.05 }}
              >
                Translate the<br />
                document.<br />
                Keep the design.
              </h1>
            </div>

            {/* RIGHT */}
            <div className="flex flex-col justify-end lg:pt-16">
              <p className="pb-enter pb-enter-delay-2 max-w-md text-[16px] leading-relaxed text-white/70 lg:text-[17px]">
                Pagebirdy translates InDesign, PDF, subtitles and more into
                40+ languages — and hands them back with every font, column,
                table and page break exactly where you left it.
              </p>
              <div className="pb-enter pb-enter-delay-3 mt-8 flex items-center gap-5">
                <Link
                  href="/login"
                  className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
                >
                  Translate free
                </Link>
                <WatchDemoButton />
              </div>
            </div>
          </div>

          {/* ── macOS-style app window mock ── */}
          <div className="pb-enter pb-enter-delay-4 relative mt-16 lg:-mx-20 xl:-mx-32" style={{
            borderRadius: "12px",
            overflow: "hidden",
            boxShadow: "0 48px 140px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08)",
          }}>
            {/* macOS title bar */}
            <div className="flex items-center gap-2 px-4 py-3" style={{ background: "#f0ece3", borderBottom: "1px solid #dad4c7" }}>
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
              <span style={{ marginLeft: "8px", fontSize: "12px", color: "#6e6a61", fontWeight: 500 }}>Pagebirdy — Jobs</span>
            </div>

            <div className="flex" style={{ minHeight: "520px" }}>
              {/* Left sidebar — clean white like Image #35 */}
              <div className="flex shrink-0 flex-col" style={{
                width: "190px",
                background: "#f8f5ee",
                borderRight: "1px solid #e8e2d8",
              }}>
                {/* Logo in sidebar */}
                <div className="px-5 py-4">
                  <span style={{
                    fontFamily: "var(--font-fraunces), Georgia, serif",
                    fontStyle: "italic",
                    fontSize: "18px",
                    fontWeight: 600,
                    color: "#15130f",
                  }}>
                    page<span style={{ color: "#e08a6f" }}>birdy</span>
                  </span>
                </div>

                {/* Nav section */}
                <div className="px-3 pb-2">
                  <div className="mb-1 px-2 pb-1 pt-3" style={{ fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em", color: "#a09a8e" }}>MAIN</div>
                  {[
                    { label: "Jobs", active: true },
                    { label: "Team", active: false },
                    { label: "Settings", active: false },
                  ].map((item) => (
                    <div key={item.label} className="flex items-center gap-2.5 rounded-md px-2 py-1.5 mb-0.5" style={{
                      background: item.active ? "#e08a6f" : "transparent",
                    }}>
                      <span style={{
                        display: "inline-block", width: "6px", height: "6px", borderRadius: "2px",
                        background: item.active ? "rgba(255,255,255,0.8)" : "#b0a898",
                      }} />
                      <span style={{
                        fontSize: "13px",
                        color: item.active ? "#fff" : "#4a463d",
                        fontWeight: item.active ? 600 : 400,
                      }}>{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Right main content */}
              <div className="flex flex-1 flex-col" style={{ background: "#fdfcf7" }}>
                {/* Header row */}
                <div className="flex items-center justify-between border-b px-6 py-4" style={{ borderColor: "#e8e2d8" }}>
                  <div>
                    <div style={{ fontSize: "18px", fontWeight: 700, color: "#15130f" }}>Jobs</div>
                    <div style={{ fontSize: "12px", color: "#9a9488", marginTop: "1px" }}>4 projects</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <div style={{
                      background: "#e08a6f", color: "#fff", fontSize: "11px",
                      fontWeight: 700, padding: "6px 14px", borderRadius: "6px",
                      letterSpacing: "0.05em",
                    }}>NEW JOB</div>
                  </div>
                </div>

                {/* Filter pills */}
                <div className="flex items-center gap-2 border-b px-6 py-2.5" style={{ borderColor: "#e8e2d8" }}>
                  {[{ l: "Today", a: false }, { l: "7 days", a: false }, { l: "30 days", a: false }, { l: "All", a: true }].map(p => (
                    <div key={p.l} style={{
                      fontSize: "12px", fontWeight: p.a ? 600 : 400, padding: "3px 12px",
                      borderRadius: "20px", border: "1px solid",
                      borderColor: p.a ? "#e08a6f" : "#dad4c7",
                      background: p.a ? "#e08a6f" : "transparent",
                      color: p.a ? "#fff" : "#6e6a61",
                    }}>{p.l}</div>
                  ))}
                </div>

                {/* Table */}
                <div className="flex-1 px-6 pt-3">
                  {/* Date group */}
                  <div className="flex items-center gap-3 py-2">
                    <span style={{ fontSize: "13px", fontWeight: 700, color: "#15130f" }}>Today</span>
                    <span style={{ fontSize: "11px", color: "#9a9488" }}>2 projects · 48 pages</span>
                  </div>
                  {/* Column headers */}
                  <div className="grid border-b pb-1.5" style={{ gridTemplateColumns: "2.5fr 0.8fr 1fr 1fr 120px", borderColor: "#e8e2d8" }}>
                    {["NAME", "TYPE", "TARGET", "CREATED", "PROGRESS"].map(h => (
                      <span key={h} style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.1em", color: "#9a9488" }}>{h}</span>
                    ))}
                  </div>
                  {/* Rows */}
                  {[
                    { name: "annual_report_2026.idml", type: "IDML", target: "Chinese", created: "Today", progress: 100, done: true },
                    { name: "product_brochure.pdf", type: "PDF", target: "Arabic", created: "Today", progress: 68, done: false },
                    { name: "marketing_deck.idml", type: "IDML", target: "French", created: "Dec 12", progress: 35, done: false },
                    { name: "newsletter_q4.idml", type: "IDML", target: "German", created: "Dec 10", progress: 100, done: true },
                    { name: "company_handbook.pdf", type: "PDF", target: "Spanish", created: "Dec 8", progress: 100, done: true },
                    { name: "press_release_q4.idml", type: "IDML", target: "Japanese", created: "Dec 7", progress: 22, done: false },
                  ].map((row, i) => (
                    <div key={row.name} className="grid items-center py-3.5" style={{
                      gridTemplateColumns: "2.5fr 0.8fr 1fr 1fr 120px",
                      borderBottom: i < 5 ? "1px solid #f0ece3" : "none",
                    }}>
                      <span style={{ fontSize: "13px", color: "#15130f", fontWeight: 500, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{row.name}</span>
                      <span style={{ fontSize: "11px", color: "#6e6a61" }}>{row.type}</span>
                      <span style={{ fontSize: "11px", color: "#6e6a61" }}>{row.target}</span>
                      <span style={{ fontSize: "11px", color: "#9a9488" }}>{row.created}</span>
                      <div className="flex items-center gap-2">
                        <div style={{ flex: 1, height: "4px", background: "#e8e2d8", borderRadius: "4px", overflow: "hidden" }}>
                          <div style={{
                            height: "100%", borderRadius: "4px",
                            width: `${row.progress}%`,
                            background: row.done ? "#4a9e5a" : "#e08a6f",
                          }} />
                        </div>
                        <span style={{ fontSize: "10px", color: "#9a9488", minWidth: "26px" }}>{row.progress}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom fade */}
            <div className="pointer-events-none absolute bottom-0 left-0 right-0" style={{
              height: "40%",
              background: "linear-gradient(to top, #0c0810 0%, #0c0810 8%, rgba(12,8,16,0.9) 40%, transparent 100%)",
            }} />
          </div>
        </div>
      </section>

      {/* ─── PRODUCTS — bento grid with visual mocks ─── */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="mb-12 flex items-center justify-between">
            <div>
              <div className="flex items-center gap-3 mb-4">
                <span className="inline-block h-2 w-2 bg-pb-accent" />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Products</span>
              </div>
              <h2 className="font-pb-mono text-4xl font-bold text-pb-text" style={{ letterSpacing: "-0.02em" }}>
                Five ways to translate.
              </h2>
            </div>
          </div>

          {/* Bento grid */}
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2 lg:grid-cols-3">

            {/* 01 Documents / PDF — large, spans 2 cols */}
            <Link href="/platform/documents" className="group relative col-span-1 overflow-hidden md:col-span-2" style={{
              background: "linear-gradient(135deg, #2a1408 0%, #1a0c06 100%)",
              border: "1px solid rgba(224,138,111,0.15)",
              borderRadius: "12px",
              minHeight: "280px",
            }}>
              {/* Color glow */}
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
                {/* Mini before/after mock */}
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
                {/* Timecode mock */}
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
                {/* Sign mock */}
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
                {/* URL mock */}
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
                {/* YT URL mock */}
                <div className="mt-4 rounded-lg bg-black/50 px-3 py-2 opacity-60 transition-opacity group-hover:opacity-90">
                  <div className="font-pb-mono text-[9px] text-white/30 truncate">youtube.com/watch?v=dQw4w9WgXcQ</div>
                  <div className="mt-2 flex gap-2">
                    {["ZH", "FR", "DE", "ES", "JA"].map(l => (
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

      {/* ─── HOW IT WORKS ─── */}
      <section className="pb-glass-section" style={{ background: "#0e0d0b" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
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
            {/* Step 01 — Upload */}
            <div className="border-white/[0.06] py-10 border-b md:border-b-0 md:border-r md:pr-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>01</span>
              {/* Upload zone visual */}
              <div className="mt-3 mb-4 opacity-60" style={{ border: "1px dashed rgba(224,138,111,0.35)", borderRadius: "6px", padding: "10px 14px" }}>
                <span className="font-pb-mono text-[11px] text-pb-accent/70">product_magazine.idml</span>
                <div className="mt-1 font-pb-mono text-[9px] text-pb-text-muted">4.2 MB — ready to translate</div>
              </div>
              <h3 className="text-[22px] font-bold text-pb-text">Upload</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Drop an IDML, PDF, or subtitle file. We read the layout tree — not a flattened text dump.</p>
            </div>

            {/* Step 02 — Pick a language */}
            <div className="border-white/[0.06] py-10 border-b md:border-b-0 md:border-r md:px-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>02</span>
              {/* Language pills */}
              <div className="mt-3 mb-4 flex flex-wrap gap-1.5 opacity-60">
                {["Chinese", "Arabic", "French", "German", "Japanese", "Spanish"].map((l) => (
                  <span key={l} className="font-pb-mono rounded-full border border-white/15 px-2.5 py-0.5 text-[9px] text-pb-text-muted">{l}</span>
                ))}
                <span className="font-pb-mono rounded-full border border-pb-accent/30 bg-pb-accent/10 px-2.5 py-0.5 text-[9px] text-pb-accent">+34 more</span>
              </div>
              <h3 className="text-[22px] font-bold text-pb-text">Pick a language</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Choose from 40+ targets. Attach a glossary to lock terms that must never be translated.</p>
            </div>

            {/* Step 03 — Download */}
            <div className="border-white/[0.06] py-10 md:pl-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>03</span>
              {/* Download ready visual */}
              <div className="mt-3 mb-4 flex items-center gap-3 opacity-60">
                <span style={{ color: "#4ade80", fontSize: "18px" }}>✓</span>
                <div>
                  <div className="font-pb-mono text-[11px] text-pb-text">product_magazine.zh.idml</div>
                  <div className="font-pb-mono text-[9px] text-pb-text-muted">Translated · ready to open</div>
                </div>
              </div>
              <h3 className="text-[22px] font-bold text-pb-text">Download</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Same extension, same styles, same page count. Open it and keep editing as if nothing happened.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── CAPABILITIES ─── */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
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

      {/* ─── FORMATS ─── */}
      <section className="pb-glass-section" style={{ background: "#0e0d0b", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-8 lg:px-14">
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
      <section id="pricing" className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
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

      {/* ─── CTA ─── */}
      <section style={{ background: "#e08a6f" }}>
        <div className="mx-auto flex max-w-[1100px] flex-col items-start justify-between gap-8 px-8 py-20 md:flex-row md:items-center lg:px-14 lg:py-24">
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
