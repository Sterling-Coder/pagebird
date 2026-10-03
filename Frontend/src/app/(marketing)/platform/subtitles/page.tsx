import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "SRT / VTT Subtitle Translation — Pagebirdy",
  description:
    "Translate subtitle files into 40+ languages. Every cue stays synced to its original timecode — no re-timing, no manual offsets.",
};

const FEATURES = [
  { n: "01", title: "Timing preserved", desc: "Every cue stays locked to its original in/out timecode. Translation never shifts a single millisecond." },
  { n: "02", title: "40+ languages", desc: "From Arabic to Vietnamese, including right-to-left scripts. One upload, one translated file back." },
  { n: "03", title: "SRT + VTT", desc: "Both subtitle formats supported. Output matches whatever you uploaded — no conversion step." },
  { n: "04", title: "Speaker labels kept", desc: "[Speaker name:] prefixes and character labels survive the translation intact." },
  { n: "05", title: "Formatting preserved", desc: "Italic and bold markers, HTML tags inside cues — they all come through unchanged." },
  { n: "06", title: "Batch translate", desc: "Upload a folder of SRT files and translate them all in one go. One language or many." },
];

const USE_CASES = [
  { label: "YouTube", desc: "Translate auto-generated captions into any language. Upload straight back to YouTube." },
  { label: "Streaming", desc: "Localise Netflix, Prime or Vimeo content for new markets without re-encoding the video." },
  { label: "Corporate training", desc: "Make internal video training accessible to global teams overnight." },
  { label: "Online courses", desc: "Reach more students. Translated subtitles on every lecture, timing untouched." },
];

const SRT_SOURCE = `1
00:00:01,000 --> 00:00:04,200
[Host] Welcome back to the channel.
Today we're covering three topics.

2
00:00:04,800 --> 00:00:08,400
First: why layout preservation matters
when translating documents.

3
00:00:09,000 --> 00:00:12,600
<i>Every cue — exactly on time.</i>`;

const SRT_TRANSLATED = `1
00:00:01,000 --> 00:00:04,200
[主持人] 欢迎回到本频道。
今天我们将讨论三个主题。

2
00:00:04,800 --> 00:00:08,400
首先：翻译文档时
为什么版面保留如此重要。

3
00:00:09,000 --> 00:00:12,600
<i>每个字幕 — 精准同步。</i>`;

