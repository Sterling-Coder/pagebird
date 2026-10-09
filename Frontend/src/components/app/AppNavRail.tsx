"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { ME_UPDATED_EVENT, getMe, type Me } from "@/lib/team";
import { Avatar } from "./Avatar";
import { useAppShell } from "./AppShell";
import { SidebarIcon } from "./AppTopBar";
import { ThemeToggle } from "./ThemeToggle";
import { ICON, Icon } from "./ui";

type Item = {
  label: string;
  href: string;
  icon: string;
  badge?: string;
  isActive: (path: string) => boolean;
};

// Project detail pages live under /app/jobs/<projectId>/..., so "Jobs" is the
// board at /app/jobs exactly and everything below it belongs to "Projects".
const GROUPS: { heading?: string; items: Item[] }[] = [
  { items: [{ label: "Home", href: "/app", icon: ICON.home, isActive: (p) => p === "/app" }] },
  {
    items: [
      { label: "Inbox", href: "/app/inbox", icon: ICON.inbox, isActive: (p) => p === "/app/inbox" },
      { label: "Jobs", href: "/app/jobs", icon: ICON.jobs, isActive: (p) => p === "/app/jobs" },
      {
        label: "Projects", href: "/app/projects", icon: ICON.projects,
        isActive: (p) => p.startsWith("/app/projects") || (p.startsWith("/app/jobs/") && p !== "/app/jobs"),
      },
    ],
  },
  {
    items: [
      { label: "Agents", href: "/app/agents", icon: ICON.agents, isActive: (p) => p.startsWith("/app/agents") },
      { label: "Glossary", href: "/app/glossary", icon: ICON.glossary, isActive: (p) => p === "/app/glossary" },
      { label: "Workflows", href: "/app/workflows", icon: ICON.flow, badge: "Beta", isActive: (p) => p === "/app/workflows" },
    ],
  },
  {
    heading: "Labs",
    items: [{ label: "Extension", href: "/app/extension", icon: ICON.puzzle, badge: "New", isActive: (p) => p === "/app/extension" }],
  },
];

const FOOTER: Item[] = [
  // /app/settings redirects to /app/profile, so Profile is the one entry for both.
  {
    label: "Profile", href: "/app/profile", icon: ICON.user,
    isActive: (p) => p.startsWith("/app/profile") || p.startsWith("/app/settings"),
  },
  { label: "Team", href: "/app/team", icon: ICON.team, isActive: (p) => p === "/app/team" },
];

function NavLink({ item, pathname }: { item: Item; pathname: string }) {
  const active = item.isActive(pathname);
  return (
    <Link
      href={item.href}
      data-tour={"nav-" + item.label.toLowerCase()}
      aria-current={active ? "page" : undefined}
      className={`flex items-center gap-2.5 rounded-lg px-2.5 py-1.5 text-[13px] transition-colors ${
        active
          ? "bg-[var(--app-nav-active)] font-semibold text-[color:var(--app-ink)]"
          : "text-[color:var(--app-nav-ink)] hover:bg-[var(--app-nav-hover)] hover:text-[color:var(--app-ink)]"
      }`}
    >
      <span className={active ? "text-[color:var(--app-ink)]" : "text-[color:var(--app-muted)]"}><Icon d={item.icon} /></span>
      {item.label}
      {item.badge ? <span className="ml-auto text-[11px] font-normal text-[color:var(--app-muted)]">{item.badge}</span> : null}
    </Link>
  );
}

export function AppNavRail() {
  const pathname = usePathname() ?? "";
  const { toggleNav } = useAppShell();
  const [me, setMe] = useState<Partial<Me> | null>(null);

  useEffect(() => {
    getMe().then(setMe).catch(() => setMe(null));
    const onUpdate = (e: Event) => setMe((prev) => ({ ...prev, ...(e as CustomEvent<Partial<Me>>).detail }));
    window.addEventListener(ME_UPDATED_EVENT, onUpdate);
    return () => window.removeEventListener(ME_UPDATED_EVENT, onUpdate);
  }, []);

  const name = me?.full_name || me?.email || null;

  return (
    <aside className="hidden w-[214px] shrink-0 flex-col px-2 pb-3 pt-3 md:flex">
      <div className="flex items-center justify-between pb-4 pl-2.5 pr-1 pt-1">
        <Link href="/app" aria-label="Pagebirdy home">
          <span className="text-[14px] tracking-[0.04em]" style={{ fontFamily: "var(--font-mono), monospace" }}>
            <span className="text-[color:var(--app-ink-soft)]">page</span>
            <span className="text-[#e08a6f]">birdy</span>
          </span>
        </Link>
        <button
          type="button"
          onClick={toggleNav}
          aria-label="Collapse sidebar"
          className="rounded-md p-1 text-[color:var(--app-muted)] transition-colors hover:bg-[var(--app-nav-hover)] hover:text-[color:var(--app-ink)]"
        >
          <SidebarIcon />
        </button>
      </div>

      <nav className="flex flex-1 flex-col gap-3.5">
        {GROUPS.map((group, i) => (
          <div key={i} className="flex flex-col gap-0.5">
            {group.heading ? <p className="px-2.5 pb-1 pt-2 text-[11px] text-[color:var(--app-muted)]">{group.heading}</p> : null}
            {group.items.map((item) => <NavLink key={item.label} item={item} pathname={pathname} />)}
          </div>
        ))}
        <div className="mt-auto flex flex-col gap-0.5">
          {FOOTER.map((item) => <NavLink key={item.label} item={item} pathname={pathname} />)}
        </div>
      </nav>

      <div className="mt-2 flex items-center gap-2 border-t border-[color:var(--app-rail-rule)] pb-1 pl-2.5 pr-1 pt-3">
        <Link
          href="/app/profile"
          data-tour="nav-user"
          aria-label="Your profile"
          className="flex min-w-0 flex-1 items-center gap-2.5 transition-colors hover:text-[color:var(--app-ink)]"
        >
          <Avatar url={me?.avatar_url} name={name ?? "?"} seed={me?.email ?? undefined} size={24} />
          <span className="truncate text-[12.5px] text-[color:var(--app-ink)]">{name ?? "Account"}</span>
        </Link>
        <ThemeToggle className="shrink-0" />
      </div>
    </aside>
  );
}
