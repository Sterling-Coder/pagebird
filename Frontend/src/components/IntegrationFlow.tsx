"use client";

import { useEffect, useRef, useState } from "react";

/* An architecture diagram that runs: a file leaves one of your tools, goes
   through each stage of the engine, and comes back in the target language as
   the same kind of file. One file at a time, round-robin over the sources and
   languages, only while the section is on screen. */

const SOURCES = [
  { tool: "InDesign", ext: ".idml", short: "Id", color: "#ff5c8a" },
  { tool: "PDF", ext: ".pdf", short: "Pdf", color: "#e8613c" },
  { tool: "Illustrator", ext: ".ai", short: "Ai", color: "#ff9a1f" },
  { tool: "Photoshop", ext: ".psd", short: "Ps", color: "#31a8ff" },
  { tool: "Office", ext: ".docx .pptx .xlsx", short: "W", color: "#4f8ff7" },
  { tool: "Websites", ext: "URL", short: "</>", color: "#4fc4a8" },
];

const STAGES = [
  { name: "Extract", note: "Text, styles and positions read from the file" },
  { name: "Protect", note: "Maths, numbers, links and brand terms locked" },
  { name: "Translate", note: "One agent per format, held to your glossary" },
  { name: "Rebuild", note: "Same layout written back, mirrored for RTL" },
  { name: "Deliver", note: "The same file type, ready to open" },
];

const OUTPUTS = [
  { name: "Español", code: "es", rtl: false },
  { name: "Français", code: "fr", rtl: false },
  { name: "Deutsch", code: "de", rtl: false },
  { name: "中文", code: "zh", rtl: false },
  { name: "日本語", code: "ja", rtl: false },
  { name: "العربية", code: "ar", rtl: true },
];

// One cycle, in ticks: the file travels in, each stage lights in turn, the
// result travels out, then it rests on the delivered state.
const TICK_MS = 380;
const IN = 2;
const OUT = 2;
const REST = 3;
const CYCLE = IN + STAGES.length + OUT + REST;

type Phase =
  | { kind: "in" }
  | { kind: "stage"; index: number }
  | { kind: "out" }
  | { kind: "rest" };

function phaseAt(tick: number): Phase {
  const t = tick % CYCLE;
  if (t < IN) return { kind: "in" };
  if (t < IN + STAGES.length) return { kind: "stage", index: t - IN };
  if (t < IN + STAGES.length + OUT) return { kind: "out" };
  return { kind: "rest" };
}

// Diagram geometry, in percent of the diagram box: the three columns and the
// row of each card. Lines are drawn in the same space.
const SRC_X = 26;
const ENGINE_L = 37;
const ENGINE_R = 63;
const OUT_X = 74;
const rowY = (i: number, n: number) => ((i + 0.5) / n) * 100;
const curve = (x0: number, y0: number, x1: number, y1: number) => {
  const mx = (x0 + x1) / 2;
  return `M ${x0} ${y0} C ${mx} ${y0}, ${mx} ${y1}, ${x1} ${y1}`;
};

