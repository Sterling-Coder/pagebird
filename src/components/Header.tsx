export function Header() {
  return (
    <>
      <div className="h-[3px] bg-ink" />
      <header className="border-b border-ink">
        <div className="mx-auto grid max-w-6xl grid-cols-3 items-center px-6 py-5 sm:px-8">
          <span className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            Vol. 01 · SaaS
          </span>
          <a
            href="#top"
            className="justify-self-center text-center text-lg font-black uppercase tracking-tight sm:text-xl"
          >
            The Docly Dispatch
          </a>
          <span className="justify-self-end font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            Remote · 2026
          </span>
        </div>
      </header>
    </>
  );
}
