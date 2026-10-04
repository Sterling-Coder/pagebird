import Link from "next/link";
import type { Metadata } from "next";
import PricingFAQ from "@/components/PricingFAQ";

export const metadata: Metadata = {
  title: "Pricing — Pagebirdy",
  description:
    "No seat fees. No per-word rates. Start free, scale when ready. Pagebirdy prices by pages — nothing else.",
};

const CHECK = (
  <span style={{ color: "#4a9e8a", fontSize: "14px", fontWeight: 700 }}>✓</span>
);
const DASH = (
  <span style={{ color: "rgba(255,255,255,0.2)", fontSize: "14px" }}>—</span>
);

const TABLE_ROWS: Array<{ label: string; free: React.ReactNode; team: React.ReactNode; enterprise: React.ReactNode }> = [
  { label: "Pages", free: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>5 free</span>, team: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>Volume packs</span>, enterprise: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>Unlimited</span> },
  { label: "Languages", free: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>40+</span>, team: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>40+</span>, enterprise: <span style={{ color: "rgba(240,236,227,0.7)", fontSize: "13px" }}>40+</span> },
  { label: "PDF + IDML", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "Subtitles (SRT/VTT)", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Image translation", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Website translation", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "QA scoring", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "Side-by-side review", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Shared glossary", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "RTL mirroring", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "SSO / SCIM", free: DASH, team: DASH, enterprise: CHECK },
  { label: "Audit log", free: DASH, team: DASH, enterprise: CHECK },
  { label: "Data residency", free: DASH, team: DASH, enterprise: CHECK },
  { label: "SLA", free: DASH, team: DASH, enterprise: CHECK },
];

const FAQ = [
  {
    q: "What counts as a page?",
    a: "One A4/Letter side of a document. A 10-page PDF uses 10 page credits. Each language adds the same count — translating into 3 languages = 3× the pages.",
  },
  {
    q: "Do pages roll over?",
    a: "Yes. Unused pages roll over for 30 days on paid plans. Free pages don't expire but are one-time only.",
  },
  {
    q: "Can I translate into multiple languages at once?",
    a: "Yes. Translating the same file into 5 languages = 5× the page count. Bulk pricing applies on Team and Enterprise.",
  },
  {
    q: "What formats are included in Team?",
    a: "All current formats: IDML, PDF, SRT, VTT, AI, PSD, EPS, HTML — plus all future formats as they launch, at no extra cost.",
  },
  {
    q: "Is my data safe?",
    a: "Files are encrypted in transit and at rest. Deleted on your retention schedule. Never used for model training — ever.",
  },
  {
    q: "Do you offer a trial?",
    a: "The free tier is the trial. No card required, no time limit. Just 5 free pages to see the output quality before you commit.",
  },
];

export default function PricingPage() {
  const colStyle = (i: number): React.CSSProperties => ({
    textAlign: "center" as const,
    padding: "16px 20px",
    borderLeft: i > 0 ? "1px solid rgba(255,255,255,0.06)" : undefined,
  });

  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden" style={{
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
        minHeight: "44vh",
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
              Translate more.<br />Pay for what you use.
            </h1>
            <div className="pb-enter pb-enter-delay-1">
              <p className="max-w-md text-[16px] leading-relaxed text-pb-text-secondary">
                No seat fees. No per-word rates. No hidden costs. Just pages — priced fairly.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Comparison table */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-24">
          <div style={{ overflowX: "auto" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "600px" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0 20px 16px 0", width: "36%" }}>
                    <span style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.16em", color: "rgba(255,255,255,0.28)", fontFamily: "var(--font-space-mono), monospace", textTransform: "uppercase" }}>
                      Feature
                    </span>
                  </th>
                  {[
                    { name: "FREE", price: "$0", sub: "Try it out" },
                    { name: "TEAM", price: "Coming soon", sub: "For growing teams" },
                    { name: "ENTERPRISE", price: "Custom", sub: "Volume + compliance" },
                  ].map((plan, i) => (
                    <th key={plan.name} style={colStyle(i + 1)}>
                      <div>
                        <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.16em", color: "rgba(255,255,255,0.35)", fontFamily: "var(--font-space-mono), monospace", marginBottom: "8px" }}>
                          {plan.name}
                        </div>
                        <div style={{ fontSize: "28px", fontWeight: 700, color: "#f0ece3", fontFamily: "var(--font-space-mono), monospace", lineHeight: 1 }}>
                          {plan.price}
                        </div>
                        <div style={{ fontSize: "11px", color: "rgba(240,236,227,0.4)", marginTop: "4px" }}>
                          {plan.sub}
                        </div>
                      </div>
                    </th>
                  ))}
                </tr>
                {/* CTA row */}
                <tr>
                  <td style={{ padding: "12px 20px 24px 0", borderBottom: "1px solid rgba(255,255,255,0.08)" }} />
                  {[
                    { cta: "Get started", href: "/login", muted: false },
                    { cta: "Notify me", href: "/contact", muted: true },
                    { cta: "Book a call", href: "/contact", muted: false },
                  ].map((c, i) => (
                    <td key={c.cta} style={{ ...colStyle(i + 1), paddingBottom: "24px", borderBottom: "1px solid rgba(255,255,255,0.08)" }}>
                      <Link href={c.href} style={{
                        display: "inline-block",
                        fontFamily: "var(--font-space-mono), monospace",
                        fontSize: "10px", fontWeight: 700, letterSpacing: "0.1em",
                        textTransform: "uppercase", textDecoration: "none",
                        padding: "9px 20px",
                        border: "1px solid",
                        borderColor: c.muted ? "rgba(255,255,255,0.12)" : "#e08a6f",
                        color: c.muted ? "rgba(240,236,227,0.45)" : "#e08a6f",
                        borderRadius: "4px",
                        transition: "all 0.15s",
                      }}>
                        {c.cta}
                      </Link>
                    </td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TABLE_ROWS.map((row, idx) => (
                  <tr key={row.label} style={{ background: idx % 2 === 0 ? "rgba(255,255,255,0.015)" : "transparent" }}>
                    <td style={{ padding: "13px 20px 13px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span style={{ fontSize: "13px", color: "rgba(240,236,227,0.6)", fontFamily: "var(--font-space-mono), monospace" }}>
                        {row.label}
                      </span>
                    </td>
                    <td style={{ ...colStyle(1), padding: "13px 20px", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>{row.free}</td>
                    <td style={{ ...colStyle(2), padding: "13px 20px", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>{row.team}</td>
                    <td style={{ ...colStyle(3), padding: "13px 20px", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>{row.enterprise}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* FAQ */}
      <PricingFAQ items={FAQ} />

      {/* Enterprise CTA */}
      <section style={{
        background: "linear-gradient(135deg, #0f0e0c 0%, #1a1410 50%, #0c0a0e 100%)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
      }}>
        <div style={{
          maxWidth: "1100px", margin: "0 auto",
          padding: "64px 56px",
          display: "flex", alignItems: "center", justifyContent: "space-between",
          gap: "40px", flexWrap: "wrap",
        }}>
          <div>
            <h2 className="pb-stencil" style={{ fontSize: "clamp(1.8rem, 3vw, 2.8rem)", lineHeight: 1.1, margin: 0 }}>
              Need volume, SSO,<br />or data residency?
            </h2>
            <p style={{ fontSize: "14px", color: "rgba(240,236,227,0.45)", marginTop: "10px" }}>
              We work directly with regulated and high-volume teams on custom arrangements.
            </p>
          </div>
          <Link href="/contact" style={{
            fontFamily: "var(--font-space-mono), monospace",
            fontSize: "11px", fontWeight: 700, letterSpacing: "0.12em",
            color: "#15130f", background: "#e08a6f",
            padding: "16px 32px", whiteSpace: "nowrap" as const,
            textDecoration: "none", textTransform: "uppercase" as const,
            flexShrink: 0, borderRadius: "4px",
          }}>
            BOOK A CALL →
          </Link>
        </div>
      </section>
    </>
  );
}
