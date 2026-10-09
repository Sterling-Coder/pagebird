import Link from "next/link";
import ClosingBand from "@/components/ClosingBand";

const INTEGRATIONS = [
  {
    category: "Print & Layout",
    color: "#e08a6f",
    items: [
      {
        name: "Adobe InDesign",
        desc: "Open translated IDML directly. No re-linking assets, no broken styles, no manual fixes.",
        detail: "Export your IDML from InDesign, upload to Pagebirdy, get back a translated IDML. Open it — every frame, style, master page, and linked asset is intact.",
        formats: [".idml"],
        soon: false,
      },
      {
        name: "Adobe Illustrator",
        desc: "Translated .ai files ready to open and edit. Text layers preserved.",
        detail: "Upload an .ai file with live text. Pagebirdy translates the text in place, maintaining point type, area type, and text on path.",
        formats: [".ai"],
        soon: false,
      },
      {
        name: "Adobe Photoshop",
        desc: "Text layers translated in place. PSD layer structure untouched.",
        detail: "Each text layer gets translated independently. Layer names, blending modes, smart objects — nothing moves.",
        formats: [".psd"],
        soon: false,
      },
    ],
  },
  {
    category: "Video & Subtitles",
    color: "#c94040",
    items: [
      {
        name: "YouTube Studio",
        desc: "Upload translated SRT directly to your video. Captions live in minutes.",
        detail: "Paste your YouTube URL, pick a target language, download the translated SRT. Upload it straight to YouTube Studio — no timecode drift, no reformatting.",
        formats: [".srt"],
        soon: false,
      },
      {
        name: "Adobe Premiere Pro",
        desc: "Import .srt and .vtt caption tracks into your timeline.",
        detail: "Translated subtitle files drop straight into Premiere's captions panel. Timecodes are preserved to the millisecond.",
        formats: [".srt", ".vtt"],
        soon: false,
      },
      {
        name: "Final Cut Pro",
        desc: "Import translated captions via .srt or .vtt.",
        detail: "Final Cut reads .srt natively. Translate once, import into any project.",
        formats: [".srt", ".vtt"],
        soon: false,
      },
    ],
  },
  {
    category: "Web & CMS",
    color: "#5a9e5a",
    items: [
      {
        name: "WordPress",
        desc: "Paste translated HTML into any page builder or block editor.",
        detail: "Export your page HTML, translate it, paste back in. Works with Elementor, Divi, Gutenberg — any builder that edits raw HTML.",
        formats: [".html"],
        soon: false,
      },
      {
        name: "Webflow",
        desc: "Export HTML from Webflow, translate, re-import.",
        detail: "Webflow's HTML export keeps class names and structure intact. Pagebirdy translates the text content only — your layout never changes.",
        formats: [".html"],
        soon: true,
      },
      {
        name: "Shopify",
        desc: "Translate product pages and store content.",
        detail: "Export product descriptions and page content as HTML, translate, import back. Works with Shopify's native translation settings.",
        formats: [".html"],
        soon: true,
      },
    ],
  },
  {
    category: "Productivity",
    color: "#8b6fbf",
    items: [
      {
        name: "Figma",
        desc: "Export frames as SVG or HTML, translate text, re-import.",
        detail: "Figma's SVG export carries text as live nodes. Translate them, bring the SVG back in, and your layout is identical — just in a new language.",
        formats: [".svg"],
        soon: true,
      },
      {
        name: "Notion",
        desc: "Translate docs and pages exported as HTML or Markdown.",
        detail: "Export any Notion page to HTML. Pagebirdy translates the content while preserving headings, tables, callouts, and toggles.",
        formats: [".html"],
        soon: true,
      },
      {
        name: "Slack",
        desc: "Trigger translations directly from your workspace.",
        detail: "Send a file link to the Pagebirdy bot in Slack. Get a translated file back in the thread — no context switching.",
        formats: [],
        soon: true,
      },
    ],
  },
];

