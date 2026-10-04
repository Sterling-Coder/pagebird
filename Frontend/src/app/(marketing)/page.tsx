import Link from "next/link";
import { WatchDemoButton } from "@/components/WatchDemoButton";
import ProductDiagram from "@/components/ProductDiagram";
import IntegrationFlow from "@/components/IntegrationFlow";

const FORMATS_EXTENDED = [
  { label: ".idml", soon: false },
  { label: ".pdf", soon: false },
  { label: ".ai", soon: false },
  { label: ".psd", soon: false },
  { label: ".eps", soon: false },
  { label: ".srt", soon: false },
  { label: ".vtt", soon: false },
  { label: ".html", soon: false },
  { label: ".docx", soon: true },
  { label: ".pptx", soon: true },
  { label: ".xlsx", soon: true },
  { label: ".xliff", soon: true },
  { label: ".indd", soon: false },
  { label: ".svg", soon: true },
  { label: ".mp4 subs", soon: true },
];

export default function Home() {
  return (
    <>
      {/* ─── §1 HERO ─── */}
      <section className="relative overflow-hidden" style={{
        minHeight: "100vh",
        background: "linear-gradient(180deg, #f4d96d 0%, #f0c84a 4%, #e8ac2e 8%, #d9841a 14%, #c95810 20%, #b83010 28%, #a01c18 36%, #7a1420 46%, #561028 56%, #380820 66%, #240618 76%, #140410 86%, #0a0308 100%)",
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
            boxShadow: "0 48px 140px rgba(0,0,0,0.5), 0 0 0 1px rgba(255,255,255,0.2)",
            backdropFilter: "blur(12px)",
            background: "rgba(255,255,255,0.08)",
          }}>
            {/* Title bar */}
            <div className="flex items-center gap-2 px-4 py-3" style={{ background: "#1a1814", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
              <span style={{ marginLeft: "10px", fontSize: "12px", color: "rgba(255,255,255,0.4)", fontWeight: 500 }}>Pagebirdy</span>
            </div>

            <div className="flex" style={{ minHeight: "520px" }}>

              {/* ── Sidebar ── */}
              <div className="flex shrink-0 flex-col" style={{ width: "220px", background: "#131210", borderRight: "1px solid rgba(255,255,255,0.07)" }}>
                <div className="flex items-center justify-between px-4 py-3.5" style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                  <span style={{ fontFamily: "var(--font-share-tech-mono), monospace", fontSize: "14px", letterSpacing: "0.04em" }}>
                    <span style={{ color: "rgba(240,236,227,0.75)" }}>page</span><span style={{ color: "#e08a6f" }}>birdy</span>
                  </span>
                  <div style={{ width: "24px", height: "24px", borderRadius: "50%", background: "linear-gradient(135deg,#e08a6f,#8b6fbf)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", fontWeight: 700, color: "#fff" }}>A</div>
                </div>

                <div className="px-3 pt-3 pb-2">
                  <div style={{ background: "#e08a6f", color: "#fff", fontSize: "11px", fontWeight: 700, padding: "7px 0", borderRadius: "6px", textAlign: "center", letterSpacing: "0.06em" }}>+ NEW JOB</div>
                </div>

                <div style={{ height: "1px", background: "rgba(255,255,255,0.06)", margin: "0 12px" }} />

                <div className="px-3 pt-3">
                  <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(255,255,255,0.28)", paddingLeft: "6px", marginBottom: "6px" }}>PROJECTS</div>

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
                    {["IDML Files", "Subtitles", "Images"].map((f, i) => (
                      <div key={f} className="flex items-center gap-1.5 rounded-md px-2 py-1.5" style={{ marginLeft: "16px", background: i === 0 ? "rgba(255,255,255,0.06)" : "transparent" }}>
                        <svg viewBox="0 0 24 24" fill="none" stroke={i === 0 ? "rgba(240,236,227,0.6)" : "rgba(255,255,255,0.22)"} strokeWidth="1.75" style={{ width: "11px", height: "11px", flexShrink: 0 }}>
                          <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                        </svg>
                        <span style={{ fontSize: "11px", color: i === 0 ? "rgba(240,236,227,0.75)" : "rgba(240,236,227,0.35)" }}>{f}</span>
                      </div>
                    ))}
                  </div>

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

              {/* ── Main area ── */}
              <div className="flex flex-1 flex-col" style={{ background: "rgba(255,252,247,0.95)" }}>
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

                <div className="flex-1 overflow-hidden px-6 pt-2">
                  <div className="grid items-center py-2" style={{ gridTemplateColumns: "28px 2.5fr 0.6fr 1fr 0.8fr 0.8fr 80px 70px", borderBottom: "1px solid #e8e2d8" }}>
                    <span />
                    {["DOCUMENT", "TYPE", "PROGRESS", "TARGET", "CREATED", "QA", "DL"].map(h => (
                      <span key={h} style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.12em", color: "#a09a8e" }}>{h}</span>
                    ))}
                  </div>

                  {/* Folder row */}
                  <div className="grid items-center py-2.5 cursor-pointer" style={{ gridTemplateColumns: "28px 2.5fr 0.6fr 1fr 0.8fr 0.8fr 80px 70px", borderBottom: "1px solid #f0ece3" }}>
                    <span style={{ display: "flex", alignItems: "center", justifyContent: "center" }}>
                      <svg viewBox="0 0 24 24" fill="none" stroke="#9a9488" strokeWidth="1.75" style={{ width: "14px", height: "14px" }}>
                        <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      </svg>
                    </span>
                    <span style={{ fontSize: "13px", color: "#15130f", fontWeight: 500, display: "flex", alignItems: "center", gap: "6px" }}>
                      IDML Files
                      <span style={{ fontSize: "10px", color: "#9a9488", fontWeight: 400 }}>3 files</span>
                    </span>
                    <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                    <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                    <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                    <span style={{ fontSize: "11px", color: "#9a9488" }}>Dec 5</span>
                    <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                    <span style={{ fontSize: "11px", color: "#c0bab2" }}>—</span>
                  </div>

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

      {/* ─── §2 PRODUCTS ─── */}
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

      {/* ─── §3 HOW IT WORKS + AI ENGINE ─── */}
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
            {/* Step 01 */}
            <div className="border-white/[0.06] py-10 border-b md:border-b-0 md:border-r md:pr-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>01</span>
              <div className="mt-3 mb-4 opacity-60" style={{ border: "1px dashed rgba(224,138,111,0.35)", borderRadius: "6px", padding: "10px 14px" }}>
                <span className="font-pb-mono text-[11px] text-pb-accent/70">product_magazine.idml</span>
                <div className="mt-1 font-pb-mono text-[9px] text-pb-text-muted">4.2 MB — ready to translate</div>
              </div>
              <h3 className="text-[22px] font-bold text-pb-text">Upload</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Drop an IDML, PDF, or subtitle file. We read the layout tree — not a flattened text dump.</p>
            </div>

            {/* Step 02 */}
            <div className="border-white/[0.06] py-10 border-b md:border-b-0 md:border-r md:px-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>02</span>
              <div className="mt-3 mb-4 flex flex-wrap gap-1.5 opacity-60">
                {["Chinese", "Arabic", "French", "German", "Japanese", "Spanish"].map((l) => (
                  <span key={l} className="font-pb-mono rounded-full border border-white/15 px-2.5 py-0.5 text-[9px] text-pb-text-muted">{l}</span>
                ))}
                <span className="font-pb-mono rounded-full border border-pb-accent/30 bg-pb-accent/10 px-2.5 py-0.5 text-[9px] text-pb-accent">+34 more</span>
              </div>
              <h3 className="text-[22px] font-bold text-pb-text">Pick a language</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Choose from 40+ targets. Attach a glossary to lock terms that must never be translated.</p>
            </div>

            {/* Step 03 */}
            <div className="border-white/[0.06] py-10 md:pl-10">
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(240,236,227,0.06)" }}>03</span>
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

          {/* ── Under the hood: AI consensus diagram ── */}
          <div className="mt-20 pt-14" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
            <div className="flex items-center gap-3 mb-8">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Under the hood</span>
            </div>
            <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 items-center">
              <div>
                <h3 className="pb-stencil" style={{ fontSize: "clamp(1.6rem,2.8vw,2.4rem)", lineHeight: 1.05, marginBottom: "14px" }}>
                  Two AI engines.<br />One consensus.
                </h3>
                <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.55)", lineHeight: 1.6, marginBottom: "20px" }}>
                  OpenAI and DeepL translate independently. When they agree, the translation ships. When they disagree, the segment is flagged for human review — catching errors before they reach your client.
                </p>
                <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
                  {[
                    { dot: "#e08a6f", text: "OpenAI GPT + DeepL in parallel" },
                    { dot: "#4a70e0", text: "Segment-level consensus check" },
                    { dot: "#4ade80", text: "Disagreements routed to human review" },
                  ].map((s) => (
                    <div key={s.text} style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                      <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: s.dot, flexShrink: 0 }} />
                      <span style={{ fontSize: "13px", color: "rgba(240,236,227,0.6)" }}>{s.text}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Compact engine diagram */}
              <div style={{ fontFamily: "var(--font-space-mono), monospace", padding: "28px", background: "rgba(255,255,255,0.02)", border: "1px solid rgba(255,255,255,0.07)", borderRadius: "12px" }}>
                <div style={{ textAlign: "center", marginBottom: "10px" }}>
                  <span style={{ display: "inline-block", padding: "6px 18px", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "6px", fontSize: "11px", color: "rgba(255,255,255,0.6)" }}>Your file</span>
                </div>
                <div style={{ textAlign: "center", color: "rgba(255,255,255,0.2)", marginBottom: "10px" }}>↓</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", marginBottom: "10px" }}>
                  <div style={{ textAlign: "center", padding: "10px 14px", border: "1px solid rgba(224,138,111,0.4)", borderRadius: "6px", fontSize: "11px", color: "#e08a6f", background: "rgba(224,138,111,0.08)" }}>OpenAI GPT</div>
                  <div style={{ textAlign: "center", padding: "10px 14px", border: "1px solid rgba(74,112,224,0.4)", borderRadius: "6px", fontSize: "11px", color: "#4a70e0", background: "rgba(74,112,224,0.08)" }}>DeepL Neural</div>
                </div>
                <div style={{ textAlign: "center", color: "rgba(255,255,255,0.2)", marginBottom: "10px" }}>↓</div>
                <div style={{ textAlign: "center", marginBottom: "10px" }}>
                  <span style={{ display: "inline-block", padding: "8px 22px", border: "1px solid rgba(255,255,255,0.15)", borderRadius: "6px", fontSize: "11px", color: "rgba(255,255,255,0.6)" }}>Consensus check</span>
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                  <div style={{ textAlign: "center", padding: "8px 12px", border: "1px solid rgba(74,222,128,0.3)", borderRadius: "6px", fontSize: "10px", color: "#4ade80", background: "rgba(74,222,128,0.08)" }}>✓ Match → ships</div>
                  <div style={{ textAlign: "center", padding: "8px 12px", border: "1px solid rgba(248,113,113,0.3)", borderRadius: "6px", fontSize: "10px", color: "#f87171", background: "rgba(248,113,113,0.08)" }}>⚠ Flagged</div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── §4 PRODUCT DIAGRAMS ─── */}
      <ProductDiagram />
      <IntegrationFlow />

      {/* ─── §5 FORMATS TICKER ─── */}
      <section style={{ background: "#0a0908", borderTop: "1px solid rgba(255,255,255,0.04)", overflow: "hidden", padding: "14px 0" }}>
        <style>{`
          @keyframes pb-ticker {
            from { transform: translateX(0); }
            to { transform: translateX(-50%); }
          }
          .pb-ticker-track {
            display: flex;
            width: max-content;
            animation: pb-ticker 28s linear infinite;
          }
          .pb-ticker-track:hover {
            animation-play-state: paused;
          }
        `}</style>
        <div className="pb-ticker-track">
          {[...FORMATS_EXTENDED, ...FORMATS_EXTENDED].map((f, i) => (
            <span key={i} style={{
              fontFamily: "var(--font-space-mono), monospace",
              fontSize: "11px",
              color: f.soon ? "rgba(240,236,227,0.18)" : "rgba(240,236,227,0.38)",
              letterSpacing: "0.08em",
              padding: "0 28px",
              whiteSpace: "nowrap",
              borderRight: "1px solid rgba(255,255,255,0.06)",
              display: "inline-flex",
              alignItems: "center",
              gap: "6px",
            }}>
              {f.label}
              {f.soon && (
                <span style={{ fontSize: "8px", letterSpacing: "0.1em", color: "rgba(240,236,227,0.2)", textTransform: "uppercase" }}>soon</span>
              )}
            </span>
          ))}
        </div>
      </section>

      {/* ─── §6 CTA ─── */}
      <section style={{
        background: "linear-gradient(135deg, #f5ede4 0%, #fdf6ef 50%, #f0e8dc 100%)",
        borderTop: "1px solid rgba(200,150,100,0.15)",
      }}>
        <div style={{
          maxWidth: "1100px", margin: "0 auto",
          padding: "56px 56px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: "40px",
        }}>
          <h2 style={{
            fontFamily: "var(--font-share-tech-mono), monospace",
            fontSize: "clamp(2rem, 3.5vw, 3.2rem)",
            lineHeight: 1.1,
            maxWidth: "600px",
            letterSpacing: "-0.01em",
            margin: 0,
            color: "#15130f",
          }}>
            Send us the document<br />you dread translating.
          </h2>
          <Link href="/login" style={{
            fontFamily: "var(--font-space-mono), monospace",
            fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            color: "#fff", background: "#c86018",
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
