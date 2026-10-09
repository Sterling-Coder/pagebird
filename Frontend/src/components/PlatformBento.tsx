import type { ReactNode } from "react";

type CardProps = {
  title: string;
  desc: string;
  /** Card fill; leave out for the neutral, outlined card. */
  bg?: string;
  /** Title and description colour on a coloured card. */
  hue?: string;
  className?: string;
  /** Text on the left, panel on the right, instead of text above the panel. */
  side?: boolean;
  /** Width of the text column on a side card. */
  textWidth?: string;
  children: ReactNode;
};

const NEUTRAL = "#1d1c1a";
const PANEL = "#1f1e1c";
const PANEL_ON_NEUTRAL = "#292826";

/** A bento card. The inner panel bleeds off the card's right and bottom edges,
 * so each card reads as a window onto a larger screen. */
function Card({ title, desc, bg, hue, className = "", side = false, textWidth = "36%", children }: CardProps) {
  const neutral = !bg;
  return (
    <div
      className={`flex flex-col overflow-hidden rounded-[24px] ${side ? "md:flex-row" : ""} ${className}`}
      style={{
        background: bg ?? NEUTRAL,
        border: neutral ? "1px solid rgba(255,255,255,0.08)" : undefined,
      }}
    >
      <div
        className={`p-6 ${side ? "md:shrink-0 md:basis-[var(--pb-text-w)]" : "pb-0"}`}
        style={side ? ({ "--pb-text-w": textWidth } as React.CSSProperties) : undefined}
      >
        <h3 className="text-[15px]" style={{ color: neutral ? "#f0ece3" : hue }}>{title}</h3>
        <p className="mt-2 text-[14px] leading-relaxed" style={{ color: neutral ? "#a8a49a" : hue, opacity: neutral ? 1 : 0.85 }}>
          {desc}
        </p>
      </div>
      <div
        className={`mt-5 flex-1 rounded-tl-[16px] p-4 text-[#f0ece3] ${side ? "ml-6 md:mt-6 md:ml-0" : "ml-6"}`}
        style={{ background: neutral ? PANEL_ON_NEUTRAL : PANEL }}
      >
        {children}
      </div>
    </div>
  );
}

function Chip({ children, color }: { children: ReactNode; color: string }) {
  return (
    <span
      className="font-pb-mono rounded-md px-2 py-0.5 text-[11px]"
      style={{ color, background: `${color}22`, border: `1px solid ${color}44` }}
    >
      {children}
    </span>
  );
}

const AGENTS = [
  { name: "Layout agent", note: "Rebuilds frames, styles and masters", fmt: ".idml .pdf", color: "#e08a6f" },
  { name: "Timecode agent", note: "Keeps every cue on its timecode", fmt: ".srt .vtt", color: "#a98bf0" },
  { name: "Office agent", note: "Keeps styles, links and formulas in place", fmt: ".docx .pptx .xlsx", color: "#f0b429" },
  { name: "OCR agent", note: "Reads and re-renders text in images", fmt: ".png .jpg .webp .psd .ai", color: "#4fc4a8" },
  { name: "Web agent", note: "Translates a public page, keeps the markup", fmt: "URL .html", color: "#6f9cff" },
];

const LANGS = [
  { code: "AR", name: "Arabic", note: "Right-to-left, mirrored" },
  { code: "ZH", name: "Chinese", note: "Simplified and Traditional" },
  { code: "JA", name: "Japanese", note: "" },
  { code: "DE", name: "German", note: "" },
  { code: "FR", name: "French", note: "" },
  { code: "ES", name: "Spanish", note: "" },
];

const FORMATS = [
  { f: ".idml", soon: false },
  { f: ".pdf", soon: false },
  { f: ".ai", soon: false },
  { f: ".psd", soon: false },
  { f: ".eps", soon: false },
  { f: ".srt", soon: false },
  { f: ".vtt", soon: false },
  { f: ".html", soon: false },
  { f: ".docx", soon: false },
  { f: ".pptx", soon: false },
  { f: ".xlsx", soon: false },
  { f: ".txt", soon: false },
  { f: ".png", soon: false },
];

