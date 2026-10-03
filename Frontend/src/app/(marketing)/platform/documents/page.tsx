import Link from "next/link";
import type { Metadata } from "next";
import { WatchDemoButton } from "@/components/WatchDemoButton";

export const metadata: Metadata = {
  title: "Document / PDF Translation — Pagebirdy",
  description:
    "Translate InDesign IDML and PDF files into 40+ languages. Fonts, columns, tables and page breaks stay exactly where they were.",
};

const CAPABILITIES = [
  {
    n: "01",
    title: "Layout preservation",
    desc: "Every font, column, table, footnote and page break lands exactly where it was. No manual cleanup, no reflowed text, no missing elements.",
  },
  {
    n: "02",
    title: "RTL mirroring",
    desc: "Arabic and Hebrew get the full treatment — margins flip, gutters swap, bullets point the right way, and the whole page mirrors inside the original frame.",
  },
  {
    n: "03",
    title: "OCR for scanned PDFs",
    desc: "Scanned documents get a full OCR pass. The translated text layer rebuilds in position over the original scan — searchable, copyable, exact.",
  },
  {
    n: "04",
    title: "Font substitution",
    desc: "No Japanese cut in your typeface? We pick a metrically compatible face from our bundled Noto library — not a generic fallback that breaks your line lengths.",
  },
  {
    n: "05",
    title: "Multi-engine consensus",
    desc: "OpenAI and DeepL run in parallel. When they disagree beyond a threshold, the segment is flagged for human review — before it ships, not after.",
  },
  {
    n: "06",
    title: "QA scoring",
    desc: "Every job gets a layout-integrity score: reflow rate, overflow count, font coverage. Catch problems in the report before the client does.",
  },
  {
    n: "07",
    title: "Side-by-side review",
    desc: "Reviewers edit the translation against the source page, paragraph by paragraph. Approved edits feed directly back into your glossary.",
  },
  {
    n: "08",
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese — including Arabic, Hebrew, Japanese, Chinese, Korean, Thai, and every major European language.",
  },
];

const LANGUAGES = [
  "Arabic", "Chinese (Simplified)", "Chinese (Traditional)", "Czech", "Danish",
  "Dutch", "Finnish", "French", "German", "Greek", "Hebrew", "Hindi",
  "Hungarian", "Indonesian", "Italian", "Japanese", "Korean", "Norwegian",
  "Polish", "Portuguese (BR)", "Portuguese (PT)", "Romanian", "Russian",
  "Spanish", "Swedish", "Thai", "Turkish", "Ukrainian", "Vietnamese",
];

const FORMATS = [".idml", ".pdf", ".ai", ".psd", ".eps"];

