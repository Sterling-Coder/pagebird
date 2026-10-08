"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { getMe } from "@/lib/team";

type Item = {
  label: string;
  href: string;
  icon: string;
  isActive: (path: string) => boolean;
};

const GROUPS: Item[][] = [
  [
    {
      label: "Home",
      href: "/app",
      icon: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
      isActive: (p) => p === "/app",
    },
  ],
  [
    {
      label: "Jobs",
      href: "/app/jobs",
      icon: "M3 3h18v18H3zM9 3v18M15 3v18",
      isActive: (p) => p.startsWith("/app/jobs"),
    },
    {
      label: "Team",
      href: "/app/team",
      icon: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
      isActive: (p) => p === "/app/team",
    },
  ],
  [
    {
      label: "Settings",
      href: "/app/settings",
      icon: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z",
      isActive: (p) => p === "/app/settings",
    },
  ],
];

export function AppNavRail() {
  const pathname = usePathname() ?? "";
  const [name, setName] = useState<string | null>(null);

  useEffect(() => {
    getMe()
      .then((me) => setName(me.full_name || me.email))
      .catch(() => setName(null));
  }, []);

  const initial = (name ?? "?").trim().charAt(0).toUpperCase();

  return (
    <aside className="hidden w-[214px] shrink-0 flex-col px-2 pb-3 pt-3 md:flex">
      <Link href="/app" aria-label="Pagebirdy home" className="px-2.5 pb-4 pt-1">
        <span className="text-[14px] tracking-[0.04em]" style={{ fontFamily: "var(--font-mono), monospace" }}>
          <span className="text-[#3a3630]">page</span>
          <span className="text-[#e08a6f]">birdy</span>
        </span>
      </Link>

      <nav className="flex flex-1 flex-col gap-3.5">
        {GROUPS.map((group, i) => (
          <div key={i} className="flex flex-col gap-0.5">
            {group.map((item) => {
              const active = item.isActive(pathname);
              return (
                <Link
                  key={item.label}
                  href={item.href}
                  aria-current={active ? "page" : undefined}
                  className={`flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[13px] transition-colors ${
                    active
                      ? "bg-[#d6d0c4] font-semibold text-ink"
                      : "text-[#6b6560] hover:bg-[#dbd5ca] hover:text-ink"
                  }`}
                >
                  <svg
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.75"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className={`h-[15px] w-[15px] shrink-0 ${active ? "text-ink" : "text-[#8f8778]"}`}
                  >
                    <path d={item.icon} />
                  </svg>
                  {item.label}
                </Link>
              );
            })}
          </div>
        ))}
      </nav>

      <div className="mt-2 flex items-center gap-2.5 border-t border-[#d3ccbf] px-2.5 pt-3">
        <span
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-full text-[10px] font-bold text-white"
          style={{ background: "linear-gradient(135deg,#6b9cf4,#8b6fbf)" }}
        >
          {initial}
        </span>
        <span className="truncate text-[12.5px] text-ink">{name ?? "Account"}</span>
      </div>
    </aside>
  );
}
