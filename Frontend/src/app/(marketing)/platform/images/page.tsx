import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Image Translator — Pagebirdy",
  description:
    "Detect and translate text embedded in any image — signs, labels, infographics, product packaging — rendered back in place, matching the original style.",
};

const FEATURES = [
  { n: "01", title: "OCR for any format", desc: "AI-powered text detection across raster and vector formats. Nothing is missed." },
  { n: "02", title: "Font style matching", desc: "Translated text is rendered back in the original weight, size, and approximate style." },
  { n: "03", title: "Signs, labels & menus", desc: "Street signs, product labels, restaurant menus, wayfinding — all handled." },
  { n: "04", title: "Vector + raster", desc: "Works on AI, PSD, EPS, PNG, JPG, and SVG files without destroying the source." },
  { n: "05", title: "Batch processing", desc: "Upload a folder of images. Every piece of text in every file comes back translated." },
  { n: "06", title: "40+ languages", desc: "Including right-to-left scripts — Arabic and Hebrew render correctly in-place." },
];

const USE_CASES = [
  "Product packaging",
  "Infographics",
  "Signage & wayfinding",
  "Marketing materials",
  "Training documents",
  "UI screenshots",
];

const FORMATS = [".ai", ".psd", ".eps", ".png", ".jpg", ".svg", ".webp"];

const ACCENT = "#4a9e8a";
const ACCENT_DIM = "rgba(74,158,138,0.15)";