export default function IntegrationFlow() {
  const ref = useRef<HTMLElement>(null);
  const [tick, setTick] = useState(0);
  const [running, setRunning] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const obs = new IntersectionObserver(([e]) => setRunning(e.isIntersecting), { threshold: 0.2 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  useEffect(() => {
    if (!running) return;
    const id = setInterval(() => setTick((t) => t + 1), TICK_MS);
    return () => clearInterval(id);
  }, [running]);

  const cycle = Math.floor(tick / CYCLE);
  const phase = phaseAt(tick);
  const src = cycle % SOURCES.length;
  const out = (cycle * 5 + 1) % OUTPUTS.length; // a different pairing each lap
  const stageDone = (i: number) =>
    phase.kind === "out" || phase.kind === "rest" || (phase.kind === "stage" && i < phase.index);
  const stageActive = (i: number) => phase.kind === "stage" && phase.index === i;
  const delivered = phase.kind === "rest";
  const source = SOURCES[src];
  const target = OUTPUTS[out];
  const fileName = `brochure${source.ext.split(" ")[0] === "URL" ? ".html" : source.ext.split(" ")[0]}`;
  const outName = fileName.replace(/(\.[a-z]+)$/, `.${target.code}$1`);

  return (
    <section ref={ref} style={{ background: "#0a0908", position: "relative", overflow: "hidden" }}>
      <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
        <div className="mb-12 grid grid-cols-1 gap-6 lg:grid-cols-[1fr_auto] lg:items-end">
          <div>
            <div className="mb-5 flex items-center gap-3">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold uppercase tracking-widest text-pb-accent">How it fits</span>
            </div>
            <h2 className="pb-stencil" style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05 }}>
              Every tool.<br />One engine.
            </h2>
            <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-pb-text-muted">
              Files leave the tools your team already uses, pass through one engine, and come back
              as the same kind of file in every language you ship.
            </p>
          </div>
          {/* Live readout of the file currently in flight */}
          <div className="font-pb-mono flex items-center gap-3 rounded-full border bg-white/[0.03] px-4 py-2 text-[12px] text-[#a8a49a]" style={{ borderColor: "rgba(255,255,255,0.10)" }}>
            <span className={`h-2 w-2 rounded-full ${delivered ? "bg-[#4caf50]" : "bg-[#e08a2c] pb-pulse"}`} />
            <span className="text-[#f0ece3]">{fileName}</span>
            <span>→</span>
            <span className={delivered ? "text-[#8fd14f]" : ""}>{delivered ? outName : `${target.name}…`}</span>
          </div>
        </div>

        {/* Diagram (stacks on small screens; the connector layer is desktop only) */}
        <div className="relative grid grid-cols-1 gap-8 md:block md:h-[470px]">
          <svg className="pointer-events-none absolute inset-0 hidden h-full w-full md:block" viewBox="0 0 100 100"
            preserveAspectRatio="none" aria-hidden>
            {SOURCES.map((s, i) => {
              const on = i === src && (phase.kind === "in" || phase.kind === "stage");
              return (
                <path key={s.tool} d={curve(SRC_X, rowY(i, SOURCES.length), ENGINE_L, 50)} fill="none"
                  stroke={on ? s.color : "rgba(255,255,255,0.10)"} strokeWidth={on ? 1.6 : 1}
                  vectorEffect="non-scaling-stroke" className={on ? "pb-flow-dash" : undefined} />
              );
            })}
            {OUTPUTS.map((o, i) => {
              const on = i === out && (phase.kind === "out" || phase.kind === "rest");
              return (
                <path key={o.code} d={curve(ENGINE_R, 50, OUT_X, rowY(i, OUTPUTS.length))} fill="none"
                  stroke={on ? "#8fd14f" : "rgba(255,255,255,0.10)"} strokeWidth={on ? 1.6 : 1}
                  vectorEffect="non-scaling-stroke" className={on && phase.kind === "out" ? "pb-flow-dash" : undefined} />
              );
            })}
          </svg>

          {/* Sources */}
          <ul className="flex flex-col gap-2 md:absolute md:inset-y-0 md:left-0 md:w-[26%] md:justify-around md:gap-0">
            {SOURCES.map((s, i) => {
              const on = i === src;
              return (
                <li key={s.tool}
                  className="flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-all duration-300"
                  style={{
                    borderColor: on ? `${s.color}88` : "rgba(255,255,255,0.08)",
                    background: on ? `${s.color}14` : "#141311",
                    boxShadow: on ? `0 0 24px ${s.color}22` : "none",
                  }}>
                  <span className="font-pb-mono flex h-8 w-8 shrink-0 items-center justify-center rounded-lg text-[11px] font-bold"
                    style={{ color: s.color, border: `1.5px solid ${s.color}` }}>{s.short}</span>
                  <div className="min-w-0">
                    <div className="text-[13px] text-[#f0ece3]">{s.tool}</div>
                    <div className="font-pb-mono truncate text-[11px] text-[#8a8478]">{s.ext}</div>
                  </div>
                </li>
              );
            })}
          </ul>

          {/* Engine */}
          <div className="relative rounded-[22px] border bg-[#151412] p-5 md:absolute md:top-1/2 md:left-[37%] md:w-[26%] md:-translate-y-1/2"
            style={{ borderColor: "rgba(255,255,255,0.10)", boxShadow: "0 0 0 1px rgba(224,138,111,0.08), 0 30px 80px rgba(0,0,0,0.5)" }}>
            <div className="mb-4 flex items-center justify-between">
              <span className="font-pb-mono text-[11px] font-bold uppercase tracking-widest text-pb-accent">Pagebirdy engine</span>
              <span className={`h-2 w-2 rounded-full ${phase.kind === "stage" ? "bg-[#e08a2c] pb-pulse" : "bg-white/20"}`} />
            </div>
            <ol className="space-y-1.5">
              {STAGES.map((st, i) => {
                const active = stageActive(i);
                const done = stageDone(i);
                return (
                  <li key={st.name} className="relative overflow-hidden rounded-lg px-3 py-2 transition-colors duration-300"
                    style={{ background: active ? "rgba(224,138,111,0.14)" : "rgba(255,255,255,0.03)" }}>
                    {active ? <span className="pb-stage-sweep absolute inset-y-0 left-0 w-full" aria-hidden /> : null}
                    <div className="relative flex items-center gap-2.5">
                      <span className="flex h-4 w-4 shrink-0 items-center justify-center rounded-full text-[9px]"
                        style={{
                          background: done ? "#8fd14f" : active ? "#e08a6f" : "transparent",
                          border: done || active ? "none" : "1px solid rgba(255,255,255,0.25)",
                          color: "#0a0908",
                        }}>{done ? "✓" : ""}</span>
                      <span className={`text-[13px] ${active || done ? "text-[#f0ece3]" : "text-[#a8a49a]"}`}>{st.name}</span>
                    </div>
                    <p className={`relative mt-0.5 pl-[26px] text-[11.5px] leading-snug ${active ? "text-[#d8c4b8]" : "text-[#6e6a61]"}`}>{st.note}</p>
                  </li>
                );
              })}
            </ol>
          </div>

          {/* Outputs */}
          <ul className="flex flex-col gap-2 md:absolute md:inset-y-0 md:right-0 md:w-[26%] md:justify-around md:gap-0">
            {OUTPUTS.map((o, i) => {
              const on = i === out && (phase.kind === "out" || phase.kind === "rest");
              const landed = i === out && delivered;
              return (
                <li key={o.code}
                  className="flex items-center gap-3 rounded-xl border px-3 py-2.5 transition-all duration-300"
                  style={{
                    borderColor: on ? "rgba(143,209,79,0.5)" : "rgba(255,255,255,0.08)",
                    background: on ? "rgba(143,209,79,0.07)" : "#141311",
                  }}>
                  <span className="font-pb-mono w-7 text-[11px] uppercase text-[#8a8478]">{o.code}</span>
                  <span dir={o.rtl ? "rtl" : "ltr"} className="text-[14px] text-[#f0ece3]">{o.name}</span>
                  {o.rtl ? <span className="rounded bg-white/[0.06] px-1.5 text-[10px] text-[#a8a49a]">RTL</span> : null}
                  <span className={`font-pb-mono ml-auto truncate text-[10.5px] transition-opacity duration-300 ${landed ? "text-[#8fd14f] opacity-100" : "opacity-0"}`}>
                    {landed ? outName : ""}
                  </span>
                </li>
              );
            })}
          </ul>
        </div>

        <div className="mt-12 grid grid-cols-1 gap-3 border-t pt-8 text-[13px] sm:grid-cols-3" style={{ borderColor: "rgba(255,255,255,0.06)" }}>
          {[
            ["Same file type back", "An .idml comes back as .idml, a deck as a deck."],
            ["Right-to-left handled", "Arabic, Hebrew, Persian and Urdu are mirrored in the page."],
            ["Nothing to install", "Upload in the app, or translate any page with the extension."],
          ].map(([t, d]) => (
            <div key={t}>
              <div className="text-[#f0ece3]">{t}</div>
              <p className="mt-1 leading-relaxed text-[#8a8478]">{d}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
