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
        background: "#0a0908",
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
        gridTemplateColumns: "1fr repeat(4, auto)",
        gap: "48px",
        maxWidth: "1100px",
        margin: "0 auto",
        padding: "48px 56px 40px",
        borderTop: "1px solid rgba(255,255,255,0.06)",
      }}>
        {/* Left — brand */}
        <div>
          <Link href="/" style={{ textDecoration: "none", display: "inline-block", marginBottom: "12px" }}>
            <span style={{ fontFamily: "var(--font-share-tech-mono), monospace", fontSize: "16px", letterSpacing: "0.04em" }}>
              <span style={{ color: "rgba(240,236,227,0.6)" }}>page</span><span style={{ color: "#e08a6f" }}>birdy</span>
            </span>
          </Link>
          <p style={{ fontSize: "11px", color: "rgba(240,236,227,0.28)", fontFamily: "var(--font-space-mono), monospace", lineHeight: 1.6, maxWidth: "180px" }}>
            Layout-preserving translation for documents, images and websites.
          </p>
        </div>

        {/* Right — 4 columns */}
        {[
          {
            title: "PLATFORM",
            links: [
              { label: "InDesign & PDF", href: "/platform/documents" },
              { label: "Word, PowerPoint, Excel", href: "/platform/documents" },
              { label: "Image Translator", href: "/platform/images" },
              { label: "Website Translator", href: "/platform/websites#link" },
              { label: "Chrome extension", href: "/platform/websites#extension" },
            ],
          },
          {
            title: "PRODUCT",
            links: [
              { label: "How it works", href: "/#how-it-works" },
              { label: "Formats", href: "/#formats" },
              { label: "Languages", href: "/platform/documents#languages" },
              { label: "Integrations", href: "/integrations" },
            ],
          },
          {
            title: "COMPANY",
            links: [
              { label: "About", href: "/about" },
              { label: "Pricing", href: "/pricing" },
              { label: "Privacy", href: "#" },
              { label: "Terms", href: "#" },
            ],
          },
          {
            title: "CONTACT",
            links: [
              { label: "hello@pagebirdy.com", href: "mailto:hello@pagebirdy.com" },
              { label: "Sales & pricing", href: "/contact" },
              { label: "Support", href: "/contact" },
              { label: "Extension early access", href: "/contact" },
              { label: "Reply within 1 business day", href: "/contact" },
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
