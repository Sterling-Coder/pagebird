"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

const NAV_ITEMS = [
  {
    label: "Jobs",
    href: "/app",
    enabled: true,
    isActive: (path: string) => path === "/app" || path.startsWith("/app/jobs"),
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <path d="M6 2h9l5 5v15H6z" />
        <path d="M15 2v5h5" />
      </svg>
    ),
  },
  {
    label: "Team",
    href: null,
    enabled: false,
    isActive: () => false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <circle cx="9" cy="8" r="3" />
        <path d="M2 21c0-3.9 3.1-7 7-7s7 3.1 7 7" />
        <path d="M16 4.2a3 3 0 0 1 0 5.8" />
        <path d="M22 21c0-3.3-2.3-6-5.5-6.8" />
      </svg>
    ),
  },
  {
    label: "Settings",
    href: null,
    enabled: false,
    isActive: () => false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
      </svg>
    ),
  },
];

export function AppNavRail() {
  const pathname = usePathname();

  return (
    <div className="flex w-56 shrink-0 flex-col border-r border-ink bg-paper-dim py-4">
      <div className="mb-6 px-4">
        <span className="font-mono text-sm font-black uppercase tracking-widest text-ink">
          Pagebird
        </span>
      </div>

      <nav className="flex flex-1 flex-col gap-1 px-2">
        {NAV_ITEMS.map((item) => {
          const active = item.enabled && item.isActive(pathname ?? "");
          const className = `relative flex items-center gap-3 px-3 py-2 text-sm transition-colors ${
            active
              ? "bg-red-dim/40 text-red"
              : item.enabled
                ? "text-ink-soft hover:bg-paper hover:text-ink"
                : "text-ink-soft/40"
          }`;
          const content = (
            <>
              {active ? (
                <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 bg-red" />
              ) : null}
              {item.icon}
              <span>{item.label}</span>
            </>
          );

          if (!item.enabled || !item.href) {
            return (
              <span key={item.label} aria-label={item.label} aria-disabled="true" className={className}>
                {content}
              </span>
            );
          }

          return (
            <Link key={item.label} href={item.href} aria-label={item.label} className={className}>
              {content}
            </Link>
          );
        })}
      </nav>
    </div>
  );
}
