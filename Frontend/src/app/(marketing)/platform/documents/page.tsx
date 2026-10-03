import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Document / PDF Translation — Pagebirdy",
  description:
    "Translate InDesign IDML and PDF files into 40+ languages. Fonts, columns, tables and page breaks stay exactly where they were.",
};

const FEATURES = [
  {
    title: "Layout preservation",
    desc: "Every font, column, table, footnote and page break lands exactly where it was — no manual cleanup.",
  },
  {
    title: "RTL mirroring",
    desc: "Arabic and Hebrew mirror the whole page — margins, gutters, bullets — not just text direction.",
  },
  {
    title: "OCR built in",
    desc: "Scanned PDFs get OCR, then a translated text layer rebuilt in position.",
  },
  {
    title: "Font substitution",
    desc: "No Japanese in your typeface? We pick a metrically compatible one, not a generic fallback.",
  },
  {
    title: "Multi-engine translation",
    desc: "OpenAI and DeepL in consensus. Disagreements get flagged for human review.",
  },
  {
    title: "QA scoring",
    desc: "Every job gets a layout-integrity score. Catch reflow and overflow before it ships.",
  },
];

const FORMATS = [".idml", ".pdf", ".ai", ".psd", ".eps", ".docx", ".pptx", ".xlsx"];

const STEPS = [
  {
    n: "01",
    title: "Upload your file",
    desc: "Drop an IDML or PDF. We read the layout tree — not a flattened text dump.",
  },
  {
    n: "02",
    title: "Pick a language",
    desc: "Choose from 40+ target languages. Attach a glossary to lock terms that must not be translated.",
  },
  {
    n: "03",
    title: "Download the result",
    desc: "Same extension, same styles, same page count. Open it and keep editing as if nothing happened.",
  },
];

export default function DocumentsPage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <div className="mb-6 flex items-center gap-3">
            <span className="font-pb-mono inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
              Document / PDF
            </span>
            <span className="font-pb-mono rounded-full bg-emerald-900/30 px-3 py-1 text-[9px] font-bold tracking-widest text-emerald-400 uppercase">
              Live
            </span>
          </div>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            document.
            <br />
            <span className="text-pb-text">Keep the design.</span>
          </h1>

          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Upload an InDesign IDML or PDF. Get it back in any of 40+ languages
            with every font, column, table and page break exactly where you left
            it.
          </p>

          <div className="mt-8 flex items-center gap-4">
            <Link
              href="/login"
              className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Translate free
            </Link>
            <button
              type="button"
              className="font-pb-mono text-[12px] tracking-widest text-pb-text-secondary uppercase transition-colors hover:text-pb-text"
            >
              Watch demo →
            </button>
          </div>
        </div>
      </section>

      {/* Product mock */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-0 overflow-hidden rounded-xl border border-pb-border md:grid-cols-2">
            <div className="flex flex-col justify-between bg-pb-bg p-8 md:p-10">
              <div>
                <span className="font-pb-mono text-[22px] text-pb-text-muted">product_magazine.idml</span>
                <div className="mt-6 space-y-3">
                  <div className="h-2 w-[88%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[96%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[70%] rounded-full bg-pb-border" />
                  <div className="mt-4 h-16 w-full rounded-lg bg-pb-bg-card" />
                  <div className="h-2 w-[92%] rounded-full bg-pb-border" />
                  <div className="h-2 w-[64%] rounded-full bg-pb-border" />
                </div>
              </div>
              <div className="mt-8 border-t border-pb-border pt-5">
                <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                  Source · English
                </span>
              </div>
            </div>
            <div className="flex flex-col justify-between bg-[#f5f0e6] p-8 text-[#1a1914] md:p-10">
              <div>
                <span className="font-pb-mono text-[22px] text-[#a09a88]">product_magazine.zh.idml</span>
                <div className="mt-6 space-y-3">
                  <div className="h-2 w-[76%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[92%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[58%] rounded-full bg-[#d9d3c4]" />
                  <div className="mt-4 h-16 w-full rounded-lg bg-[#e8e2d4]" />
                  <div className="h-2 w-[84%] rounded-full bg-[#d9d3c4]" />
                  <div className="h-2 w-[50%] rounded-full bg-[#d9d3c4]" />
                </div>
              </div>
              <div className="mt-8 border-t border-[#d1cbbe] pt-5">
                <span className="font-pb-mono text-[11px] tracking-widest text-[#a09a88] uppercase">
                  Translated · Chinese
                </span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* How it works */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            How it works
          </span>
          <h2 className="font-pb-display max-w-lg text-4xl text-pb-text md:text-5xl">
            Three steps. Zero cleanup.
          </h2>
          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-3">
            {STEPS.map((s) => (
              <div key={s.n} className="flex flex-col gap-5 rounded-xl border border-pb-border bg-pb-bg p-8">
                <span className="font-pb-mono text-4xl font-bold text-pb-accent/30">{s.n}</span>
                <h3 className="text-xl font-bold text-pb-text">{s.title}</h3>
                <p className="text-[14px] leading-relaxed text-pb-text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Capabilities
          </span>
          <h2 className="font-pb-display max-w-2xl text-4xl text-pb-text md:text-5xl">
            Everything the file carried, carried across.
          </h2>
          <div className="mt-14 grid grid-cols-1 gap-px overflow-hidden rounded-xl border border-pb-border bg-pb-border md:grid-cols-2 lg:grid-cols-3">
            {FEATURES.map((f) => (
              <div key={f.title} className="flex flex-col gap-2.5 bg-pb-bg-card p-7">
                <h3 className="text-[15px] font-bold text-pb-text">{f.title}</h3>
                <p className="text-[13px] leading-relaxed text-pb-text-muted">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Formats */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-pb-mono mr-4 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Supported formats
            </span>
            {FORMATS.map((f) => (
              <span
                key={f}
                className="font-pb-mono rounded-full border border-pb-border px-4 py-1.5 text-[12px] text-pb-text-secondary"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Send us the document you dread translating.
          </h2>
          <Link
            href="/login"
            className="font-pb-mono shrink-0 rounded-full bg-pb-bg px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-text uppercase transition-all hover:bg-pb-bg-raised"
          >
            Translate free →
          </Link>
        </div>
      </section>
    </>
  );
}
