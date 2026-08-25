import { ImageCollage } from "./ImageCollage";
import { CTAArrow } from "./CTAArrow";

export function Hero() {
  return (
    <section id="top" className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly · Translation × Layout × Accuracy
      </span>

      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-7xl lg:text-8xl">
        One file for
        <br />
        every language,
        <br />
        every layout,
        <br />
        <span className="text-red">every pixel.</span>
      </h1>

      <div className="relative mt-10 flex flex-wrap items-center gap-4">
        <a
          href="#demo"
          className="bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
        >
          Try it free →
        </a>
        <a
          href="#how-it-works"
          className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
        >
          See how it works
        </a>
        <CTAArrow />
      </div>

      <p className="mt-6 font-mono text-[11px] uppercase tracking-widest text-muted">
        No card required · First document free
      </p>

      <ImageCollage />
    </section>
  );
}
