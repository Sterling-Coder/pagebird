export function AboutContact() {
  return (
    <section className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 text-center sm:px-8">
        <h2 className="text-3xl font-black uppercase tracking-tight sm:text-4xl">
          Want to talk to us directly?
        </h2>
        <p className="mx-auto mt-4 max-w-md text-ink-soft">
          If you&apos;re dealing with the translation handoff problem right
          now, we want to hear about it.
        </p>
        <a
          href="mailto:hello@docly.example"
          className="mt-8 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
        >
          hello@docly.example
        </a>
      </div>
    </section>
  );
}