export default function SubtitlesPage() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section
        className="relative min-h-screen overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 110% 75% at 68% 28%, #5c14c8 0%, #280a82 18%, #0e0830 40%, #0a090f 70%)",
        }}
      >
        {/* Scan lines */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(140,100,255,0.07) 0px, rgba(140,100,255,0.07) 1px, transparent 1px, transparent 170px)",
          }}
        />
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(180deg, transparent 0px, transparent 3px, rgba(0,0,0,0.04) 3px, rgba(0,0,0,0.04) 4px)",
          }}
        />

        <div className="relative mx-auto max-w-7xl px-6 pt-36 pb-20 lg:px-10 lg:pt-44 lg:pb-32">
          {/* Label */}
          <div className="mb-8 flex items-center gap-4">
            <div className="flex items-center gap-2">
              <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
              <span
                className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
                style={{ color: "#8b6fbf" }}
              >
                SRT / VTT Subtitles
              </span>
            </div>
            <span
              className="font-pb-mono rounded-full border px-2.5 py-0.5 text-[9px] font-bold tracking-widest uppercase"
              style={{ borderColor: "rgba(139,111,191,0.3)", color: "rgba(139,111,191,0.6)" }}
            >
              Coming soon
            </span>
          </div>

          {/* Headline */}
          <h1
            className="font-pb-mono max-w-4xl"
            style={{
              fontSize: "clamp(3.5rem, 9vw, 8rem)",
              lineHeight: 0.92,
              letterSpacing: "-0.02em",
            }}
          >
            <span style={{ color: "rgba(240,236,227,0.2)" }}>Subtitles.</span>
            <br />
            <span style={{ color: "rgba(240,236,227,0.7)" }}>Translated.</span>
            <br />
            <span style={{ color: "#f0ece3" }}>On time.</span>
          </h1>

          <div className="mt-12 flex max-w-5xl flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <p className="max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Upload your SRT or VTT file. Every cue comes back translated —
              and stays synced to its original timecode. No manual offset, no
              re-timing.
            </p>
            <div className="flex shrink-0 items-center gap-5">
              <Link
                href="/contact"
                className="font-pb-mono rounded-full px-7 py-3 text-[12px] font-bold tracking-widest uppercase transition-all hover:brightness-110"
                style={{ background: "#8b6fbf", color: "#0a090f" }}
              >
                Join the waitlist
              </Link>
              <span className="font-pb-mono text-[12px] tracking-widest text-pb-text-muted uppercase">
                Shipping soon →
              </span>
            </div>
          </div>

          {/* SRT mock — before / after */}
          <div
            className="mt-20 overflow-hidden"
            style={{ border: "1px solid rgba(139,111,191,0.18)", borderRadius: "2px" }}
          >
            <div className="grid grid-cols-1 md:grid-cols-2">
              {/* Source */}
              <div
                className="p-8 lg:p-12"
                style={{ background: "#0a0910", borderRight: "1px solid rgba(139,111,191,0.12)" }}
              >
                <div className="mb-6 flex items-center justify-between">
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                    Source · English
                  </span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted/50">.srt</span>
                </div>
                <pre
                  className="font-pb-mono whitespace-pre-wrap text-[13px] leading-relaxed"
                  style={{ color: "rgba(240,236,227,0.55)" }}
                >
                  {SRT_SOURCE}
                </pre>
              </div>

              {/* Translated */}
              <div className="p-8 lg:p-12" style={{ background: "#110e1e" }}>
                <div className="mb-6 flex items-center justify-between">
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                    Translated · Chinese
                  </span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted/50">.zh.srt</span>
                </div>
                <pre
                  className="font-pb-mono whitespace-pre-wrap text-[13px] leading-relaxed"
                  style={{ color: "rgba(240,236,227,0.85)" }}
                >
                  {SRT_TRANSLATED}
                </pre>
              </div>
            </div>

            {/* Footer strip */}
            <div
              className="px-8 py-3 lg:px-12"
              style={{ borderTop: "1px solid rgba(139,111,191,0.12)", background: "#0a090f" }}
            >
              <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                Timecodes untouched · cue count identical · ready to upload
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section style={{ background: "#0a090f" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="mb-6 flex items-center gap-2">
            <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
            <span
              className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
              style={{ color: "#8b6fbf" }}
            >
              How it works
            </span>
          </div>
          <h2
            className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl lg:text-6xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Three steps.
            <br />
            Zero re-timing.
          </h2>

          <div
            className="mt-20 grid grid-cols-1 gap-0 md:grid-cols-3"
            style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
          >
            {[
              { n: "01", title: "Upload", desc: "Drop an .srt or .vtt file. We parse every cue — timecode, speaker label, formatting mark." },
              { n: "02", title: "Pick a language", desc: "Choose from 40+ target languages. We translate the text, leave every timestamp exactly as it was." },
              { n: "03", title: "Download", desc: "Same format, same cue count, same timecodes. Upload straight to YouTube, Vimeo or your editor." },
            ].map((s, i) => (
              <div
                key={s.n}
                className="py-10"
                style={{
                  borderRight: i < 2 ? "1px solid rgba(255,255,255,0.05)" : undefined,
                  paddingRight: i < 2 ? "2.5rem" : undefined,
                  paddingLeft: i > 0 ? "2.5rem" : undefined,
                }}
              >
                <span
                  className="font-pb-mono block text-[80px] font-bold leading-none"
                  style={{ color: "rgba(139,111,191,0.08)" }}
                >
                  {s.n}
                </span>
                <h3 className="mt-4 text-[22px] font-bold text-pb-text">{s.title}</h3>
                <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── editorial numbered rows */}
      <section style={{ background: "#0d0b18" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex flex-col justify-between gap-4 pb-12 md:flex-row md:items-end" style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
            <div>
              <div className="mb-6 flex items-center gap-2">
                <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>
                  Capabilities
                </span>
              </div>
              <h2
                className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                Everything a subtitle
                <br />
                file can hold.
              </h2>
            </div>
            <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
              06 features
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2" style={{ borderBottom: "1px solid rgba(255,255,255,0.03)" }}>
            {FEATURES.map((f, i) => (
              <div
                key={f.n}
                className="flex gap-6 py-8"
                style={{
                  borderBottom: "1px solid rgba(255,255,255,0.04)",
                  borderRight: i % 2 === 0 ? "1px solid rgba(255,255,255,0.04)" : undefined,
                  paddingRight: i % 2 === 0 ? "3rem" : undefined,
                  paddingLeft: i % 2 === 1 ? "3rem" : undefined,
                }}
              >
                <span
                  className="font-pb-mono mt-0.5 shrink-0 text-[11px]"
                  style={{ color: "rgba(139,111,191,0.5)" }}
                >
                  {f.n}
                </span>
                <div>
                  <h3 className="text-[15px] font-bold text-pb-text">{f.title}</h3>
                  <p className="mt-1 text-[13px] leading-relaxed text-pb-text-muted">{f.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── USE CASES ─── */}
      <section style={{ background: "#0a090f" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="mb-6 flex items-center gap-2">
            <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>
              Use cases
            </span>
          </div>
          <h2
            className="font-pb-mono mb-16 text-4xl font-bold text-pb-text md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            For every screen,
            <br />
            every language.
          </h2>

          <div className="grid grid-cols-1 gap-0 md:grid-cols-2 lg:grid-cols-4" style={{ borderLeft: "1px solid rgba(255,255,255,0.05)", borderTop: "1px solid rgba(255,255,255,0.05)" }}>
            {USE_CASES.map((u) => (
              <div
                key={u.label}
                className="p-8"
                style={{ borderRight: "1px solid rgba(255,255,255,0.05)", borderBottom: "1px solid rgba(255,255,255,0.05)" }}
              >
                <span className="font-pb-mono block text-[13px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>
                  {u.label}
                </span>
                <p className="mt-3 text-[13.5px] leading-relaxed text-pb-text-muted">{u.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FORMATS ─── */}
      <section style={{ background: "#0d0b18", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-8 lg:px-10">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-pb-mono mr-6 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Formats
            </span>
            {[".srt", ".vtt"].map((f) => (
              <span
                key={f}
                className="font-pb-mono px-4 py-1.5 text-[12px] text-pb-text-muted"
                style={{ border: "1px solid rgba(255,255,255,0.06)" }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ background: "#5c14c8" }}>
        <div
          className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-10 lg:py-24"
        >
          <div>
            <h2
              className="font-pb-mono max-w-2xl text-3xl font-bold md:text-5xl"
              style={{ letterSpacing: "-0.02em", color: "rgba(240,236,227,0.95)" }}
            >
              Be first to know
              <br />
              when subtitles launch.
            </h2>
            <p className="mt-4 text-[15px] text-pb-text-muted">
              We&rsquo;ll ship it fast. Join the waitlist and we&rsquo;ll notify you first.
            </p>
          </div>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 px-8 py-3.5 text-[12px] font-bold tracking-widest uppercase transition-all"
            style={{
              border: "2px solid rgba(240,236,227,0.9)",
              color: "rgba(240,236,227,0.9)",
            }}
          >
            Join the waitlist →
          </Link>
        </div>
      </section>
    </>
  );
}
