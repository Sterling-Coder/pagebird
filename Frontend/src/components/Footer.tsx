import Link from "next/link";

const PLATFORM_LINKS = [
  { label: "Overview", href: "/platform" },
  { label: "Documents / PDF", href: "/platform/documents" },
  { label: "Subtitles", href: "/platform/subtitles" },
  { label: "Images", href: "/platform/images" },
  { label: "Websites", href: "/platform/websites" },
  { label: "YouTube", href: "/platform/youtube" },
];

const COMPANY_LINKS = [
  { label: "Pricing", href: "/pricing" },
  { label: "Contact", href: "/contact" },
  { label: "Privacy", href: "#" },
  { label: "Terms", href: "#" },
];

export default function Footer() {
  return (
    <footer
      style={{
        background: "rgba(8,7,6,0.95)",
        backdropFilter: "blur(20px)",
        WebkitBackdropFilter: "blur(20px)",
        borderTop: "1px solid rgba(255,255,255,0.06)",
      }}
    >
      {/* Top gradient strip */}
      <div
        style={{
          height: "1px",
          background: "linear-gradient(90deg, #c8a820, #c86018, #b03010, #8a1c10, #5a1018, #2e0a20)",
        }}
      />

      <div className="mx-auto max-w-[1100px] px-8 pt-16 pb-8 lg:px-14">
        {/* Main row */}
        <div className="grid grid-cols-1 gap-12 md:grid-cols-3">
          {/* Left: wordmark + tagline + email */}
          <div className="flex flex-col gap-4">
            <Link href="/" className="flex items-baseline gap-0">
              <span
                style={{
                  fontFamily: "var(--font-share-tech-mono), monospace",
                  letterSpacing: "0.04em",
                  fontSize: "28px",
                  color: "rgba(240,236,227,0.6)",
                  fontWeight: 400,
                }}
              >
                page
              </span>
              <span
                style={{
                  fontFamily: "var(--font-share-tech-mono), monospace",
                  letterSpacing: "0.04em",
                  fontSize: "28px",
                  color: "#e08a6f",
                  fontWeight: 400,
                }}
              >
                birdy
              </span>
            </Link>
            <p className="font-pb-mono text-[12px] text-pb-text-muted">
              Same file. Any language.
            </p>
            <a
              href="mailto:hello@pagebirdy.com"
              className="font-pb-mono text-[12px] text-pb-text-secondary transition-colors hover:text-white"
            >
              hello@pagebirdy.com
            </a>
          </div>

          {/* Platform links */}
          <div className="flex flex-col gap-4">
            <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Platform
            </span>
            <div className="flex flex-col gap-2.5">
              {PLATFORM_LINKS.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className="text-[13px] text-pb-text-secondary transition-colors hover:text-white"
                >
                  {l.label}
                </Link>
              ))}
            </div>
          </div>

          {/* Company links */}
          <div className="flex flex-col gap-4">
            <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
              Company
            </span>
            <div className="flex flex-col gap-2.5">
              {COMPANY_LINKS.map((l) => (
                <Link
                  key={l.href}
                  href={l.href}
                  className="text-[13px] text-pb-text-secondary transition-colors hover:text-white"
                >
                  {l.label}
                </Link>
              ))}
            </div>
          </div>
        </div>

        {/* Bottom row */}
        <div
          className="mt-14 flex flex-col items-start justify-between gap-3 pt-6 sm:flex-row sm:items-center"
          style={{ borderTop: "1px solid rgba(255,255,255,0.05)" }}
        >
          <span className="font-pb-mono text-[11px] text-pb-text-muted">
            © {new Date().getFullYear()} Pagebirdy. All rights reserved.
          </span>
          <a
            href="mailto:hello@pagebirdy.com"
            className="font-pb-mono text-[11px] text-pb-text-muted transition-colors hover:text-white"
          >
            hello@pagebirdy.com
          </a>
        </div>
      </div>
    </footer>
  );
}
