import Link from "next/link";
import type { Metadata } from "next";
import PricingFAQ, { type FAQItem } from "@/components/PricingFAQ";
import ClosingBand from "@/components/ClosingBand";

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
  { label: "Word, PowerPoint, Excel", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "Image translation", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Website translation", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Chrome extension", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "QA report", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "Side-by-side review", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "Shared glossary", free: DASH, team: CHECK, enterprise: CHECK },
  { label: "RTL mirroring", free: CHECK, team: CHECK, enterprise: CHECK },
  { label: "SSO / SCIM", free: DASH, team: DASH, enterprise: CHECK },
  { label: "Audit log", free: DASH, team: DASH, enterprise: CHECK },
  { label: "Data residency", free: DASH, team: DASH, enterprise: CHECK },
  { label: "SLA", free: DASH, team: DASH, enterprise: CHECK },
];

const FAQ_CATEGORIES = [
  "Plans & billing",
  "Files & formats",
  "Languages",
  "Chrome extension",
  "Privacy & data",
];

const FAQ: FAQItem[] = [
  // Plans & billing
  {
    category: "Plans & billing",
    q: "Is there a free trial?",
    a: "Yes. Every account starts with a 14-day free trial, and no card is needed to sign up. Upload real files and judge the output before you decide anything.",
  },
  {
    category: "Plans & billing",
    q: "What counts as a page?",
    a: "One A4/Letter side of a document. A 10-page PDF uses 10 page credits. Each target language counts separately, so translating into 3 languages uses 3× the pages.",
  },
  {
    category: "Plans & billing",
    q: "Can I translate into several languages at once?",
    a: "Yes. Pick as many target languages as you need for the same file. Each language is its own job and counts its own pages. Bulk pricing applies on Team and Enterprise.",
  },
  {
    category: "Plans & billing",
    q: "Do pages roll over?",
    a: "Unused pages roll over for 30 days on paid plans.",
  },
  {
    category: "Plans & billing",
    q: "When is the Team plan available?",
    a: "Team is coming soon. Use “Notify me” in the table above and we’ll tell you when it opens. If you need volume, SSO or data residency now, talk to us about Enterprise.",
  },
  // Files & formats
  {
    category: "Files & formats",
    q: "Which files can I translate?",
    a: "InDesign (.idml), PDF, Word (.docx), PowerPoint (.pptx), Excel (.xlsx), plain text, images (PNG, JPEG, WEBP, PSD and Illustrator .ai) and public web pages. You get back the same kind of file with the layout kept in place.",
  },
  {
    category: "Files & formats",
    q: "Can I upload an InDesign .indd file?",
    a: "Not directly. In InDesign, choose File → Export → InDesign Markup (IDML) and upload the .idml. IDML is our most complete path: styles, frames and threading come back intact.",
  },
  {
    category: "Files & formats",
    q: "What about older .doc, .ppt or .xls files?",
    a: "Legacy Office formats aren’t supported. Open the file in Word, PowerPoint or Excel and save it as .docx, .pptx or .xlsx, then upload that.",
  },
  {
    category: "Files & formats",
    q: "How are images handled?",
    a: "Text in the image is translated and set back in place. Illustrator files stay vector, so you can keep editing them. Photoshop (.psd) files come back as a flattened PNG.",
  },
  {
    category: "Files & formats",
    q: "How does website translation work?",
    a: "Paste the URL of a public page. Pagebirdy fetches it and gives you a translated, read-only copy that opens in a sandbox. Your live site is never changed.",
  },
  {
    category: "Files & formats",
    q: "How long does a job take?",
    a: "Jobs run in the background, so you can close the tab and come back. The Files page shows progress, and if a job fails it tells you why.",
  },
  {
    category: "Files & formats",
    q: "Can I check translation quality?",
    a: "Yes. You can run a QA report on any finished job. It scores the translation and points out passages worth a second look.",
  },
  // Languages
  {
    category: "Languages",
    q: "Which languages are supported?",
    a: "40+ languages, including the major European and Asian languages and the main right-to-left scripts. You choose the target language for each upload.",
  },
  {
    category: "Languages",
    q: "Do right-to-left languages work?",
    a: "Yes. Arabic, Hebrew, Persian and Urdu are mirrored inside the page: the page template stays where it is, and text, columns and reading order flip within it so the result reads naturally.",
  },
  // Chrome extension
  {
    category: "Chrome extension",
    q: "What does the Chrome extension do?",
    a: "Select text on any page to see its translation right beside it, or translate the whole page in place with one click.",
  },
  {
    category: "Chrome extension",
    q: "Do I need a separate account for the extension?",
    a: "No. Sign in with your Pagebirdy login and the extension uses the same account and languages.",
  },
  {
    category: "Chrome extension",
    q: "Does translating a page change the website?",
    a: "No. The extension only changes what you see in your own tab. Reload the page to get the original back.",
  },
  // Privacy & data
  {
    category: "Privacy & data",
    q: "Is my data safe?",
    a: "Files are encrypted in transit and stored per job in private storage. They are never used to train models.",
  },
  {
    category: "Privacy & data",
    q: "Can I delete my files?",
    a: "Yes. Deleting a job removes it and all of its files, the original and the translations, from storage.",
  },
  {
    category: "Privacy & data",
    q: "What does the extension send to Pagebirdy?",
    a: "Only the text you select, or the page text when you ask for a full-page translation. Nothing is sent while you just browse.",
  },
];

