import Link from "next/link";

/** The full-width coloured band that closes a marketing page. Each page gets
 * its own colour; `dark` picks dark text for light fills. */
export default function ClosingBand({ color, title, sub, cta, href, dark = false }: {
  color: string;
  title: React.ReactNode;
  sub?: string;
  cta: string;
  href: string;
  dark?: boolean;
}) {
  const ink = dark ? "#0a0908" : "#ffffff";
  return (
    <section style={{ background: color }}>
      <div className="mx-auto flex max-w-[1100px] flex-col items-start justify-between gap-8 px-6 py-20 md:flex-row md:items-center lg:px-14 lg:py-24">
        <div>
          <h2 className="max-w-2xl text-[clamp(2rem,4.2vw,3.25rem)] font-bold leading-[1.05] tracking-[-0.02em]" style={{ color: ink }}>
            {title}
          </h2>
          {sub ? <p className="mt-4 max-w-xl text-[15px] leading-relaxed" style={{ color: ink, opacity: 0.75 }}>{sub}</p> : null}
        </div>
        <Link href={href}
          className="font-pb-mono shrink-0 border-2 px-8 py-3.5 text-[12px] font-bold uppercase tracking-widest transition-colors"
          style={{ borderColor: ink, color: dark ? "#ffffff" : color, background: ink }}>
          {cta} →
        </Link>
      </div>
    </section>
  );
}
