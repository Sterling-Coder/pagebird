export function TranslatorHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly · Document Translator
      </span>

      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-7xl lg:text-8xl">
        Upload a file.
        <br />
        <span className="text-red">Get it back translated.</span>
      </h1>

      <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
        DOC, PDF, INDD and IDML — 30+ languages, 95% accuracy, layout
        untouched. Upload it as it already exists, no re-export, no cleanup.
      </p>

      <div className="mt-10 flex flex-wrap items-center gap-4">
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
      </div>
    </section>
  );
}