export default function PricingPage() {
  const colStyle = (i: number): React.CSSProperties => ({
    textAlign: "center" as const,
    padding: "16px 20px",
    borderLeft: i > 0 ? "1px solid rgba(255,255,255,0.06)" : undefined,
  });

  return (
    <div style={{ background: "#0a0908" }}>
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
      <section style={{ background: "#0a0908" }}>
        <div className="mx-auto max-w-[1100px] px-4 py-16 sm:px-8 lg:px-14 lg:py-24">
          <div style={{ overflowX: "auto", background: "#1d1c1a", border: "1px solid rgba(255,255,255,0.08)", borderRadius: 24, padding: "28px 24px 12px" }}>
            <table style={{ width: "100%", borderCollapse: "collapse", minWidth: "600px" }}>
              <thead>
                <tr>
                  <th style={{ textAlign: "left", padding: "0 20px 16px 0", width: "36%" }}>
                    <span style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.16em", color: "rgba(255,255,255,0.28)", fontFamily: "var(--font-space-mono), monospace", textTransform: "uppercase" }}>
                      Feature
                    </span>
                  </th>
                  {[
                    { name: "FREE", price: "$0", sub: "14-day trial, no card" },
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
                        fontSize: "13px", fontWeight: 600,
                        textDecoration: "none",
                        padding: "9px 20px",
                        border: "1px solid",
                        borderColor: c.muted ? "rgba(255,255,255,0.12)" : "#c86018",
                        background: c.muted ? "#292826" : "#c86018",
                        color: c.muted ? "#a8a49a" : "#fff",
                        borderRadius: "999px",
                        transition: "all 0.15s",
                      }}>
                        {c.cta}
                      </Link>
                    </td>
                  ))}
                </tr>
              </thead>
              <tbody>
                {TABLE_ROWS.map((row) => (
                  <tr key={row.label}>
                    <td style={{ padding: "13px 20px 13px 0", borderBottom: "1px solid rgba(255,255,255,0.04)" }}>
                      <span style={{ fontSize: "14px", color: "#a8a49a" }}>
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
      <PricingFAQ items={FAQ} categories={FAQ_CATEGORIES} />

      {/* Enterprise */}
      <ClosingBand
        color="#d99a2b"
        dark
        title={<>Need volume, SSO<br />or data residency?</>}
        sub="We set up regulated and high-volume teams directly: your formats, your glossaries, your security review."
        cta="Book a call"
        href="/contact"
      />
    </div>
  );
}
