type Question = { q: string; a: string };

const QUESTIONS: Question[] = [
  {
    q: "How is a \"page\" counted?",
    a: "One page of source content, regardless of word count. A two-column INDD spread counts as one page per side.",
  },
  {
    q: "What happens if I go over my included pages?",
    a: "Overage bills at the same per-page rate as the Pay as you go plan — no surprise tiers, no throttling.",
  },
  {
    q: "Can I mix formats in one plan?",
    a: "Yes. DOC, PDF, INDD and IDML all draw from the same page allowance.",
  },
  {
    q: "Is there a free trial?",
    a: "Your first document is free on every plan, including Pay as you go.",
  },
  {
    q: "Do you offer refunds?",
    a: "If a translated document comes back with broken layout, that page doesn't count against your allowance and isn't billed.",
  },
];

export function PricingFAQ() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            FAQ
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Questions people actually ask.
          </h2>
        </div>
        <div className="divide-y divide-rule border-t border-rule">
          {QUESTIONS.map((item) => (
            <div key={item.q} className="grid gap-2 py-6 sm:grid-cols-[minmax(0,320px)_1fr] sm:gap-8">
              <h3 className="font-black uppercase text-base">{item.q}</h3>
              <p className="text-sm leading-relaxed text-ink-soft">{item.a}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
