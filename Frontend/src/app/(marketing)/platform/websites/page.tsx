import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Website Translator — Pagebirdy",
  description:
    "Translate your entire website into 40+ languages. Every page, navigation link, footer and dynamic content — without touching your CSS or breaking your layout.",
};

const FEATURES = [
  {
    n: "01",
    title: "Every page translated",
    desc: "Navigation, footers, dynamic content, modals — the crawler reads the full DOM, not just visible text.",
  },
  {
    n: "02",
    title: "SEO-friendly URLs",
    desc: "/en/pricing → /fr/pricing. Hreflang tags injected. Search engines index every language independently.",
  },
  {
    n: "03",
    title: "CMS-aware",
    desc: "Reads from headless CMS APIs — Contentful, Sanity, Prismic — not just rendered HTML.",
  },
  {
    n: "04",
    title: "Keeps your design",
    desc: "CSS, images, layout untouched. Only the text changes. Your design system stays yours.",
  },
  {
    n: "05",
    title: "Automatic",
    desc: "New pages and copy changes translated as they publish. No manual re-runs.",
  },
  {
    n: "06",
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including RTL scripts. Arabic and Hebrew mirror layout automatically.",
  },
];

const USE_CASES = [
  "E-commerce",
  "Marketing sites",
  "SaaS products",
  "Documentation",
  "Landing pages",
  "Developer portals",
];

const STEPS = [
  {
    n: "01",
    title: "Point at a URL",
    desc: "Give Pagebirdy your domain. The crawler maps every page, route and API endpoint automatically.",
  },
  {
    n: "02",
    title: "Crawler reads every page",
    desc: "Every navigation link, footer, modal and CMS-sourced string gets extracted and translated in parallel.",
  },
  {
    n: "03",
    title: "Get your translated site",
    desc: "Same structure. Same CSS. Same images. New language — SEO-ready, with hreflang tags already set.",
  },
];