export default function ImagesPage() {
  return (
    <>
      {/* ─── HERO ─── */}
      <section
        className="relative min-h-screen overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 110% 75% at 68% 28%, #0a7870 0%, #053830 18%, #021818 40%, #0a0c0b 70%)",
        }}
      >
        {/* Vertical scan lines */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(60,200,180,0.07) 0px, rgba(60,200,180,0.07) 1px, transparent 1px, transparent 170px)",
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
              <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
              <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
                Image Translator
              </span>
            </div>
            <span className="font-pb-mono rounded-full border px-3 py-0.5 text-[9px] font-bold tracking-widest uppercase"
              style={{ borderColor: "rgba(74,158,138,0.3)", color: ACCENT, background: ACCENT_DIM }}>
              Coming soon
            </span>
          </div>

          <div className="grid grid-cols-1 items-end gap-12 lg:grid-cols-[55fr_45fr] lg:gap-16">
            <h1
              className="pb-enter pb-enter-delay-1 pb-stencil"
              style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}
            >
              Text in images.<br />Translated<br />in place.
            </h1>
            <div className="pb-enter pb-enter-delay-2 flex flex-col gap-8">
              <p className="text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
                Detect text embedded in any image — signs, labels, infographics, product
                packaging — and render it back translated, matching the original style.
              </p>
              <div className="pb-enter pb-enter-delay-3 flex items-center gap-5">
                <Link href="/contact" className="font-pb-mono rounded-full px-7 py-3 text-[12px] font-bold tracking-widest uppercase transition-all hover:brightness-110"
                  style={{ background: ACCENT, color: "#0a0c0b" }}>
                  Join waitlist
                </Link>
                <span className="font-pb-mono text-[12px] tracking-widest text-pb-text-muted uppercase">· No card required</span>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── OCR DETECTION DIAGRAM ─── */}
      <section style={{ background: "#080f0e", borderTop: "1px solid rgba(74,158,138,0.08)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:items-center">
            {/* Left: text */}
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
                  Detection
                </span>
              </div>
              <h2 className="font-pb-mono text-3xl font-bold text-pb-text md:text-4xl" style={{ letterSpacing: "-0.02em" }}>
                Found 14 text regions.
              </h2>
              <p className="mt-5 text-[15px] leading-relaxed text-pb-text-secondary">
                Google Cloud Vision scans every pixel. Text in signs, labels, infographics, product packaging, street signs — all detected, all translatable. Nothing is missed because nothing is a text layer — it&apos;s all pixels.
              </p>
              <p className="mt-6 font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
                Supported: .ai · .psd · .eps · .png · .jpg · .svg
              </p>
            </div>

            {/* Right: CSS OCR detection diagram */}
            <div className="relative" style={{
              background: "#0a1a14",
              border: "1px solid rgba(74,158,138,0.15)",
              borderRadius: "8px",
              padding: "32px",
              minHeight: "320px",
            }}>
              <div className="font-pb-mono mb-4 text-[10px] tracking-widest text-pb-text-muted uppercase">Source image</div>

              {/* Mock image background */}
              <div className="relative overflow-hidden" style={{
                background: "repeating-linear-gradient(45deg, rgba(255,255,255,0.02) 0px, rgba(255,255,255,0.02) 1px, transparent 1px, transparent 12px)",
                border: "1px dashed rgba(255,255,255,0.15)",
                borderRadius: "4px",
                height: "220px",
                padding: "12px",
              }}>
                {/* Simulated detected bounding boxes at various positions */}
                {[
                  { top: "8%", left: "5%", w: "45%", label: "Heading", color: "#e08a6f" },
                  { top: "8%", left: "55%", w: "35%", label: "Price tag", color: "#8b6fbf" },
                  { top: "35%", left: "5%", w: "60%", label: "Sign text", color: ACCENT },
                  { top: "55%", left: "5%", w: "40%", label: "Caption", color: "#c8a820" },
                  { top: "55%", left: "50%", w: "45%", label: "Label", color: "#c94040" },
                  { top: "78%", left: "5%", w: "85%", label: "Footer text", color: ACCENT },
                ].map((box, i) => (
                  <div key={i} style={{
                    position: "absolute",
                    top: box.top, left: box.left, width: box.w,
                    height: "16%",
                    border: `1.5px dashed ${box.color}`,
                    borderRadius: "2px",
                  }}>
                    <span style={{
                      position: "absolute", top: "-16px", left: "0",
                      fontFamily: "var(--font-space-mono), monospace",
                      fontSize: "8px", color: box.color, whiteSpace: "nowrap",
                      background: "#0a1a14", padding: "0 3px",
                    }}>{box.label}</span>
                  </div>
                ))}
                {/* Detection count badge */}
                <div style={{
                  position: "absolute", bottom: "8px", right: "8px",
                  background: `rgba(74,158,138,0.9)`, color: "#0a1a14",
                  fontFamily: "var(--font-space-mono), monospace",
                  fontSize: "10px", fontWeight: 700, padding: "3px 10px", borderRadius: "4px",
                }}>14 regions detected</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── IMAGE MOCK ─── */}
      <section className="pb-glass-section bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="overflow-hidden" style={{ border: "1px solid rgba(255,255,255,0.08)", borderRadius: "2px" }}>
            <div className="grid grid-cols-2">
              {/* Source image mock — a street sign in English */}
              <div
                className="flex flex-col items-center justify-center gap-8 border-r p-12 lg:p-16"
                style={{ borderColor: "rgba(255,255,255,0.07)", background: "#0e0d0b", minHeight: "320px" }}
              >
                <div className="flex items-center justify-between w-full mb-4">
                  <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">Source image · English</span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted/50">.png</span>
                </div>
                {/* CSS sign art */}
                <div
                  className="flex w-full max-w-xs flex-col gap-3 p-6"
                  style={{ background: "#1e3a2e", border: "3px solid #2d5a44", borderRadius: "4px" }}
                >
                  <div className="h-[3px] w-[70%] self-center" style={{ background: "rgba(255,255,255,0.5)" }} />
                  <div className="h-[3px] w-[90%] self-center" style={{ background: "rgba(255,255,255,0.3)" }} />
                  <div className="mt-2 flex flex-col gap-2">
                    <div className="h-[10px] w-[55%]" style={{ background: "rgba(255,255,255,0.6)" }} />
                    <div className="h-[10px] w-[40%]" style={{ background: "rgba(255,255,255,0.4)" }} />
                  </div>
                  <div className="mt-3 h-[3px] w-[60%] self-center" style={{ background: "rgba(255,255,255,0.2)" }} />
                </div>
                <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                  Original text detected
                </span>
              </div>

              {/* Translated image mock */}
              <div
                className="flex flex-col items-center justify-center gap-8 p-12 lg:p-16"
                style={{ background: "#0a1f18", minHeight: "320px" }}
              >
                <div className="flex items-center justify-between w-full mb-4">
                  <span className="font-pb-mono text-[11px] tracking-widest uppercase" style={{ color: ACCENT }}>Translated · Arabic</span>
                  <span className="font-pb-mono text-[10px] text-pb-text-muted/50">.png</span>
                </div>
                {/* CSS sign art — Arabic version (RTL) */}
                <div
                  className="flex w-full max-w-xs flex-col gap-3 p-6"
                  style={{ background: "#1e3a2e", border: "3px solid #2d5a44", borderRadius: "4px" }}
                >
                  <div className="h-[3px] w-[70%] self-center" style={{ background: "rgba(74,158,138,0.6)" }} />
                  <div className="h-[3px] w-[90%] self-center" style={{ background: "rgba(74,158,138,0.3)" }} />
                  <div className="mt-2 flex flex-col items-end gap-2">
                    <div className="h-[10px] w-[55%]" style={{ background: "rgba(74,158,138,0.7)" }} />
                    <div className="h-[10px] w-[40%]" style={{ background: "rgba(74,158,138,0.4)" }} />
                  </div>
                  <div className="mt-3 h-[3px] w-[60%] self-center" style={{ background: "rgba(74,158,138,0.2)" }} />
                </div>
                <span className="font-pb-mono text-[10px] tracking-widest uppercase" style={{ color: ACCENT }}>
                  Text rendered back in place
                </span>
              </div>
            </div>
            {/* Bottom bar */}
            <div
              className="px-8 py-3"
              style={{ borderTop: "1px solid rgba(255,255,255,0.05)", background: "#0e0d0b" }}
            >
              <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted uppercase">
                Same image structure · same layout · text replaced in position
              </span>
            </div>
          </div>
        </div>
      </section>

      {/* ─── SIGN BEFORE / AFTER ─── */}
      <section style={{ background: "#060d0c", borderTop: "1px solid rgba(74,158,138,0.08)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="flex flex-col items-start gap-10 lg:flex-row lg:items-center lg:gap-16">
            {/* Before */}
            <div className="flex-1">
              <span className="font-pb-mono mb-4 block text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Before</span>
              <div
                className="flex flex-col items-center justify-center gap-4 p-10"
                style={{ background: "#0e1a15", border: "2px solid rgba(255,255,255,0.08)", borderRadius: "4px" }}
              >
                {/* Fake sign */}
                <div
                  className="w-full max-w-[260px] px-6 py-5 text-center"
                  style={{ background: "#1a3828", border: "3px solid #2a5840" }}
                >
                  <div className="font-pb-mono text-[13px] font-bold tracking-widest text-white">OPEN DAILY</div>
                  <div className="font-pb-mono mt-1 text-[11px] tracking-widest" style={{ color: "rgba(255,255,255,0.6)" }}>9AM – 5PM</div>
                  <div className="mt-3 h-px w-full" style={{ background: "rgba(255,255,255,0.15)" }} />
                  <div className="font-pb-mono mt-3 text-[10px] tracking-widest" style={{ color: "rgba(255,255,255,0.4)" }}>PARKING AVAILABLE</div>
                </div>
                <div
                  className="rounded-full px-3 py-1 font-pb-mono text-[10px] tracking-widest uppercase"
                  style={{ background: "rgba(255,80,80,0.15)", color: "#ff6060", border: "1px solid rgba(255,80,80,0.25)" }}
                >
                  English text detected
                </div>
              </div>
            </div>

            {/* Arrow */}
            <div className="flex items-center justify-center lg:flex-col">
              <span className="font-pb-mono text-[28px] font-bold" style={{ color: ACCENT }}>→</span>
            </div>

            {/* After */}
            <div className="flex-1">
              <span className="font-pb-mono mb-4 block text-[10px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>After · Arabic</span>
              <div
                className="flex flex-col items-center justify-center gap-4 p-10"
                style={{ background: "#0a1f1a", border: `2px solid rgba(74,158,138,0.25)`, borderRadius: "4px" }}
              >
                {/* Same sign, Arabic */}
                <div
                  className="w-full max-w-[260px] px-6 py-5 text-center"
                  style={{ background: "#1a3828", border: `3px solid rgba(74,158,138,0.4)` }}
                >
                  <div className="font-pb-mono text-[13px] font-bold tracking-widest" style={{ color: ACCENT }}>مفتوح يومياً</div>
                  <div className="font-pb-mono mt-1 text-[11px] tracking-widest" style={{ color: `${ACCENT}80` }}>٩ص – ٥م</div>
                  <div className="mt-3 h-px w-full" style={{ background: `${ACCENT}20` }} />
                  <div className="font-pb-mono mt-3 text-[10px] tracking-widest" style={{ color: `${ACCENT}50` }}>مواقف متاحة</div>
                </div>
                <div
                  className="rounded-full px-3 py-1 font-pb-mono text-[10px] tracking-widest uppercase"
                  style={{ background: "rgba(74,158,138,0.15)", color: ACCENT, border: `1px solid rgba(74,158,138,0.3)` }}
                >
                  Rendered back in place
                </div>
              </div>
            </div>
          </div>

          <p className="mt-8 text-center font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
            Same position. Same style. Translated.
          </p>
        </div>
      </section>

      {/* ─── PIPELINE DIAGRAM ─── */}
      <section className="pb-glass-section bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
              The Pipeline
            </span>
          </div>
          <h2
            className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Six steps.<br />Same pixels.
          </h2>

          <div className="mt-16 grid grid-cols-1 gap-0 md:grid-cols-2 lg:grid-cols-3">
            {[
              { n: "01", title: "Upload", desc: "AI, PSD, PNG, JPG accepted", color: ACCENT },
              { n: "02", title: "Detect", desc: "OCR finds every text region", color: "#3a9e82" },
              { n: "03", title: "Map", desc: "Position, size, font style captured", color: "#2a8e72" },
              { n: "04", title: "Translate", desc: "Text translated, length matched", color: "#1a7e62" },
              { n: "05", title: "Match", desc: "Font style identified and matched", color: "#0a6e52" },
              { n: "06", title: "Render", desc: "Translated text drawn back in place", color: "#005e42" },
            ].map((stage, i) => (
              <div
                key={stage.n}
                className="flex gap-5 py-8"
                style={{
                  borderBottom: i < 3 ? "1px solid rgba(255,255,255,0.04)" : undefined,
                  borderRight: i % 3 !== 2 ? "1px solid rgba(255,255,255,0.04)" : undefined,
                  paddingLeft: i % 3 === 0 ? "0" : "2rem",
                  paddingRight: i % 3 === 2 ? "0" : "2rem",
                }}
              >
                <div
                  className="mt-1 h-full w-[3px] shrink-0 self-stretch"
                  style={{ background: stage.color, minHeight: "48px" }}
                />
                <div>
                  <span className="font-pb-mono text-[11px]" style={{ color: stage.color }}>{stage.n}</span>
                  <h3 className="mt-1 text-[17px] font-bold text-pb-text">{stage.title}</h3>
                  <p className="mt-1 text-[13px] text-pb-text-muted">{stage.desc}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── LAYERS PRESERVED ─── */}
      <section style={{ background: "rgba(74,158,138,0.04)", borderTop: "1px solid rgba(74,158,138,0.1)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:items-center">
            {/* Left: layer panel mock */}
            <div style={{
              background: "#0c1a14",
              border: "1px solid rgba(74,158,138,0.2)",
              borderRadius: "8px",
              overflow: "hidden",
            }}>
              {/* Panel header */}
              <div className="flex items-center gap-2 px-5 py-3" style={{ borderBottom: "1px solid rgba(74,158,138,0.12)", background: "#0a1510" }}>
                <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Layers</span>
                <span className="font-pb-mono text-[10px] text-pb-text-muted">— product_label.psd</span>
              </div>
              {/* Layers */}
              {[
                { name: "Heading text", type: "Text layer", action: "Translated in place", changed: true },
                { name: "Body copy", type: "Text layer", action: "Translated in place", changed: true },
                { name: "Price / quantity", type: "Text layer", action: "Translated in place", changed: true },
                { name: "Product photo", type: "Image layer", action: "Untouched", changed: false },
                { name: "Background", type: "Solid color", action: "Untouched", changed: false },
                { name: "Logo", type: "Smart object", action: "Untouched", changed: false },
              ].map((layer, i) => (
                <div key={i} className="flex items-center justify-between px-5 py-3" style={{
                  borderBottom: i < 5 ? "1px solid rgba(255,255,255,0.04)" : "none",
                  background: layer.changed ? "rgba(74,158,138,0.05)" : "transparent",
                }}>
                  <div className="flex items-center gap-3">
                    <span style={{
                      display: "inline-block", width: "8px", height: "8px", borderRadius: "2px",
                      background: layer.changed ? ACCENT : "rgba(255,255,255,0.2)",
                      flexShrink: 0,
                    }} />
                    <div>
                      <div className="font-pb-mono text-[12px] text-pb-text">{layer.name}</div>
                      <div className="font-pb-mono text-[10px] text-pb-text-muted">{layer.type}</div>
                    </div>
                  </div>
                  <span className="font-pb-mono text-[10px] tracking-wider" style={{
                    color: layer.changed ? ACCENT : "rgba(255,255,255,0.25)",
                  }}>{layer.action}</span>
                </div>
              ))}
            </div>

            {/* Right: text */}
            <div>
              <h2 className="font-pb-mono text-3xl font-bold text-pb-text md:text-4xl" style={{ letterSpacing: "-0.02em" }}>
                Your PSD layers<br />stay intact.
              </h2>
              <p className="mt-5 text-[15px] leading-relaxed text-pb-text-secondary">
                Text layers get translated. Image layers, masks, blend modes, effects — untouched. Open the translated PSD in Photoshop and keep editing exactly where you left off.
              </p>
              <p className="mt-5 text-[15px] leading-relaxed text-pb-text-secondary">
                Same for Illustrator .ai files — text objects are translated, artwork paths are preserved. The structure is identical.
              </p>
              <div className="mt-8 flex flex-col gap-3">
                {[
                  "Text layers → translated",
                  "Image layers → preserved",
                  "Masks & effects → preserved",
                  "Smart objects → preserved",
                ].map(item => (
                  <div key={item} className="flex items-center gap-3 font-pb-mono text-[13px]">
                    <span style={{ color: ACCENT }}>✓</span>
                    <span style={{ color: item.includes("translated") ? "rgba(240,236,227,0.8)" : "rgba(240,236,227,0.4)" }}>{item}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section style={{ background: "#070908", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
              How it works
            </span>
          </div>
          <h2
            className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl lg:text-6xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Upload.<br />Detect.<br />Replace.
          </h2>

          <div className="mt-20 grid grid-cols-1 gap-0 md:grid-cols-3">
            {[
              { n: "01", title: "Upload image", desc: "Drop an AI, PSD, EPS, PNG, JPG, or SVG. We read every layer — nothing is flattened." },
              { n: "02", title: "AI detects text", desc: "Computer vision maps every text region: position, font style, size, color, language." },
              { n: "03", title: "Render in place", desc: "Translated text replaces the original in the exact same position, matched to the original style." },
            ].map((s, i) => (
              <div
                key={s.n}
                className={`border-white/[0.05] py-10 ${i < 2 ? "md:border-r md:pr-10" : ""} ${i > 0 ? "md:pl-10" : ""} ${i < 2 ? "border-b md:border-b-0" : ""}`}
              >
                <span
                  className="font-pb-mono block text-[80px] font-bold leading-none"
                  style={{ color: "rgba(74,158,138,0.12)" }}
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

      {/* ─── FEATURES ─── numbered rows */}
      <section className="pb-glass-section bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-32">
          <div className="flex flex-col justify-between gap-4 border-b pb-12 md:flex-row md:items-end" style={{ borderColor: "rgba(255,255,255,0.05)" }}>
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
                  Capabilities
                </span>
              </div>
              <h2
                className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                Every pixel.<br />Every word.
              </h2>
            </div>
            <span className="font-pb-mono text-[11px] tracking-widest text-pb-text-muted uppercase">
              06 features
            </span>
          </div>

          <div className="grid grid-cols-1 divide-y md:grid-cols-2 md:divide-y-0" style={{ "--tw-divide-opacity": "1" } as React.CSSProperties}>
            {FEATURES.map((f, i) => (
              <div
                key={f.n}
                className={`flex gap-6 py-8 ${i % 2 === 0 ? "md:border-r md:pr-12" : "md:pl-12"}`}
                style={{ borderColor: "rgba(255,255,255,0.04)" }}
              >
                <span className="font-pb-mono mt-0.5 shrink-0 text-[11px]" style={{ color: `${ACCENT}60` }}>
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

      {/* ─── USE CASES ─── rich version */}
      <section style={{ background: "#070908", borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="mb-16 flex flex-col justify-between gap-6 lg:flex-row lg:items-end">
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: ACCENT }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: ACCENT }}>
                  Use cases
                </span>
              </div>
              <h2 className="font-pb-mono text-3xl font-bold text-pb-text md:text-4xl" style={{ letterSpacing: "-0.02em" }}>
                Where image translation<br />actually ships.
              </h2>
            </div>
            <p className="max-w-xs text-[14px] leading-relaxed text-pb-text-muted">
              Any industry that ships visual assets across markets needs image translation. Here&apos;s where it matters most.
            </p>
          </div>
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
            {[
              {
                title: "Product packaging",
                desc: "Translate ingredient lists, instructions, legal copy, and nutritional info on packaging artwork — without rebuilding from scratch.",
                formats: ".ai .psd",
              },
              {
                title: "Infographics",
                desc: "Charts, diagrams, explainer graphics, step-by-step visuals — all text translated in its original position.",
                formats: ".ai .svg .png",
              },
              {
                title: "Signage & wayfinding",
                desc: "Retail signage, venue directories, airport wayfinding, event graphics — adapted for each market.",
                formats: ".ai .psd .eps",
              },
              {
                title: "Social & ad creatives",
                desc: "Adapt social posts, story graphics, banner ads, and display creatives for different language markets.",
                formats: ".psd .png",
              },
              {
                title: "Training materials",
                desc: "Illustrated how-to guides, visual job aids, safety posters, onboarding decks — translated with graphics intact.",
                formats: ".psd .ai .png",
              },
              {
                title: "Menus & hospitality",
                desc: "Restaurant menus, hotel directories, venue guides, room service cards — in any language, same design.",
                formats: ".ai .psd .pdf",
              },
            ].map((u, i) => (
              <div
                key={u.title}
                className="flex flex-col gap-3 p-8"
                style={{
                  borderLeft: `3px solid rgba(74,158,138,${i === 0 ? "0.7" : "0.2"})`,
                  borderBottom: i < 3 ? "1px solid rgba(255,255,255,0.04)" : "none",
                  borderRight: i % 3 !== 2 ? "1px solid rgba(255,255,255,0.04)" : "none",
                  background: i === 0 ? "rgba(74,158,138,0.04)" : "transparent",
                }}
              >
                <h3 className="text-[16px] font-bold text-pb-text">{u.title}</h3>
                <p className="text-[13px] leading-relaxed text-pb-text-muted flex-1">{u.desc}</p>
                <span className="font-pb-mono text-[10px] tracking-widest text-pb-text-muted">{u.formats}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FORMATS ─── */}
      <section className="pb-glass-section bg-pb-bg" style={{ borderTop: "1px solid rgba(255,255,255,0.04)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-8 lg:px-14">
          <div className="flex flex-wrap items-center gap-2">
            <span className="font-pb-mono mr-6 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Formats
            </span>
            {FORMATS.map((f) => (
              <span
                key={f}
                className="font-pb-mono px-4 py-1.5 text-[12px] text-pb-text-muted"
                style={{ border: "1px solid rgba(74,158,138,0.15)" }}
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ background: ACCENT }}>
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-14 lg:py-24">
          <div>
            <h2
              className="font-pb-mono max-w-xl text-3xl font-bold md:text-4xl lg:text-5xl"
              style={{ color: "#0a0c0b", letterSpacing: "-0.02em" }}
            >
              Join the waitlist for<br />Image Translator.
            </h2>
            <p className="mt-3 text-[14px]" style={{ color: "rgba(10,12,11,0.6)" }}>
              Be the first to translate images at scale.
            </p>
          </div>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 border-2 px-8 py-3.5 text-[12px] font-bold tracking-widest uppercase transition-all hover:opacity-80"
            style={{ borderColor: "#0a0c0b", background: "#0a0c0b", color: ACCENT }}
          >
            Join waitlist →
          </Link>
        </div>
      </section>
    </>
  );
}
