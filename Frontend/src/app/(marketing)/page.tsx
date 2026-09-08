import Link from "next/link";
import { ScrollReveal } from "@/components/ScrollReveal";

const PROBLEMS = [
  {
    n: "01",
    title: "Text expands, boxes don't",
    body: "German runs 30% longer than English. Pagebird reflows inside the original frame before anything overflows.",
  },
  {
    n: "02",
    title: "Tables and footnotes survive",
    body: "Cells stay in their columns. Footnote markers stay bound to their sentences, however long the translation runs.",
  },
  {
    n: "03",
    title: "Right-to-left is first-class",
    body: "Arabic and Hebrew mirror the whole page — margins, gutters, bullets — not just the sentence direction.",
  },
];

const STEPS = [
  {
    n: "1",
    title: "Drop the file in",
    body: "DOCX, PDF, PPTX, XLSX, IDML or HTML — Pagebird reads the layout tree, not a flattened text dump.",
    accent: false,
  },
  {
    n: "2",
    title: "Pick languages + glossary",
    body: "Attach a termbase and lock the terms that must never be translated — product names, legal phrases.",
    accent: false,
  },
  {
    n: "3",
    title: "Download it, translated",
    body: "Same extension, same styles, same page count. Open it and keep editing as if nothing happened.",
    accent: true,
  },
];

const FEATURES = [
  {
    n: "01",
    title: "Style inheritance preserved",
    body: "Heading levels, numbered lists and the table of contents rebuild themselves with translated text.",
  },
  {
    n: "02",
    title: "Font substitution that matches",
    body: "No Japanese cut in your typeface? Pagebird picks a metrically compatible one, not a generic fallback.",
  },
  {
    n: "03",
    title: "Termbase + glossary control",
    body: "Import a TBX or CSV once. Locked terms are never translated; approved terms always used.",
  },
  {
    n: "04",
    title: "Side-by-side review",
    body: "A reviewer edits the translation against the source page. Comments stay anchored to the paragraph.",
  },
  {
    n: "05",
    title: "Your files stay yours",
    body: "Encrypted in transit and at rest, deleted on your schedule, never used to train models. [SOC 2 / GDPR status].",
  },
  {
    n: "06",
    title: "API + watched folders",
    body: "Point Pagebird at a SharePoint, Drive or S3 folder and every new file returns translated automatically.",
  },
];

const FORMATS = [".docx", ".pdf", ".pptx", ".xlsx", ".idml", ".srt", ".html", ".xliff"];

const PLANS = [
  {
    name: "STARTER",
    price: "$40",
    tagline: "For one person translating the occasional document.",
    features: ["200 pages / month", "DOCX, PDF, PPTX, XLSX", "All 40+ languages"],
    cta: "Start free",
    href: "/login",
    variant: "light" as const,
    rotate: "-rotate-2",
  },
  {
    name: "TEAM — MOST CHOSEN",
    price: "$400",
    tagline: "For teams shipping in several languages at once.",
    features: [
      "2,000 pages / month",
      "InDesign IDML + subtitles",
      "Shared glossary + termbase",
      "Side-by-side review",
    ],
    cta: "Start 14-day trial",
    href: "/login",
    variant: "dark" as const,
    rotate: "rotate-1.5 md:-translate-y-3.5",
  },
  {
    name: "ENTERPRISE",
    price: "Talk to us",
    tagline: "For regulated teams with volume, audit and residency needs.",
    features: ["Unlimited pages, pooled", "SSO, SCIM, audit log", "[EU / US] data residency"],
    cta: "Book a call",
    href: "/contact",
    variant: "light" as const,
    rotate: "-rotate-1",
  },
];

