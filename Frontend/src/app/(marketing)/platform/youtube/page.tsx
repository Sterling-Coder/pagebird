import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "YouTube Subtitle Translator — Pagebirdy",
  description:
    "Paste a YouTube link. We pull the captions, translate them into 40+ languages, and hand back a ready-to-upload SRT file.",
};

const FEATURES = [
  { n: "01", title: "Auto-fetch captions", desc: "Paste a URL. We pull the captions directly — no download, no manual export needed." },
  { n: "02", title: "All YouTube formats", desc: "Auto-generated or manual captions, community contributions — we handle every format YouTube provides." },
  { n: "03", title: "40+ target languages", desc: "From Spanish to Japanese to Arabic. Right-to-left scripts included." },
  { n: "04", title: "SRT + VTT output", desc: "Download in any format YouTube accepts — or the format your video platform needs." },
  { n: "05", title: "Batch translation", desc: "Paste multiple URLs at once. Translate an entire channel's backlog in one job." },
  { n: "06", title: "Creator-ready", desc: "Output formatted exactly for YouTube's subtitle upload tool. No reformatting needed." },
];

const USE_CASES = [
  { label: "YouTube Creators", desc: "Reach global audiences without recording in multiple languages." },
  { label: "Course Creators", desc: "Make your courses accessible to students worldwide." },
  { label: "Corporate Video", desc: "Localise training videos, product demos, and announcements." },
  { label: "Podcast Clips", desc: "Translate video podcast clips for different regional audiences." },
];

