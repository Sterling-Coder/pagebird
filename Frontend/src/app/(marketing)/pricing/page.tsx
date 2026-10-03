import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Pricing — Pagebirdy",
  description:
    "Start free. Scale when ready. Your first documents are free — we price by volume, not per seat.",
};

const PLANS = [
  {
    name: "Free",
    price: "$0",
    desc: "Try it out with your first documents.",
    features: ["5 pages free", "PDF + IDML", "All 40+ languages", "QA scoring"],
    cta: "Get started",
    href: "/login",
    accent: false,
  },
  {
    name: "Team",
    price: "Coming soon",
    desc: "For teams shipping in several languages.",
    features: [
      "Volume page packs",
      "All formats + subtitles",
      "Shared glossary",
      "Side-by-side review",
      "Priority support",
    ],
    cta: "Coming soon",
    href: null,
    accent: true,
  },
  {
    name: "Enterprise",
    price: "Custom",
    desc: "For regulated teams with volume and audit needs.",
    features: [
      "Unlimited pages",
      "SSO + audit log",
      "Data residency",
      "Custom integrations",
      "Dedicated support",
    ],
    cta: "Book a call",
    href: "/contact",
    accent: false,
  },
];

const FAQ = [
  {
    q: "What counts as a page?",
    a: "One page of an IDML or PDF file. A 12-page document uses 12 page credits.",
  },
  {
    q: "Can I translate subtitles on the free plan?",
    a: "Subtitle translation is coming soon. When it launches, the free plan will include a limited number of subtitle files.",
  },
  {
    q: "Do you charge per seat?",
    a: "No. We price by volume (pages translated), not per user. Add your whole team at no extra cost.",
  },
  {
    q: "What happens when I run out of free pages?",
    a: "Your existing translations stay available. To translate more, upgrade to a paid plan or contact us for a custom quote.",
  },
];

export default function PricingPage() {
  return (
    <>
      {/* Hero */}
      <section className="border-b border-pb-border bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 pt-20 pb-16 lg:px-10 lg:pt-28 lg:pb-20">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            Pricing
          </span>
          <div className="flex flex-col justify-between gap-8 md:flex-row md:items-end">
            <div>
              <h1 className="font-pb-display max-w-lg text-5xl text-pb-text md:text-7xl">
                Start free.
                <br />
                Scale when ready.
              </h1>
              <p className="mt-6 max-w-md text-[16px] leading-relaxed text-pb-text-secondary">
                Your first documents are free. When you need more, talk to us — we
                price by volume, not per seat.
              </p>
            </div>
            <Link
              href="/contact"
              className="font-pb-mono inline-flex shrink-0 items-center rounded-full bg-pb-accent px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Book a call
            </Link>
          </div>
        </div>
      </section>

      {/* Plans */}
      <section className="bg-pb-bg">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
            {PLANS.map((plan) => (
              <div
                key={plan.name}
                className={`rounded-xl border p-8 ${
                  plan.accent
                    ? "border-pb-accent/30 bg-pb-bg-card shadow-[0_0_40px_rgba(224,138,111,0.08)]"
                    : "border-pb-border bg-pb-bg-card"
                }`}
              >
                <span
                  className={`font-pb-mono text-[10px] font-bold tracking-widest uppercase ${
                    plan.accent ? "text-pb-accent" : "text-pb-text-muted"
                  }`}
                >
                  {plan.name}
                </span>
                <p className="mt-3 text-3xl font-bold text-pb-text">{plan.price}</p>
                <p className="mt-2 text-[13px] text-pb-text-muted">{plan.desc}</p>
                <div className="mt-6 space-y-2.5 text-[13px] text-pb-text-secondary">
                  {plan.features.map((f) => (
                    <span key={f} className="block">— {f}</span>
                  ))}
                </div>
                {plan.href ? (
                  <Link
                    href={plan.href}
                    className={`font-pb-mono mt-8 block rounded-full py-2.5 text-center text-[11px] font-bold tracking-widest uppercase transition-colors ${
                      plan.accent
                        ? "bg-pb-accent text-pb-bg hover:brightness-110"
                        : "border border-pb-border text-pb-text hover:border-pb-text"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                ) : (
                  <span className="font-pb-mono mt-8 block cursor-not-allowed rounded-full bg-pb-accent/20 py-2.5 text-center text-[11px] font-bold tracking-widest text-pb-accent uppercase opacity-60">
                    {plan.cta}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="border-t border-pb-border bg-pb-bg-raised">
        <div className="mx-auto max-w-7xl px-6 py-20 lg:px-10 lg:py-28">
          <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
            <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
            FAQ
          </span>
          <h2 className="font-pb-display max-w-lg text-4xl text-pb-text md:text-5xl">
            Common questions.
          </h2>
          <div className="mt-14 grid grid-cols-1 gap-6 md:grid-cols-2">
            {FAQ.map((item) => (
              <div
                key={item.q}
                className="flex flex-col gap-3 rounded-xl border border-pb-border bg-pb-bg p-7"
              >
                <h3 className="text-[15px] font-bold text-pb-text">{item.q}</h3>
                <p className="text-[13px] leading-relaxed text-pb-text-muted">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className="bg-pb-accent">
        <div className="mx-auto flex max-w-7xl flex-col items-start justify-between gap-8 px-6 py-16 md:flex-row md:items-center lg:px-10 lg:py-20">
          <h2 className="font-pb-display max-w-2xl text-3xl text-pb-bg md:text-5xl">
            Need a custom quote? Let&apos;s talk.
          </h2>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 rounded-full bg-pb-bg px-8 py-3.5 text-[12px] font-bold tracking-widest text-pb-text uppercase transition-all hover:bg-pb-bg-raised"
          >
            Book a call →
          </Link>
        </div>
      </section>
    </>
  );
}
