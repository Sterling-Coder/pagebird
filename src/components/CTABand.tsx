export function CTABand() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 text-center sm:px-8">
        <h2 className="mx-auto max-w-2xl font-black uppercase text-4xl tracking-tight sm:text-5xl">
          Send the file as it is. Get it back the same way.
        </h2>
        <p className="mx-auto mt-4 max-w-md text-ink-soft">
          Free to try on your first document, no card required.
        </p>
        <div className="mt-8 flex flex-wrap items-center justify-center gap-4">
          <a
            href="/translator#demo"
            className="bg-red px-7 py-3.5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90"
          >
            Try it free →
          </a>
          <a
            href="/translator#formats"
            className="border border-ink px-7 py-3.5 font-mono text-[11px] uppercase tracking-widest transition-colors hover:bg-ink hover:text-paper"
          >
            See supported formats
          </a>
        </div>
      </div>
    </section>
  );
}