export default function YouTubePage() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section
        className="relative min-h-screen overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 110% 75% at 68% 28%, #c41414 0%, #7a0808 18%, #300410 40%, #0c090a 70%)",
        }}
      >
        {/* Vertical scan lines */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(220,60,60,0.07) 0px, rgba(220,60,60,0.07) 1px, transparent 1px, transparent 170px)",
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
          {/* Badge row */}
          <div className="mb-8 flex items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="inline-block h-2 w-2" style={{ background: "#c94040" }} />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">
                YouTube Subtitle Translator
              </span>
            </div>
            <span
              className="font-pb-mono rounded-full border px-3 py-1 text-[9px] font-bold tracking-widest uppercase"
              style={{ borderColor: "rgba(255,255,255,0.15)", color: "rgba(255,255,255,0.4)" }}
            >
              Coming soon
            </span>
          </div>

          {/* Headline */}
          <h1
            className="pb-enter font-pb-mono max-w-5xl"
            style={{
              fontSize: "clamp(3.5rem, 10vw, 9rem)",
              lineHeight: 0.9,
              letterSpacing: "-0.02em",
              color: "rgba(240,236,227,0.22)",
              fontWeight: 700,
            }}
          >
            YouTube
            <br />
            <span style={{ color: "#f0ece3" }}>captions.</span>
            <br />
            Any language.
          </h1>

          <div className="pb-enter pb-enter-delay-2 mt-12 flex max-w-5xl flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <p className="max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Paste a YouTube link. We pull the captions, translate them into 40+
              languages, and hand back a ready-to-upload SRT file. No account needed.
            </p>
            <div className="flex shrink-0 items-center gap-5">
              <Link
                href="/contact"
                className="font-pb-mono rounded-full px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
                style={{ background: "#c94040" }}
              >
                Join waitlist
              </Link>
              <Link
                href="/platform"
                className="font-pb-mono text-[12px] tracking-widest text-pb-text-secondary uppercase transition-colors hover:text-pb-text"
              >
                All products →
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* ─── URL MOCK ─── */}
      <section style={{ background: "#0c0a09", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="mb-10">
            <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              How it looks
            </span>
          </div>

          {/* URL input mock */}
          <div
            className="overflow-hidden"
            style={{ borderRadius: "12px", border: "1px solid rgba(255,255,255,0.08)" }}
          >
            {/* Input bar */}
            <div
              className="flex items-center gap-4 px-6 py-5"
              style={{ background: "#161412", borderBottom: "1px solid rgba(255,255,255,0.06)" }}
            >
              <span
                className="font-pb-mono flex-1 text-[14px]"
                style={{ color: "rgba(240,236,227,0.35)" }}
              >
                youtube.com/watch?v=dQw4w9WgXcQ
              </span>
              <div className="flex items-center gap-3">
                <span className="font-pb-mono text-[11px] text-pb-text-muted">→ Chinese</span>
                <span
                  className="font-pb-mono rounded-full px-4 py-1.5 text-[11px] font-bold tracking-widest text-white uppercase"
                  style={{ background: "#c94040" }}
                >
                  Translate
                </span>
              </div>
            </div>

            {/* SRT output mock */}
            <div
              className="grid grid-cols-1 gap-0 md:grid-cols-2"
              style={{ background: "#100e0c" }}
            >
              {/* Original */}
              <div
                className="p-8"
                style={{ borderRight: "1px solid rgba(255,255,255,0.04)" }}
              >
                <div className="mb-5 flex items-center justify-between">
                  <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                    Original · English
                  </span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted">.srt</span>
                </div>
                <pre
                  className="font-pb-mono space-y-4 text-[12px] leading-relaxed"
                  style={{ color: "rgba(240,236,227,0.3)" }}
                >
{`1
00:00:01,000 --> 00:00:04,500
Never gonna give you up,
never gonna let you down

2
00:00:04,800 --> 00:00:08,200
Never gonna run around
and desert you`}
                </pre>
              </div>

              {/* Translated */}
              <div className="p-8">
                <div className="mb-5 flex items-center justify-between">
                  <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                    Translated · Chinese
                  </span>
                  <span
                    className="font-pb-mono text-[10px]"
                    style={{ color: "#c94040" }}
                  >
                    Ready to upload
                  </span>
                </div>
                <pre
                  className="font-pb-mono space-y-4 text-[12px] leading-relaxed text-pb-text-secondary"
                >
{`1
00:00:01,000 --> 00:00:04,500
永远不会放弃你，
永远不会让你失望

2
00:00:04,800 --> 00:00:08,200
永远不会跑走
或抛弃你`}
                </pre>
              </div>
            </div>

            {/* Download row */}
            <div
              className="flex items-center justify-between px-6 py-4"
              style={{ background: "#0c0a09", borderTop: "1px solid rgba(255,255,255,0.04)" }}
            >
              <span className="font-pb-mono text-[11px] text-pb-text-muted">
                Timecodes preserved · Upload directly to YouTube Studio
              </span>
              <span
                className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
                style={{ color: "#c94040" }}
              >
                ↓ Download .srt
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── PIPELINE DIAGRAM ─── */}
      <section style={{ background: "#100808", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2" style={{ background: "#c94040" }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#c94040" }}>
              The Pipeline
            </span>
          </div>
          <h2
            className="font-pb-mono mb-16 text-4xl font-bold text-pb-text md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Six steps. Upload-ready.
          </h2>

          {/* 6-stage pipeline */}
          <div className="relative">
            {/* Connecting line */}
            <div
              className="absolute top-8 left-0 right-0 hidden h-px md:block"
              style={{ background: "linear-gradient(90deg, transparent, rgba(201,64,64,0.3) 10%, rgba(201,64,64,0.3) 90%, transparent)" }}
            />
            <div className="grid grid-cols-2 gap-px md:grid-cols-3 lg:grid-cols-6">
              {[
                { n: "01", title: "Paste", desc: "YouTube URL pasted in" },
                { n: "02", title: "Fetch", desc: "Captions pulled via YouTube API" },
                { n: "03", title: "Parse", desc: "Cues and timecodes split" },
                { n: "04", title: "Translate", desc: "Each cue translated (40+ languages)" },
                { n: "05", title: "Format", desc: "YouTube-spec SRT assembled" },
                { n: "06", title: "Download", desc: "Ready to upload to YouTube Studio" },
              ].map((stage, i) => (
                <div
                  key={stage.n}
                  className="relative flex flex-col gap-4 p-6"
                  style={{
                    background: `rgba(201,64,64,${0.03 + i * 0.015})`,
                    border: "1px solid rgba(201,64,64,0.12)",
                  }}
                >
                  <span
                    className="font-pb-mono text-[11px] font-bold tracking-widest"
                    style={{ color: `rgba(201,64,64,${0.4 + i * 0.1})` }}
                  >
                    {stage.n}
                  </span>
                  <h3 className="text-[16px] font-bold text-pb-text">{stage.title}</h3>
                  <p className="text-[12px] leading-relaxed text-pb-text-muted">{stage.desc}</p>
                  {/* Arrow between stages */}
                  {i < 5 && (
                    <span
                      className="absolute -right-3 top-1/2 z-10 hidden -translate-y-1/2 text-[18px] lg:block"
                      style={{ color: "rgba(201,64,64,0.4)" }}
                    >
                      →
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* YouTube Studio upload visual */}
          <div className="mt-16 grid grid-cols-1 gap-8 lg:grid-cols-2">
            {/* Studio mock */}
            <div
              className="overflow-hidden"
              style={{ borderRadius: "12px", border: "1px solid rgba(255,255,255,0.06)", background: "#0e0c0b" }}
            >
              {/* Top bar */}
              <div
                className="flex items-center gap-3 px-5 py-3"
                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)", background: "#161412" }}
              >
                <div className="flex gap-1.5">
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/10" />
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/10" />
                  <span className="inline-block h-2.5 w-2.5 rounded-full bg-white/10" />
                </div>
                <span className="font-pb-mono text-[11px] text-pb-text-muted">YouTube Studio · Subtitles</span>
              </div>

              <div className="p-6">
                <p className="font-pb-mono mb-5 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
                  Subtitles
                </p>

                {/* Uploaded file row */}
                <div
                  className="mb-3 flex items-center justify-between rounded-lg px-4 py-3"
                  style={{ background: "rgba(255,255,255,0.03)", border: "1px solid rgba(255,255,255,0.05)" }}
                >
                  <div className="flex items-center gap-3">
                    <span
                      className="flex h-5 w-5 items-center justify-center rounded-full text-[10px]"
                      style={{ background: "rgba(34,197,94,0.15)", color: "#22c55e" }}
                    >
                      ✓
                    </span>
                    <span className="font-pb-mono text-[12px] text-pb-text">video_title.zh.srt</span>
                  </div>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted">Uploaded</span>
                </div>

                {/* Language badges */}
                <p className="font-pb-mono mb-3 text-[10px] tracking-widest text-pb-text-muted uppercase">
                  Languages
                </p>
                <div className="flex flex-wrap gap-2">
                  {["EN → ZH", "EN → FR", "EN → DE", "EN → ES", "EN → JA", "EN → AR"].map((lang) => (
                    <span
                      key={lang}
                      className="font-pb-mono rounded-full px-3 py-1 text-[10px] font-bold"
                      style={{
                        background: "rgba(201,64,64,0.12)",
                        border: "1px solid rgba(201,64,64,0.25)",
                        color: "#c94040",
                      }}
                    >
                      {lang}
                    </span>
                  ))}
                </div>
              </div>
            </div>

            {/* Caption */}
            <div className="flex flex-col justify-center">
              <h3
                className="font-pb-mono text-2xl font-bold text-pb-text md:text-3xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                Drop it straight into<br />YouTube Studio.
              </h3>
              <p className="mt-4 text-[15px] leading-relaxed text-pb-text-muted">
                No editing. No reformatting. Our SRT output is spec-compliant with YouTube&apos;s subtitle upload tool — upload it directly and you&apos;re done.
              </p>
              <p className="mt-6 text-[13px] text-pb-text-muted">
                Supports SRT, VTT, and YouTube&apos;s own caption format.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section className="bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2" style={{ background: "#c94040" }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#c94040" }}>
              How it works
            </span>
          </div>
          <h2
            className="font-pb-mono mb-16 text-4xl font-bold text-pb-text md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Paste. Translate. Upload.
          </h2>

          <div className="grid grid-cols-1 gap-0 md:grid-cols-3">
            {[
              { n: "01", title: "Paste your URL", desc: "Drop in any YouTube URL. We handle public videos, unlisted, and playlists." },
              { n: "02", title: "We fetch & translate", desc: "We pull the captions directly from YouTube and translate into your chosen language." },
              { n: "03", title: "Download & upload", desc: "Get your SRT or VTT file. Open YouTube Studio, upload under the video's subtitles tab." },
            ].map((s, i) => (
              <div
                key={s.n}
                className={`py-10 ${i < 2 ? "md:border-r md:pr-10" : ""} ${i > 0 ? "md:pl-10" : ""} ${i < 2 ? "border-b border-white/[0.04] md:border-b-0" : ""}`}
              >
                <span
                  className="font-pb-mono block text-[80px] font-bold leading-none"
                  style={{ color: "rgba(201,64,64,0.12)" }}
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

      {/* ─── FEATURES — horizontal rows ─── */}
      <section style={{ background: "#0c0a09", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 lg:px-10">
          <div className="border-b border-white/[0.04] py-16">
            <h2
              className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl"
              style={{ letterSpacing: "-0.02em" }}
            >
              Everything a creator needs.
            </h2>
          </div>
          {FEATURES.map((f) => (
            <div
              key={f.n}
              className="flex items-start gap-8 border-b border-white/[0.04] py-6"
            >
              <span className="font-pb-mono mt-0.5 w-8 shrink-0 text-[11px]" style={{ color: "#c94040" }}>
                {f.n}
              </span>
              <div className="flex flex-1 flex-col gap-1 md:flex-row md:gap-12">
                <h3 className="w-56 shrink-0 text-[15px] font-bold text-pb-text">{f.title}</h3>
                <p className="text-[14px] leading-relaxed text-pb-text-muted">{f.desc}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* ─── CREATOR STAT SECTION ─── */}
      <section className="bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="grid grid-cols-1 gap-16 md:grid-cols-2">
            <div>
              <p
                className="font-pb-mono text-[80px] font-bold leading-none md:text-[100px]"
                style={{ color: "rgba(201,64,64,0.25)" }}
              >
                2.7B
              </p>
              <p className="mt-4 text-[18px] font-semibold text-pb-text">
                YouTube users don&apos;t speak English.
              </p>
              <p className="mt-3 text-[14px] leading-relaxed text-pb-text-muted">
                Your content exists. Your audience exists. The only gap is language.
              </p>
            </div>
            <div className="flex flex-col justify-center">
              <h2
                className="font-pb-mono text-3xl font-bold text-pb-text md:text-4xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                Your content.<br />Every language.<br />Every market.
              </h2>
              <p className="mt-6 text-[15px] leading-relaxed text-pb-text-muted">
                Built for YouTube creators who publish globally — no translation agency, no
                per-minute pricing, no waiting. One link, 40+ languages, minutes.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── USE CASES ─── */}
      <section style={{ background: "#0c0a09", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="flex items-center gap-3 mb-12">
            <span className="inline-block h-2 w-2" style={{ background: "#c94040" }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: "#c94040" }}>
              Use cases
            </span>
          </div>
          <div className="grid grid-cols-1 gap-0 md:grid-cols-2 lg:grid-cols-4">
            {USE_CASES.map((u, i) => (
              <div
                key={u.label}
                className={`py-8 ${i < 3 ? "md:border-r md:pr-8" : ""} ${i > 0 ? "md:pl-8" : ""} ${i < 2 ? "border-b border-white/[0.04] lg:border-b-0" : ""}`}
              >
                <h3 className="text-[17px] font-bold text-pb-text">{u.label}</h3>
                <p className="mt-2 text-[13px] leading-relaxed text-pb-text-muted">{u.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ background: "#c94040" }}>
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-10 lg:py-24">
          <h2
            className="font-pb-mono max-w-2xl text-3xl font-bold text-white md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Join the waitlist for<br />YouTube Subtitle Translator.
          </h2>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 border-2 border-white bg-white px-8 py-3.5 text-[12px] font-bold tracking-widest uppercase transition-all hover:bg-transparent hover:text-white"
            style={{ color: "#c94040" }}
          >
            Join waitlist →
          </Link>
        </div>
      </section>
    </>
  );
}
