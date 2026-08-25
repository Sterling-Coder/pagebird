export function AccuracyBand() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
      <div className="grid gap-10 lg:grid-cols-[0.7fr_1.3fr] lg:items-center">
        <div>
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Accuracy
          </span>
          <p className="mt-3 font-black uppercase text-7xl tracking-tight sm:text-8xl">
            95%
          </p>
          <p className="mt-2 text-sm text-muted">
            measured against professional human review, per document.
          </p>
        </div>
        <div className="grid gap-6 border-t border-rule pt-8 sm:grid-cols-3">
          <div>
            <h3 className="font-black uppercase text-lg">Text in context</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              Docly reads the surrounding paragraph, not just the string, so
              idioms and technical terms land correctly.
            </p>
          </div>
          <div>
            <h3 className="font-black uppercase text-lg">Images included</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              Text baked into diagrams, screenshots and callouts is detected
              and translated too — not skipped.
            </p>
          </div>
          <div>
            <h3 className="font-black uppercase text-lg">Layout untouched</h3>
            <p className="mt-2 text-sm leading-relaxed text-ink-soft">
              Frames, tables and page breaks stay exactly where they were,
              even when the translated text runs longer or shorter.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
