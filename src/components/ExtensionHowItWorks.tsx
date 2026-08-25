const STEPS = [
  {
    n: "01",
    title: "Install the extension",
    body: "Add Docly to Chrome, Firefox, or Edge in one click. No account needed to start.",
  },
  {
    n: "02",
    title: "Highlight any text",
    body: "Select text on any page — an inbox, a ticket, a doc in your browser.",
  },
  {
    n: "03",
    title: "Pick a language",
    body: "Right-click, choose a language from the menu that appears.",
  },
  {
    n: "04",
    title: "It's replaced in place",
    body: "The translated text swaps in where the original was — the page layout never moves.",
  },
];

export function ExtensionHowItWorks() {
  return (
    <section className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
      <div className="mb-12 max-w-xl">
        <span className="font-mono text-[11px] uppercase tracking-widest text-red">
          How it works
        </span>
        <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
          Four steps. Never leave the page.
        </h2>
      </div>
      <div className="grid gap-0 border-t border-rule sm:grid-cols-2 lg:grid-cols-4">
        {STEPS.map((step) => (
          <div key={step.n} className="border-b border-r border-rule px-1 py-8 pr-6 last:border-r-0 sm:px-6">
            <span className="font-mono text-sm text-red">{step.n}</span>
            <h3 className="mt-4 text-xl font-black uppercase">{step.title}</h3>
            <p className="mt-3 text-sm leading-relaxed text-ink-soft">
              {step.body}
            </p>
          </div>
        ))}
      </div>
    </section>
  );
}
