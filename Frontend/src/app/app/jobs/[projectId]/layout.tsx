"use client";

import Link from "next/link";
import { usePathname, useParams } from "next/navigation";
import { useEffect, useState } from "react";
import { getProject, type Project } from "@/lib/projects";
import { getJobType } from "@/lib/jobTypes";
import { languageName } from "@/lib/languageNames";
import { AppTopBar } from "@/components/app/AppTopBar";
import { T } from "@/components/app/UploadPane";

const TABS = [
  { label: "Files", segment: "files" },
  { label: "Settings", segment: "settings" },
  { label: "Linguistic assets", segment: "linguistic-assets" },
  { label: "Statistics", segment: "statistics" },
];

export default function ProjectLayout({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    getProject(params.projectId)
      .then((p) => {
        setProject(p);
        setMissing(false);
      })
      .catch(() => setMissing(true));
  }, [params.projectId]);

  const type = getJobType(project?.job_type);

  return (
    <div className={`flex h-full w-full ${T.surface}`}>
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar />
        <div className={`border-b ${T.border} px-6 pt-5`}>
          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-[17px] font-semibold text-ink">{project?.name ?? (missing ? "Project not found" : "…")}</h1>
            {type ? (
              <span className={`inline-flex items-center gap-1.5 rounded-full ${T.surface2} px-2.5 py-0.5 text-[11.5px] text-ink-soft`}>
                <span className="h-2 w-2 rounded-full" style={{ background: type.color }} />
                {type.label}
              </span>
            ) : null}
            {project ? (
              <span className="text-[12px] text-muted">
                {languageName(project.source_lang) ?? "English"} → {languageName(project.target_lang) ?? "choose per upload"}
              </span>
            ) : null}
          </div>
          {missing ? (
            <p className={`mt-2 text-[12.5px] ${T.error}`}>
              This project couldn&apos;t be loaded. It may have been deleted, or you may not have access.{" "}
              <Link href="/app/projects" className="underline">Back to projects</Link>
            </p>
          ) : null}
          <nav className="mt-4 flex gap-5 text-[13px]" aria-label="Project sections">
            {TABS.map((tab) => {
              const href = `/app/jobs/${params.projectId}/${tab.segment}`;
              const active = pathname?.startsWith(href);
              return (
                <Link
                  key={tab.segment}
                  href={href}
                  aria-current={active ? "page" : undefined}
                  className={`-mb-px border-b-2 pb-2.5 transition-colors ${
                    active ? `${T.accentBorder} font-medium text-ink` : "border-transparent text-ink-soft hover:text-ink"
                  }`}
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
  );
}
