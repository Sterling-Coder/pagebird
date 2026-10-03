import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "YouTube Subtitle Translation — Pagebirdy",
  description:
    "Paste a YouTube link. We pull the captions, translate them, and hand back a ready-to-upload SRT.",
};

const FEATURES = [
  {
    title: "Paste a link",
    desc: "No downloads, no ffmpeg. Paste the YouTube URL and we pull the captions automatically.",
  },
  {
    title: "Auto-detect source language",
    desc: "We read the existing captions and detect the source language — no manual selection needed.",
  },
  {
    title: "Timing preserved",
    desc: "Every cue stays synced to its original timecode. No drift, no re-timing.",
  },
  {
    title: "Ready-to-upload SRT",
    desc: "Download the translated file and upload it straight to YouTube Studio as a new subtitle track.",
  },
  {
    title: "Multi-engine translation",
    desc: "OpenAI and DeepL in consensus for the best result on every caption line.",
  },
  {
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including CJK and right-to-left scripts.",
  },
];

const STEPS = [
  {
    n: "01",
    title: "Paste the YouTube URL",
    desc: "Drop a link to any public YouTube video. We fetch the existing captions.",
  },
  {
    n: "02",
    title: "Pick a language",
    desc: "Choose from 40+ target languages. Attach a glossary to lock brand names and terms.",
  },
  {
    n: "03",
    title: "Download the SRT",
    desc: "Get a translated .srt file ready to upload to YouTube Studio or any video platform.",
  },
];

export default function YouTubePage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <div className="mb-6 flex items-center gap-3">
            <span className="font-pb-mono inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
              YouTube Subtitles
            </span>
            <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
              Coming soon
            </span>
          </div>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            captions.
            <br />
            <span className="text-pb-text">Reach every viewer.</span>
          </h1>

          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Paste a YouTube link. We pull the captions, translate them into 40+
            languages, and hand back a ready-to-upload SRT — timing intact.
          </p>

          <div className="mt-8">
            <Link
              href="/contact"
              className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Join waitlist
            </Link>
          </div>
        </div>
      </section>

      {/* Product mock — YouTube flow */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="overflow-hidden rounded-xl border border-pb-border">
            <div className="bg-pb-bg-card p-8 md:p-10">
              <div className="mx-auto max-w-2xl">
                <div className="flex items-center gap-3 rounded-lg border border-pb-border bg-pb-bg px-5 py-4">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-5 w-5 shrink-0 text-pb-text-muted">
                    <path d="M22.54 6.42a2.78 2.78 0 0 0-1.94-2C18.88 4 12 4 12 4s-6.88 0-8.6.46a2.78 2.78 0 0 0-1.94 2A29 29 0 0 0 1 11.75a29 29 0 0 0 .46 5.33A2.78 2.78 0 0 0 3.4 19.1c1.72.46 8.6.46 8.6.46s6.88 0 8.6-.46a2.78 2.78 0 0 0 1.94-1.93 29 29 0 0 0 .46-5.42 29 29 0 0 0-.46-5.33z" />
                    <polygon points="9.75 15.02 15.5 11.75 9.75 8.48 9.75 15.02" />
                  </svg>
                  <span className="font-mono text-[14px] text-pb-text-secondary">
                    https://youtube.com/watch?v=dQw4w9WgXcQ
                  </span>
                </div>

                <div className="mt-6 flex items-center gap-3">
                  <span className="font-pb-mono rounded-full bg-emerald-900/30 px-3 py-1 text-[9px] font-bold tracking-widest text-emerald-400 uppercase">
                    Detected: English
                  </span>
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4 w-4 text-pb-text-muted">
                    <path d="M5 12h14M12 5l7 7-7 7" />
                  </svg>
                  <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
                    Target: Korean
                  </span>
                </div>

                <div className="mt-8 space-y-3">
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-pb-bg p-4 font-mono text-[12px]">
                      <span className="text-pb-text-muted">00:00:05 → 00:00:08</span>
                      <p className="mt-1 text-pb-text-secondary">Never gonna give you up</p>
                    </div>
                    <div className="rounded-lg bg-[#f5f0e6] p-4 font-mono text-[12px]">
                      <span className="text-[#a09a88]">00:00:05 → 00:00:08</span>
                      <p className="mt-1 text-[#1a1914]">절대 포기하지 않을 거야</p>
                    </div>
                  </div>
                  <div className="grid grid-cols-2 gap-3">
                    <div className="rounded-lg bg-pb-bg p-4 font-mono text-[12px]">
                      <span className="text-pb-text-muted">00:00:09 → 00:00:12</span>
                      <p className="mt-1 text-pb-text-secondary">Never gonna let you down</p>
                    </div>
                    <div className="rounded-lg bg-[#f5f0e6] p-4 font-mono text-[12px]">
                      <span className="text-[#a09a88]">00:00:09 → 00:00:12</span>
                      <p className="mt-1 text-[#1a1914]">절대 실망시키지 않을 거야</p>
                    </div>
                  </div>
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
            Link. Translate. Upload.
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
            Captions translated. Timing untouched.
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
            Get notified when YouTube translation launches.
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