const TOOLS = [
  { short: "Id", name: "InDesign", color: "#ff3d7f", soon: false },
  { short: "Ai", name: "Illustrator", color: "#ff9a1f", soon: false },
  { short: "Ps", name: "Photoshop", color: "#31a8ff", soon: false },
  { short: "Pr", name: "Premiere Pro", color: "#9999ff", soon: false },
  { short: "Yt", name: "YouTube Studio", color: "#ff4e45", soon: false },
  { short: "Wp", name: "WordPress", color: "#7a9cc6", soon: true },
];

const INDUSTRIES = [
  { label: "Marketing agencies", color: "#e08a6f" },
  { label: "Publishers and magazines", color: "#e8c547" },
  { label: "Legal and compliance", color: "#4fc4a8" },
  { label: "Film and subtitle studios", color: "#a98bf0" },
  { label: "Product and SaaS teams", color: "#8fd14f" },
  { label: "E-commerce brands", color: "#6f9cff" },
];

export default function PlatformBento() {
  return (
    <section id="platform" style={{ background: "#0a0908", position: "relative", zIndex: 20, isolation: "isolate" }}>
      <div className="mx-auto max-w-[1100px] px-8 py-24 lg:px-14">
        <div className="grid grid-cols-1 gap-4 md:grid-cols-6">
          {/* Intro, sitting in the grid beside the first card */}
          <div className="flex flex-col justify-center py-6 md:col-span-3 md:pr-10">
            <h2 className="text-[24px] font-normal leading-snug text-[#f0ece3]">
              Everything your global team needs
            </h2>
            <p className="mt-4 max-w-[440px] text-[15px] leading-relaxed text-[#a8a49a]">
              Agents built for each format, every language you ship in, and the
              tools your team already opens. Not another dashboard waiting for
              you to fill it.
            </p>
          </div>

          {/* Agents — neutral, outlined */}
          <Card
            className="md:col-span-3 md:h-[340px]"
            title="Translation agents"
            desc="One agent per format, each built around how that file actually works."
          >
            <div className="space-y-2">
              {AGENTS.map((a) => (
                <div key={a.name} className="flex items-center gap-3 rounded-xl bg-white/[0.04] px-3 py-2.5">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: a.color }} />
                  <div className="min-w-0 flex-1">
                    <div className="text-[13px]">{a.name}</div>
                    <div className="truncate text-[11.5px] text-white/50">{a.note}</div>
                  </div>
                  <Chip color={a.color}>{a.fmt}</Chip>
                </div>
              ))}
            </div>
          </Card>

          {/* Languages — plum, wide */}
          <Card
            side
            className="md:col-span-4 md:h-[260px]"
            bg="#3b1655"
            hue="#c493ff"
            title="40+ languages"
            desc="Right-to-left scripts are mirrored inside the page, not just reversed."
          >
            <div className="grid grid-cols-2 gap-x-6 gap-y-1">
              {LANGS.map((l) => (
                <div key={l.code} className="flex items-center gap-3 py-1.5">
                  <span className="font-pb-mono w-6 text-[11px] text-[#c493ff]">{l.code}</span>
                  <span className="text-[13px]">{l.name}</span>
                  {l.note ? <span className="ml-auto truncate text-[11px] text-white/45">{l.note}</span> : null}
                </div>
              ))}
            </div>
          </Card>

          {/* Delivery — neutral, small */}
          <div
            className="flex flex-col justify-between rounded-[24px] p-6 md:col-span-2 md:h-[260px]"
            style={{ background: NEUTRAL, border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <h3 className="text-[15px] text-[#f0ece3]">Inbox</h3>
            <div>
              <p className="text-[13px] text-[#a8a49a]">Finished files land where your team works</p>
              <div className="mt-3 flex gap-2">
                {["Email", "Slack", "Drive"].map((x) => (
                  <span key={x} className="rounded-md bg-white/[0.06] px-2 py-1 text-[11.5px] text-[#d8d3c8]">{x}</span>
                ))}
              </div>
            </div>
          </div>

          {/* Formats — umber */}
          <Card
            side
            textWidth="40%"
            className="md:col-span-3 md:h-[360px]"
            bg="#3d2410"
            hue="#f0b46a"
            title="Formats"
            desc="Native files in, native files out. More are on the way."
          >
            <div className="grid grid-cols-2 gap-1.5">
              {FORMATS.map((x) => (
                <div key={x.f} className="flex items-center justify-between rounded-md bg-white/[0.04] px-2.5 py-1.5">
                  <span className="font-pb-mono text-[12px]">{x.f}</span>
                  <span className="text-[10.5px]" style={{ color: x.soon ? "#8a8478" : "#8fd14f" }}>
                    {x.soon ? "Soon" : "Live"}
                  </span>
                </div>
              ))}
            </div>
          </Card>

          {/* Tools — navy */}
          <Card
            side
            textWidth="38%"
            className="md:col-span-3 md:h-[360px]"
            bg="#0f3256"
            hue="#7fb2ec"
            title="Works with your tools"
            desc="Open translated files straight in the apps your team already uses."
          >
            <div className="space-y-2">
              {TOOLS.map((t) => (
                <div key={t.name} className="flex items-center gap-3 rounded-xl bg-white/[0.04] px-3 py-2" style={{ opacity: t.soon ? 0.5 : 1 }}>
                  <span
                    className="font-pb-mono flex h-7 w-7 items-center justify-center rounded-md text-[11px] font-bold"
                    style={{ color: t.color, border: `1.5px solid ${t.color}` }}
                  >
                    {t.short}
                  </span>
                  <span className="text-[12.5px]">{t.name}</span>
                  {t.soon ? <span className="ml-auto text-[11px] text-white/45">Soon</span> : null}
                </div>
              ))}
            </div>
          </Card>

          {/* Workflow — no card, nodes on a dotted field */}
          <div
            className="relative flex flex-col justify-center rounded-[24px] p-2 md:col-span-3 md:row-span-2"
            style={{
              backgroundImage: "radial-gradient(rgba(255,255,255,0.10) 1px, transparent 1px)",
              backgroundSize: "18px 18px",
            }}
          >
            <p className="mb-6 max-w-[300px] text-[14px] leading-relaxed text-[#a8a49a]">
              <span className="text-[#f0ece3]">Upload to delivery, hands-off.</span> Each step runs in order and the file comes back in the same format.
            </p>
            <div className="flex flex-wrap items-center gap-2 lg:flex-nowrap">
              {[
                { k: "Trigger", v: "New upload", c: "#4fc4a8" },
                { k: "Agent", v: "Translate", c: "#a98bf0" },
                { k: "Tool", v: "Rebuild layout", c: "#e08a6f" },
                { k: "Deliver", v: "Same format", c: "#6f9cff" },
              ].map((n, i, arr) => (
                <div key={n.k} className="flex items-center gap-2">
                  <div className="rounded-2xl border bg-[#1f1e1c] px-3 py-2 shadow-[0_8px_24px_rgba(0,0,0,0.4)]"
                    style={{ borderColor: "rgba(255,255,255,0.10)" }}>
                    <div className="text-[10.5px] uppercase tracking-[0.06em]" style={{ color: n.c }}>{n.k}</div>
                    <div className="mt-0.5 whitespace-nowrap text-[12.5px] text-[#f0ece3]">{n.v}</div>
                  </div>
                  {i < arr.length - 1 ? <span className="h-px w-3 bg-white/25" /> : null}
                </div>
              ))}
            </div>
          </div>

          {/* QA — neutral, small */}
          <Card
            className="md:col-span-3 md:h-[220px]"
            title="QA report"
            desc="Run a report on any finished job."
          >
            <div className="space-y-2 text-[12.5px]">
              {[
                { n: "brand_guide.idml", v: "94%", c: "#8fd14f" },
                { n: "invoice_template.pdf", v: "Flagged", c: "#ff6f6f" },
              ].map((r) => (
                <div key={r.n} className="flex items-center justify-between rounded-md bg-white/[0.04] px-3 py-2">
                  <span className="truncate">{r.n}</span>
                  <span className="ml-2 shrink-0" style={{ color: r.c }}>{r.v}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Glossary — olive, table bleeding off the edge */}
          <Card
            side
            textWidth="40%"
            className="md:col-span-3 md:h-[220px]"
            bg="#2c3d0f"
            hue="#a4c862"
            title="Glossary"
            desc="Lock brand terms so they are never translated or reworded."
          >
            <div className="text-[12px]">
              <div className="flex gap-2 border-b border-white/10 pb-2 text-white/50">
                <span className="flex-1">English</span>
                <span className="flex-1">French</span>
                <span className="w-12 text-right">State</span>
              </div>
              {[
                { a: "Pagebirdy", b: "Pagebirdy", s: "Locked" },
                { a: "Annual report", b: "Rapport annuel", s: "Locked" },
                { a: "Draft", b: "Brouillon", s: "Open" },
              ].map((r) => (
                <div key={r.a} className="flex gap-2 border-b border-white/[0.06] py-2">
                  <span className="flex-1 truncate">{r.a}</span>
                  <span className="flex-1 truncate">{r.b}</span>
                  <span className="w-12 text-right" style={{ color: r.s === "Locked" ? "#c4e684" : "#8a8478" }}>{r.s}</span>
                </div>
              ))}
            </div>
          </Card>

          {/* Industries — neutral */}
          <div
            className="overflow-hidden rounded-[24px] p-6 md:col-span-3"
            style={{ background: NEUTRAL, border: "1px solid rgba(255,255,255,0.08)" }}
          >
            <h3 className="text-[15px] text-[#f0ece3]">For every team that ships in more than one language</h3>
            <div className="mt-5 grid grid-cols-1 gap-2 sm:grid-cols-2">
              {INDUSTRIES.map((i) => (
                <div key={i.label} className="flex items-center gap-2.5 rounded-xl bg-[#292826] px-3 py-3 text-[13px] text-[#f0ece3]">
                  <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: i.color }} />
                  {i.label}
                </div>
              ))}
            </div>
          </div>

          {/* Background jobs — wine, folded corner */}
          <div className="relative md:col-span-3">
            <Card
              className="h-full"
              bg="#4d1a38"
              hue="#ee6a8c"
              title="It keeps going"
              desc="Translation runs in the background. Close the tab, and the finished file lands in your inbox."
            >
              <div className="space-y-2.5">
                {[
                  { n: "annual_report_fr.idml", s: "Delivered", p: 100, c: "#4fc4a8" },
                  { n: "legal_terms_v2.pdf", s: "Translating", p: 64, c: "#e8c547" },
                  { n: "store_banners.psd", s: "Queued", p: 8, c: "#8a8478" },
                ].map((j) => (
                  <div key={j.n}>
                    <div className="flex items-center justify-between text-[12.5px]">
                      <span>{j.n}</span>
                      <span style={{ color: j.c }}>{j.s}</span>
                    </div>
                    <div className="mt-1.5 h-1 rounded-full bg-white/10">
                      <div className="h-1 rounded-full" style={{ width: `${j.p}%`, background: j.c }} />
                    </div>
                  </div>
                ))}
              </div>
            </Card>
            <span
              aria-hidden
              className="pointer-events-none absolute top-0 right-0 h-10 w-10"
              style={{ background: "linear-gradient(225deg, #0a0908 50%, #6a2449 50%)", borderTopRightRadius: "24px" }}
            />
          </div>
        </div>
      </div>
    </section>
  );
}