export default function WebsitesPage() {
  const accent = "#5a9e5a";
  const accentDim = "rgba(90,158,90,0.12)";

  return (
    <>
      {/* ─── HERO ─── */}
      <section
        className="relative min-h-screen overflow-hidden"
        style={{
          background:
            "radial-gradient(ellipse 110% 75% at 68% 28%, #145c14 0%, #0a2e0a 18%, #051405 40%, #090c09 70%)",
        }}
      >
        {/* Vertical scan lines */}
        <div
          className="pointer-events-none absolute inset-0"
          style={{
            backgroundImage:
              "repeating-linear-gradient(90deg, rgba(60,180,80,0.07) 0px, rgba(60,180,80,0.07) 1px, transparent 1px, transparent 170px)",
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
          {/* Label row */}
          <div className="mb-8 flex items-center gap-4">
            <div className="flex items-center gap-3">
              <span className="inline-block h-2 w-2" style={{ background: accent }} />
              <span
                className="font-pb-mono text-[11px] font-bold tracking-widest uppercase"
                style={{ color: accent }}
              >
                Website Translator
              </span>
            </div>
            <span
              className="font-pb-mono rounded-full border px-3 py-1 text-[9px] font-bold tracking-widest text-pb-text-muted uppercase"
              style={{ borderColor: "rgba(255,255,255,0.12)" }}
            >
              Coming soon
            </span>
          </div>

          {/* Headline */}
          <h1
            className="font-pb-mono max-w-5xl"
            style={{
              fontSize: "clamp(3.5rem, 9vw, 8rem)",
              lineHeight: 0.92,
              letterSpacing: "-0.02em",
              color: "rgba(240,236,227,0.22)",
            }}
          >
            Translate
            <br />
            <span style={{ color: "#f0ece3" }}>your entire</span>
            <br />
            website.
          </h1>

          <div className="mt-12 flex max-w-5xl flex-col gap-8 lg:flex-row lg:items-end lg:justify-between">
            <p className="max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
              Point Pagebirdy at any URL. Every page, navigation link, footer and
              dynamic content comes back translated — without touching your CSS or
              breaking your layout.
            </p>
            <div className="flex shrink-0 items-center gap-5">
              <Link
                href="/contact"
                className="font-pb-mono rounded-full px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
                style={{ background: accent }}
              >
                Join the waitlist
              </Link>
              <span className="font-pb-mono text-[12px] tracking-widest text-pb-text-muted uppercase">
                Coming 2025 →
              </span>
            </div>
          </div>

          {/* Browser mock */}
          <div
            className="mt-20 overflow-hidden"
            style={{ borderRadius: "12px", border: "1px solid rgba(255,255,255,0.1)" }}
          >
            {/* Browser chrome */}
            <div
              className="flex items-center gap-3 px-5 py-3"
              style={{ background: "rgba(20,20,16,0.9)", borderBottom: "1px solid rgba(255,255,255,0.07)" }}
            >
              <div className="flex gap-1.5">
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: "rgba(255,255,255,0.1)" }} />
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: "rgba(255,255,255,0.1)" }} />
                <span className="h-2.5 w-2.5 rounded-full" style={{ background: "rgba(255,255,255,0.1)" }} />
              </div>
              <div
                className="font-pb-mono mx-auto flex items-center gap-2 rounded px-4 py-1 text-[11px]"
                style={{ background: "rgba(255,255,255,0.06)", color: "rgba(240,236,227,0.5)" }}
              >
                <span>yoursite.com</span>
                <span style={{ color: accent }}>→</span>
                <span style={{ color: accent }}>yoursite.com/fr</span>
              </div>
            </div>
            {/* Side-by-side content */}
            <div className="grid grid-cols-2">
              {/* English */}
              <div
                className="p-8 lg:p-10"
                style={{ background: "rgba(10,12,10,0.8)", borderRight: "1px solid rgba(255,255,255,0.06)" }}
              >
                {/* Nav mock */}
                <div className="mb-6 flex items-center justify-between">
                  <span className="h-2 w-16 rounded" style={{ background: "rgba(255,255,255,0.12)" }} />
                  <div className="flex gap-4">
                    {[40, 32, 36, 28].map((w, i) => (
                      <span key={i} className="h-1.5 rounded" style={{ width: w, background: "rgba(255,255,255,0.08)" }} />
                    ))}
                  </div>
                </div>
                {/* Hero text */}
                <div className="space-y-2 mb-4">
                  <div className="h-3 w-[72%] rounded" style={{ background: "rgba(255,255,255,0.15)" }} />
                  <div className="h-3 w-[88%] rounded" style={{ background: "rgba(255,255,255,0.15)" }} />
                  <div className="h-3 w-[55%] rounded" style={{ background: "rgba(255,255,255,0.10)" }} />
                </div>
                <div className="h-8 w-28 rounded-full" style={{ background: "rgba(255,255,255,0.08)" }} />
                <div className="mt-6 h-20 w-full rounded" style={{ background: "rgba(255,255,255,0.05)" }} />
                <div className="font-pb-mono mt-6 text-[10px] tracking-widest text-pb-text-muted uppercase">Source · English</div>
              </div>
              {/* French */}
              <div className="p-8 lg:p-10" style={{ background: "rgba(15,20,15,0.8)" }}>
                {/* Nav mock */}
                <div className="mb-6 flex items-center justify-between">
                  <span className="h-2 w-16 rounded" style={{ background: "rgba(90,158,90,0.2)" }} />
                  <div className="flex gap-4">
                    {[44, 30, 38, 24].map((w, i) => (
                      <span key={i} className="h-1.5 rounded" style={{ width: w, background: "rgba(90,158,90,0.12)" }} />
                    ))}
                  </div>
                </div>
                {/* Hero text */}
                <div className="space-y-2 mb-4">
                  <div className="h-3 w-[80%] rounded" style={{ background: "rgba(90,158,90,0.2)" }} />
                  <div className="h-3 w-[68%] rounded" style={{ background: "rgba(90,158,90,0.2)" }} />
                  <div className="h-3 w-[60%] rounded" style={{ background: "rgba(90,158,90,0.14)" }} />
                </div>
                <div className="h-8 w-32 rounded-full" style={{ background: "rgba(90,158,90,0.15)" }} />
                <div className="mt-6 h-20 w-full rounded" style={{ background: "rgba(90,158,90,0.08)" }} />
                <div className="font-pb-mono mt-6 text-[10px] tracking-widest uppercase" style={{ color: accent }}>Translated · French</div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ─── HOW IT WORKS ─── */}
      <section style={{ background: "#0a0c0a" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2" style={{ background: accent }} />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: accent }}>
              How it works
            </span>
          </div>
          <h2
            className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl lg:text-6xl"
            style={{ letterSpacing: "-0.02em" }}
          >
            Three steps.<br />Entire site.
          </h2>

          <div className="mt-20 grid grid-cols-1 gap-0 md:grid-cols-3">
            {STEPS.map((s, i) => (
              <div
                key={s.n}
                className={`py-10 ${i < 2 ? "md:border-r md:pr-10" : ""} ${i > 0 ? "md:pl-10" : ""} ${i < 2 ? "border-b md:border-b-0" : ""}`}
                style={{ borderColor: "rgba(90,158,90,0.12)" }}
              >
                <span
                  className="font-pb-mono block text-[80px] font-bold leading-none"
                  style={{ color: "rgba(90,158,90,0.08)" }}
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

      {/* ─── FEATURES ─── */}
      <section style={{ background: "#0c0f0c" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex flex-col justify-between gap-4 pb-12 md:flex-row md:items-end" style={{ borderBottom: "1px solid rgba(90,158,90,0.1)" }}>
            <div>
              <div className="flex items-center gap-3 mb-6">
                <span className="inline-block h-2 w-2" style={{ background: accent }} />
                <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color: accent }}>
                  Capabilities
                </span>
              </div>
              <h2
                className="font-pb-mono text-4xl font-bold text-pb-text md:text-5xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                Nothing left<br />untranslated.
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
                className={`flex gap-6 py-8 ${i % 2 === 0 ? "md:pr-12" : "md:pl-12"}`}
                style={{ borderColor: "rgba(90,158,90,0.08)", borderRight: i % 2 === 0 ? "1px solid rgba(90,158,90,0.08)" : undefined, borderBottom: "1px solid rgba(90,158,90,0.06)" }}
              >
                <span className="font-pb-mono mt-0.5 shrink-0 text-[11px]" style={{ color: `${accent}88` }}>
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

      {/* ─── BIG NUMBER ─── */}
      <section style={{ background: "#0a0c0a", borderTop: "1px solid rgba(90,158,90,0.08)" }}>
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-32">
          <div className="flex flex-col items-start gap-8 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <p
                className="font-pb-mono font-bold leading-none"
                style={{
                  fontSize: "clamp(4rem, 15vw, 12rem)",
                  color: "rgba(90,158,90,0.12)",
                  letterSpacing: "-0.04em",
                }}
              >
                500+
              </p>
              <h2
                className="font-pb-mono -mt-4 text-3xl font-bold text-pb-text md:text-5xl"
                style={{ letterSpacing: "-0.02em" }}
              >
                pages. In minutes.
              </h2>
              <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-pb-text-muted">
                A 500-page site that would take a team weeks to translate manually goes through
                Pagebirdy in minutes. Every page. Every string. Every language.
              </p>
            </div>
            {/* Use cases */}
            <div className="flex flex-col gap-2 shrink-0">
              <span className="font-pb-mono mb-3 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Works for</span>
              {USE_CASES.map((u) => (
                <div key={u} className="flex items-center gap-3">
                  <span className="h-px w-4" style={{ background: accent }} />
                  <span className="text-[14px] font-semibold text-pb-text">{u}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ background: accent }}>
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-10 lg:py-24">
          <h2
            className="font-pb-mono max-w-2xl text-3xl font-bold md:text-5xl"
            style={{ letterSpacing: "-0.02em", color: "#050f05" }}
          >
            Join the waitlist for<br />Website Translator.
          </h2>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 border-2 px-8 py-3.5 text-[12px] font-bold tracking-widest uppercase transition-all"
            style={{
              borderColor: "#050f05",
              background: "#050f05",
              color: accent,
            }}
            onMouseEnter={undefined}
          >
            Get early access →
          </Link>
        </div>
      </section>
    </>
  );
}