const FAQS = [
  {
    q: "Does the translated file open in Word and InDesign normally?",
    a: "Yes. Pagebird writes back into the original file format — styles, master pages and linked assets stay editable.",
  },
  {
    q: "What happens with scanned PDFs?",
    a: "Pagebird runs OCR, rebuilds the text layer in position, and returns a searchable PDF with the scan preserved underneath.",
  },
  {
    q: "Can our own translators review the output?",
    a: "Invite them as reviewers. They edit side by side with the source and approved terms feed back into your glossary.",
  },
  {
    q: "Are our documents used to train models?",
    a: "No. Files are encrypted, deleted on your retention window, and never used as training data. [Add certification status here.]",
  },
];

const CLIENTS = ["[Client One]", "[Client Two]", "[Client Three]", "[Client Four]", "[Client Five]"];

function DocMock({
  heading,
  meta,
  rotate,
  shadow,
}: {
  heading: string;
  meta: string;
  rotate: string;
  shadow?: boolean;
}) {
  return (
    <div
      className={`${rotate} ${shadow ? "shadow-[14px_14px_0_var(--color-pb-accent)]" : ""} relative flex h-[420px] w-[320px] flex-col gap-2.5 border-[3px] border-pb-card-ink bg-white p-6`}
    >
      <div className="flex items-center justify-between border-b-[3px] border-pb-card-ink/20 pb-2.5">
        <span className="font-pb-display text-pb-card-ink text-sm">{heading}</span>
        <span className="font-pb-mono-brand text-pb-card-faint text-[8px]">{meta}</span>
      </div>
      <span className="h-1 w-[88%] bg-pb-card-ink/15" />
      <span className="h-1 w-[96%] bg-pb-card-ink/15" />
      <span className="h-1 w-[70%] bg-pb-card-ink/15" />
      <span className="mt-1.5 h-[60px] bg-[#f3efe5]" />
      <span className="mt-1.5 h-1 w-[92%] bg-pb-card-ink/15" />
      <span className="h-1 w-[64%] bg-pb-card-ink/15" />
    </div>
  );
}

