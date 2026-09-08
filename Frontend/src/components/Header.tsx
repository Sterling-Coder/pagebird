"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV = [
  { href: "/product", label: "Product" },
  { href: "/integrations", label: "Integrations" },
  { href: "/#pricing", label: "Pricing" },
  { href: "/contact", label: "Contact" },
];

export default function Header() {
  const pathname = usePathname();

  return (
    <header className="flex items-center justify-between border-b-[3px] border-pb-ink px-6 py-5 md:px-14">
      <Link
        href="/"
        className="text-[27px] italic"
        style={{ fontFamily: "var(--font-fraunces), Georgia, serif" }}
      >
        page<span className="text-pb-accent">bird</span>
      </Link>
      <nav className="hidden items-center gap-9 text-[13.5px] font-semibold tracking-wide uppercase md:flex">
        {NAV.map((item) => (
          <Link
            key={item.href}
            href={item.href}
            className={
              pathname === item.href
                ? "border-b-[3px] border-pb-accent pb-[3px]"
                : "hover:text-pb-accent"
            }
          >
            {item.label}
          </Link>
        ))}
      </nav>
      <div className="flex items-center gap-6">
        <Link
          href="/login"
          className="hidden text-[13.5px] font-semibold tracking-wide uppercase hover:text-pb-accent sm:inline"
        >
          Log in
        </Link>
        <Link
          href="/login"
          className="flex h-[42px] items-center bg-pb-accent px-5 text-[13.5px] font-bold tracking-wide text-pb-paper uppercase"
        >
          Try free
        </Link>
      </div>
    </header>
  );
}
