import Link from "next/link";

const COLUMNS = [
  {
    title: "Platform",
    links: [
      { label: "Overview", href: "/platform" },
      { label: "Documents / PDF", href: "/platform/documents" },
      { label: "Subtitles", href: "/platform/subtitles" },
      { label: "Images", href: "/platform/images" },
      { label: "Websites", href: "/platform/websites" },
      { label: "YouTube", href: "/platform/youtube" },
    ],
  },
  {
    title: "Company",
    links: [
      { label: "Pricing", href: "/pricing" },
      { label: "Contact", href: "/contact" },
      { label: "Privacy", href: "#" },
      { label: "Terms", href: "#" },
    ],
  },
];

export default function Footer() {
  return (
    <footer
      className="pb-glass-section"
      style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
    >
      <div className="mx-auto max-w-[1100px] px-8 pt-16 pb-8 lg:px-14">
        <div className="flex flex-col justify-between gap-12 md:flex-row">
          <div className="flex flex-col gap-4">
            <span
              className="text-4xl italic text-pb-text md:text-5xl"
              style={{ fontFamily: "var(--font-fraunces), Georgia, serif" }}
            >
              page<span className="text-pb-accent">birdy</span>
            </span>
            <p className="max-w-xs text-[13px] leading-relaxed text-pb-text-muted">
              Layout-preserving document translation. Same file, any language.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-12 md:gap-16">
            {COLUMNS.map((col) => (
              <div key={col.title} className="flex flex-col gap-3">
                <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
                  {col.title}
                </span>
                {col.links.map((link) => (
                  <Link
                    key={link.label}
                    href={link.href}
                    className="text-[13px] text-pb-text-secondary transition-colors hover:text-pb-text"
                  >
                    {link.label}
                  </Link>
                ))}
              </div>
            ))}
          </div>
        </div>

        <div
          className="mt-14 flex flex-col items-start justify-between gap-4 pt-6 md:flex-row md:items-center"
          style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}
        >
          <span className="font-pb-mono text-[11px] tracking-wide text-pb-text-muted">
            © {new Date().getFullYear()} Pagebirdy. All rights reserved.
          </span>
          <span className="font-pb-mono text-[11px] tracking-wide text-pb-text-muted">
            hello@pagebirdy.com
          </span>
        </div>
      </div>
    </footer>
  );
}