export default function IntegrationsPage() {
  return (
    <div style={{ background: "#0c0b09", minHeight: "100vh" }}>

      {/* Hero */}
      <section style={{
        background: "linear-gradient(180deg, #0d3a52 0%, #0f4a68 4%, #1a5a80 8%, #1f6b95 14%, #2178a8 20%, #1e7fb3 28%, #1b86b5 36%, #1a7faa 46%, #176fa0 56%, #145a95 66%, #0f4578 76%, #0a2e52 86%, #050a18 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        paddingTop: "120px",
        paddingBottom: "80px",
      }}>
        <div className="mx-auto max-w-[1100px] px-8 lg:px-14">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Integrations</span>
          </div>
          <h1 className="pb-stencil pb-enter" style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)", lineHeight: 1.0, maxWidth: "700px" }}>
            Works with the<br />tools you already use.
          </h1>
          <p className="pb-enter pb-enter-delay-1 mt-6 max-w-xl text-[16px] leading-relaxed text-pb-text-muted">
            Pagebirdy reads and writes native file formats. No export step, no conversion, no re-linking. Open the translated file exactly where you left off.
          </p>
          <div className="pb-enter pb-enter-delay-2 mt-10 flex flex-wrap gap-3">
            {["Adobe CC", "YouTube", "Premiere", "WordPress", "Figma", "Slack"].map(t => (
              <span key={t} className="font-pb-mono rounded-full border border-white/10 px-4 py-1.5 text-[11px] text-pb-text-muted">
                {t}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* Integration categories */}
      {INTEGRATIONS.map((cat, ci) => (
        <section key={cat.category} style={{
          borderBottom: "1px solid rgba(255,255,255,0.04)",
          background: ci % 2 === 0 ? "#0c0b09" : "#0e0d0b",
        }}>
          <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-20">
            {/* Category header */}
            <div className="mb-10 flex items-center gap-4">
              <div style={{ width: "3px", height: "28px", background: cat.color, borderRadius: "2px" }} />
              <h2 className="font-pb-mono text-[22px] font-bold text-pb-text">{cat.category}</h2>
            </div>

            {/* Items grid */}
            <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
              {cat.items.map((item) => (
                <div key={item.name} style={{
                  background: "#131210",
                  border: `1px solid ${item.soon ? "rgba(255,255,255,0.06)" : `${cat.color}25`}`,
                  borderRadius: "10px",
                  padding: "24px",
                  opacity: item.soon ? 0.6 : 1,
                  position: "relative",
                  overflow: "hidden",
                }}>
                  {/* Color glow top */}
                  {!item.soon && (
                    <div style={{
                      position: "absolute", top: 0, left: 0, right: 0, height: "2px",
                      background: cat.color,
                    }} />
                  )}

                  <div className="flex items-start justify-between mb-3">
                    <h3 style={{ fontSize: "16px", fontWeight: 700, color: "#f0ece3" }}>{item.name}</h3>
                    {item.soon ? (
                      <span className="font-pb-mono rounded-full border border-white/10 px-2 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">Soon</span>
                    ) : (
                      <span className="font-pb-mono rounded-full border px-2 py-0.5 text-[8px] tracking-widest uppercase" style={{ color: cat.color, borderColor: `${cat.color}50` }}>Live</span>
                    )}
                  </div>

                  <p style={{ fontSize: "13px", color: "rgba(240,236,227,0.55)", lineHeight: 1.6, marginBottom: "14px" }}>
                    {item.desc}
                  </p>

                  <p style={{ fontSize: "12px", color: "rgba(240,236,227,0.35)", lineHeight: 1.6, marginBottom: "16px" }}>
                    {item.detail}
                  </p>

                  {item.formats.length > 0 && (
                    <div className="flex flex-wrap gap-1.5">
                      {item.formats.map(f => (
                        <span key={f} className="font-pb-mono rounded px-2 py-0.5 text-[10px]" style={{
                          background: `${cat.color}12`,
                          color: cat.color,
                          border: `1px solid ${cat.color}30`,
                        }}>{f}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        </section>
      ))}

      {/* API section teaser */}
      <section style={{ background: "#0e0d0b", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-20">
          <div className="grid grid-cols-1 gap-12 lg:grid-cols-2 items-center">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2 bg-pb-accent" />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">API Access</span>
              </div>
              <h2 className="pb-stencil" style={{ fontSize: "clamp(1.8rem,3vw,2.8rem)", lineHeight: 1.05 }}>
                Build it into<br />your pipeline.
              </h2>
              <p className="mt-6 text-[15px] leading-relaxed text-pb-text-muted max-w-md">
                Automate translation jobs, poll job status, and download results — all via REST. Fits any CI/CD or publishing workflow.
              </p>
              <div className="mt-8 flex gap-3">
                <Link href="/contact" className="font-pb-mono rounded-full bg-pb-accent px-6 py-2.5 text-[11px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110">
                  Join waitlist →
                </Link>
                <span className="font-pb-mono rounded-full border border-white/10 px-6 py-2.5 text-[11px] text-pb-text-muted">Coming soon</span>
              </div>
            </div>

            {/* Code mock */}
            <div style={{
              background: "#0a0908", borderRadius: "10px", padding: "24px",
              border: "1px solid rgba(255,255,255,0.08)",
              fontFamily: "var(--font-space-mono), monospace",
            }}>
              <div className="flex items-center gap-2 mb-4">
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#ff5f57" }} />
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#febc2e" }} />
                <div style={{ width: "10px", height: "10px", borderRadius: "50%", background: "#28c840" }} />
              </div>
              <div style={{ fontSize: "11px", lineHeight: 1.8 }}>
                <div style={{ color: "rgba(255,255,255,0.3)" }}># Upload a file</div>
                <div><span style={{ color: "#e08a6f" }}>POST</span> <span style={{ color: "rgba(255,255,255,0.7)" }}>/v1/jobs</span></div>
                <div style={{ color: "rgba(255,255,255,0.3)", marginTop: "8px" }}># Poll status</div>
                <div><span style={{ color: "#4a70e0" }}>GET</span> <span style={{ color: "rgba(255,255,255,0.7)" }}>/v1/jobs/&#123;id&#125;</span></div>
                <div style={{ color: "rgba(255,255,255,0.3)", marginTop: "8px" }}># Download result</div>
                <div><span style={{ color: "#4ade80" }}>GET</span> <span style={{ color: "rgba(255,255,255,0.7)" }}>/v1/jobs/&#123;id&#125;/download</span></div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* CTA */}
      <ClosingBand
        color="#b0306a"
        title={<>Your workflow,<br />40+ languages.</>}
        sub="Open the translated file in the app it came from."
        cta="Translate free"
        href="/login"
      />
    </div>
  );
}
