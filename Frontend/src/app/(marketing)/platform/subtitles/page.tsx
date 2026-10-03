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

        <div className="relative mx-auto max-w-[1100px] px-8 pt-36 pb-20 lg:px-14 lg:pt-44 lg:pb-32">
          {/* Label row */}
          <div className="pb-enter-label mb-10 flex items-center justify-between">
            <div className="flex items-center gap-3">
              <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>
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

          {/* Two-column: headline left, description right */}
          <div className="grid grid-cols-1 items-end gap-12 lg:grid-cols-[55fr_45fr] lg:gap-16">
            <h1
              className="pb-enter pb-enter-delay-1 pb-stencil"
              style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}
            >
              Subtitles.<br />Translated.<br />On time.
            </h1>

            <div className="pb-enter pb-enter-delay-2 flex flex-col gap-8">
              <p className="text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
                Upload your SRT or VTT file. Every cue comes back translated —
                and stays synced to its original timecode. No manual offset, no
                re-timing.
              </p>
              <div className="pb-enter pb-enter-delay-3 flex items-center gap-5">
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

      {/* ─── PIPELINE DIAGRAM ─── */}
      <section className="pb-glass-section" style={{ background: "#0d0b14" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
          <div className="mb-6 flex items-center gap-2">
            <span className="inline-block h-2 w-2" style={{ background: "#8b6fbf" }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#8b6fbf" }}>
              The Pipeline
            </span>
          </div>
          <h2
            className="font-pb-mono mb-16 text-4xl font-bold text-pb-text md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Six steps.
            <br />
            Zero re-timing.
          </h2>

          {/* Horizontal flow — scrollable on mobile */}
          <div className="overflow-x-auto pb-4">
            <div className="flex min-w-max items-stretch gap-0">
              {[
                { n: "01", title: "Upload", desc: ".srt or .vtt file in", color: "#8b6fbf" },
                { n: "02", title: "Parse", desc: "Timecodes and cue text separated", color: "#7a5cb0" },
                { n: "03", title: "Extract", desc: "Text isolated, tags preserved", color: "#694da0" },
                { n: "04", title: "Translate", desc: "Cue text translated (40+ languages)", color: "#5a3e90" },
                { n: "05", title: "Rebuild", desc: "Timecodes reattached exactly", color: "#4b2f80" },
                { n: "06", title: "Export", desc: "Ready-to-upload .srt back", color: "#8b6fbf" },
              ].map((stage, i) => (
                <div key={stage.n} className="flex items-center">
                  <div
                    className="flex flex-col gap-3 p-6"
                    style={{
                      minWidth: "160px",
                      background: "rgba(255,255,255,0.02)",
                      borderLeft: `3px solid ${stage.color}`,
                      border: "1px solid rgba(255,255,255,0.06)",
                      borderLeftWidth: "3px",
                      borderLeftColor: stage.color,
                    }}
                  >
                    <span className="font-pb-mono text-[11px]" style={{ color: "rgba(139,111,191,0.5)" }}>{stage.n}</span>
                    <span className="text-[15px] font-bold text-pb-text">{stage.title}</span>
                    <span className="text-[12px] leading-snug text-pb-text-muted">{stage.desc}</span>
                  </div>
                  {i < 5 && (
                    <span className="font-pb-mono mx-3 shrink-0 text-[18px]" style={{ color: "rgba(139,111,191,0.35)" }}>→</span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Timecode preservation visual */}
          <div className="mt-20">
            <div className="mb-8 flex items-center gap-3">
              <h3 className="font-pb-mono text-[22px] font-bold text-pb-text">Timecodes: untouched.</h3>
              <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                Before → After
              </span>
            </div>
            <div className="grid grid-cols-1 gap-0 overflow-hidden md:grid-cols-2" style={{ border: "1px solid rgba(139,111,191,0.15)", borderRadius: "2px" }}>
              {/* English source */}
              <div className="p-8" style={{ background: "#0a090e", borderRight: "1px solid rgba(139,111,191,0.1)" }}>
                <span className="font-pb-mono mb-5 block text-[10px] tracking-widest text-pb-text-muted uppercase">Source · English</span>
                <div className="space-y-5">
                  {[
                    { tc: "00:00:01,000 --> 00:00:04,200", text: "[Host] Welcome back to the channel." },
                    { tc: "00:00:04,800 --> 00:00:08,400", text: "First: why layout preservation matters." },
                    { tc: "00:00:09,000 --> 00:00:12,600", text: "<i>Every cue — exactly on time.</i>" },
                  ].map((cue, i) => (
                    <div key={i}>
                      <span className="font-pb-mono block text-[12px]" style={{ color: "#8b6fbf" }}>{cue.tc}</span>
                      <span className="font-pb-mono block mt-1 text-[13px]" style={{ color: "rgba(240,236,227,0.6)" }}>{cue.text}</span>
                    </div>
                  ))}
                </div>
              </div>
              {/* French translated */}
              <div className="p-8" style={{ background: "#0d0b14" }}>
                <span className="font-pb-mono mb-5 block text-[10px] tracking-widest text-pb-text-muted uppercase">Translated · French</span>
                <div className="space-y-5">
                  {[
                    { tc: "00:00:01,000 --> 00:00:04,200", text: "[Hôte] Bienvenue sur la chaîne." },
                    { tc: "00:00:04,800 --> 00:00:08,400", text: "D'abord : pourquoi la mise en page compte." },
                    { tc: "00:00:09,000 --> 00:00:12,600", text: "<i>Chaque sous-titre — exactement à l'heure.</i>" },
                  ].map((cue, i) => (
                    <div key={i}>
                      <span className="font-pb-mono block text-[12px]" style={{ color: "#4ade80" }}>{cue.tc}</span>
                      <span className="font-pb-mono block mt-1 text-[13px]" style={{ color: "rgba(240,236,227,0.85)" }}>{cue.text}</span>
                    </div>
                  ))}
                </div>
              </div>
            </div>
            <p className="font-pb-mono mt-3 text-[11px] tracking-widest text-pb-text-muted uppercase">
              Purple = source timecodes · Green = same timecodes after translation · Text changes, timing never does.
            </p>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="pb-glass-section" style={{ background: "#0a090f" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
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
            {/* 01 Upload */}
            <div className="py-10" style={{ borderRight: "1px solid rgba(255,255,255,0.05)", paddingRight: "2.5rem" }}>
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(139,111,191,0.08)" }}>01</span>
              <div className="mt-3 mb-4 flex items-center gap-2 opacity-60" style={{ border: "1px dashed rgba(139,111,191,0.35)", borderRadius: "6px", padding: "8px 12px", display: "inline-flex" }}>
                <span className="font-pb-mono text-[10px]" style={{ color: "#8b6fbf" }}>episode_01.srt</span>
                <span className="font-pb-mono text-[9px] text-pb-text-muted">· 48 cues</span>
              </div>
              <h3 className="mt-2 text-[22px] font-bold text-pb-text">Upload</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Drop an .srt or .vtt file. We parse every cue — timecode, speaker label, formatting mark.</p>
            </div>

            {/* 02 Pick a language */}
            <div className="py-10" style={{ borderRight: "1px solid rgba(255,255,255,0.05)", paddingLeft: "2.5rem", paddingRight: "2.5rem" }}>
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(139,111,191,0.08)" }}>02</span>
              <div className="mt-3 mb-4 flex flex-wrap gap-1.5 opacity-60">
                {["French", "Spanish", "German", "Japanese"].map((l) => (
                  <span key={l} className="font-pb-mono rounded-full border border-white/15 px-2 py-0.5 text-[9px] text-pb-text-muted">{l}</span>
                ))}
                <span className="font-pb-mono rounded-full border px-2 py-0.5 text-[9px]" style={{ borderColor: "rgba(139,111,191,0.3)", color: "#8b6fbf", background: "rgba(139,111,191,0.1)" }}>+36</span>
              </div>
              <h3 className="mt-2 text-[22px] font-bold text-pb-text">Pick a language</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Choose from 40+ targets. We translate the text, leave every timestamp exactly as it was.</p>
            </div>

            {/* 03 Download */}
            <div className="py-10" style={{ paddingLeft: "2.5rem" }}>
              <span className="font-pb-mono block text-[80px] font-bold leading-none" style={{ color: "rgba(139,111,191,0.08)" }}>03</span>
              <div className="mt-3 mb-4 opacity-60">
                <div className="flex items-center gap-2">
                  <span style={{ color: "#4ade80", fontSize: "14px" }}>✓</span>
                  <span className="font-pb-mono text-[11px] text-pb-text">episode_01.fr.srt</span>
                </div>
                <div className="mt-1.5 font-pb-mono text-[9px] text-pb-text-muted">00:00:01,000 → 00:00:04,000 · intact</div>
              </div>
              <h3 className="mt-2 text-[22px] font-bold text-pb-text">Download</h3>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">Same format, same cue count, same timecodes. Upload straight to YouTube, Vimeo or your editor.</p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── FEATURES ─── editorial numbered rows */}
      <section className="pb-glass-section" style={{ background: "#0d0b18" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
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
      <section className="pb-glass-section" style={{ background: "#0a090f" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
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
        <div className="mx-auto max-w-[1100px] px-8 py-8 lg:px-14">
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
      <section className="pb-glass-section" style={{ background: "#5c14c8" }}>
        <div
          className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-14 lg:py-24"
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
