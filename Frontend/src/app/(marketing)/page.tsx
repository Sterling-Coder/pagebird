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
                <span className="inline-block h-2 w-2 rounded-full" style={{ background: "rgba(0,0,0,0.45)" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-[0.15em] uppercase" style={{ color: "rgba(0,0,0,0.55)" }}>
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

          {/* ── macOS app window — kanban board ── */}
          <div className="pb-enter pb-enter-delay-4 relative mt-16 lg:-mx-20 xl:-mx-32" style={{
            borderRadius: "12px",
            background: "#e2ddd6",
            boxShadow: "0 60px 160px rgba(0,0,0,0.5), 0 0 0 1px rgba(0,0,0,0.12)",
          }}>
            {/* Title bar */}
            <div className="flex items-center gap-2 px-5 py-3" style={{ background: "#e8e2d8", borderBottom: "1px solid #d8d2c8" }}>
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#ff5f57" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#febc2e" }} />
              <span className="inline-block h-3 w-3 rounded-full" style={{ background: "#28c840" }} />
              <span style={{ marginLeft: "12px", fontSize: "12px", color: "#9a9284", fontWeight: 500 }}>Pagebirdy</span>
            </div>

            {/* Inner layout — sidebar + main as inset floating panels */}
            <div className="flex gap-2 p-2" style={{ minHeight: "680px" }}>

              {/* ── Sidebar — WHITE theme ── */}
              <div className="flex shrink-0 flex-col" style={{ width: "214px", background: "#ffffff", borderRadius: "8px", overflow: "hidden", boxShadow: "1px 0 0 #e2ddd6" }}>
                {/* Logo */}
                <div className="flex items-center px-4 py-3.5" style={{ borderBottom: "1px solid #e8e2d8" }}>
                  <span style={{ fontFamily: "var(--font-share-tech-mono), monospace", fontSize: "13.5px", letterSpacing: "0.04em" }}>
                    <span style={{ color: "#3a3630" }}>page</span><span style={{ color: "#e08a6f" }}>birdy</span>
                  </span>
                </div>

                {/* Work section */}
                <div className="px-2 pt-3 pb-1">
                  <div style={{ fontSize: "9.5px", color: "#b0a898", letterSpacing: "0.1em", fontWeight: 600, padding: "2px 8px 6px" }}>Work</div>
                  {[
                    { label: "Dashboard", icon: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" },
                    { label: "Inbox", icon: "M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 mb-0.5">
                      <svg viewBox="0 0 24 24" fill="none" stroke="#b0a898" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d={item.icon} />
                      </svg>
                      <span style={{ fontSize: "12.5px", color: "#6b6560" }}>{item.label}</span>
                    </div>
                  ))}
                  {/* Active: Jobs */}
                  <div className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 mb-0.5" style={{ background: "#f0ece3" }}>
                    <svg viewBox="0 0 24 24" fill="none" stroke="#3a3630" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                      <line x1="9" y1="3" x2="9" y2="21" /><line x1="15" y1="3" x2="15" y2="21" />
                    </svg>
                    <span style={{ fontSize: "12.5px", color: "#1a1814", fontWeight: 600 }}>Jobs</span>
                  </div>
                </div>

                <div style={{ height: "1px", background: "#e8e2d8", margin: "6px 10px" }} />

                {/* Projects section */}
                <div className="px-2 pb-1">
                  <div style={{ fontSize: "9.5px", color: "#b0a898", letterSpacing: "0.1em", fontWeight: 600, padding: "2px 8px 6px" }}>Projects</div>
                  {[
                    { label: "Q4 Campaigns", active: true },
                    { label: "Legal Docs", active: false },
                    { label: "Brand Assets", active: false },
                    { label: "Marketing Hub", active: false },
                  ].map(p => (
                    <div key={p.label} className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 mb-0.5" style={{ background: p.active ? "rgba(224,138,111,0.1)" : "transparent" }}>
                      <svg viewBox="0 0 24 24" fill="none" stroke={p.active ? "#e08a6f" : "#b0a898"} strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      </svg>
                      <span style={{ fontSize: "12.5px", color: p.active ? "#e08a6f" : "#6b6560", fontWeight: p.active ? 600 : 400 }}>{p.label}</span>
                    </div>
                  ))}
                </div>

                <div style={{ height: "1px", background: "#e8e2d8", margin: "6px 10px" }} />

                {/* Settings */}
                <div className="px-2">
                  {[
                    { label: "Team", icon: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z" },
                    { label: "Settings", icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z" },
                  ].map(item => (
                    <div key={item.label} className="flex items-center gap-2.5 rounded-md px-2.5 py-1.5 mb-0.5">
                      <svg viewBox="0 0 24 24" fill="none" stroke="#b0a898" strokeWidth="1.75" style={{ width: "13px", height: "13px", flexShrink: 0 }}>
                        <path d={item.icon} />
                      </svg>
                      <span style={{ fontSize: "12.5px", color: "#6b6560" }}>{item.label}</span>
                    </div>
                  ))}
                </div>

                {/* User row */}
                <div className="mt-auto flex items-center gap-2.5 px-4 py-3" style={{ borderTop: "1px solid #e8e2d8" }}>
                  <div style={{ width: "26px", height: "26px", borderRadius: "50%", background: "linear-gradient(135deg,#e08a6f,#8b6fbf)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "10px", fontWeight: 700, color: "#fff", flexShrink: 0 }}>A</div>
                  <span style={{ fontSize: "12px", color: "#6b6560" }}>Alex Chen</span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="#b0a898" strokeWidth="2" style={{ width: "12px", height: "12px", marginLeft: "auto" }}>
                    <path d="m7 15 5 5 5-5M7 9l5-5 5 5" />
                  </svg>
                </div>
              </div>

              {/* ── Main area — WHITE theme ── */}
              <div className="flex flex-1 flex-col overflow-hidden" style={{ background: "#f5f3f0", borderRadius: "8px" }}>

                {/* Top bar */}
                <div className="flex items-center justify-between px-5 py-3" style={{ borderBottom: "1px solid #e2ddd6", background: "#f5f3f0" }}>
                  <div className="flex items-center gap-3">
                    <svg viewBox="0 0 24 24" fill="none" stroke="#6b6560" strokeWidth="1.75" style={{ width: "14px", height: "14px" }}>
                      <rect x="3" y="3" width="18" height="18" rx="2" ry="2" />
                      <line x1="9" y1="3" x2="9" y2="21" /><line x1="15" y1="3" x2="15" y2="21" />
                    </svg>
                    <span style={{ fontSize: "13px", fontWeight: 600, color: "#1a1814" }}>Jobs</span>
                    <span style={{ fontSize: "11px", color: "#8a8478", background: "#e8e2d8", padding: "1px 7px", borderRadius: "10px" }}>47</span>
                    <span style={{ fontSize: "11px", color: "#9a9488" }}>Translation queue for Q4 Campaigns</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <div style={{ border: "1.5px solid #d8d2c8", color: "#6b6560", fontSize: "11px", padding: "4px 12px", borderRadius: "6px", fontWeight: 500, background: "#fff" }}>Sources •</div>
                    <div style={{ background: "#e08a6f", color: "#fff", fontSize: "11px", fontWeight: 700, padding: "5px 14px", borderRadius: "6px", letterSpacing: "0.04em" }}>+ Upload</div>
                  </div>
                </div>

                {/* Filter chips */}
                <div className="flex items-center gap-1.5 px-5 py-2" style={{ borderBottom: "1px solid #e2ddd6", background: "#f5f3f0" }}>
                  {["All", "Documents", "Subtitles", "Images"].map(f => (
                    <div key={f} style={{ fontSize: "11px", color: "#8a8478", padding: "3px 10px", borderRadius: "20px", border: "1px solid #d8d2c8", cursor: "pointer" }}>{f}</div>
                  ))}
                  <div style={{ fontSize: "11px", color: "#1a1814", padding: "3px 10px", borderRadius: "20px", background: "#1a1814", border: "1px solid #1a1814", fontWeight: 600, color: "#f5f3f0" }}>Active</div>
                  <div style={{ fontSize: "11px", color: "#8a8478", padding: "3px 10px", borderRadius: "20px", border: "1px solid #d8d2c8" }}>Archived (6)</div>
                </div>

                {/* Info banner */}
                <div className="mx-4 mt-3 mb-1 flex items-start justify-between rounded-lg px-4 py-3" style={{ background: "rgba(74,112,224,0.06)", border: "1px solid rgba(74,112,224,0.2)" }}>
                  <div>
                    <div style={{ fontSize: "12px", fontWeight: 600, color: "#4a70e0" }}>✦ AI consensus check running on 3 jobs</div>
                    <div style={{ fontSize: "11px", color: "#7a90c8", marginTop: "3px" }}>OpenAI and DeepL are comparing segments. Flagged items will appear in QA Review.</div>
                  </div>
                  <span style={{ fontSize: "11px", color: "#9a9488", cursor: "pointer", flexShrink: 0, marginLeft: "16px" }}>Dismiss</span>
                </div>

                {/* Kanban columns */}
                <div className="flex flex-1 gap-3 overflow-hidden px-4 py-3" style={{ minHeight: 0, background: "#ece8e2" }}>
                  {[
                    {
                      name: "Queued", dot: "#9a9488", count: 5,
                      cards: [
                        { id: "PB-218", title: "annual_report_fr.idml", tags: ["French"], assignee: "M", date: "Dec 5" },
                        { id: "PB-217", title: "legal_terms_v2.pdf", tags: ["Arabic", "German"], assignee: "J", date: "Dec 5" },
                        { id: "PB-216", title: "product_launch.srt", tags: ["Chinese"], assignee: null, date: "Dec 4" },
                        { id: "PB-215", title: "store_banners.psd", tags: ["Spanish"], assignee: "A", date: "Dec 4" },
                      ],
                    },
                    {
                      name: "Translating", dot: "#d97706", count: 8,
                      cards: [
                        { id: "PB-214", title: "q4_campaign_deck.idml — Chinese", tags: ["Layout Agent"], assignee: "M", date: "Dec 5" },
                        { id: "PB-213", title: "product_brochure.pdf — Arabic", tags: ["Layout Agent"], assignee: "J", date: "Dec 4" },
                        { id: "PB-212", title: "marketing_video.srt — French", tags: ["Timecode Agent"], assignee: "A", date: "Dec 3" },
                        { id: "PB-211", title: "signage_package.ai — German", tags: ["OCR Agent"], assignee: "M", date: "Dec 3" },
                      ],
                    },
                    {
                      name: "QA Review", dot: "#3b82f6", count: 4,
                      cards: [
                        { id: "PB-210", title: "brand_guide.idml — Japanese", tags: ["94% match"], assignee: "J", date: "Dec 2" },
                        { id: "PB-209", title: "invoice_template.pdf — Spanish", tags: ["Flagged"], assignee: "A", date: "Dec 2", flagged: true },
                        { id: "PB-208", title: "app_screenshots.psd — Korean", tags: ["88% match"], assignee: "M", date: "Dec 1" },
                      ],
                    },
                    {
                      name: "Delivered", dot: "#16a34a", count: 30,
                      cards: [
                        { id: "PB-207", title: "homepage_copy.html — French", tags: ["Done"], assignee: "J", date: "Nov 30" },
                        { id: "PB-206", title: "manual_v3.idml — Arabic", tags: ["Done"], assignee: "A", date: "Nov 29" },
                        { id: "PB-205", title: "subtitles_ep12.srt — Chinese", tags: ["Done"], assignee: "M", date: "Nov 28" },
                        { id: "PB-204", title: "print_ad_pack.ai — German", tags: ["Done"], assignee: "J", date: "Nov 27" },
                      ],
                    },
                  ].map(col => (
                    <div key={col.name} className="flex shrink-0 flex-col" style={{ width: "232px", minWidth: "232px" }}>
                      {/* Column header */}
                      <div className="flex items-center gap-2 mb-2 px-1">
                        <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: col.dot, display: "inline-block", flexShrink: 0 }} />
                        <span style={{ fontSize: "12px", fontWeight: 600, color: "#3a3630" }}>{col.name}</span>
                        <span style={{ fontSize: "11px", color: "#9a9488" }}>{col.count}</span>
                        <span style={{ marginLeft: "auto", fontSize: "16px", color: "#b0a898", lineHeight: 1 }}>+</span>
                        <span style={{ fontSize: "14px", color: "#b0a898", lineHeight: 1 }}>···</span>
                      </div>

                      {/* Cards */}
                      <div className="flex flex-col gap-2 overflow-hidden">
                        {col.cards.map(card => (
                          <div key={card.id} style={{
                            background: "#ffffff",
                            border: `1px solid ${"flagged" in card && card.flagged ? "rgba(220,38,38,0.25)" : "#e2ddd6"}`,
                            borderRadius: "8px",
                            padding: "10px 12px",
                            boxShadow: "0 1px 3px rgba(0,0,0,0.06)",
                          }}>
                            {/* Card header */}
                            <div className="flex items-center gap-1.5 mb-1.5">
                              <svg viewBox="0 0 16 12" style={{ width: "12px", height: "10px", flexShrink: 0 }}>
                                <rect x="0" y="6" width="3" height="6" fill="#e08a6f" rx="0.5" />
                                <rect x="4.5" y="3" width="3" height="9" fill="#e08a6f" rx="0.5" opacity="0.7" />
                                <rect x="9" y="0" width="3" height="12" fill="#e08a6f" rx="0.5" opacity="0.5" />
                              </svg>
                              <span style={{ fontSize: "10px", color: "#9a9488", fontFamily: "var(--font-space-mono), monospace" }}>{card.id}</span>
                            </div>
                            <div style={{ fontSize: "12.5px", color: "#1a1814", fontWeight: 500, lineHeight: 1.35, marginBottom: "8px" }}>{card.title}</div>
                            <div className="flex flex-wrap gap-1 mb-2">
                              {card.tags.map(t => (
                                <span key={t} style={{
                                  fontSize: "10px", padding: "2px 7px", borderRadius: "4px",
                                  background: t === "Flagged" ? "#fee2e2" : t === "Done" ? "#dcfce7" : "#f0ece3",
                                  color: t === "Flagged" ? "#dc2626" : t === "Done" ? "#16a34a" : "#6b6560",
                                  border: `1px solid ${t === "Flagged" ? "#fca5a5" : t === "Done" ? "#86efac" : "#d8d2c8"}`,
                                }}>{t}</span>
                              ))}
                            </div>
                            <div className="flex items-center justify-between">
                              {card.assignee ? (
                                <div style={{ width: "20px", height: "20px", borderRadius: "50%", background: "linear-gradient(135deg,#6b9cf4,#8b6fbf)", display: "flex", alignItems: "center", justifyContent: "center", fontSize: "9px", fontWeight: 700, color: "#fff" }}>{card.assignee}</div>
                              ) : <span />}
                              <span style={{ fontSize: "10px", color: "#9a9488" }}>
                                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" style={{ width: "10px", height: "10px", display: "inline", marginRight: "3px", verticalAlign: "middle" }}>
                                  <rect x="3" y="4" width="18" height="18" rx="2" /><line x1="16" y1="2" x2="16" y2="6" /><line x1="8" y1="2" x2="8" y2="6" /><line x1="3" y1="10" x2="21" y2="10" />
                                </svg>
                                {card.date}
                              </span>
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  {/* 5th column peeking */}
                  <div className="flex shrink-0 flex-col" style={{ width: "50px", minWidth: "50px", overflow: "hidden" }}>
                    <div className="flex items-center gap-1.5 mb-2 px-1">
                      <span style={{ width: "7px", height: "7px", borderRadius: "50%", background: "#8b6fbf", display: "inline-block" }} />
                      <span style={{ fontSize: "12px", fontWeight: 600, color: "#6b6560", whiteSpace: "nowrap" }}>Do</span>
                    </div>
                    <div style={{ background: "#ffffff", border: "1px solid #e2ddd6", borderRadius: "8px", padding: "10px 12px", overflow: "hidden", boxShadow: "0 1px 3px rgba(0,0,0,0.06)" }}>
                      <svg viewBox="0 0 16 12" style={{ width: "12px", height: "10px" }}>
                        <rect x="0" y="6" width="3" height="6" fill="#8b6fbf" rx="0.5" />
                        <rect x="4.5" y="3" width="3" height="9" fill="#8b6fbf" rx="0.5" opacity="0.7" />
                        <rect x="9" y="0" width="3" height="12" fill="#8b6fbf" rx="0.5" opacity="0.5" />
                      </svg>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Bottom fade */}
            <div className="pointer-events-none absolute bottom-0 left-0 right-0" style={{
              height: "32%",
              background: "linear-gradient(to top, #080507 0%, #080507 5%, rgba(8,5,7,0.85) 40%, transparent 100%)",
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

      {/* ─── §2.5 BENTO FEATURE GRID ─── */}
      <section style={{ background: "#0a0908", position: "relative", zIndex: 20, isolation: "isolate" }}>
        <div className="mx-auto max-w-[1100px] px-8 lg:px-14" style={{ paddingTop: "80px", paddingBottom: "100px" }}>

          {/* Section header */}
          <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "12px" }}>
            <span style={{ width: "8px", height: "8px", background: "#e08a6f", display: "inline-block" }} />
            <span style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "11px", fontWeight: 700, letterSpacing: "0.16em", color: "#e08a6f", textTransform: "uppercase" }}>Platform</span>
          </div>
          <h2 className="pb-stencil" style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05, marginBottom: "48px", maxWidth: "560px" }}>
            Everything your global<br />team needs.
          </h2>

          {/* Two-column masonry */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px", alignItems: "start" }}>

            {/* ── LEFT COLUMN ── */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

              {/* Card A — Translation Agents (PURPLE) */}
              <div style={{ background: "#2a1060", border: "1px solid rgba(139,111,191,0.3)", borderRadius: "16px", padding: "28px", overflow: "hidden", position: "relative" }}>
                <div style={{ position: "absolute", top: 0, right: 0, width: "280px", height: "280px", background: "radial-gradient(ellipse at top right, rgba(139,111,191,0.25), transparent 70%)", pointerEvents: "none" }} />
                <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "#b89fe8", textTransform: "uppercase", marginBottom: "14px" }}>Translation Agents</div>
                <div style={{ fontSize: "22px", fontWeight: 700, color: "#f0ece3", marginBottom: "8px" }}>Specialist agents.<br />One for every format.</div>
                <div style={{ fontSize: "13px", color: "rgba(240,236,227,0.5)", lineHeight: 1.7, marginBottom: "24px" }}>Each format gets a dedicated parser. Layout, timecode, OCR — purpose-built, not generic.</div>
                {[
                  { color: "#e08a6f", name: "Layout Agent",    fmt: ".idml  .pdf",    detail: "Rebuilds frames, styles, masters" },
                  { color: "#8b6fbf", name: "Timecode Agent",  fmt: ".srt  .vtt",     detail: "Syncs every cue to its timecode" },
                  { color: "#4a9e8a", name: "OCR Agent",       fmt: ".psd  .ai  .eps", detail: "Reads + renders text in images" },
                  { color: "#4a70e0", name: "Web Agent",       fmt: ".html  .md",     detail: "Translates content, keeps markup" },
                ].map(a => (
                  <div key={a.name} style={{ display: "flex", alignItems: "center", gap: "12px", background: "#3a1878", border: "1px solid #4a2090", borderRadius: "10px", padding: "10px 14px", marginBottom: "8px" }}>
                    <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: a.color, flexShrink: 0 }} />
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontSize: "12.5px", fontWeight: 600, color: "rgba(240,236,227,0.88)" }}>{a.name}</div>
                      <div style={{ fontSize: "10.5px", color: "rgba(240,236,227,0.38)", marginTop: "1px" }}>{a.detail}</div>
                    </div>
                    <span style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "9.5px", color: a.color, background: "#3d1880", border: `1px solid ${a.color}50`, padding: "2px 8px", borderRadius: "4px", flexShrink: 0 }}>{a.fmt}</span>
                  </div>
                ))}
              </div>

              {/* Card B — Workflow node diagram (DARK DOTTED) */}
              <div style={{ background: "#161616", border: "1px solid rgba(255,255,255,0.09)", borderRadius: "16px", padding: "28px", overflow: "hidden", position: "relative", backgroundImage: "radial-gradient(rgba(255,255,255,0.055) 1px, transparent 1px)", backgroundSize: "22px 22px" }}>
                <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(255,255,255,0.3)", textTransform: "uppercase", marginBottom: "20px" }}>Translation workflow</div>
                <div style={{ display: "flex", alignItems: "center", gap: "0" }}>
                  {/* Trigger */}
                  <div style={{ background: "#1a1a1a", border: "1px solid rgba(255,255,255,0.12)", borderRadius: "10px", padding: "12px 16px", minWidth: "110px" }}>
                    <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "9px", color: "rgba(255,255,255,0.35)", letterSpacing: "0.1em", marginBottom: "6px" }}>TRIGGER</div>
                    <div style={{ display: "flex", alignItems: "center", gap: "6px" }}>
                      <span style={{ width: "18px", height: "18px", borderRadius: "4px", background: "#1a3828", border: "1px solid rgba(74,222,128,0.5)", display: "flex", alignItems: "center", justifyContent: "center" }}>
                        <svg viewBox="0 0 12 12" fill="#4ade80" style={{ width: "8px", height: "8px" }}><polygon points="3,2 10,6 3,10" /></svg>
                      </span>
                      <div>
                        <div style={{ fontSize: "10.5px", fontWeight: 600, color: "#f0ece3" }}>START</div>
                        <div style={{ fontSize: "9px", color: "rgba(255,255,255,0.35)" }}>File upload</div>
                      </div>
                    </div>
                  </div>
                  {/* Arrow */}
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.15)", margin: "0 6px", position: "relative" }}>
                    <div style={{ position: "absolute", right: "-4px", top: "-3px", width: "7px", height: "7px", borderTop: "1.5px solid rgba(255,255,255,0.3)", borderRight: "1.5px solid rgba(255,255,255,0.3)", transform: "rotate(45deg)" }} />
                  </div>
                  {/* Steps */}
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px" }}>
                    {[
                      { icon: "✦", color: "#8b6fbf", label: "AGENT", sub: "AI Translate" },
                      { icon: "◈", color: "#4a9e8a", label: "TOOL",  sub: "QA Check" },
                    ].map(s => (
                      <div key={s.label} style={{ background: "#1a1a1a", border: `1px solid ${s.color}35`, borderRadius: "8px", padding: "8px 12px", display: "flex", alignItems: "center", gap: "8px" }}>
                        <span style={{ fontSize: "12px", color: s.color }}>{s.icon}</span>
                        <div>
                          <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "9px", color: "rgba(255,255,255,0.3)", letterSpacing: "0.1em" }}>{s.label}</div>
                          <div style={{ fontSize: "11px", fontWeight: 600, color: "#f0ece3" }}>{s.sub}</div>
                        </div>
                      </div>
                    ))}
                  </div>
                  {/* Arrow */}
                  <div style={{ flex: 1, height: "1px", background: "rgba(255,255,255,0.15)", margin: "0 6px", position: "relative" }}>
                    <div style={{ position: "absolute", right: "-4px", top: "-3px", width: "7px", height: "7px", borderTop: "1.5px solid rgba(255,255,255,0.3)", borderRight: "1.5px solid rgba(255,255,255,0.3)", transform: "rotate(45deg)" }} />
                  </div>
                  {/* Send */}
                  <div style={{ background: "#1a1a1a", border: "1px solid rgba(74,112,224,0.3)", borderRadius: "10px", padding: "12px 16px", minWidth: "100px" }}>
                    <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "9px", color: "rgba(74,112,224,0.7)", letterSpacing: "0.1em", marginBottom: "4px" }}>DELIVER</div>
                    <div style={{ fontSize: "11px", fontWeight: 600, color: "#f0ece3" }}>Translated</div>
                    <div style={{ fontSize: "9.5px", color: "rgba(255,255,255,0.35)" }}>Same format</div>
                  </div>
                </div>
              </div>

              {/* Card C — Industries (OLIVE/GREEN) */}
              <div style={{ background: "#162818", border: "1px solid rgba(90,158,90,0.3)", borderRadius: "16px", padding: "28px" }}>
                <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(90,158,90,0.7)", textTransform: "uppercase", marginBottom: "18px" }}>Industries</div>
                <div style={{ fontSize: "18px", fontWeight: 700, color: "#f0ece3", marginBottom: "18px" }}>Every team that ships globally.</div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "8px" }}>
                  {[
                    { color: "#e08a6f", label: "Marketing Agencies" },
                    { color: "#c8a820", label: "Publishers & Magazines" },
                    { color: "#4a9e8a", label: "Legal & Compliance" },
                    { color: "#8b6fbf", label: "Film & Subtitle Studios" },
                    { color: "#5a9e5a", label: "Product & SaaS Teams" },
                    { color: "#4a70e0", label: "E-commerce Brands" },
                  ].map(u => (
                    <div key={u.label} style={{ display: "flex", alignItems: "center", gap: "8px", background: "#1e3520", borderRadius: "8px", padding: "8px 10px" }}>
                      <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: u.color, flexShrink: 0 }} />
                      <span style={{ fontSize: "11.5px", color: "rgba(240,236,227,0.65)", lineHeight: 1.3 }}>{u.label}</span>
                    </div>
                  ))}
                </div>
              </div>

            </div>

            {/* ── RIGHT COLUMN ── */}
            <div style={{ display: "flex", flexDirection: "column", gap: "12px" }}>

              {/* Top row: 2 small cards */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {/* Card D — Languages stat */}
                <div style={{ background: "#0e2240", border: "1px solid rgba(74,112,224,0.3)", borderRadius: "16px", padding: "28px 24px" }}>
                  <div style={{ fontSize: "56px", fontWeight: 700, color: "#4a70e0", lineHeight: 1, marginBottom: "4px" }}>40+</div>
                  <div style={{ fontSize: "15px", fontWeight: 700, color: "#f0ece3", marginBottom: "8px" }}>Languages</div>
                  <div style={{ fontSize: "12px", color: "rgba(240,236,227,0.45)", lineHeight: 1.6 }}>Arabic, Chinese, RTL — all handled natively.</div>
                  <div style={{ marginTop: "16px", display: "flex", flexWrap: "wrap", gap: "4px" }}>
                    {["AR","ZH","JA","DE","FR","ES","PT","RU"].map(l => (
                      <span key={l} style={{ fontSize: "9.5px", fontFamily: "var(--font-space-mono),monospace", color: "#7a9ee8", background: "#162d52", padding: "2px 6px", borderRadius: "3px" }}>{l}</span>
                    ))}
                  </div>
                </div>
                {/* Card E — Async (PINK/MAGENTA) */}
                <div style={{ background: "#3a0e22", border: "1px solid rgba(200,70,120,0.3)", borderRadius: "16px", padding: "28px 24px" }}>
                  <div style={{ fontSize: "28px", marginBottom: "10px" }}>⟳</div>
                  <div style={{ fontSize: "15px", fontWeight: 700, color: "#f0ece3", marginBottom: "8px" }}>It keeps going.</div>
                  <div style={{ fontSize: "13px", fontWeight: 600, color: "#d64882", marginBottom: "8px" }}>Runs and finishes on its own.</div>
                  <div style={{ fontSize: "12px", color: "rgba(240,236,227,0.45)", lineHeight: 1.6 }}>Upload and go. Translation runs in the background. File lands in your inbox.</div>
                </div>
              </div>

              {/* Card F — Integrations (DARK TEAL/BLUE) */}
              <div style={{ background: "#0c2030", border: "1px solid rgba(74,158,138,0.3)", borderRadius: "16px", padding: "28px" }}>
                <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(74,158,138,0.7)", textTransform: "uppercase", marginBottom: "14px" }}>Integrations</div>
                <div style={{ fontSize: "20px", fontWeight: 700, color: "#f0ece3", marginBottom: "8px" }}>Works with your stack.</div>
                <div style={{ fontSize: "13px", color: "rgba(240,236,227,0.48)", lineHeight: 1.65, marginBottom: "20px" }}>
                  Translated files open directly in InDesign, Premiere, WordPress. No re-linking. No conversion. No broken layers.
                </div>
                <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "6px" }}>
                  {[
                    { name: "Adobe InDesign",    live: true  },
                    { name: "Adobe Illustrator", live: true  },
                    { name: "Adobe Photoshop",   live: true  },
                    { name: "YouTube Studio",    live: true  },
                    { name: "Premiere Pro",      live: true  },
                    { name: "Final Cut Pro",     live: false },
                    { name: "WordPress",         live: false },
                    { name: "Slack",             live: false },
                  ].map(i => (
                    <div key={i.name} style={{ display: "flex", alignItems: "center", gap: "7px", background: i.live ? "#133a2e" : "#0f2535", border: `1px solid ${i.live ? "#1d5040" : "#163040"}`, borderRadius: "8px", padding: "8px 10px" }}>
                      <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: i.live ? "#4a9e8a" : "rgba(255,255,255,0.2)", flexShrink: 0 }} />
                      <span style={{ fontSize: "11.5px", color: i.live ? "rgba(240,236,227,0.72)" : "rgba(240,236,227,0.32)" }}>{i.name}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Bottom row: 2 cards */}
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "12px" }}>
                {/* Card G — QA Consensus (DARK INDIGO) */}
                <div style={{ background: "#12123c", border: "1px solid rgba(74,112,224,0.28)", borderRadius: "16px", padding: "24px" }}>
                  <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(74,112,224,0.6)", textTransform: "uppercase", marginBottom: "14px" }}>Quality</div>
                  <div style={{ fontSize: "16px", fontWeight: 700, color: "#f0ece3", marginBottom: "8px" }}>Two engines.<br />One consensus.</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: "6px", marginTop: "16px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#241840", border: "1px solid #382255", borderRadius: "7px", padding: "8px 10px" }}>
                      <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#e08a6f" }} />
                      <span style={{ fontSize: "11px", fontFamily: "var(--font-space-mono),monospace", color: "#e08a6f" }}>OpenAI GPT</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#181848", border: "1px solid #222260", borderRadius: "7px", padding: "8px 10px" }}>
                      <span style={{ width: "5px", height: "5px", borderRadius: "50%", background: "#4a70e0" }} />
                      <span style={{ fontSize: "11px", fontFamily: "var(--font-space-mono),monospace", color: "#4a70e0" }}>DeepL Neural</span>
                    </div>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "#162040", border: "1px solid #1e3050", borderRadius: "7px", padding: "8px 10px" }}>
                      <span style={{ fontSize: "11px", color: "#4ade80" }}>✓</span>
                      <span style={{ fontSize: "11px", fontFamily: "var(--font-space-mono),monospace", color: "#4ade80" }}>Consensus — ships</span>
                    </div>
                  </div>
                </div>
                {/* Card H — Formats + Glossary (AMBER) */}
                <div style={{ background: "#261a08", border: "1px solid rgba(200,168,32,0.3)", borderRadius: "16px", padding: "24px" }}>
                  <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "10px", fontWeight: 700, letterSpacing: "0.14em", color: "rgba(200,168,32,0.6)", textTransform: "uppercase", marginBottom: "14px" }}>Formats</div>
                  <div style={{ fontSize: "48px", fontWeight: 700, color: "#c8a820", lineHeight: 1, marginBottom: "4px" }}>8</div>
                  <div style={{ fontSize: "14px", fontWeight: 700, color: "#f0ece3", marginBottom: "14px" }}>Native formats.</div>
                  <div style={{ display: "flex", flexWrap: "wrap", gap: "5px", marginBottom: "16px" }}>
                    {[".idml",".pdf",".srt",".vtt",".ai",".psd",".eps",".html"].map(f => (
                      <span key={f} style={{ fontSize: "9.5px", fontFamily: "var(--font-space-mono),monospace", color: "#c8a820", background: "#342210", border: "1px solid #4a3018", padding: "2px 7px", borderRadius: "4px" }}>{f}</span>
                    ))}
                  </div>
                  <div style={{ height: "1px", background: "#342210", marginBottom: "14px" }} />
                  <div style={{ fontSize: "11.5px", fontWeight: 600, color: "rgba(240,236,227,0.65)", marginBottom: "4px" }}>Lock brand terms.</div>
                  <div style={{ fontFamily: "var(--font-space-mono),monospace", fontSize: "9.5px", color: "#8a7040", background: "#342210", borderRadius: "5px", padding: "5px 8px" }}>glossary.csv → 48 locked terms</div>
                </div>
              </div>

            </div>
          </div>
        </div>
      </section>


      {/* ─── §4 PRODUCT DIAGRAMS ─── */}
      <ProductDiagram />
      <IntegrationFlow />


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
