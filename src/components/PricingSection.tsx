type Row = { label: string; value: string };

type Plan = {
  name: string;
  price: string;
  period: string;
  rows: Row[];
  cta: string;
  href: string;
};

const PLANS: Plan[] = [
  {
    name: "Pay as you go",
    price: "$0.08",
    period: "per page",
    rows: [
      { label: "Formats", value: "DOC · PDF · INDD · IDML" },
      { label: "Languages", value: "30+" },
      { label: "Accuracy", value: "95%" },
      { label: "Billing", value: "No subscription" },
    ],
    cta: "Try it free",
    href: "#demo",
  },
  {
    name: "Team",
    price: "$149",
    period: "per month",
    rows: [
      { label: "Included pages", value: "2,000 / mo" },
      { label: "Formats", value: "DOC · PDF · INDD · IDML" },
      { label: "Queue", value: "Priority" },
      { label: "Billing", value: "Monthly, cancel anytime" },
    ],
    cta: "Start a project",
    href: "#demo",
  },
  {
    name: "Agency",
    price: "Custom",
    period: "volume pricing",
    rows: [
      { label: "Included pages", value: "Unlimited" },
      { label: "Support", value: "Dedicated + SLA" },
      { label: "Access", value: "API" },
      { label: "Billing", value: "Annual contract" },
    ],
    cta: "Talk to sales",
    href: "#demo",
  },
];

function PricingCard({ plan }: { plan: Plan }) {
  return (
    <div className="relative">
      <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
      <div className="relative z-10 border-2 border-ink bg-paper p-6">
        <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
          {plan.name}
        </p>
        <p className="mt-2">
          <span className="text-4xl font-black">{plan.price}</span>{" "}
          <span className="font-mono text-xs uppercase tracking-widest text-muted">
            {plan.period}
          </span>
        </p>

        <div className="mt-6">
          {plan.rows.map((row) => (
            <div
              key={row.label}
              className="flex items-baseline justify-between gap-4 border-b border-dashed border-rule py-3 font-mono text-[13px]"
            >
              <span className="text-muted">{row.label}</span>
              <span className="text-right text-ink-soft">{row.value}</span>
            </div>
          ))}
        </div>

        <div className="relative mt-6">
          <div
            className="absolute inset-0 translate-x-1 translate-y-1 bg-ink"
            aria-hidden="true"
          />
          <a
            href={plan.href}
            className="relative z-10 block border-2 border-ink bg-red px-6 py-3 text-center font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90"
          >
            {plan.cta} →
          </a>
        </div>
      </div>
    </div>
  );
}

type PricingSectionProps = {
  variant?: "teaser" | "full";
};

export function PricingSection({ variant = "full" }: PricingSectionProps) {
  return (
    <section id="pricing" className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-12 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Pricing
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Pay for pages. Not for seats.
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            No per-user licenses. Pricing follows document volume, the way
            translation cost already works for your team.
          </p>
        </div>

        <div className="grid gap-10 pt-2 sm:grid-cols-3 sm:gap-8">
          {PLANS.map((plan) => (
            <PricingCard key={plan.name} plan={plan} />
          ))}
        </div>

        {variant === "teaser" ? (
          <div className="mt-10">
            <a
              href="/pricing"
              className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 transition-colors hover:text-ink hover:decoration-ink"
            >
              See full pricing, FAQ and plan comparison →
            </a>
          </div>
        ) : null}
      </div>
    </section>
  );
}
