import Link from "next/link";
import ClosingBand from "@/components/ClosingBand";

// Plain dark: one solid ground, hairline rules instead of boxes, colour only as solid fills.
const BG = "#0e0d0c";
const RULE = "#2a2826";
const TEXT = "#f0ece3";
const SECONDARY = "#a8a49a";
const MUTED = "#8a8478";
const CORAL = "#e08a6f";
const PURPLE = "#8b6fbf";
const TEAL = "#4fc4a8";
const BLUE = "#6f9cff";
const PRIMARY = "#c86018";

const INTEGRATIONS = [
  {
    category: "Print & Layout",
    color: CORAL,
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
    color: BLUE,
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
    color: TEAL,
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
    color: PURPLE,
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
    <div style={{ background: BG, minHeight: "100vh" }}>
      {/* Hero */}
      <section style={{ borderBottom: `1px solid ${RULE}` }}>
        <div className="mx-auto max-w-[1100px] px-4 pt-28 pb-16 sm:px-8 lg:px-14 lg:pt-36 lg:pb-20">
          <span className="pb-enter-label text-[12px] font-semibold tracking-[0.15em] uppercase" style={{ color: CORAL }}>
            Integrations
          </span>
          <h1
            className="pb-enter mt-5 font-semibold tracking-[-0.02em]"
            style={{ fontSize: "clamp(2.25rem, 5vw, 4rem)", lineHeight: 1.05, maxWidth: "720px", color: TEXT, textWrap: "balance" }}
          >
            Works with the tools you already use.
          </h1>
          <p className="pb-enter pb-enter-delay-1 mt-6 max-w-xl text-[17px] leading-relaxed" style={{ color: SECONDARY }}>
            Pagebirdy reads and writes native file formats. No export step, no conversion, no re-linking. Open the
            translated file exactly where you left off.
          </p>
          <ul className="pb-enter pb-enter-delay-2 mt-10 flex flex-wrap gap-x-6 gap-y-3">
            {INTEGRATIONS.map((cat) => (
              <li key={cat.category}>
                <a href={`#${slug(cat.category)}`} className="flex items-center gap-2 text-[14px] transition-colors hover:text-[#f0ece3]" style={{ color: SECONDARY }}>
                  <span aria-hidden className="h-2 w-2 rounded-full" style={{ background: cat.color }} />
                  {cat.category}
                </a>
              </li>
            ))}
          </ul>
        </div>
      </section>

      {/* Integration categories: category on the left, a ruled list of tools on the right */}
      {INTEGRATIONS.map((cat) => {
        const live = cat.items.filter((i) => !i.soon).length;
        return (
          <section key={cat.category} id={slug(cat.category)} className="scroll-mt-20" style={{ borderBottom: `1px solid ${RULE}` }}>
            <div className="mx-auto grid max-w-[1100px] grid-cols-1 gap-8 px-4 py-14 sm:px-8 lg:grid-cols-[260px_minmax(0,1fr)] lg:gap-16 lg:px-14 lg:py-20">
              <div className="lg:sticky lg:top-28 lg:self-start">
                <div className="flex items-center gap-3">
                  <span aria-hidden className="h-3 w-3 rounded-full" style={{ background: cat.color }} />
                  <h2 className="text-[22px] font-semibold tracking-tight" style={{ color: TEXT }}>{cat.category}</h2>
                </div>
                <p className="mt-2 text-[13px]" style={{ color: MUTED }}>
                  {live} live{cat.items.length > live ? ` · ${cat.items.length - live} coming soon` : ""}
                </p>
              </div>

              <ul className="min-w-0">
                {cat.items.map((item, i) => (
                  <li
                    key={item.name}
                    className="grid grid-cols-1 gap-x-10 gap-y-3 py-6 md:grid-cols-[minmax(0,1fr)_minmax(0,1.2fr)]"
                    style={{ borderTop: i === 0 ? "none" : `1px solid ${RULE}`, paddingTop: i === 0 ? 0 : undefined }}
                  >
                    <div className="min-w-0">
                      <div className="flex flex-wrap items-center gap-x-3 gap-y-1">
                        <h3 className="text-[17px] font-semibold" style={{ color: item.soon ? SECONDARY : TEXT }}>{item.name}</h3>
                        {item.soon ? (
                          <span className="text-[12px]" style={{ color: MUTED }}>Coming soon</span>
                        ) : (
                          <span className="rounded-full px-2 py-0.5 text-[11px] font-semibold" style={{ background: cat.color, color: BG }}>Live</span>
                        )}
                      </div>
                      <p className="mt-2 text-[14px] leading-relaxed" style={{ color: SECONDARY }}>{item.desc}</p>
                    </div>
                    <div className="min-w-0">
                      <p className="text-[13.5px] leading-relaxed" style={{ color: MUTED }}>{item.detail}</p>
                      {item.formats.length > 0 ? (
                        <p className="font-pb-mono mt-3 text-[12px]" style={{ color: item.soon ? MUTED : cat.color }}>
                          {item.formats.join("  ")}
                        </p>
                      ) : null}
                    </div>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        );
      })}

      {/* API section teaser */}
      <section style={{ borderBottom: `1px solid ${RULE}` }}>
        <div className="mx-auto grid max-w-[1100px] grid-cols-1 items-center gap-12 px-4 py-16 sm:px-8 lg:grid-cols-2 lg:px-14 lg:py-20">
          <div>
            <span className="text-[12px] font-semibold tracking-[0.15em] uppercase" style={{ color: CORAL }}>API access</span>
            <h2 className="mt-5 font-semibold tracking-[-0.02em]" style={{ fontSize: "clamp(1.8rem,3vw,2.6rem)", lineHeight: 1.08, color: TEXT }}>
              Build it into your pipeline.
            </h2>
            <p className="mt-6 max-w-md text-[15px] leading-relaxed" style={{ color: SECONDARY }}>
              Automate translation jobs, poll job status, and download results, all via REST. Fits any CI/CD or
              publishing workflow.
            </p>
            <div className="mt-8 flex flex-wrap items-center gap-5">
              <Link
                href="/contact"
                className="rounded-full px-6 py-2.5 text-[14px] font-semibold text-white transition-[filter] hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08a6f]"
                style={{ background: PRIMARY }}
              >
                Join the waitlist
              </Link>
              <span className="text-[13px]" style={{ color: MUTED }}>Coming soon</span>
            </div>
          </div>

          {/* Endpoints as a ruled list, not a code window */}
          <dl className="font-pb-mono min-w-0 text-[13px]">
            {[
              ["Upload a file", "POST", "/v1/jobs", CORAL],
              ["Poll status", "GET", "/v1/jobs/{id}", BLUE],
              ["Download result", "GET", "/v1/jobs/{id}/download", TEAL],
            ].map(([label, verb, path, color], i) => (
              <div key={path} className="flex flex-col gap-1 py-4" style={{ borderTop: i === 0 ? "none" : `1px solid ${RULE}` }}>
                <dt className="text-[11px] tracking-widest uppercase" style={{ color: MUTED }}>{label}</dt>
                <dd className="flex min-w-0 items-center gap-3">
                  <span className="shrink-0 rounded px-1.5 py-0.5 text-[11px] font-bold" style={{ background: color, color: BG }}>{verb}</span>
                  <span className="truncate" style={{ color: TEXT }}>{path}</span>
                </dd>
              </div>
            ))}
          </dl>
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

function slug(s: string) {
  return s.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "");
}
