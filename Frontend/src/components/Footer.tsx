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

      {/* Giant wordmark */}
      <div style={{ textAlign: "center", padding: "60px 24px 40px" }}>
        <Link href="/">
          <span style={{
            fontFamily: "var(--font-share-tech-mono), monospace",
            fontSize: "clamp(60px, 10vw, 120px)",
            letterSpacing: "0.04em",
            fontWeight: 400,
            backgroundImage: "linear-gradient(90deg, #c8a820 0%, #e08a6f 30%, #8b6fbf 60%, #4a9e8a 80%, #c94040 100%)",
            WebkitBackgroundClip: "text",
            backgroundClip: "text",
            WebkitTextFillColor: "transparent",
            color: "transparent",
            display: "block",
          }}>
            pagebirdy
          </span>
        </Link>
        <p style={{
          fontSize: "13px",
          color: "rgba(240,236,227,0.35)",
          marginTop: "10px",
          fontFamily: "var(--font-space-mono), monospace",
          letterSpacing: "0.12em",
        }}>
          SAME FILE. ANY LANGUAGE.
        </p>
      </div>

      {/* Divider */}
      <div style={{
        height: "1px",
        background: "linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent)",
        margin: "0 40px",
      }} />

      {/* Horizontal links */}
      <div style={{
        display: "flex",
        flexWrap: "wrap",
        justifyContent: "center",
        alignItems: "center",
        gap: "6px 4px",
        padding: "28px 24px",
      }}>
        {ALL_LINKS.map((l, i) => (
          <span key={l.href} style={{ display: "flex", alignItems: "center", gap: "4px" }}>
            <Link
              href={l.href}
              className="footer-link"
              style={{
                fontSize: "12px",
                color: "rgba(240,236,227,0.38)",
                fontFamily: "var(--font-space-mono), monospace",
                letterSpacing: "0.04em",
                textDecoration: "none",
              }}
            >
              {l.label}
            </Link>
            {i < ALL_LINKS.length - 1 && (
              <span style={{ color: "rgba(255,255,255,0.12)", fontSize: "11px" }}>·</span>
            )}
          </span>
        ))}
      </div>

      {/* Bottom bar */}
      <div style={{
        borderTop: "1px solid rgba(255,255,255,0.04)",
        display: "flex",
        justifyContent: "space-between",
        alignItems: "center",
        padding: "16px 40px",
        flexWrap: "wrap",
        gap: "8px",
      }}>
        <span style={{
          fontSize: "11px",
          color: "rgba(240,236,227,0.25)",
          fontFamily: "var(--font-space-mono), monospace",
        }}>
          © 2026 Pagebirdy
        </span>
        <a
          href="mailto:hello@pagebirdy.com"
          style={{
            fontSize: "11px",
            color: "rgba(240,236,227,0.25)",
            fontFamily: "var(--font-space-mono), monospace",
            textDecoration: "none",
          }}
        >
          hello@pagebirdy.com
        </a>
      </div>
    </footer>
  );
}
