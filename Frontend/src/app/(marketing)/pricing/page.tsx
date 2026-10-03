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
      <section className="relative overflow-hidden" style={{
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
        minHeight: "42vh",
      }}>
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(90deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 80px)",
        }} />
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(180deg, transparent 0px, transparent 2px, rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 3px)",
        }} />
        <div className="relative mx-auto max-w-[1100px] px-8 pt-28 pb-16 lg:px-14 lg:pt-36">
          <div className="pb-enter-label flex items-center gap-3 mb-8">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Pricing</span>
          </div>
          <div className="grid grid-cols-1 gap-8 lg:grid-cols-2 lg:items-end">
            <h1 className="pb-enter pb-stencil" style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}>
              Start free.<br />Scale when ready.
            </h1>
            <div className="pb-enter pb-enter-delay-1">
              <p className="max-w-md text-[16px] leading-relaxed text-pb-text-secondary">
                Your first documents are free. When you need more, talk to us — we price by volume, not per seat.
              </p>
              <Link
                href="/contact"
                className="font-pb-mono mt-6 inline-flex items-center rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
              >
                Book a call
              </Link>
            </div>
          </div>
        </div>
      </section>

      {/* Plans */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-24">
          <div className="grid grid-cols-1 divide-y md:grid-cols-3 md:divide-x md:divide-y-0" style={{ "--tw-divide-color": "rgba(255,255,255,0.06)" } as React.CSSProperties}>
            {PLANS.map((plan, i) => (
              <div key={plan.name} className={`py-10 ${i > 0 ? "md:pl-10" : ""} ${i < 2 ? "md:pr-10" : ""}`}>
                <span className={`font-pb-mono text-[10px] font-bold tracking-widest uppercase ${plan.accent ? "text-pb-accent" : "text-pb-text-muted"}`}>
                  {plan.name}
                </span>
                <p className="mt-4 text-[32px] font-bold text-pb-text">{plan.price}</p>
                <p className="mt-2 text-[13px] text-pb-text-muted">{plan.desc}</p>
                <div className="mt-8 space-y-2.5 text-[13px] text-pb-text-secondary">
                  {plan.features.map((f) => (
                    <span key={f} className="block">— {f}</span>
                  ))}
                </div>
                {plan.href ? (
                  <Link
                    href={plan.href}
                    className={`font-pb-mono mt-10 block border py-3 text-center text-[11px] font-bold tracking-widest uppercase transition-all ${
                      plan.accent
                        ? "border-pb-accent/40 text-pb-accent hover:bg-pb-accent hover:text-pb-bg"
                        : "border-white/[0.08] text-pb-text hover:border-pb-text"
                    }`}
                  >
                    {plan.cta}
                  </Link>
                ) : (
                  <span className="font-pb-mono mt-10 block cursor-not-allowed border border-white/[0.04] py-3 text-center text-[11px] font-bold tracking-widest text-pb-text-muted uppercase opacity-50">
                    {plan.cta}
                  </span>
                )}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-24">
          <div className="flex items-center gap-3 mb-12">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">FAQ</span>
          </div>
          <div className="grid grid-cols-1 gap-0 md:grid-cols-2">
            {FAQ.map((item, i) => (
              <div
                key={item.q}
                className={`flex flex-col gap-3 py-8 ${i % 2 === 0 ? "md:border-r md:pr-12" : "md:pl-12"}`}
                style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}
              >
                <h3 className="text-[15px] font-bold text-pb-text">{item.q}</h3>
                <p className="text-[13px] leading-relaxed text-pb-text-muted">{item.a}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section style={{ background: "#e08a6f" }}>
        <div className="mx-auto flex max-w-[1100px] flex-col items-start justify-between gap-8 px-8 py-16 md:flex-row md:items-center lg:px-14 lg:py-20">
          <h2 className="font-pb-mono text-3xl font-bold text-pb-bg md:text-4xl" style={{ letterSpacing: "-0.02em" }}>
            Need a custom quote? Let&apos;s talk.
          </h2>
          <Link
            href="/contact"
            className="font-pb-mono shrink-0 border-2 border-pb-bg bg-pb-bg px-8 py-3 text-[12px] font-bold tracking-widest text-pb-accent uppercase transition-all hover:bg-transparent hover:text-pb-bg"
          >
            Book a call →
          </Link>
        </div>
      </section>
    </>
  );
}
