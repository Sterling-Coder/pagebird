import Link from "next/link";
import { WatchDemoButton } from "@/components/WatchDemoButton";
import ProductDiagram from "@/components/ProductDiagram";
import IntegrationFlow from "@/components/IntegrationFlow";
import PlatformBento from "@/components/PlatformBento";
import ExtensionSection from "@/components/ExtensionSection";

const FORMATS_EXTENDED = [
  { label: ".idml", soon: false },
  { label: ".pdf", soon: false },
  { label: ".ai", soon: false },
  { label: ".psd", soon: false },
  { label: ".eps", soon: false },
  { label: ".srt", soon: false },
  { label: ".vtt", soon: false },
  { label: ".html", soon: false },
  { label: ".docx", soon: false },
  { label: ".pptx", soon: false },
  { label: ".xlsx", soon: false },
  { label: ".txt", soon: false },
  { label: ".png", soon: false },
  { label: ".jpg", soon: false },
  { label: ".webp", soon: false },
  { label: ".xliff", soon: true },
  { label: ".indd", soon: true },
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
                  <div style={{ fontSize: "11px", padding: "3px 10px", borderRadius: "20px", background: "#1a1814", border: "1px solid #1a1814", fontWeight: 600, color: "#f5f3f0" }}>Active</div>
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

      {/* ─── §2 PLATFORM ─── */}
      <PlatformBento />
      <ExtensionSection />


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
