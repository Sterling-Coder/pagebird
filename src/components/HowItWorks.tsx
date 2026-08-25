const STEPS = [
  {
    n: "01",
    title: "Upload the file",
    body: "Drop in a DOC, PDF, INDD or IDML file as it already exists. No re-export, no cleanup, no template.",
  },
  {
    n: "02",
    title: "Docly reads the layout",
    body: "Text frames, tables, captions and image anchors are mapped before a single word is translated, so nothing shifts later.",
  },
  {
    n: "03",
    title: "Text is translated in place",
    body: "Each string is translated inside its original frame, at 95% accuracy, in any of 30+ languages you choose.",
  },
  {
    n: "04",
    title: "Export, pixel for pixel",
    body: "Get back the same file format, same page count, same images — just in a different language.",
  },
];

export function HowItWorks() {
  return (
    <section id="how-it-works" className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
      <div className="mb-12 max-w-xl">
        <span className="font-mono text-[11px] uppercase tracking-widest text-red">
          How it works
        </span>
        <h2 className="mt-3 font-black uppercase text-3xl tracking-tight sm:text-4xl">
          Four steps. No handoff to a second tool.
        </h2>
      </div>
      <div className="grid gap-0 border-t border-rule sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step) => (
          <div key={step.n} className="border-b border-r border-rule px-1 py-8 pr-6 last:border-r-0 sm:px-6">
            <span className="font-mono text-sm text-red">{step.n}</span>
            <h3 className="mt-4 font-black uppercase text-xl">{step.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">
              {step.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
