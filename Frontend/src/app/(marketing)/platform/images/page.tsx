import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Image Translation — Pagebirdy",
  description:
    "Detect and translate text embedded in images — signs, labels, infographics — and render it back in place.",
};

const FEATURES = [
  {
    title: "Text detection",
    desc: "OCR locates every text region in the image — signs, labels, captions, infographic callouts.",
  },
  {
    title: "In-place rendering",
    desc: "Translated text is rendered back at the same position, matching the original font size and color.",
  },
  {
    title: "Background inpainting",
    desc: "The area behind the original text is reconstructed so the replacement looks native, not pasted.",
  },
  {
    title: "Batch processing",
    desc: "Drop a folder of images. Every file comes back translated without manual work.",
  },
  {
    title: "Multi-engine translation",
    desc: "OpenAI and DeepL in consensus for the best result on every text region.",
  },
  {
    title: "40+ languages",
    desc: "From Afrikaans to Vietnamese, including CJK and right-to-left scripts.",
  },
];

const FORMATS = [".png", ".jpg", ".jpeg", ".webp", ".tiff", ".bmp"];

export default function ImagesPage() {
  return (
    <>
      {/* Hero */}
      <section className="pb-hero-gradient pb-hero-lines relative overflow-hidden">
        <div className="relative mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-24">
          <div className="mb-6 flex items-center gap-3">
            <span className="font-pb-mono inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
              <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
              Image Translator
            </span>
            <span className="font-pb-mono rounded-full bg-pb-accent-dim px-3 py-1 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
              Coming soon
            </span>
          </div>

          <h1 className="pb-headline-dot max-w-4xl text-5xl md:text-7xl lg:text-8xl">
            Translate the
            <br />
            image.
            <br />
            <span className="text-pb-text">Keep the visual.</span>
          </h1>

          <p className="mt-8 max-w-lg text-[16px] leading-relaxed text-pb-text-secondary lg:text-[17px]">
            Upload an image with embedded text — signs, infographics, product
            labels — and get it back with every word translated and rendered in
            place.
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

      {/* Product mock — image translation */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-0 overflow-hidden rounded-xl border border-pb-border md:grid-cols-2">
            <div className="flex flex-col justify-between bg-pb-bg p-8 md:p-10">
              <span className="font-pb-mono mb-4 text-[11px] tracking-widest text-pb-text-muted uppercase">
                Source · English
              </span>
              <div className="flex aspect-[4/3] items-center justify-center rounded-lg bg-pb-bg-card">
                <div className="flex flex-col items-center gap-3 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-pb-accent/10">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-8 w-8 text-pb-accent">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <path d="m21 15-5-5L5 21" />
                    </svg>
                  </div>
                  <div className="font-pb-mono text-[13px] text-pb-text-muted">
                    <p>&quot;Annual Report 2024&quot;</p>
                    <p>&quot;Revenue Growth&quot;</p>
                    <p>&quot;Key Metrics&quot;</p>
                  </div>
                </div>
              </div>
            </div>
            <div className="flex flex-col justify-between bg-[#f5f0e6] p-8 text-[#1a1914] md:p-10">
              <span className="font-pb-mono mb-4 text-[11px] tracking-widest text-[#a09a88] uppercase">
                Translated · Japanese
              </span>
              <div className="flex aspect-[4/3] items-center justify-center rounded-lg bg-[#e8e2d4]">
                <div className="flex flex-col items-center gap-3 text-center">
                  <div className="flex h-16 w-16 items-center justify-center rounded-xl bg-[#d9d3c4]">
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-8 w-8 text-[#a09a88]">
                      <rect x="3" y="3" width="18" height="18" rx="2" />
                      <circle cx="8.5" cy="8.5" r="1.5" />
                      <path d="m21 15-5-5L5 21" />
                    </svg>
                  </div>
                  <div className="font-pb-mono text-[13px] text-[#5a5648]">
                    <p>&quot;年次報告書 2024&quot;</p>
                    <p>&quot;収益成長&quot;</p>
                    <p>&quot;主要指標&quot;</p>
                  </div>
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
            Every word in the image, translated in place.
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

      {/* Formats */}
      <section className="border-t border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-12 lg:px-10">
          <div className="flex flex-wrap items-center gap-3">
            <span className="font-pb-mono mr-4 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Supported formats
            </span>
            {FORMATS.map((f) => (
              <span
                key={f}
                className="font-pb-mono rounded-full border border-pb-border px-4 py-1.5 text-[12px] text-pb-text-secondary"
              >
                {f}
              </span>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Get notified when image translation launches.
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
