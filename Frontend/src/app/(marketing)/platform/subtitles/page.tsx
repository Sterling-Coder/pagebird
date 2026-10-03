import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SRT / VTT Subtitle Translation — Pagebirdy",
  description:
    "Translate SRT and VTT subtitle files into 40+ languages. Every cue stays synced to its original timecode.",
};

const FEATURES = [
  {
    title: "Timing preserved",
    desc: "Every cue stays synced to its original start and end timecodes — no drift, no manual re-timing.",
  },
  {
    title: "SRT + VTT",
    desc: "Both common subtitle formats supported. Upload one, get back the same extension translated.",
  },
  {
    title: "Context-aware translation",
    desc: "Adjacent cues inform each sentence. Pronouns, tone and formality stay consistent across the whole file.",
  },
  {
    title: "Multi-engine consensus",
    desc: "OpenAI and DeepL translate in parallel. Disagreements get flagged for review.",
  },
  {
    title: "Glossary support",
    desc: "Lock brand names, product terms and character names so they never get translated.",
  },
  {
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including right-to-left scripts like Arabic and Hebrew.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Upload your subtitle file",
    desc: "Drop an .srt or .vtt file. We parse every cue and its timecodes.",
  },
  {
    n: "02",
    title: "Pick a language",
    desc: "Choose from 40+ target languages. Attach a glossary to lock terms that must not change.",
  },
  {
    n: "03",
    title: "Download",
    desc: "Same format, same timecodes, translated text. Upload straight to your video platform.",
  },
];

export default function SubtitlesPage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <div className="mb-6 flex items-center gap-3">
            <span className="font-pb-mono inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
              SRT / VTT Subtitles
            </span>
            <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
              Coming soon
            </span>
          </div>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            subtitles.
            <br />
            <span className="text-pb-text">Keep the timing.</span>
          </h1>

          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Upload an SRT or VTT file. Get it back in any of 40+ languages with
            every cue locked to its original timecode — ready to upload.
          </p>

          <div className="mt-8 flex items-center gap-4">
            <Link
              href="/contact"
              className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Join waitlist
            </Link>
          </div>
        </div>
      </section>

      {/* Product mock — subtitle viewer */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-0 overflow-hidden rounded-xl border border-pb-border md:grid-cols-2">
            <div className="flex flex-col gap-4 bg-pb-bg p-8 md:p-10">
              <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                Source · English
              </span>
              <div className="space-y-4 font-mono text-[13px] leading-relaxed text-pb-text-secondary">
                <div className="rounded-lg bg-pb-bg-card p-4">
                  <span className="text-pb-text-muted">00:01:15,000 → 00:01:18,500</span>
                  <p className="mt-1 text-pb-text">The quarterly results exceeded all expectations.</p>
                </div>
                <div className="rounded-lg bg-pb-bg-card p-4">
                  <span className="text-pb-text-muted">00:01:19,000 → 00:01:23,000</span>
                  <p className="mt-1 text-pb-text">Revenue grew 34% year over year.</p>
                </div>
                <div className="rounded-lg bg-pb-bg-card p-4">
                  <span className="text-pb-text-muted">00:01:24,000 → 00:01:28,500</span>
                  <p className="mt-1 text-pb-text">Let me walk you through the key drivers.</p>
                </div>
              </div>
            </div>
            <div className="flex flex-col gap-4 bg-[#f5f0e6] p-8 text-[#1a1914] md:p-10">
              <span className="font-pb-mono text-[11px] tracking-widest text-[#a09a88] uppercase">
                Translated · Spanish
              </span>
              <div className="space-y-4 font-mono text-[13px] leading-relaxed text-[#5a5648]">
                <div className="rounded-lg bg-[#e8e2d4] p-4">
                  <span className="text-[#a09a88]">00:01:15,000 → 00:01:18,500</span>
                  <p className="mt-1 text-[#1a1914]">Los resultados trimestrales superaron todas las expectativas.</p>
                </div>
                <div className="rounded-lg bg-[#e8e2d4] p-4">
                  <span className="text-[#a09a88]">00:01:19,000 → 00:01:23,000</span>
                  <p className="mt-1 text-[#1a1914]">Los ingresos crecieron un 34% interanual.</p>
                </div>
                <div className="rounded-lg bg-[#e8e2d4] p-4">
                  <span className="text-[#a09a88]">00:01:24,000 → 00:01:28,500</span>
                  <p className="mt-1 text-[#1a1914]">Permítame explicar los factores clave.</p>
                </div>
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
            Upload. Translate. Re-upload.
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
            Features
          </span>
          <h2 className="font-pb-display max-w-2xl text-4xl text-pb-text md:text-5xl">
            Subtitles translated. Timing untouched.
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

      {/* CTA */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Get notified when subtitle translation launches.
          </h2>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 rounded-full bg-pb-bg px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-text uppercase transition-all hover:bg-pb-bg-raised"
          >
            Join waitlist →
          </Link>
        </div>
      </section>
    </>
  );
}
