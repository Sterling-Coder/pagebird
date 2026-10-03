import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Website Translation — Pagebirdy",
  description:
    "Point at a URL and get every page translated — navigation, footers, dynamic content included.",
};

const FEATURES = [
  {
    title: "Full-page crawl",
    desc: "Give us the root URL. We crawl every linked page and translate them all — navigation, footers, nested routes.",
  },
  {
    title: "Dynamic content",
    desc: "JavaScript-rendered text, SPAs, and client-side routing are handled. Not just static HTML.",
  },
  {
    title: "SEO-friendly output",
    desc: "Translated pages keep meta tags, Open Graph data and structured data intact for each language.",
  },
  {
    title: "Incremental updates",
    desc: "Changed pages get re-translated. Unchanged ones stay cached. No full re-crawl needed.",
  },
  {
    title: "Multi-engine translation",
    desc: "OpenAI and DeepL in consensus for the best result on every text node.",
  },
  {
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including CJK and right-to-left scripts.",
  },
];

export default function WebsitesPage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <div className="mb-6 flex items-center gap-3">
            <span className="font-pb-mono inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
              Website Translator
            </span>
            <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
              Coming soon
            </span>
          </div>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            website.
            <br />
            <span className="text-pb-text">Keep the structure.</span>
          </h1>

          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Point at a live URL. We crawl every page, translate every text node,
            and hand back a complete multilingual site — navigation, footers,
            dynamic content included.
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

      {/* Product mock — website preview */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-0 overflow-hidden rounded-xl border border-pb-border md:grid-cols-2">
            <div className="flex flex-col bg-pb-bg p-8 md:p-10">
              <span className="font-pb-mono mb-4 text-[11px] tracking-widest text-pb-text-muted uppercase">
                Source · example.com
              </span>
              <div className="flex flex-col gap-3 rounded-lg bg-pb-bg-card p-6">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-pb-text-muted/30" />
                  <div className="h-2 w-2 rounded-full bg-pb-text-muted/30" />
                  <div className="h-2 w-2 rounded-full bg-pb-text-muted/30" />
                  <div className="ml-2 h-5 flex-1 rounded bg-pb-border" />
                </div>
                <div className="mt-2 flex gap-4">
                  <div className="h-2 w-12 rounded bg-pb-border" />
                  <div className="h-2 w-10 rounded bg-pb-border" />
                  <div className="h-2 w-14 rounded bg-pb-border" />
                  <div className="h-2 w-8 rounded bg-pb-border" />
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-6 w-3/4 rounded bg-pb-border" />
                  <div className="h-2 w-full rounded bg-pb-border/60" />
                  <div className="h-2 w-[90%] rounded bg-pb-border/60" />
                  <div className="h-2 w-[70%] rounded bg-pb-border/60" />
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <div className="h-14 rounded bg-pb-border/40" />
                  <div className="h-14 rounded bg-pb-border/40" />
                  <div className="h-14 rounded bg-pb-border/40" />
                </div>
              </div>
            </div>
            <div className="flex flex-col bg-[#f5f0e6] p-8 text-[#1a1914] md:p-10">
              <span className="font-pb-mono mb-4 text-[11px] tracking-widest text-[#a09a88] uppercase">
                Translated · fr.example.com
              </span>
              <div className="flex flex-col gap-3 rounded-lg bg-[#e8e2d4] p-6">
                <div className="flex items-center gap-2">
                  <div className="h-2 w-2 rounded-full bg-[#a09a88]/30" />
                  <div className="h-2 w-2 rounded-full bg-[#a09a88]/30" />
                  <div className="h-2 w-2 rounded-full bg-[#a09a88]/30" />
                  <div className="ml-2 h-5 flex-1 rounded bg-[#d9d3c4]" />
                </div>
                <div className="mt-2 flex gap-4">
                  <div className="h-2 w-14 rounded bg-[#d9d3c4]" />
                  <div className="h-2 w-12 rounded bg-[#d9d3c4]" />
                  <div className="h-2 w-10 rounded bg-[#d9d3c4]" />
                  <div className="h-2 w-10 rounded bg-[#d9d3c4]" />
                </div>
                <div className="mt-4 space-y-2">
                  <div className="h-6 w-[80%] rounded bg-[#d9d3c4]" />
                  <div className="h-2 w-full rounded bg-[#d9d3c4]/60" />
                  <div className="h-2 w-[85%] rounded bg-[#d9d3c4]/60" />
                  <div className="h-2 w-[65%] rounded bg-[#d9d3c4]/60" />
                </div>
                <div className="mt-4 grid grid-cols-3 gap-2">
                  <div className="h-14 rounded bg-[#d9d3c4]/40" />
                  <div className="h-14 rounded bg-[#d9d3c4]/40" />
                  <div className="h-14 rounded bg-[#d9d3c4]/40" />
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Features
          </span>
          <h2 className="font-pb-display max-w-2xl text-4xl text-pb-text md:text-5xl">
            Your whole site, in any language.
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
            Get notified when website translation launches.
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
