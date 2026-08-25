export function HomeHero() {
  return (
    <section className="mx-auto max-w-6xl px-6 pb-16 pt-14 sm:px-8 sm:pt-20">
      <span className="font-mono text-[12px] uppercase tracking-widest text-red">
        Docly
      </span>
      <h1 className="mt-6 text-[3rem] font-black uppercase leading-[0.95] tracking-tight sm:text-6xl lg:text-7xl">
        Translation that doesn&apos;t
        <br />
        <span className="text-red">touch the layout.</span>
      </h1>
      <p className="mt-6 max-w-lg text-lg leading-relaxed text-ink-soft">
        Two ways to use it: translate a whole document, or translate what
        you&apos;re looking at right now in your browser. Same accuracy,
        same layout-first approach, either way.
      </p>
    </section>
  );
}