export default function DocumentsPage() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section
        className="relative min-h-screen overflow-hidden"
        style={{
          background:
            "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
        }}
      >
        {/* Vertical scan lines */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(255,140,60,0.07) 0px, rgba(255,140,60,0.07) 1px, transparent 1px, transparent 170px)",
          }}
        />
        {/* Horizontal noise */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(180deg, transparent 0px, transparent 3px, rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.04) 4px)",
          }}
        />

        <div className="relative mx-auto max-w-[1100px] px-8 pt-36 pb-20 lg:px-14 lg:pt-44 lg:pb-32">
          {/* Label row */}
          <div className="pb-enter-label mb-10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="inline-block h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
                Document / PDF
              </span>
            </div>
            <span
              className="font-pb-mono rounded-full border px-2.5 py-0.5 text-[9px] font-bold tracking-widest uppercase"
              style={{ borderColor: "rgba(52,211,153,0.35)", background: "rgba(6,78,59,0.3)", color: "#6ee7b7" }}
            >
              Live
            </span>
          </div>

          {/* Two-column: headline left, description right */}
          <div className="grid grid-cols-1 items-end gap-12 lg:grid-cols-[55fr_45fr] lg:gap-16">
            <h1
              className="pb-enter pb-enter-delay-1 pb-stencil"
              style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}
            >
              Translate the<br />
              document.<br />
              Keep the design.
            </h1>

            <div className="pb-enter pb-enter-delay-2 flex flex-col gap-8">
              <p className="text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
                Upload an InDesign IDML or PDF. Get it back in any of 40+
                languages with every font, column, table and page break exactly
                where you left it.
              </p>
              <div className="pb-enter pb-enter-delay-3 flex items-center gap-5">
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
        </div>
      </section>

      {/* ─── BEFORE / AFTER ─── */}
      <section className="pb-glass-section" style={{ background: "#0a0908" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="mb-10 flex items-center justify-between">
            <span
              className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.3)" }}
            >
              Source vs. output — identical layout
            </span>
            <span
              className="font-pb-mono text-[10px] tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.2)" }}
            >
              .idml → .zh.idml
            </span>
          </div>

          <div
            className="grid grid-cols-2 overflow-hidden"
            style={{ border: "1px solid rgba(255,255,255,0.07)" }}
          >
            {/* Source */}
            <div
              className="flex flex-col justify-between p-8 lg:p-12"
              style={{
                background: "#0e0d0b",
                borderRight: "1px solid rgba(255,255,255,0.07)",
              }}
            >
              <div>
                <div className="flex items-center justify-between mb-8">
                  <span
                    className="font-pb-mono text-[11px] tracking-widest uppercase"
                    style={{ color: "rgba(240,236,227,0.35)" }}
                  >
                    Source · English
                  </span>
                  <span
                    className="font-pb-mono text-[10px]"
                    style={{ color: "rgba(240,236,227,0.15)" }}
                  >
                    .idml
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="h-[3px] w-[88%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="h-[3px] w-[96%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="h-[3px] w-[70%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="mt-6 h-20 w-full" style={{ background: "rgba(255,255,255,0.05)" }} />
                  <div className="mt-6 h-[3px] w-[92%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="h-[3px] w-[64%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="h-[3px] w-[80%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                  <div className="h-[3px] w-[55%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                </div>
              </div>
            </div>

            {/* Output */}
            <div
              className="flex flex-col justify-between p-8 lg:p-12"
              style={{ background: "#f5f0e6" }}
            >
              <div>
                <div className="flex items-center justify-between mb-8">
                  <span
                    className="font-pb-mono text-[11px] tracking-widest uppercase"
                    style={{ color: "#a09a88" }}
                  >
                    Translated · Chinese
                  </span>
                  <span
                    className="font-pb-mono text-[10px]"
                    style={{ color: "rgba(26,25,20,0.3)" }}
                  >
                    .zh.idml
                  </span>
                </div>
                <div className="space-y-3">
                  <div className="h-[3px] w-[76%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="h-[3px] w-[88%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="h-[3px] w-[58%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="mt-6 h-20 w-full" style={{ background: "rgba(26,25,20,0.06)" }} />
                  <div className="mt-6 h-[3px] w-[82%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="h-[3px] w-[50%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="h-[3px] w-[70%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                  <div className="h-[3px] w-[42%]" style={{ background: "rgba(26,25,20,0.15)" }} />
                </div>
              </div>
            </div>
          </div>

          <div
            className="border-t px-0 py-4"
            style={{ borderColor: "rgba(255,255,255,0.06)" }}
          >
            <span
              className="font-pb-mono text-[10px] tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.25)" }}
            >
              Identical layout · same page count · same styles · same master pages
            </span>
          </div>
        </div>
      </section>

      {/* ─── PIPELINE DIAGRAM ─── */}
      <section className="pb-glass-section" style={{ background: "#0e0d0b" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          {/* Label + headline */}
          <div className="mb-4 flex items-center gap-3">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              How it works
            </span>
          </div>
          <div className="mb-3 flex flex-col justify-between gap-4 md:flex-row md:items-end">
            <h2
              className="font-pb-mono text-pb-text"
              style={{ fontSize: "clamp(2rem, 5vw, 4rem)", lineHeight: 1, letterSpacing: "-0.025em" }}
            >
              Under the hood.
            </h2>
            <span
              className="font-pb-mono text-[11px] tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.25)" }}
            >
              Six stages. Every one automated.
            </span>
          </div>

          {/* Pipeline — horizontal scroll on mobile */}
          <div className="mt-14 overflow-x-auto pb-4">
            <div className="flex min-w-[900px] items-stretch gap-0">
              {[
                { n: "01", name: "Upload",    desc: "IDML or PDF dropped in",        color: "#e08a6f" },
                { n: "02", name: "Parse",     desc: "Layout tree read, frames mapped", color: "#c4a862" },
                { n: "03", name: "Extract",   desc: "Text pulled with position data", color: "#8a9e5a" },
                { n: "04", name: "Translate", desc: "OpenAI + DeepL in consensus",    color: "#5a8ab0" },
                { n: "05", name: "Reflow",    desc: "Text replaced, reflow checked",  color: "#8a5ab0" },
                { n: "06", name: "Export",    desc: "Original format, translated",    color: "#e08a6f" },
              ].map((stage, i) => (
                <div key={stage.n} className="flex items-center">
                  {/* Stage box */}
                  <div
                    className="flex h-full min-h-[140px] w-[140px] flex-col justify-between p-4"
                    style={{
                      borderLeft: `2px solid ${stage.color}`,
                      borderTop: "1px solid rgba(255,255,255,0.07)",
                      borderRight: "1px solid rgba(255,255,255,0.07)",
                      borderBottom: "1px solid rgba(255,255,255,0.07)",
                      background: "rgba(255,255,255,0.02)",
                    }}
                  >
                    <span
                      className="font-pb-mono text-[11px]"
                      style={{ color: "rgba(240,236,227,0.18)" }}
                    >
                      {stage.n}
                    </span>
                    <div>
                      <span className="block text-[14px] font-bold text-pb-text">{stage.name}</span>
                      <span
                        className="mt-1 block text-[11px] leading-snug"
                        style={{ color: "rgba(240,236,227,0.4)" }}
                      >
                        {stage.desc}
                      </span>
                    </div>
                  </div>
                  {/* Arrow (not after last) */}
                  {i < 5 && (
                    <span
                      className="mx-2 shrink-0 text-[18px]"
                      style={{ color: "rgba(240,236,227,0.2)" }}
                    >
                      →
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* LTR → RTL page comparison */}
          <div className="mt-20">
            <p
              className="font-pb-mono mb-8 text-[11px] font-bold tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.3)" }}
            >
              Full page mirror, not just text direction.
            </p>
            <div className="grid grid-cols-1 gap-6 md:grid-cols-[1fr_auto_1fr]">
              {/* LTR page */}
              <div
                className="overflow-hidden p-6"
                style={{ border: "1px solid rgba(255,255,255,0.07)", background: "rgba(255,255,255,0.02)" }}
              >
                <span
                  className="font-pb-mono mb-4 block text-[10px] tracking-widest uppercase"
                  style={{ color: "rgba(240,236,227,0.3)" }}
                >
                  English · LTR
                </span>
                {/* Simulated LTR page layout */}
                <div className="grid grid-cols-[2fr_1fr] gap-3">
                  <div className="space-y-2">
                    <div className="h-[3px] w-full" style={{ background: "rgba(255,255,255,0.15)" }} />
                    <div className="h-[3px] w-[85%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                    <div className="h-[3px] w-[90%]" style={{ background: "rgba(255,255,255,0.1)" }} />
                    <div className="mt-3 h-12" style={{ background: "rgba(255,255,255,0.05)" }} />
                    <div className="h-[3px] w-[80%]" style={{ background: "rgba(255,255,255,0.08)" }} />
                    <div className="h-[3px] w-[70%]" style={{ background: "rgba(255,255,255,0.08)" }} />
                  </div>
                  <div className="space-y-2">
                    <div className="h-[3px] w-full" style={{ background: "rgba(255,255,255,0.08)" }} />
                    <div className="h-[3px] w-[75%]" style={{ background: "rgba(255,255,255,0.06)" }} />
                    <div className="h-16" style={{ background: "rgba(255,255,255,0.04)" }} />
                  </div>
                </div>
                {/* LTR bullets */}
                <div className="mt-3 space-y-1.5">
                  {[65, 78, 55].map((w, i) => (
                    <div key={i} className="flex items-center gap-2">
                      <div className="h-1.5 w-1.5 shrink-0" style={{ background: "rgba(224,138,111,0.5)", borderRadius: "50%" }} />
                      <div className="h-[2px]" style={{ width: `${w}%`, background: "rgba(255,255,255,0.1)" }} />
                    </div>
                  ))}
                </div>
              </div>

              {/* Arrow */}
              <div className="flex items-center justify-center">
                <span className="font-pb-mono text-[28px]" style={{ color: "rgba(224,138,111,0.4)" }}>→</span>
              </div>

              {/* RTL page */}
              <div
                className="overflow-hidden p-6"
                style={{ border: "1px solid rgba(167,139,250,0.2)", background: "rgba(167,139,250,0.03)" }}
              >
                <span
                  className="font-pb-mono mb-4 block text-right text-[10px] tracking-widest uppercase"
                  style={{ color: "rgba(167,139,250,0.5)" }}
                >
                  Arabic · RTL ✓
                </span>
                {/* Simulated RTL page layout — mirrored */}
                <div className="grid grid-cols-[1fr_2fr] gap-3" style={{ direction: "rtl" }}>
                  <div className="space-y-2">
                    <div className="h-[3px] w-full" style={{ background: "rgba(167,139,250,0.15)" }} />
                    <div className="h-[3px] w-[75%]" style={{ background: "rgba(167,139,250,0.1)" }} />
                    <div className="h-16" style={{ background: "rgba(167,139,250,0.05)" }} />
                  </div>
                  <div className="space-y-2">
                    <div className="h-[3px] w-full" style={{ background: "rgba(167,139,250,0.2)" }} />
                    <div className="h-[3px] w-[85%]" style={{ background: "rgba(167,139,250,0.15)" }} />
                    <div className="h-[3px] w-[90%]" style={{ background: "rgba(167,139,250,0.15)" }} />
                    <div className="mt-3 h-12" style={{ background: "rgba(167,139,250,0.07)" }} />
                    <div className="h-[3px] w-[80%]" style={{ background: "rgba(167,139,250,0.1)" }} />
                    <div className="h-[3px] w-[70%]" style={{ background: "rgba(167,139,250,0.1)" }} />
                  </div>
                </div>
                {/* RTL bullets */}
                <div className="mt-3 space-y-1.5">
                  {[65, 78, 55].map((w, i) => (
                    <div key={i} className="flex items-center justify-end gap-2">
                      <div className="h-[2px]" style={{ width: `${w}%`, background: "rgba(167,139,250,0.15)" }} />
                      <div className="h-1.5 w-1.5 shrink-0" style={{ background: "rgba(167,139,250,0.5)", borderRadius: "50%" }} />
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── RTL SHOWCASE ─── */}
      <section
        className="relative overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 100% 80% at 30% 50%, #1a0a2e 0%, #0e0c1a 50%, #0a0908 100%)",
        }}
      >
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(120,80,255,0.05) 0px, rgba(120,80,255,0.05) 1px, transparent 1px, transparent 170px)",
          }}
        />
        <div className="relative mx-auto max-w-[1100px] px-8 py-24 lg:px-14 lg:py-36">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:gap-24">
            {/* Copy */}
            <div className="flex flex-col justify-center">
              <div className="mb-8 flex items-center gap-3">
                <span className="inline-block h-2 w-2" style={{ background: "#a78bfa" }} />
                <span
                  className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
                  style={{ color: "#a78bfa" }}
                >
                  RTL support
                </span>
              </div>
              <h2
                className="font-pb-mono text-pb-text"
                style={{
                  fontSize: "clamp(2.5rem, 6vw, 5.5rem)",
                  lineHeight: 0.95,
                  letterSpacing: "-0.025em",
                }}
              >
                Right to left.
                <br />
                <span style={{ color: "rgba(240,236,227,0.3)" }}>First class.</span>
              </h2>
              <p className="mt-8 max-w-sm text-[15px] leading-relaxed text-pb-text-secondary">
                Arabic and Hebrew get the full treatment — margins flip, gutters
                swap, bullets point the right way, and the whole page mirrors
                inside the original frame. Not just text direction. The whole layout.
              </p>
              <div className="mt-10 flex gap-8">
                <div>
                  <span className="font-pb-mono block text-[32px] font-bold text-pb-text">22+</span>
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">RTL languages</span>
                </div>
                <div>
                  <span className="font-pb-mono block text-[32px] font-bold text-pb-text">100%</span>
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">Layout mirrored</span>
                </div>
              </div>
            </div>

            {/* Mock — Arabic mirrored page */}
            <div className="flex items-center justify-center">
              <div
                className="w-full max-w-sm overflow-hidden"
                style={{
                  border: "1px solid rgba(167,139,250,0.2)",
                  background: "rgba(167,139,250,0.04)",
                }}
              >
                {/* Header row mirrored */}
                <div
                  className="flex items-center justify-end gap-3 p-5"
                  style={{ borderBottom: "1px solid rgba(167,139,250,0.1)", direction: "rtl" }}
                >
                  <div className="h-2 w-16" style={{ background: "rgba(167,139,250,0.25)" }} />
                  <div className="h-2 w-10" style={{ background: "rgba(167,139,250,0.15)" }} />
                  <div className="h-2 w-20" style={{ background: "rgba(167,139,250,0.2)" }} />
                </div>
                {/* Arabic text lines (RTL) */}
                <div className="space-y-3 p-6" style={{ direction: "rtl" }}>
                  <div className="flex justify-end gap-2">
                    <div className="h-[3px] w-[85%]" style={{ background: "rgba(167,139,250,0.3)" }} />
                  </div>
                  <div className="flex justify-end gap-2">
                    <div className="h-[3px] w-[92%]" style={{ background: "rgba(167,139,250,0.25)" }} />
                  </div>
                  <div className="flex justify-end gap-2">
                    <div className="h-[3px] w-[68%]" style={{ background: "rgba(167,139,250,0.2)" }} />
                  </div>
                  <div className="mt-4 h-16 w-full" style={{ background: "rgba(167,139,250,0.08)" }} />
                  <div className="flex justify-end">
                    <div className="h-[3px] w-[78%]" style={{ background: "rgba(167,139,250,0.25)" }} />
                  </div>
                  <div className="flex justify-end">
                    <div className="h-[3px] w-[55%]" style={{ background: "rgba(167,139,250,0.2)" }} />
                  </div>
                  {/* Bullet points RTL */}
                  <div className="mt-2 space-y-2">
                    {[70, 82, 61].map((w, i) => (
                      <div key={i} className="flex items-center justify-end gap-2">
                        <div className="h-[3px]" style={{ width: `${w}%`, background: "rgba(167,139,250,0.2)" }} />
                        <div className="h-1.5 w-1.5 shrink-0" style={{ background: "#a78bfa", borderRadius: "50%" }} />
                      </div>
                    ))}
                  </div>
                </div>
                <div
                  className="px-5 py-3"
                  style={{ borderTop: "1px solid rgba(167,139,250,0.1)" }}
                >
                  <span
                    className="font-pb-mono block text-right text-[10px] tracking-widest uppercase"
                    style={{ color: "rgba(167,139,250,0.5)" }}
                  >
                    Arabic · mirrored layout ✓
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="pb-glass-section" style={{ background: "#0a0908" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="mb-16 flex items-center gap-3">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              How it works
            </span>
          </div>

          <div className="grid grid-cols-1 gap-0 md:grid-cols-3">
            {[
              {
                n: "01",
                title: "Upload your file",
                desc: "Drop an IDML or PDF. We read the full layout tree — text frames, linked graphics, master pages — not a flattened text dump.",
              },
              {
                n: "02",
                title: "Pick language + glossary",
                desc: "Choose from 40+ targets. Import a TBX or CSV to lock terms that must never be translated — product names, legal phrases, brand terms.",
              },
              {
                n: "03",
                title: "Download the result",
                desc: "Same file extension, same styles, same page count. Open it in InDesign or Acrobat and keep editing as if nothing happened.",
              },
            ].map((s, i) => (
              <div
                key={s.n}
                className={`py-10 ${i < 2 ? "md:border-r md:pr-10" : ""} ${i > 0 ? "md:pl-10" : ""} border-b md:border-b-0`}
                style={{ borderColor: "rgba(255,255,255,0.06)" }}
              >
                <span
                  className="font-pb-mono block text-[72px] font-bold leading-none"
                  style={{ color: "rgba(224,138,111,0.12)" }}
                >
                  {s.n}
                </span>
                <h3 className="mt-4 text-[20px] font-bold text-pb-text">{s.title}</h3>
                <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CAPABILITIES ─── editorial numbered rows */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="flex flex-col justify-between gap-4 pb-12 md:flex-row md:items-end" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
            <div>
              <div className="mb-6 flex items-center gap-3">
                <span className="inline-block h-2 w-2 bg-pb-accent" />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
                  Capabilities
                </span>
              </div>
              <h2
                className="font-pb-mono text-pb-text"
                style={{ fontSize: "clamp(2rem, 5vw, 4rem)", lineHeight: 1, letterSpacing: "-0.025em" }}
              >
                Everything the file
                <br />
                carried, carried across.
              </h2>
            </div>
            <span
              className="font-pb-mono text-[11px] tracking-widest uppercase"
              style={{ color: "rgba(240,236,227,0.25)" }}
            >
              08 capabilities
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2">
            {CAPABILITIES.map((c, i) => (
              <div
                key={c.n}
                className={`flex gap-6 py-8 ${i % 2 === 0 ? "md:border-r md:pr-12" : "md:pl-12"}`}
                style={{ borderBottom: "1px solid rgba(255,255,255,0.04)", borderColor: "rgba(255,255,255,0.04)" }}
              >
                <span className="font-pb-mono mt-0.5 shrink-0 text-[11px]" style={{ color: "rgba(224,138,111,0.5)" }}>
                  {c.n}
                </span>
                <div>
                  <h3 className="text-[15px] font-bold text-pb-text">{c.title}</h3>
                  <p className="mt-1.5 text-[13px] leading-relaxed text-pb-text-muted">{c.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FORMATS ─── */}
      <section style={{ background: "#0a0908", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-8 lg:px-14">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-pb-mono mr-4 text-[10px] font-bold tracking-widest uppercase" style={{ color: "rgba(240,236,227,0.3)" }}>
              Supported formats
            </span>
            {FORMATS.map((f) => (
              <span
                key={f}
                className="font-pb-mono px-4 py-1.5 text-[12px]"
                style={{ border: "1px solid rgba(255,255,255,0.08)", color: "rgba(240,236,227,0.5)" }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── LANGUAGES ─── */}
      <section className="pb-glass-section bg-pb-bg">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-20">
          <div className="mb-10 flex items-center gap-3">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              40+ languages
            </span>
          </div>
          <div className="flex flex-wrap gap-x-6 gap-y-3">
            {LANGUAGES.map((lang) => (
              <span key={lang} className="font-pb-mono text-[13px] text-pb-text-secondary">
                {lang}
              </span>
            ))}
            <span className="font-pb-mono text-[13px] text-pb-text-muted">+ many more →</span>
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ background: "#e08a6f" }}>
        <div className="mx-auto flex max-w-[1100px] flex-col items-start justify-between gap-8 px-8 py-20 md:flex-row md:items-center lg:px-14 lg:py-24">
          <h2
            className="font-pb-mono max-w-2xl font-bold"
            style={{
              color: "#131210",
              fontSize: "clamp(2rem, 5vw, 4rem)",
              lineHeight: 1,
              letterSpacing: "-0.025em",
            }}
          >
            Send us the document
            <br />
            you dread translating.
          </h2>
          <Link
            href="/login"
            className="font-pb-mono shrink-0 border-2 border-[#131210] bg-[#131210] px-8 py-3.5 text-[12px] font-bold tracking-widest text-[#e08a6f] uppercase transition-all hover:bg-transparent hover:text-[#131210]"
          >
            Translate free →
          </Link>
        </div>
      </section>
    </>
  );
}
