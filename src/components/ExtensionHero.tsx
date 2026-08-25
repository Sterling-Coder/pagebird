export function ExtensionHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly · Browser Extension
      </span>

      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-7xl lg:text-8xl">
        Select it.
        <br />
        <span className="text-red">Translate it in place.</span>
      </h1>

      <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
        Highlight any text on any page — an email, a ticket, a spec doc in
        your browser — and Docly replaces it with the translated version,
        right where it was. No copy-paste, no separate tab.
      </p>

      <div className="mt-10 flex flex-wrap items-center gap-4">
        <a
          href="#extension-demo"
          className="bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
        >
          Add to browser →
        </a>
        <a
          href="/translator"
          className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
        >
          Translating a document instead?
        </a>
      </div>
    </section>
  );
}
