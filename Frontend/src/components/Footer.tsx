import Link from "next/link";

const ALL_LINKS = [
  { label: "Overview", href: "/platform" },
  { label: "Documents/PDF", href: "/platform/documents" },
  { label: "Subtitles", href: "/platform/subtitles" },
  { label: "Images", href: "/platform/images" },
  { label: "Websites", href: "/platform/websites" },
  { label: "YouTube", href: "/platform/youtube" },
  { label: "Pricing", href: "/pricing" },
  { label: "Contact", href: "/contact" },
  { label: "Privacy", href: "#" },
  { label: "Terms", href: "#" },
];

export default function Footer() {
  return (
    <footer
      style={{
        background: "rgba(8,7,6,0.98)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
      }}
    >
      {/* Rainbow gradient bar */}
      <div style={{
        height: "1px",
        background: "linear-gradient(90deg, #c8a820, #e08a6f, #8b6fbf, #4a9e8a, #c94040)",
      }} />


      {/* Link columns */}
      <div style={{
        display: "grid",
        gridTemplateColumns: "repeat(4, 1fr)",
        gap: "32px",
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "0 56px 40px",
        borderTop: "1px solid rgba(255,255,255,0.06)",
        paddingTop: "40px",
      }}>
        {[
          {
            title: "PLATFORM",
            links: [
              { label: "Overview", href: "/platform" },
              { label: "Documents / PDF", href: "/platform/documents" },
              { label: "SRT / VTT Subtitles", href: "/platform/subtitles" },
              { label: "Image Translator", href: "/platform/images" },
              { label: "Website Translator", href: "/platform/websites" },
              { label: "YouTube Subtitles", href: "/platform/youtube" },
            ],
          },
          {
            title: "PRODUCT",
            links: [
              { label: "How it works", href: "/#how-it-works" },
              { label: "Capabilities", href: "/#capabilities" },
              { label: "Formats", href: "/#formats" },
              { label: "Languages", href: "/platform/documents#languages" },
              { label: "RTL support", href: "/platform/documents#rtl" },
              { label: "QA & Review", href: "/platform/documents#qa" },
            ],
          },
          {
            title: "COMPANY",
            links: [
              { label: "Pricing", href: "/pricing" },
              { label: "Contact", href: "/contact" },
              { label: "Privacy", href: "#" },
              { label: "Terms", href: "#" },
            ],
          },
          {
            title: "COMING SOON",
            links: [
              { label: ".docx / .pptx", href: "#" },
              { label: ".xlsx", href: "#" },
              { label: "API access", href: "#" },
              { label: "Glossary import", href: "#" },
              { label: "Team plans", href: "#" },
            ],
          },
        ].map((col) => (
          <div key={col.title}>
            <div style={{ fontSize: "9px", fontWeight: 700, letterSpacing: "0.16em", color: "rgba(255,255,255,0.28)", marginBottom: "14px", fontFamily: "var(--font-space-mono), monospace" }}>
              {col.title}
            </div>
            {col.links.map((l) => (
              <Link key={l.label} href={l.href} className="footer-link" style={{
                display: "block",
                fontSize: "12px",
                color: "rgba(240,236,227,0.38)",
                fontFamily: "var(--font-space-mono), monospace",
                letterSpacing: "0.02em",
                textDecoration: "none",
                marginBottom: "8px",
              }}>
                {l.label}
              </Link>
            ))}
          </div>
        ))}
      </div>

      {/* Bottom bar */}
      <div style={{
        borderTop: "1px solid rgba(255,255,255,0.04)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "16px 56px",
        flexWrap: "wrap",
        gap: "8px",
        maxWidth: "1100px",
        margin: "0 auto",
      }}>
        <span style={{ fontSize: "11px", color: "rgba(240,236,227,0.25)", fontFamily: "var(--font-space-mono), monospace" }}>
          © 2026 Pagebirdy
        </span>
        <a href="mailto:hello@pagebirdy.com" style={{ fontSize: "11px", color: "rgba(240,236,227,0.25)", fontFamily: "var(--font-space-mono), monospace", textDecoration: "none" }}>
          hello@pagebirdy.com
        </a>
      </div>

      {/* Giant wordmark — full width, touching edges */}
      <div style={{ overflow: "hidden", lineHeight: 0.85, paddingBottom: "0" }}>
        <Link href="/" style={{ textDecoration: "none", display: "block" }}>
          <span className="pb-stencil" style={{
            fontSize: "18.8vw",
            letterSpacing: "-0.02em",
            display: "block",
            textAlign: "center",
            lineHeight: 0.9,
          }}>
            pagebirdy
          </span>
        </Link>
        <div style={{ textAlign: "center", paddingBottom: "16px", marginTop: "8px" }}>
          <span style={{ fontSize: "11px", color: "rgba(240,236,227,0.2)", fontFamily: "var(--font-space-mono), monospace", letterSpacing: "0.18em" }}>
            SAME FILE. ANY LANGUAGE.
          </span>
        </div>
      </div>
    </footer>
  );
}