export default function Home() {
  return (
    <>
      {/* HERO */}
      <section className="relative overflow-hidden border-b-[3px] border-pb-ink px-6 md:px-14">
        <svg
          className="pointer-events-none absolute inset-0 h-full w-full opacity-40"
          viewBox="0 0 1600 800"
          preserveAspectRatio="xMidYMid slice"
          fill="none"
          aria-hidden="true"
        >
          <path
            d="M1080 -60 C 1450 120, 1180 380, 1500 650 C 1680 800, 1900 720, 2000 560"
            stroke="#8a9a5b"
            strokeWidth="2.5"
          />
        </svg>
        <div className="grid grid-cols-1 border-b-[3px] border-pb-ink md:grid-cols-[1.15fr_0.85fr]">
          <div className="flex flex-col justify-center gap-7 border-pb-ink py-14 md:border-r-[3px] md:py-24 md:pr-14">
            <span className="font-pb-mono-brand text-[12.5px] font-bold tracking-widest text-pb-accent uppercase">
              — document translation, reinvented
            </span>
            <h1 className="font-pb-display text-6xl md:text-8xl">
              Same page.
              <br />
              Any
              <br />
              <span className="text-pb-accent italic">language.</span>
            </h1>
            <p className="max-w-[460px] text-[17px] leading-relaxed text-pb-muted">
              Pagebird translates DOCX, PDF, PPTX and InDesign files into 40+ languages
              and hands them back with every column, table, footnote and page break
              exactly where you left it.
            </p>
            <div className="mt-2 flex items-center">
              <Link
                href="/login"
                className="flex h-14 items-center gap-2.5 bg-pb-ink px-7 text-[15px] font-bold text-pb-paper"
              >
                Translate a document free
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="square">
                  <path d="M5 12h14" />
                  <path d="m13 6 6 6-6 6" />
                </svg>
              </Link>
              <button className="flex h-14 items-center border-[3px] border-l-0 border-pb-ink px-6.5 text-[15px] font-bold">
                Watch demo
              </button>
            </div>
          </div>

          <div className="group relative flex items-center justify-center p-10">
            <div className="pb-float relative">
              <div
                className="absolute inset-x-10 -bottom-4 h-8 rounded-[50%] bg-black/15 blur-xl transition-all duration-500 ease-out group-hover:inset-x-6 group-hover:opacity-70"
                aria-hidden="true"
              />
              <div className="absolute transition-transform duration-500 ease-out group-hover:translate-x-10 group-hover:translate-y-5 group-hover:rotate-[11deg]">
                <DocMock heading="ノースウィンド" meta="第3四半期" rotate="rotate-[7deg] translate-x-7 translate-y-2.5" />
              </div>
              <div className="relative transition-transform duration-500 ease-out group-hover:-translate-x-11 group-hover:-translate-y-2 group-hover:-rotate-9">
                <DocMock heading="Northwind" meta="Q3 2026" rotate="-rotate-6 -translate-x-7.5 -translate-y-1.5" shadow />
                <div
                  className="pointer-events-none absolute inset-0 -rotate-6 -translate-x-7.5 -translate-y-1.5 bg-gradient-to-br from-white/70 via-transparent to-transparent opacity-60"
                  aria-hidden="true"
                />
                <span className="font-pb-mono-brand absolute -right-2 -bottom-8.5 rotate-3 border-2 border-pb-ink bg-pb-paper px-2 py-0.75 text-[10.5px] font-bold text-pb-accent transition-transform duration-500 group-hover:rotate-6">
                  ↳ identical layout
                </span>
              </div>
            </div>
          </div>
        </div>

        <div className="flex items-center justify-between py-4">
          <span className="font-pb-mono-brand text-xs text-pb-faint">
            NO CARD REQUIRED — FIRST 5 PAGES FREE ON EVERY PLAN
          </span>
          <span className="font-pb-mono-brand text-xs text-pb-faint">01 / SCROLL</span>
        </div>
      </section>

      {/* LOGO STRIP */}
      <section className="flex items-center gap-0 border-b-[3px] border-pb-ink px-6 py-6 md:px-14">
        <span className="font-pb-mono-brand pr-10 text-xs font-bold tracking-wide">TRUSTED BY</span>
        <div className="flex flex-1 flex-wrap items-center justify-around gap-6">
          {CLIENTS.map((c) => (
            <span key={c} className="font-pb-display text-xl text-[#a9a492]">
              {c}
            </span>
          ))}
        </div>
      </section>

      {/* PROBLEM */}
      <section className="border-b-[3px] border-pb-ink bg-pb-ink text-pb-paper">
        <div className="border-b-[3px] border-pb-card-ink/15 px-6 py-14 md:px-14 md:py-16">
          <h2 className="font-pb-display max-w-3xl text-4xl md:text-5xl">
            Translating the text is easy. Keeping the document is the hard part.
          </h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3">
          {PROBLEMS.map((p, i) => (
            <div
              key={p.n}
              className={`flex flex-col gap-3.5 p-10 ${i < 2 ? "border-b-[3px] border-pb-card-ink/15 md:border-r-[3px] md:border-b-0" : ""}`}
            >
              <span className="font-pb-display text-5xl text-pb-accent">{p.n}</span>
              <h3 className="text-lg font-bold">{p.title}</h3>
              <p className="text-pb-card-muted text-sm leading-relaxed">{p.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section className="border-b-[3px] border-pb-ink px-6 py-18 md:px-14">
        <div className="mb-14 flex items-baseline justify-between">
          <h2 className="font-pb-display text-4xl md:text-5xl">How it works</h2>
          <span className="font-pb-mono-brand hidden text-xs text-pb-faint md:inline">
            03 STEPS — 0 CLEANUP
          </span>
        </div>
        <div className="relative grid grid-cols-1 gap-7 md:grid-cols-3">
          <div className="pb-line-grow absolute top-4 right-0 left-0 hidden h-[3px] bg-pb-ink md:block" />
          {STEPS.map((s) => (
            <div key={s.n} className="group relative z-10 flex flex-col gap-4">
              <span
                className={`font-pb-mono-brand flex h-8 w-8 items-center justify-center text-[13px] font-bold text-pb-paper transition-transform duration-300 group-hover:scale-110 ${s.accent ? "bg-pb-accent animate-pulse" : "bg-pb-ink"}`}
              >
                {s.n}
              </span>
              <div
                className={`flex flex-col gap-2.5 border-[3px] border-pb-card-ink bg-white p-6 transition-all duration-300 ease-out group-hover:-translate-y-1.5 ${s.accent ? "shadow-[8px_8px_0_var(--color-pb-accent)] group-hover:shadow-[12px_12px_0_var(--color-pb-accent)]" : "group-hover:shadow-[8px_8px_0_var(--color-pb-accent)]"}`}
              >
                <h3 className="text-pb-card-ink text-[17px] font-bold">{s.title}</h3>
                <p className="text-pb-card-muted text-[13.5px] leading-relaxed">{s.body}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* FEATURES */}
      <section className="border-b-[3px] border-pb-ink bg-pb-ink px-6 py-18 text-pb-paper md:px-14">
        <div className="mb-12 flex items-baseline justify-between">
          <h2 className="font-pb-display max-w-xl text-4xl text-pb-paper md:text-5xl">
            Everything the file carried, carried across.
          </h2>
          <span className="font-pb-mono-brand hidden text-xs text-[#8c8877] md:inline">
            06 CAPABILITIES
          </span>
        </div>
        <div className="grid grid-cols-1 border-t-2 border-l-2 border-[#38372c] md:grid-cols-3">
          {FEATURES.map((f, i) => (
            <div
              key={f.n}
              className={`flex flex-col gap-2.5 border-r-2 border-b-2 border-[#38372c] p-7.5 ${
                i % 3 === 2 ? "md:border-r-0" : ""
              }`}
            >
              <span className="font-pb-mono-brand text-[11px] text-pb-accent">{f.n}</span>
              <h3 className="text-[16.5px] font-bold">{f.title}</h3>
              <p className="text-[13.5px] leading-relaxed text-[#a29e8e]">{f.body}</p>
            </div>
          ))}
        </div>
        <div className="flex items-center gap-8 border-t-2 border-[#38372c] py-5">
          <span className="font-pb-mono-brand pr-2 text-xs font-bold tracking-wide">FORMATS</span>
          <div className="flex flex-wrap items-center gap-7 text-sm font-semibold text-[#c4c0b0]">
            {FORMATS.map((f) => (
              <span key={f}>{f}</span>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="border-b-[3px] border-pb-ink px-6 py-22 pb-18 md:px-14">
        <div className="mb-16 flex flex-col justify-between gap-6 md:flex-row md:items-baseline">
          <h2 className="font-pb-display text-4xl md:text-5xl">
            Priced by pages.
            <br />
            Not by seat.
          </h2>
          <p className="max-w-80 text-sm leading-relaxed text-pb-muted">
            A page is a page whether you translate it into one language or six. Unused
            pages roll over for [X] days.
          </p>
        </div>

        <div className="flex flex-col items-center justify-center gap-8 px-0 md:flex-row md:items-start md:gap-2 md:px-5">
          {PLANS.map((plan) => (
            <div
              key={plan.name}
              className={`flex w-full max-w-75 flex-col gap-4.5 border-[3px] p-8 ${plan.rotate} ${
                plan.variant === "dark"
                  ? "z-10 border-pb-ink bg-pb-ink text-pb-paper shadow-[12px_12px_0_var(--color-pb-accent)]"
                  : "border-pb-card-ink bg-white text-pb-card-ink"
              }`}
            >
              <span
                className={`font-pb-mono-brand text-[11px] font-bold tracking-wide ${
                  plan.variant === "dark" ? "text-pb-accent" : "text-pb-card-ink"
                }`}
              >
                {plan.name}
              </span>
              <span className="font-pb-display text-4xl">
                {plan.price}
                {plan.price.startsWith("$") && (
                  <span className="font-sans text-sm font-medium">/mo</span>
                )}
              </span>
              <p className={`text-[13px] leading-relaxed ${plan.variant === "dark" ? "text-[#a29e8e]" : "text-pb-card-muted"}`}>
                {plan.tagline}
              </p>
              <div className={`h-0.5 ${plan.variant === "dark" ? "bg-[#38372c]" : "bg-pb-card-ink/20"}`} />
              <div
                className={`flex flex-col gap-2.25 text-[13px] ${
                  plan.variant === "dark" ? "text-[#c4c0b0]" : "text-pb-card-muted"
                }`}
              >
                {plan.features.map((f) => (
                  <span key={f}>— {f}</span>
                ))}
              </div>
              <Link
                href={plan.href}
                className={`mt-2 flex h-11.5 items-center justify-center text-[13.5px] font-bold ${
                  plan.variant === "dark"
                    ? "bg-pb-accent text-pb-paper"
                    : "border-[3px] border-pb-card-ink text-pb-card-ink"
                }`}
              >
                {plan.cta}
              </Link>
            </div>
          ))}
        </div>
      </section>

      {/* TESTIMONIAL */}
      <section className="border-b-[3px] border-pb-ink bg-pb-ink px-6 py-18 text-pb-paper md:px-14">
        <ScrollReveal className="flex items-start gap-10">
          <span className="font-pb-display text-[80px] leading-[0.7] text-pb-accent md:text-[120px]">
            &ldquo;
          </span>
          <div className="flex flex-col gap-5.5 pt-6">
            <p className="font-pb-display max-w-3xl text-2xl font-semibold italic md:text-3xl">
              Our Q3 investor deck used to take a full day to reformat by hand after
              translation. Pagebird gave it back in nine minutes, tables and all.
            </p>
            <div className="flex items-center gap-3">
              <span className="h-2 w-2 bg-pb-accent" />
              <span className="font-pb-mono-brand text-[12.5px] font-bold">
                Priya Nakamura — Head of Investor Relations, Northwind
              </span>
            </div>
          </div>
        </ScrollReveal>
      </section>

      {/* FAQ */}
      <section className="flex flex-col gap-10 border-b-[3px] border-pb-ink px-6 py-18 md:flex-row md:px-14">
        <div className="flex w-full flex-shrink-0 flex-col gap-3.5 md:w-85">
          <h2 className="font-pb-display text-3xl md:text-4xl">Questions we get asked</h2>
          <p className="text-sm leading-relaxed text-pb-muted">
            Something else on your mind?{" "}
            <Link href="/contact" className="underline">
              Ask us directly
            </Link>{" "}
            — we answer within [X] business hours.
          </p>
        </div>
        <div className="flex flex-1 flex-col md:border-l-[3px] md:border-pb-ink md:pl-10">
          {FAQS.map((f, i) => (
            <div
              key={f.q}
              className={`flex flex-col gap-2 py-5.5 ${i < FAQS.length - 1 ? "border-b-2 border-pb-line" : ""}`}
            >
              <h3 className="text-[16.5px] font-bold">{f.q}</h3>
              <p className="text-sm leading-relaxed text-pb-muted">{f.a}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="flex flex-col items-start justify-between gap-6 border-b-[3px] border-pb-ink bg-pb-accent px-6 py-14 text-pb-ink md:flex-row md:items-center md:px-14">
        <h2 className="font-pb-display max-w-2xl text-3xl md:text-5xl">
          Send us the document you dread translating.
        </h2>
        <Link
          href="/login"
          className="flex h-14.5 flex-shrink-0 items-center bg-pb-ink px-7.5 text-[15.5px] font-bold text-pb-paper"
        >
          Translate a document free →
        </Link>
      </section>
    </>
  );
}
