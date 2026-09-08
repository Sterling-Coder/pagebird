const COLUMNS = [
  {
    title: "Product",
    links: ["Overview", "Layout engine", "Pricing"],
  },
  {
    title: "Use cases",
    links: ["Legal contracts", "Financial reports", "Marketing decks"],
  },
  {
    title: "Developers",
    links: ["API reference", "Integrations", "Status"],
  },
  {
    title: "Company",
    links: ["Contact", "Privacy", "Terms"],
  },
];

export default function Footer() {
  return (
    <footer className="px-6 pt-14 pb-8 md:px-14">
      <div className="flex flex-col justify-between gap-10 border-b-[3px] border-pb-ink pb-10 md:flex-row">
        <span className="font-pb-display text-6xl italic tracking-tight lowercase md:text-8xl">
          page<span className="text-pb-accent">bird</span>
        </span>
        <div className="grid grid-cols-2 gap-10 pt-3 md:grid-cols-4 md:gap-12">
          {COLUMNS.map((col) => (
            <div key={col.title} className="flex flex-col gap-2.5">
              <span className="font-pb-mono-brand text-[11px] font-bold tracking-wide">
                {col.title.toUpperCase()}
              </span>
              {col.links.map((link) => (
                <span key={link} className="text-[13.5px] text-pb-muted">
                  {link}
                </span>
              ))}
            </div>
          ))}
        </div>
      </div>
      <div className="flex items-center justify-between pt-6">
        <span className="font-pb-mono-brand text-xs text-pb-faint">
          © 2026 PAGEBIRD. ALL RIGHTS RESERVED.
        </span>
        <span className="font-pb-mono-brand text-xs text-pb-faint">
          [HELLO@PAGEBIRD.COM]
        </span>
      </div>
    </footer>
  );
}
