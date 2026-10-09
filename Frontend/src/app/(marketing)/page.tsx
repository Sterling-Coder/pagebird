import Link from "next/link";
import { WatchDemoButton } from "@/components/WatchDemoButton";
import ProductDiagram from "@/components/ProductDiagram";
import IntegrationFlow from "@/components/IntegrationFlow";
import PlatformBento from "@/components/PlatformBento";
import ExtensionSection from "@/components/ExtensionSection";
import HeroMockup from "@/components/HeroMockup";
import HeroWall from "@/components/HeroWall";
import HeroScroll from "@/components/HeroScroll";

const FORMATS_EXTENDED = [
  { label: ".idml", soon: false },
  { label: ".pdf", soon: false },
  { label: ".ai", soon: false },
  { label: ".psd", soon: false },
  { label: ".eps", soon: false },
  { label: ".srt", soon: false },
  { label: ".vtt", soon: false },
  { label: ".html", soon: false },
  { label: ".docx", soon: false },
  { label: ".pptx", soon: false },
  { label: ".xlsx", soon: false },
  { label: ".txt", soon: false },
  { label: ".png", soon: false },
  { label: ".jpg", soon: false },
  { label: ".webp", soon: false },
  { label: ".xliff", soon: true },
  { label: ".indd", soon: true },
  { label: ".svg", soon: true },
  { label: ".mp4 subs", soon: true },
];

export default function Home() {
  return (
    <>
      {/* ─── §1 HERO ─── */}
      {/* The light ramp is part of the hero and scrolls away with it; the glass
          wall flattens into hairline rules on the way out. */}
      <div className="pb-hero relative">
      <HeroScroll />
      <div className="pointer-events-none absolute inset-0" aria-hidden>
        <div className="pb-backdrop absolute inset-0 overflow-hidden">
          <HeroWall />
          {/* Hairline column grid: drawn first on load, then fades once the app window has built */}
          <div className="pb-hero-grid absolute inset-0" />
          {/* The same rules, back again once the visitor scrolls past the hero */}
          <div className="pb-hero-rules absolute inset-0" />
          <div className="pb-hero-grain absolute inset-0" />
        </div>
      </div>
      <section className="relative" style={{ minHeight: "100vh" }}>

        <div className="relative mx-auto max-w-[1100px] px-8 pt-28 pb-16 lg:px-14 lg:pt-32 lg:pb-24">

          {/* ── Two-column top: label+headline LEFT, description+CTA RIGHT ── */}
          <div className="grid grid-cols-1 gap-10 lg:grid-cols-[55%_45%] lg:gap-0">
            {/* LEFT */}
            <div className="flex flex-col justify-end lg:pr-12">
              <div className="pb-enter-label mb-6 flex items-center gap-3">
                <span className="inline-block h-2 w-2 rounded-full" style={{ background: "rgba(0,0,0,0.45)" }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-[0.15em] uppercase" style={{ color: "rgba(0,0,0,0.55)" }}>
                  Layout-preserving translation
                </span>
              </div>

              <h1
                className="pb-enter pb-enter-delay-1 pb-stencil"
                style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)", lineHeight: 1.05 }}
              >
                Translate the<br />
                document.<br />
                Keep the design.
              </h1>
            </div>

            {/* RIGHT */}
            <div className="flex flex-col justify-end lg:pt-16">
              <p className="pb-enter pb-enter-delay-2 max-w-md text-[16px] leading-relaxed text-white/70 lg:text-[17px]">
                Pagebirdy translates InDesign, PDF, subtitles and more into
                40+ languages — and hands them back with every font, column,
                table and page break exactly where you left it.
              </p>
              <div className="pb-enter pb-enter-delay-3 mt-8 flex items-center gap-5">
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

          {/* ── App window: Home and Agents screens ── */}
          <HeroMockup />
        </div>
      </section>

      </div>

      {/* ─── §2 PLATFORM ─── */}
      <PlatformBento />
      <ExtensionSection />


      {/* ─── §4 PRODUCT DIAGRAMS ─── */}
      <ProductDiagram />
      <IntegrationFlow />


      {/* ─── §6 CTA ─── */}
      <section style={{
        background: "linear-gradient(135deg, #f5ede4 0%, #fdf6ef 50%, #f0e8dc 100%)",
        borderTop: "1px solid rgba(200,150,100,0.15)",
      }}>
        <div style={{
          maxWidth: "1100px", margin: "0 auto",
          padding: "56px 56px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: "40px",
        }}>
          <h2 style={{
            fontFamily: "var(--font-share-tech-mono), monospace",
            fontSize: "clamp(2rem, 3.5vw, 3.2rem)",
            lineHeight: 1.1,
            maxWidth: "600px",
            letterSpacing: "-0.01em",
            margin: 0,
            color: "#15130f",
          }}>
            Send us the document<br />you dread translating.
          </h2>
          <Link href="/login" style={{
            fontFamily: "var(--font-space-mono), monospace",
            fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            color: "#fff", background: "#c86018",
            padding: "16px 32px", whiteSpace: "nowrap",
            textDecoration: "none", textTransform: "uppercase",
            flexShrink: 0,
            borderRadius: "4px",
          }}>
            TRANSLATE FREE →
          </Link>
        </div>
      </section>
    </>
  );
}
