"use client";

import { useEffect, useRef, useState } from "react";
import type { ReactNode } from "react";

/* One tab per product. Each runs its own agent's steps in order, and the
   preview turns from the original into the translation as the last step
   lands. Tabs advance on their own while the section is on screen; hovering
   or picking one holds it. */

type Product = {
  id: string;
  n: string;
  label: string;
  agent: string;
  color: string;
  input: string;
  output: string;
  steps: string[];
  before: ReactNode;
  after: ReactNode;
};

function Lines({ widths, accent }: { widths: number[]; accent?: number }) {
  return (
    <div className="space-y-1.5">
      {widths.map((w, i) => (
        <div key={i} className="h-1.5 rounded-full" style={{ width: `${w}%`, background: i === accent ? "#e08a6f" : "rgba(21,19,15,0.18)" }} />
      ))}
    </div>
  );
}

function Page({ lang, title, body }: { lang: string; title: string; body: string }) {
  return (
    <div className="h-full rounded-lg bg-[#fbf8f2] p-4 text-[#15130f] shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="mb-2 flex items-center justify-between text-[9px] uppercase tracking-[0.1em] text-[#8a8478]">
        <span>Annual report</span><span>{lang}</span>
      </div>
      <div className="mb-2 h-16 rounded-md bg-gradient-to-br from-[#e8ac2e] to-[#c95810]" />
      <div className="text-[13px] font-semibold leading-tight">{title}</div>
      <p className="mt-1 text-[10.5px] leading-snug text-[#4a463d]">{body}</p>
      <div className="mt-3 grid grid-cols-2 gap-3">
        <Lines widths={[100, 92, 96, 70]} />
        <Lines widths={[95, 100, 88, 60]} />
      </div>
    </div>
  );
}

function Slide({ title, bullets }: { title: string; bullets: string[] }) {
  return (
    <div className="flex h-full flex-col rounded-lg bg-[#15233d] p-4 text-white shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="text-[9px] uppercase tracking-[0.1em] text-white/50">Q4 deck · slide 3</div>
      <div className="mt-2 text-[15px] font-semibold leading-tight">{title}</div>
      <ul className="mt-3 space-y-1.5 text-[11px] text-white/80">
        {bullets.map((b) => <li key={b} className="flex gap-2"><span className="text-[#6f9cff]">▪</span>{b}</li>)}
      </ul>
      <div className="mt-auto flex items-end gap-1.5 pt-3">
        {[40, 62, 50, 78, 66].map((h, i) => <div key={i} className="w-4 rounded-sm bg-[#6f9cff]" style={{ height: h * 0.5 }} />)}
        <span className="ml-2 font-mono text-[10px] text-white/50">=SUM(B2:B6)</span>
      </div>
    </div>
  );
}

function Banner({ text, sub }: { text: string; sub: string }) {
  return (
    <div className="relative flex h-full items-center justify-center overflow-hidden rounded-lg shadow-[0_10px_30px_rgba(0,0,0,0.35)]"
      style={{ background: "radial-gradient(circle at 30% 30%, #4fc4a8, #1f6f63 60%, #12403a)" }}>
      <div className="absolute right-4 bottom-4 h-16 w-16 rounded-full bg-white/10" />
      <div className="text-center">
        <div className="text-[26px] font-black tracking-tight text-[#fff6d6] drop-shadow">{text}</div>
        <div className="mt-1 text-[11px] font-semibold uppercase tracking-[0.2em] text-white/80">{sub}</div>
        <div className="mt-3 inline-block rounded-full bg-[#fff6d6] px-3 py-1 text-[11px] font-bold text-[#12403a]">-40%</div>
      </div>
    </div>
  );
}

function Browser({ url, nav, title, cta }: { url: string; nav: string[]; title: string; cta: string }) {
  return (
    <div className="flex h-full flex-col overflow-hidden rounded-lg bg-white text-[#15130f] shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      <div className="flex items-center gap-1.5 border-b border-[#eee] bg-[#f4f2ee] px-3 py-1.5">
        {["#ff5f57", "#febc2e", "#28c840"].map((c) => <span key={c} className="h-2 w-2 rounded-full" style={{ background: c }} />)}
        <span className="ml-2 truncate rounded bg-white px-2 py-0.5 font-mono text-[9.5px] text-[#8a8478]">{url}</span>
      </div>
      <div className="flex gap-3 px-4 pt-3 text-[10px] text-[#6b6560]">{nav.map((n) => <span key={n}>{n}</span>)}</div>
      <div className="px-4 pt-4">
        <div className="text-[16px] font-semibold leading-tight">{title}</div>
        <Lines widths={[90, 74]} />
        <span className="mt-3 inline-block rounded-full bg-[#5a9e5a] px-3 py-1 text-[10px] font-semibold text-white">{cta}</span>
      </div>
    </div>
  );
}

function Selection({ translated }: { translated: boolean }) {
  return (
    <div className="relative h-full rounded-lg bg-white p-4 text-[12px] leading-relaxed text-[#4a463d] shadow-[0_10px_30px_rgba(0,0,0,0.35)]">
      Our team reviews every order within one business day, and{" "}
      <mark className="rounded bg-[#f5d9bd] px-0.5 text-[#15130f]">refunds go to the original payment method.</mark>{" "}
      Contact support if anything looks wrong.
      <div className={`absolute left-6 right-6 bottom-4 rounded-lg border border-[#e2d6c8] bg-[#fffaf4] p-3 shadow-[0_8px_24px_rgba(0,0,0,0.12)] transition-all duration-500 ${
        translated ? "translate-y-0 opacity-100" : "translate-y-2 opacity-0"}`}>
        <div className="text-[9px] uppercase tracking-[0.1em] text-[#8a6a4a]">Pagebirdy → ES</div>
        <div className="mt-1 text-[12px] text-[#15130f]">Los reembolsos se emiten al método de pago original.</div>
      </div>
    </div>
  );
}

const PRODUCTS: Product[] = [
  {
    id: "documents", n: "01", label: "InDesign & PDF", agent: "Layout agent", color: "#e08a6f",
    input: "report.idml", output: "report.es.idml",
    steps: ["Read frames", "Protect maths", "Translate", "Fit to frame", "Same file out"],
    before: <Page lang="EN" title="A year of steady growth" body="Revenue grew in every region while costs held flat." />,
    after: <Page lang="ES" title="Un año de crecimiento constante" body="Los ingresos crecieron en todas las regiones con costos estables." />,
  },
  {
    id: "office", n: "02", label: "Word, PowerPoint, Excel", agent: "Office agent", color: "#6f9cff",
    input: "q4_deck.pptx", output: "q4_deck.fr.pptx",
    steps: ["Read runs", "Keep styles", "Translate", "Shrink to fit", "Same file out"],
    before: <Slide title="What we shipped this quarter" bullets={["Faster onboarding", "Two new regions", "Half the support tickets"]} />,
    after: <Slide title="Ce que nous avons livré ce trimestre" bullets={["Intégration plus rapide", "Deux nouvelles régions", "Moitié moins de tickets"]} />,
  },
  {
    id: "images", n: "03", label: "Images", agent: "OCR agent", color: "#4fc4a8",
    input: "banner.png", output: "banner.de.png",
    steps: ["Read text", "Skip prices", "Translate", "Repaint", "Check pixels"],
    before: <Banner text="SALE TODAY" sub="Summer collection" />,
    after: <Banner text="HEUTE SALE" sub="Sommerkollektion" />,
  },
  {
    id: "websites", n: "04", label: "Website link", agent: "Web agent", color: "#8fd14f",
    input: "acme.com/pricing", output: "Read-only copy",
    steps: ["Safe fetch", "Strip scripts", "Translate", "Keep markup", "Share copy"],
    before: <Browser url="acme.com/pricing" nav={["Product", "Pricing", "Sign in"]} title="Simple pricing for every team" cta="Start free" />,
    after: <Browser url="acme.com/pricing · DE" nav={["Produkt", "Preise", "Anmelden"]} title="Einfache Preise für jedes Team" cta="Kostenlos starten" />,
  },
  {
    id: "extension", n: "05", label: "Chrome extension", agent: "In your browser", color: "#a98bf0",
    input: "Any web page", output: "Translated in place",
    steps: ["Select text", "Send", "Translate", "Show beside it", "Or whole page"],
    before: <Selection translated={false} />,
    after: <Selection translated />,
  },
];

const STEP_MS = 650;

export default function ProductDiagram() {
  const ref = useRef<HTMLElement>(null);
  const [active, setActive] = useState(0);
  const [step, setStep] = useState(0);
  const [visible, setVisible] = useState(false);
  const [held, setHeld] = useState(false);

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
    const obs = new IntersectionObserver(([e]) => setVisible(e.isIntersecting), { threshold: 0.25 });
    obs.observe(el);
    return () => obs.disconnect();
  }, []);

  // Steps tick forward; after the last one the preview rests on the
  // translation, then (unless held) the next product starts.
  useEffect(() => {
    if (!visible) return;
    const product = PRODUCTS[active];
    const last = product.steps.length;
    const id = setTimeout(() => {
      if (step < last + 3) setStep(step + 1);
      else if (!held) { setActive((active + 1) % PRODUCTS.length); setStep(0); }
    }, STEP_MS);
    return () => clearTimeout(id);
  }, [visible, active, step, held]);

  const product = PRODUCTS[active];
  const done = step >= product.steps.length;

  return (
    <section ref={ref} style={{ background: "#0a0908" }}>
      <div className="mx-auto max-w-[1100px] px-8 py-24 lg:px-14 lg:py-32">
        <div className="mb-12">
          <div className="mb-5 flex items-center gap-3">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold uppercase tracking-widest text-pb-accent">How each product works</span>
          </div>
          <h2 className="pb-stencil" style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05, maxWidth: "640px" }}>
            Five products.<br />Five specialized agents.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-8 lg:grid-cols-[280px_1fr]"
          onMouseEnter={() => setHeld(true)} onMouseLeave={() => setHeld(false)}>
          {/* Tabs */}
          <div className="flex flex-col gap-1.5">
            {PRODUCTS.map((p, i) => {
              const on = i === active;
              const pct = on ? Math.min(100, (step / (p.steps.length + 3)) * 100) : 0;
              return (
                <button key={p.id} type="button" onClick={() => { setActive(i); setStep(0); }}
                  className="relative overflow-hidden rounded-2xl px-4 py-3.5 text-left transition-colors"
                  style={{ background: on ? "#171614" : "transparent", border: `1px solid ${on ? "rgba(255,255,255,0.08)" : "transparent"}` }}>
                  <div className="flex items-baseline gap-3">
                    <span className="font-pb-mono text-[10.5px]" style={{ color: on ? p.color : "rgba(255,255,255,0.3)" }}>{p.n}</span>
                    <div>
                      <div className="text-[14px]" style={{ color: on ? "#f0ece3" : "rgba(240,236,227,0.5)" }}>{p.label}</div>
                      {on ? <div className="mt-0.5 text-[12px]" style={{ color: p.color }}>{p.agent}</div> : null}
                    </div>
                  </div>
                  {on ? (
                    <span className="absolute bottom-0 left-0 h-[2px] transition-[width] duration-500 ease-linear"
                      style={{ width: `${pct}%`, background: p.color }} />
                  ) : null}
                </button>
              );
            })}
          </div>

          {/* Stage */}
          <div className="rounded-[24px] p-5 sm:p-6" style={{ background: "#141311", border: "1px solid rgba(255,255,255,0.07)" }}>
            {/* in → out */}
            <div className="font-pb-mono mb-5 flex flex-wrap items-center gap-2 text-[11.5px]">
              <span className="rounded-full px-3 py-1 text-[#d8d3c8]" style={{ background: "rgba(255,255,255,0.05)" }}>{product.input}</span>
              <span className="text-[#6e6a61]">→</span>
              <span className="rounded-full px-3 py-1 transition-colors duration-300"
                style={{ background: done ? `${product.color}22` : "rgba(255,255,255,0.03)", color: done ? product.color : "#6e6a61" }}>
                {product.output}
              </span>
            </div>

            {/* Steps */}
            <ol className="mb-6 grid grid-cols-5 gap-2">
              {product.steps.map((s, i) => {
                const state = i < step ? "done" : i === step ? "now" : "next";
                return (
                  <li key={s} className="min-w-0">
                    <div className="h-1 overflow-hidden rounded-full" style={{ background: "rgba(255,255,255,0.08)" }}>
                      <div className="h-full rounded-full transition-[width] duration-500 ease-out"
                        style={{ width: state === "done" ? "100%" : state === "now" ? "55%" : "0%", background: product.color }} />
                    </div>
                    <div className="mt-2 truncate text-[11.5px] transition-colors"
                      style={{ color: state === "next" ? "#6e6a61" : "#f0ece3" }}>{s}</div>
                  </li>
                );
              })}
            </ol>

            {/* Preview: original fades out, translation fades in once the steps finish */}
            <div key={product.id} className="relative h-[280px]">
              <div className="absolute inset-0 transition-all duration-500"
                style={{ opacity: done ? 0 : 1, transform: done ? "scale(0.98)" : "scale(1)" }}>{product.before}</div>
              <div className="absolute inset-0 transition-all duration-500"
                style={{ opacity: done ? 1 : 0, transform: done ? "scale(1)" : "scale(1.02)" }}>{product.after}</div>
              <span className="font-pb-mono absolute top-3 right-3 rounded-full px-2.5 py-1 text-[10px] uppercase tracking-[0.1em]"
                style={{ background: "rgba(10,9,8,0.75)", color: done ? product.color : "#a8a49a" }}>
                {done ? "Translated" : "Original"}
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
