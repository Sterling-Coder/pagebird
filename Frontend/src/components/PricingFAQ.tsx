"use client";

interface FAQItem {
  q: string;
  a: string;
}

export default function PricingFAQ({ items }: { items: FAQItem[] }) {
  return (
    <section className="pb-glass-section" style={{ background: "#0a0908" }}>
      <div className="mx-auto max-w-[900px] px-8 py-16 lg:px-14 lg:py-24">
        <div className="flex items-center gap-3 mb-16">
          <span className="inline-block h-2 w-2 bg-pb-accent" />
          <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Common questions</span>
        </div>
        <div className="space-y-3">
          {items.map((item) => (
            <div
              key={item.q}
              style={{
                border: "1px solid rgba(255,255,255,0.08)",
                borderRadius: "8px",
                padding: "20px 24px",
                backgroundColor: "rgba(255,255,255,0.02)",
                transition: "all 0.2s ease",
                cursor: "pointer",
              }}
              className="hover:bg-opacity-[0.04] hover:border-pb-accent/30"
              onMouseEnter={(e) => {
                (e.currentTarget as HTMLElement).style.backgroundColor = "rgba(255,255,255,0.04)";
                (e.currentTarget as HTMLElement).style.borderColor = "rgba(224,138,111,0.2)";
              }}
              onMouseLeave={(e) => {
                (e.currentTarget as HTMLElement).style.backgroundColor = "rgba(255,255,255,0.02)";
                (e.currentTarget as HTMLElement).style.borderColor = "rgba(255,255,255,0.08)";
              }}
            >
              <h3 style={{ fontSize: "15px", fontWeight: 700, color: "#f0ece3", margin: "0 0 10px 0" }}>
                {item.q}
              </h3>
              <p style={{ fontSize: "13px", lineHeight: 1.7, color: "rgba(240,236,227,0.5)", margin: 0 }}>
                {item.a}
              </p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
