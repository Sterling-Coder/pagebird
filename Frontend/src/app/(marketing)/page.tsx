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

          {/* ── macOS app window — full product sidebar + jobs ── */}
          <div className="pb-enter pb-enter-delay-4 relative mt-16 lg:-mx-20 xl:-mx-32" style={{
            borderRadius: "12px",
            overflow: "hidden",
            boxShadow: "0 48px 140px rgba(0,0,0,0.7), 0 0 0 1px rgba(255,255,255,0.08)",
          }}>
            {/* Title bar */}
            <div className="flex items-center gap-2 px-4 py-3" style={{ background: "#1a1814", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
              <span style={{ marginLeft: "10px", fontSize: "12px", color: "rgba(255,255,255,0.4)", fontWeight: 500 }}>Pagebirdy</span>
            </div>

            <div className="flex" style={{ minHeight: "520px" }}>

              {/* ── Sidebar: dark with all products ── */}
              <div className="flex shrink-0 flex-col" style={{ width: "220px", background: "#131210", borderRight: "1px solid rgba(255,255,255,0.07)" }}>
                {/* Logo + user */}
                <div className="flex items-center justify-between px-4 py-3.5" style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                  <span style={{ fontFamily: "var(--font-share-tech-mono), monospace", fontSize: "14px", letterSpacing: "0.04em" }}>
                    <span style={{ color: "rgba(240,236,227,0.75)" }}>page</span><span style={{ color: "#e08a6f" }}>birdy</span>
                  </span>
                  {/* Avatar */}
                  <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "linear-gradient(135deg,#e08a6f,#8b6fbf)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", fontWeight: 700, color: "#fff" }}>A</div>
                </div>

                {/* New Job button */}
                <div className="px-3 pt-3 pb-2">
                  <div style={{ background: "#e08a6f", color: "#fff", fontSize: "11px", fontWeight: 700, padding: "7px 0", borderRadius: "6px", textAlign: "center", letterSpacing: "0.06em" }}>+ NEW JOB</div>
                </div>

                <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", margin: "0 12px" }} />

                {/* Projects tree */}
                <div className="px-3 pt-3">
                  <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(255,255,255,0.28)", paddingLeft: "6px", marginBottom: "6px" }}>PROJECTS</div>

                  {/* Active project — expanded */}
                  <div style={{ marginBottom: "2px" }}>
                    <div className="flex items-center gap-1.5 rounded-md px-2 py-2" style={{ background: "rgba(224,138,111,0.12)" }}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="#e08a6f" strokeWidth="2" style={{ width: "10px", height: "10px", flexShrink: 0 }}>
                        <path d="m6 9 6 6 6-6" />
                      </svg>
                      <svg viewBox="0 0 24 24" fill="none" stroke="#e08a6f" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      </svg>
                      <span style={{ fontSize: "12px", color: "#e08a6f", fontWeight: 600, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>Q4 Campaigns</span>
                    </div>
                    {/* Nested folders */}
                    {["IDML Files", "Subtitles", "Images"].map((f, i) => (
                      <div key={f} className="flex items-center gap-1.5 rounded-md px-2 py-1.5" style={{ marginLeft: "16px", background: i === 0 ? "rgba(255,255,255,0.06)" : "transparent" }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke={i === 0 ? "rgba(240,236,227,0.6)" : "rgba(255,255,255,0.22)"} strokeWidth="1.75" style={{ width: "11px", height: "11px", flexShrink: 0 }}>
                          <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                        </svg>
                        <span style={{ fontSize: "11px", color: i === 0 ? "rgba(240,236,227,0.75)" : "rgba(240,236,227,0.35)" }}>{f}</span>
                      </div>
                    ))}
                  </div>

                  {/* Other projects — collapsed */}
                  {["Brand Assets", "Legal Docs"].map(p => (
                    <div key={p} className="flex items-center gap-1.5 rounded-md px-2 py-2 mb-0.5">
                      <svg viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.25)" strokeWidth="2" style={{ width: "10px", height: "10px", flexShrink: 0 }}>
                        <path d="m9 18 6-6-6-6" />
                      </svg>
                      <svg viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.22)" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      </svg>
                      <span style={{ fontSize: "12px", color: "rgba(240,236,227,0.38)" }}>{p}</span>
                    </div>
                  ))}
                </div>

                <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", margin: "12px 12px 0" }} />

                {/* Bottom nav */}
                <div className="px-3 pt-2">
                  {[
                    { label: "Team", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" },
                    { label: "Settings", icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1-2.83 2.83l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-4 0v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83-2.83l.06-.06A1.65 1.65 0 0 0 4.68 15a1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1 0-4h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 2.83-2.83l.06.06A1.65 1.65 0 0 0 9 4.68a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 4 0v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 2.83l-.06.06A1.65 1.65 0 0 0 19.4 9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 0 4h-.09a1.65 1.65 0 0 0-1.51 1z" },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2.5 rounded-md px-2 py-2 mb-0.5">
                      <svg viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,0.3)" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d={item.icon} />
                      </svg>
                      <span style={{ fontSize: "12px", color: "rgba(240,236,227,0.38)" }}>{item.label}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* ── Main: Project / folder / file structure ── */}
              <div className="flex flex-1 flex-col" style={{ background: "#fdfcf7" }}>
                {/* Breadcrumb + header */}
                <div className="flex items-center justify-between px-6 py-3" style={{ borderBottom: "1px solid #e8e2d8" }}>
                  <div className="flex items-center gap-1.5" style={{ fontSize: "12px", color: "#9a9488" }}>
                    <span style={{ color: "#6e6a61", cursor: "pointer" }}>Projects</span>
                    <span>/</span>
                    <span style={{ color: "#15130f", fontWeight: 600 }}>Q4 Campaigns</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div style={{ border: "1px solid #dad4c7", color: "#6e6a61", fontSize: "11px", fontWeight: 600, padding: "5px 12px", borderRadius: "6px" }}>CREATE FOLDER</div>
                    <div style={{ background: "#e08a6f", color: "#fff", fontSize: "11px", fontWeight: 700, padding: "5px 12px", borderRadius: "6px" }}>UPLOAD</div>
                  </div>
                </div>

                {/* Tab bar: Files, Settings, Linguistic Assets, Statistics */}
                <div className="flex items-center gap-0 px-6" style={{ borderBottom: "1px solid #e8e2d8" }}>
                  {[{ l: "Files", a: true }, { l: "Settings", a: false }, { l: "Linguistic Assets", a: false }, { l: "Statistics", a: false }].map(t => (
                    <div key={t.l} style={{
                      fontSize: "11px", fontWeight: t.a ? 700 : 500, padding: "8px 14px",
                      color: t.a ? "#e08a6f" : "#9a9488",
                      borderBottom: t.a ? "2px solid #e08a6f" : "2px solid transparent",
                      marginBottom: "-1px",
                    }}>{t.l}</div>
                  ))}
                </div>

                {/* Table */}
                <div className="flex-1 overflow-hidden px-6 pt-2">
                  {/* Column headers */}
                  <div className="grid items-center py-2" style={{ gridTemplateColumns: "28px 2.5fr 0.6fr 1fr 0.8fr 0.8fr 80px 70px", borderBottom: "1px solid #e8e2d8" }}>
                    <span />
                    {["DOCUMENT", "TYPE", "PROGRESS", "TARGET", "CREATED", "QA", "DL"].map(h => (
                      <span key={h} style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.12em", color: "#a09a8e" }}>{h}</span>
                    ))}
                  </div>

                  {/* Folder row */}
                  {[
                    { type: "folder", name: "IDML Files", sub: "3 files" },
                  ].map(row => (
                    <div key={row.name} className="grid items-center py-2.5 cursor-pointer" style={{ gridTemplateColumns: "28px 2.5fr 0.6fr 1fr 0.8fr 0.8fr 80px 70px", borderBottom: "1px solid #f0ece3" }}>
                      <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="#9a9488" strokeWidth="1.75" style={{ width: "14px", height: "14px" }}>
                          <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                        </svg>
                      </span>
                      <span style={{ fontSize: "13px", color: "#15130f", fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
                        {row.name}
                        <span style={{ fontSize: "10px", color: "#9a9488", fontWeight: 400 }}>{row.sub}</span>
                      </span>
                      <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                      <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                      <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                      <span style={{ fontSize: "11px", color: "#9a9488" }}>Dec 5</span>
                      <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                      <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                    </div>
                  ))}

                  {/* File rows */}
                  {[
                    { name: "annual_report_2026.idml", type: "idml", target: "Chinese", created: "Today", progress: 100, qa: "94%", done: true },
                    { name: "product_brochure.pdf", type: "pdf", target: "Arabic", created: "Today", progress: 72, qa: "—", done: false },
                    { name: "product_launch.srt", type: "srt", target: "French", created: "Dec 12", progress: 100, qa: "RUN QA", done: true },
                    { name: "marketing_signage.ai", type: "ai", target: "German", created: "Dec 10", progress: 100, qa: "88%", done: true },
                    { name: "company_website.html", type: "html", target: "Spanish", created: "Dec 8", progress: 48, qa: "—", done: false },
                  ].map((row, i) => (
                    <div key={row.name} className="grid items-center py-2.5 cursor-pointer hover:bg-[#f8f5ee]" style={{ gridTemplateColumns: "28px 2.5fr 0.6fr 1fr 0.8fr 0.8fr 80px 70px", borderBottom: i < 4 ? "1px solid #f4f0e8" : "none" }}>
                      <span style={{ paddingLeft: "4px" }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke="#c0bab2" strokeWidth="1.75" style={{ width: "12px", height: "12px" }}>
                          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                          <polyline points="14 2 14 8 20 8" />
                        </svg>
                      </span>
                      <span style={{ fontSize: "13px", color: "#15130f", fontWeight: 400, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", paddingRight: "8px" }}>{row.name}</span>
                      <span style={{ fontSize: "10px", fontWeight: 700, color: "#9a9488", textTransform: "uppercase", letterSpacing: "0.06em" }}>{row.type}</span>
                      <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                        <div style={{ flex: 1, maxWidth: "80px", height: "4px", background: "#e8e2d8", borderRadius: "2px", overflow: "hidden" }}>
                          <div style={{ height: "100%", width: `${row.progress}%`, background: row.done ? "#4a9e5a" : "#e08a6f", borderRadius: "2px" }} />
                        </div>
                      </div>
                      <span style={{ fontSize: "11px", color: "#6e6a61" }}>{row.target}</span>
                      <span style={{ fontSize: "11px", color: "#9a9488" }}>{row.created}</span>
                      <span style={{ fontSize: "10px", color: row.qa === "RUN QA" ? "#9a9488" : row.qa === "—" ? "#c0bab2" : "#15130f", border: row.qa === "RUN QA" ? "1px solid #dad4c7" : "none", padding: row.qa === "RUN QA" ? "2px 6px" : "0", borderRadius: "4px" }}>{row.qa}</span>
                      <span>
                        <svg viewBox="0 0 24 24" fill="none" stroke={row.done ? "#6e6a61" : "#dad4c7"} strokeWidth="1.75" style={{ width: "14px", height: "14px" }}>
                          <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                          <polyline points="7 10 12 15 17 10" />
                          <line x1="12" y1="15" x2="12" y2="3" />
                        </svg>
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            {/* Bottom fade */}
            <div className="pointer-events-none absolute bottom-0 left-0 right-0" style={{
              height: "35%",
              background: "linear-gradient(to top, #0c0810 0%, #0c0810 6%, rgba(12,8,16,0.9) 35%, transparent 100%)",
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

      {/* ─── TRANSLATION ENGINE FLOW DIAGRAM ─── */}
      <section className="pb-glass-section" style={{ background: "#0a0908" }}>
        <style>{`
          @keyframes pbFlowDash {
            from { stroke-dashoffset: 300; }
            to   { stroke-dashoffset: 0; }
          }
          .pb-flow-anim { animation: pbFlowDash 2.4s linear infinite; }
          .pb-flow-anim-d1 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 0s; }
          .pb-flow-anim-d2 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 0.48s; }
          .pb-flow-anim-d3 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 0.96s; }
          .pb-flow-anim-d4 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 1.44s; }
          .pb-flow-anim-d5 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 1.92s; }
          .pb-flow-out-d1 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 0.24s; }
          .pb-flow-out-d2 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 0.6s; }
          .pb-flow-out-d3 { animation: pbFlowDash 2.4s linear infinite; animation-delay: 1.0s; }
        `}</style>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          {/* Header */}
          <div className="mb-14 flex flex-col items-center text-center">
            <div className="mb-4 flex items-center gap-2">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">The Translation Engine</span>
            </div>
            <h2 className="pb-stencil max-w-2xl" style={{ fontSize: "clamp(2rem, 3.5vw, 3.2rem)", lineHeight: 1.05 }}>
              Every file format. One engine.
            </h2>
            <p className="mt-5 max-w-lg text-[15px] leading-relaxed text-pb-text-muted">
              Upload anything. Our engine reads the layout tree, translates through AI consensus, and rebuilds the output exactly as you left it.
            </p>
          </div>

          {/* SVG Flow Diagram */}
          <div className="overflow-x-auto">
            <svg viewBox="0 0 900 400" width="100%" style={{ maxWidth: "900px", display: "block", margin: "0 auto" }} aria-hidden="true">
              {/* ── Input nodes ── */}
              {/* .idml  y=60 */}
              <circle cx="60" cy="60"  r="7" fill="#e08a6f" />
              <text x="75" y="65" fill="rgba(240,236,227,0.7)" fontSize="12" fontFamily="monospace">.idml</text>
              {/* .pdf   y=130 */}
              <circle cx="60" cy="130" r="7" fill="#d4785a" />
              <text x="75" y="135" fill="rgba(240,236,227,0.7)" fontSize="12" fontFamily="monospace">.pdf</text>
              {/* .srt   y=200 */}
              <circle cx="60" cy="200" r="7" fill="#8b6fbf" />
              <text x="75" y="205" fill="rgba(240,236,227,0.7)" fontSize="12" fontFamily="monospace">.srt / .vtt</text>
              {/* .ai    y=270 */}
              <circle cx="60" cy="270" r="7" fill="#4a9e8a" />
              <text x="75" y="275" fill="rgba(240,236,227,0.7)" fontSize="12" fontFamily="monospace">.ai / .psd</text>
              {/* .html  y=340 */}
              <circle cx="60" cy="340" r="7" fill="#5a9e5a" />
              <text x="75" y="345" fill="rgba(240,236,227,0.7)" fontSize="12" fontFamily="monospace">.html</text>

              {/* ── Input paths (dim base) ── */}
              <path d="M67,60  C280,60  280,200 430,200" stroke="#e08a6f" strokeWidth="1.5" fill="none" opacity="0.18" />
              <path d="M67,130 C280,130 280,200 430,200" stroke="#d4785a" strokeWidth="1.5" fill="none" opacity="0.18" />
              <path d="M67,200 C200,200 200,200 430,200" stroke="#8b6fbf" strokeWidth="1.5" fill="none" opacity="0.18" />
              <path d="M67,270 C280,270 280,200 430,200" stroke="#4a9e8a" strokeWidth="1.5" fill="none" opacity="0.18" />
              <path d="M67,340 C280,340 280,200 430,200" stroke="#5a9e5a" strokeWidth="1.5" fill="none" opacity="0.18" />

              {/* ── Animated overlay paths ── */}
              <path className="pb-flow-anim-d1" d="M67,60  C280,60  280,200 430,200" stroke="#e08a6f" strokeWidth="1.5" fill="none" opacity="0.7" strokeDasharray="40 260" />
              <path className="pb-flow-anim-d2" d="M67,130 C280,130 280,200 430,200" stroke="#d4785a" strokeWidth="1.5" fill="none" opacity="0.7" strokeDasharray="40 260" />
              <path className="pb-flow-anim-d3" d="M67,200 C200,200 200,200 430,200" stroke="#8b6fbf" strokeWidth="1.5" fill="none" opacity="0.7" strokeDasharray="40 260" />
              <path className="pb-flow-anim-d4" d="M67,270 C280,270 280,200 430,200" stroke="#4a9e8a" strokeWidth="1.5" fill="none" opacity="0.7" strokeDasharray="40 260" />
              <path className="pb-flow-anim-d5" d="M67,340 C280,340 280,200 430,200" stroke="#5a9e5a" strokeWidth="1.5" fill="none" opacity="0.7" strokeDasharray="40 260" />

              {/* ── Central node ── */}
              <circle cx="450" cy="200" r="52" fill="rgba(224,138,111,0.06)" stroke="rgba(224,138,111,0.25)" strokeWidth="1" />
              <circle cx="450" cy="200" r="38" fill="rgba(224,138,111,0.1)" stroke="rgba(224,138,111,0.35)" strokeWidth="1" />
              <circle cx="450" cy="200" r="22" fill="rgba(224,138,111,0.18)" />
              <text x="450" y="192" textAnchor="middle" fill="rgba(240,236,227,0.9)" fontSize="9" fontFamily="monospace" fontWeight="bold" letterSpacing="1">AI ENGINE</text>
              <text x="450" y="206" textAnchor="middle" fill="rgba(224,138,111,0.8)" fontSize="8" fontFamily="monospace">consensus</text>

              {/* ── Output paths (dim base) ── */}
              <path d="M470,200 C600,200 700,100 840,80"  stroke="rgba(240,236,227,0.15)" strokeWidth="1.5" fill="none" />
              <path d="M470,200 C600,200 700,200 840,200" stroke="rgba(240,236,227,0.15)" strokeWidth="1.5" fill="none" />
              <path d="M470,200 C600,200 700,300 840,320" stroke="rgba(240,236,227,0.15)" strokeWidth="1.5" fill="none" />

              {/* ── Animated output paths ── */}
              <path className="pb-flow-out-d1" d="M470,200 C600,200 700,100 840,80"  stroke="rgba(240,236,227,0.6)" strokeWidth="1.5" fill="none" strokeDasharray="40 200" />
              <path className="pb-flow-out-d2" d="M470,200 C600,200 700,200 840,200" stroke="rgba(240,236,227,0.6)" strokeWidth="1.5" fill="none" strokeDasharray="40 200" />
              <path className="pb-flow-out-d3" d="M470,200 C600,200 700,300 840,320" stroke="rgba(240,236,227,0.6)" strokeWidth="1.5" fill="none" strokeDasharray="40 200" />

              {/* ── Output nodes ── */}
              <circle cx="845" cy="80"  r="6" fill="rgba(240,236,227,0.5)" />
              <text x="858" y="85"  fill="rgba(240,236,227,0.5)" fontSize="11" fontFamily="monospace">Chinese</text>
              <circle cx="845" cy="200" r="6" fill="rgba(240,236,227,0.8)" />
              <text x="858" y="205" fill="rgba(240,236,227,0.8)" fontSize="11" fontFamily="monospace" fontWeight="bold">Arabic</text>
              <circle cx="845" cy="320" r="6" fill="rgba(240,236,227,0.5)" />
              <text x="858" y="325" fill="rgba(240,236,227,0.5)" fontSize="11" fontFamily="monospace">French</text>

              {/* ── Labels alongside ── */}
              <text x="450" y="268" textAnchor="middle" fill="rgba(240,236,227,0.3)" fontSize="9" fontFamily="monospace">OpenAI + DeepL</text>
              <text x="450" y="280" textAnchor="middle" fill="rgba(240,236,227,0.3)" fontSize="9" fontFamily="monospace">Layout preserved · RTL · 40+ langs</text>
            </svg>
          </div>

          {/* Stat pills */}
          <div className="mt-12 flex flex-wrap items-center justify-center gap-4">
            {[
              { n: "40+", label: "languages" },
              { n: "6", label: "file formats" },
              { n: "2", label: "AI engines in consensus" },
            ].map((s) => (
              <div key={s.label} className="flex items-center gap-3 rounded-full border border-white/10 px-6 py-3" style={{ background: "rgba(255,255,255,0.04)" }}>
                <span className="font-pb-mono text-[22px] font-bold text-pb-accent">{s.n}</span>
                <span className="text-[13px] text-pb-text-muted">{s.label}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CAPABILITIES — 3 visual feature panels ─── */}

      {/* Panel 1: Layout preservation */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 items-center lg:grid-cols-2">
            {/* Left: text */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: "#e08a6f" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#e08a6f" }}>Capabilities</span>
              </div>
              <h2 className="pb-stencil text-4xl md:text-5xl" style={{ fontSize: "clamp(2rem,3.5vw,3rem)", lineHeight: 1.05 }}>
                Layout preserved.<br />Pixel-perfect.
              </h2>
              <p className="mt-6 text-[15px] leading-relaxed text-pb-text-muted max-w-md">
                Every font, frame, column and table in your InDesign or PDF file stays exactly where it was. Not approximate — exact. Text expands? We reflow inside the original frame.
              </p>
              <div className="mt-8 flex flex-wrap gap-2">
                {["40+ languages", "Zero cleanup", "Same file format"].map(pill => (
                  <span key={pill} className="font-pb-mono text-[11px] tracking-wide" style={{
                    border: "1px solid rgba(224,138,111,0.3)", borderRadius: "20px",
                    padding: "5px 14px", color: "#e08a6f",
                  }}>{pill}</span>
                ))}
              </div>
            </div>
            {/* Right: document layout mock */}
            <div style={{ position: "relative" }}>
              <div style={{
                background: "#f5f0e6", borderRadius: "8px", padding: "24px",
                border: "1px solid rgba(224,138,111,0.2)",
                boxShadow: "0 20px 60px rgba(0,0,0,0.3)",
              }}>
                {/* Ruler marks */}
                <div style={{ display: "flex", gap: "2px", marginBottom: "12px" }}>
                  {Array.from({ length: 20 }).map((_, i) => (
                    <div key={i} style={{ flex: 1, height: i % 5 === 0 ? "8px" : "4px", background: "rgba(224,138,111,0.3)" }} />
                  ))}
                </div>
                {/* Two columns with orange frame borders */}
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div style={{ border: "1.5px solid rgba(224,138,111,0.5)", borderRadius: "3px", padding: "10px" }}>
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginBottom: "6px", width: "90%" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginBottom: "6px", width: "75%" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginBottom: "6px", width: "85%" }} />
                    <div style={{ height: "40px", background: "rgba(224,138,111,0.12)", marginTop: "8px", borderRadius: "2px" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginTop: "8px", marginBottom: "6px", width: "80%" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, width: "60%" }} />
                  </div>
                  <div style={{ border: "1.5px solid rgba(224,138,111,0.5)", borderRadius: "3px", padding: "10px" }}>
                    <div style={{ height: "60px", background: "rgba(224,138,111,0.08)", borderRadius: "2px", marginBottom: "8px" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginBottom: "6px", width: "95%" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, marginBottom: "6px", width: "70%" }} />
                    <div style={{ height: "3px", background: "#1a1914", opacity: 0.5, width: "88%" }} />
                  </div>
                </div>
                {/* Bottom frame annotation */}
                <div style={{ marginTop: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
                  <div style={{ flex: 1, height: "1px", background: "rgba(224,138,111,0.3)" }} />
                  <span style={{ fontSize: "9px", fontFamily: "monospace", color: "#e08a6f", whiteSpace: "nowrap" }}>FRAME PRESERVED</span>
                  <div style={{ flex: 1, height: "1px", background: "rgba(224,138,111,0.3)" }} />
                </div>
              </div>
              {/* Translated version — offset card */}
              <div style={{
                position: "absolute", bottom: "-20px", right: "-20px",
                background: "#1a1812", borderRadius: "8px", padding: "16px",
                border: "1px solid rgba(224,138,111,0.15)", width: "160px",
                boxShadow: "0 12px 40px rgba(0,0,0,0.4)",
              }}>
                <div style={{ fontSize: "9px", fontFamily: "monospace", color: "#e08a6f", marginBottom: "8px", letterSpacing: "0.08em" }}>中文 OUTPUT</div>
                <div style={{ height: "2px", background: "rgba(255,255,255,0.15)", marginBottom: "5px", width: "85%" }} />
                <div style={{ height: "2px", background: "rgba(255,255,255,0.15)", marginBottom: "5px", width: "70%" }} />
                <div style={{ height: "2px", background: "rgba(255,255,255,0.15)", width: "90%" }} />
                <div style={{ height: "28px", background: "rgba(224,138,111,0.08)", marginTop: "6px", borderRadius: "2px" }} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Panel 2: RTL */}
      <section className="pb-glass-section" style={{ borderTop: "1px solid rgba(255,255,255,0.05)", background: "rgba(139,111,191,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 items-center lg:grid-cols-2">
            {/* Left: LTR → RTL page mock */}
            <div className="flex items-center gap-6">
              {/* LTR page */}
              <div style={{ flex: 1, background: "#f5f0e6", borderRadius: "6px", padding: "16px", border: "1px solid rgba(255,255,255,0.1)" }}>
                <div style={{ fontSize: "8px", fontFamily: "monospace", color: "#a09a88", marginBottom: "8px" }}>ENGLISH</div>
                {[90, 75, 95, 60].map((w, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", gap: "4px", marginBottom: "5px" }}>
                    <div style={{ width: "8px", height: "8px", background: "rgba(26,25,20,0.2)", borderRadius: "1px", flexShrink: 0 }} />
                    <div style={{ height: "3px", background: "rgba(26,25,20,0.25)", width: `${w}%` }} />
                  </div>
                ))}
                <div style={{ height: "30px", background: "rgba(26,25,20,0.07)", marginTop: "8px", borderRadius: "2px" }} />
              </div>
              {/* Arrow */}
              <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: "4px" }}>
                <div style={{ fontSize: "18px", color: "#8b6fbf" }}>→</div>
                <div style={{ fontSize: "8px", fontFamily: "monospace", color: "#8b6fbf", letterSpacing: "0.06em" }}>mirror</div>
              </div>
              {/* RTL page */}
              <div style={{ flex: 1, background: "#1a1020", borderRadius: "6px", padding: "16px", border: "1px solid rgba(139,111,191,0.3)" }}>
                <div style={{ fontSize: "8px", fontFamily: "monospace", color: "#8b6fbf", marginBottom: "8px", textAlign: "right" }}>عربي</div>
                {[85, 70, 90, 55].map((w, i) => (
                  <div key={i} style={{ display: "flex", alignItems: "center", justifyContent: "flex-end", gap: "4px", marginBottom: "5px" }}>
                    <div style={{ height: "3px", background: "rgba(139,111,191,0.4)", width: `${w}%` }} />
                    <div style={{ width: "8px", height: "8px", background: "rgba(139,111,191,0.3)", borderRadius: "1px", flexShrink: 0 }} />
                  </div>
                ))}
                <div style={{ height: "30px", background: "rgba(139,111,191,0.08)", marginTop: "8px", borderRadius: "2px" }} />
              </div>
            </div>
            {/* Right: text */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>RTL Support</span>
              </div>
              <h2 className="pb-stencil text-4xl" style={{ fontSize: "clamp(2rem,3.5vw,3rem)", lineHeight: 1.05 }}>
                Right-to-left.<br />First class.
              </h2>
              <p className="mt-6 text-[15px] leading-relaxed text-pb-text-muted max-w-md">
                Arabic and Hebrew don&apos;t just get translated — the entire page mirrors. Margins swap, gutters invert, bullets point the right way. 22 RTL languages supported.
              </p>
              <div className="mt-8 flex flex-wrap gap-2">
                {["Arabic", "Hebrew", "Urdu", "Farsi", "+18 more"].map(lang => (
                  <span key={lang} className="font-pb-mono text-[11px] tracking-wide" style={{
                    border: "1px solid rgba(139,111,191,0.3)", borderRadius: "20px",
                    padding: "5px 14px", color: "#8b6fbf",
                  }}>{lang}</span>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Panel 3: QA */}
      <section className="pb-glass-section" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 items-center lg:grid-cols-2">
            {/* Left: text */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: "#4a9e8a" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#4a9e8a" }}>Quality Assurance</span>
              </div>
              <h2 className="pb-stencil text-4xl" style={{ fontSize: "clamp(2rem,3.5vw,3rem)", lineHeight: 1.05 }}>
                QA before<br />it ships.
              </h2>
              <p className="mt-6 text-[15px] leading-relaxed text-pb-text-muted max-w-md">
                Every translation gets a layout-integrity score. Catch overflow, reflow, and broken tables before your client does. Side-by-side review lets your translators edit against the source.
              </p>
              <div className="mt-8 flex flex-wrap gap-2">
                {["Layout scoring", "Side-by-side review", "Segment editing"].map(pill => (
                  <span key={pill} className="font-pb-mono text-[11px] tracking-wide" style={{
                    border: "1px solid rgba(74,158,138,0.3)", borderRadius: "20px",
                    padding: "5px 14px", color: "#4a9e8a",
                  }}>{pill}</span>
                ))}
              </div>
            </div>
            {/* Right: QA score mock */}
            <div style={{
              background: "#0e0d0b", borderRadius: "12px", padding: "28px",
              border: "1px solid rgba(74,158,138,0.2)",
              boxShadow: "0 20px 60px rgba(0,0,0,0.4)",
            }}>
              <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginBottom: "20px" }}>
                <span style={{ fontSize: "64px", fontWeight: 800, color: "#4a9e8a", lineHeight: 1, fontFamily: "monospace" }}>94%</span>
                <span style={{ fontSize: "13px", color: "rgba(255,255,255,0.4)" }}>integrity score</span>
              </div>
              <div style={{ height: "1px", background: "rgba(255,255,255,0.08)", marginBottom: "16px" }} />
              {[
                { label: "Layout integrity", ok: true },
                { label: "Text overflow", ok: true },
                { label: "Font coverage", ok: true },
                { label: "RTL mirroring", ok: true },
                { label: "2 segments flagged for review", ok: false },
              ].map(item => (
                <div key={item.label} style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "10px" }}>
                  <span style={{ fontSize: "14px", color: item.ok ? "#4a9e8a" : "#e08a6f", flexShrink: 0 }}>{item.ok ? "✓" : "⚠"}</span>
                  <span style={{ fontSize: "13px", color: item.ok ? "rgba(240,236,227,0.7)" : "#e08a6f" }}>{item.label}</span>
                </div>
              ))}
              <div style={{ marginTop: "16px", background: "rgba(74,158,138,0.08)", borderRadius: "6px", padding: "10px 14px", border: "1px solid rgba(74,158,138,0.2)" }}>
                <span style={{ fontSize: "11px", fontFamily: "monospace", color: "#4a9e8a" }}>→ Open review editor</span>
              </div>
            </div>
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

      {/* ─── COMING SOON TEASER ─── */}
      <section style={{ background: "#0a0908", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div style={{ maxWidth: "1100px", margin: "0 auto", padding: "28px 56px", textAlign: "center" }}>
          <p style={{ fontFamily: "var(--font-space-mono), monospace", fontSize: "11px", color: "rgba(240,236,227,0.3)", letterSpacing: "0.12em", textTransform: "uppercase", marginBottom: "14px" }}>
            More formats arriving soon
          </p>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "8px", flexWrap: "wrap" }}>
            {[".docx", ".pptx", ".xlsx", ".xliff"].map((fmt) => (
              <span key={fmt} style={{
                fontFamily: "var(--font-space-mono), monospace",
                fontSize: "11px", color: "rgba(240,236,227,0.25)",
                border: "1px solid rgba(255,255,255,0.08)",
                padding: "4px 12px", display: "inline-flex", alignItems: "center", gap: "8px",
              }}>
                {fmt}
                <span style={{ fontSize: "8px", color: "rgba(240,236,227,0.2)", letterSpacing: "0.1em" }}>SOON</span>
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── dark with gradient headline */}
      <section style={{
        background: "linear-gradient(135deg, #0f0e0c 0%, #1a1410 50%, #0c0a0e 100%)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{
          maxWidth: "1100px", margin: "0 auto",
          padding: "56px 56px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: "40px",
        }}>
          <h2 className="pb-stencil" style={{
            fontSize: "clamp(2rem, 3.5vw, 3.2rem)",
            lineHeight: 1.1,
            maxWidth: "600px",
            letterSpacing: "-0.01em",
            margin: 0,
          }}>
            Send us the document<br />you dread translating.
          </h2>
          <Link href="/login" style={{
            fontFamily: "var(--font-space-mono), monospace",
            fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            color: "#15130f", background: "#e08a6f",
            padding: "16px 32px", whiteSpace: "nowrap",
            textDecoration: "none", textTransform: "uppercase",
            flexShrink: 0,
            borderRadius: "4px",
          }}>
            TRANSLATE FREE →
          </Link>
        </div>
      </section>
    </>
  );
}
