"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getProject, type Project } from "@/lib/projects";
import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";

const TABS = [
  { label: "Settings", segment: "settings" },
  { label: "Files", segment: "files" },
  { label: "Linguistic assets", segment: "linguistic-assets" },
  { label: "Statistics", segment: "statistics" },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [navOpen, setNavOpen] = useState(true);

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
  }, [params.projectId]);

  return (
    <div className="flex h-screen bg-paper">
      {navOpen ? <AppNavRail /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar
          navOpen={navOpen}
          onToggleNav={() => setNavOpen((v) => !v)}
          breadcrumb={
            <span>
              Projects / {project?.name ?? "…"} /{" "}
              {TABS.find((tab) => pathname?.startsWith(`/app/jobs/${params.projectId}/${tab.segment}`))?.label ?? ""}
            </span>
          }
        />
        <div className="flex min-h-0 flex-1">
          <div className="flex min-w-0 flex-1 flex-col">
            <div className="border-b border-rule px-6 py-4">
              <p className="text-lg font-bold text-ink">{project?.name ?? "…"}</p>
              <nav className="mt-3 flex gap-4 font-mono text-[11px] uppercase tracking-widest">
                {TABS.map((tab) => {
                  const href = `/app/jobs/${params.projectId}/${tab.segment}`;
                  const active = pathname?.startsWith(href);
                  return (
                    <Link
                      key={tab.segment}
                      href={href}
                      className={active ? "text-red" : "text-ink-soft hover:text-ink"}
                    >
                      {tab.label}
                    </Link>
                  );
                })}
              </nav>
            </div>
            <div className="flex min-h-0 min-w-0 flex-1 flex-col">{children}</div>
          </div>
        </div>
      </div>
    </div>
  );
}
