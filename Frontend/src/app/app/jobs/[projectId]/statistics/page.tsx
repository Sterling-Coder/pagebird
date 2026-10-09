"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getProject, listAllProjectFiles, type JobSummary, type Project } from "@/lib/projects";
import { fileKindLabel } from "@/lib/jobTypes";
import { T } from "@/components/app/UploadPane";

const SEGMENT_LABEL: Record<string, string> = {
  approved: "Edited by a reviewer",
  translated: "Machine translated",
  needs_human: "Flagged for review",
  failed: "Couldn't be translated",
  skipped: "Left as is (numbers, codes…)",
};

function Stat({ label, value, tone }: { label: string; value: number | string; tone?: string }) {
  return (
    <div className={`rounded-xl ${T.surface2} px-4 py-3`}>
      <p className={`text-[20px] font-semibold ${tone ?? "text-ink"}`}>{value}</p>
      <p className="text-[12px] text-muted">{label}</p>
    </div>
  );
}

export default function ProjectStatisticsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<JobSummary[] | null>(null);

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
    listAllProjectFiles(params.projectId).then(setFiles).catch(() => setFiles([]));
  }, [params.projectId]);

  const counts = project?.status_counts ?? {};
  const segmentTotal = Object.values(counts).reduce((a, b) => a + b, 0);
  const byStatus = (s: string) => (files ?? []).filter((f) => f.status === s).length;
  const byKind = Object.entries(
    (files ?? []).reduce<Record<string, number>>((acc, f) => {
      const k = fileKindLabel(f);
      acc[k] = (acc[k] ?? 0) + 1;
      return acc;
    }, {})
  );

  if (files !== null && files.length === 0) {
    return (
      <div className="px-6 py-5">
        <p className={`max-w-2xl rounded-2xl ${T.surface2} px-4 py-6 text-center text-[13px] text-muted`}>
          No statistics yet —{" "}
          <Link href={`/app/jobs/${params.projectId}/files?upload=1`} className={`${T.accentText} hover:underline`}>
            add a file
          </Link>{" "}
          and its progress and segment counts show up here.
        </p>
      </div>
    );
  }

  return (
    <div className="overflow-auto px-6 py-5 text-[13px] text-ink-soft">
      <section className={`max-w-3xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Files</h2>
        <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
          <Stat label="Total" value={files === null ? "…" : files.length} />
          <Stat label="Translated" value={files === null ? "…" : byStatus("complete")} tone="text-[#2e7d32]" />
          <Stat label="Translating" value={files === null ? "…" : byStatus("processing")} tone="text-[#9a5a14]" />
          <Stat label="Failed" value={files === null ? "…" : byStatus("failed")} tone={byStatus("failed") ? "text-[#b3261e]" : undefined} />
        </div>
        {byKind.length ? (
          <p className="mt-3 text-[12px] text-muted">{byKind.map(([k, n]) => `${n} ${k}`).join(" · ")}</p>
        ) : null}
      </section>

      <section className={`mt-4 max-w-3xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Segments</h2>
        <p className="mt-0.5 text-[12px] text-muted">Every sentence or text run across the project&apos;s files, by state.</p>
        {segmentTotal === 0 ? (
          <p className="mt-3 text-muted">No segments yet — they appear once a file finishes translating.</p>
        ) : (
          <ul className="mt-3 space-y-2">
            {Object.entries(counts)
              .sort((a, b) => b[1] - a[1])
              .map(([status, count]) => (
                <li key={status}>
                  <div className="flex justify-between text-[12.5px]">
                    <span className="text-ink">{SEGMENT_LABEL[status] ?? status}</span>
                    <span className="text-muted">{count} · {Math.round((count / segmentTotal) * 100)}%</span>
                  </div>
                  <div className="mt-1 h-1.5 overflow-hidden rounded-full bg-[var(--app-surface-2,#f0ece3)]">
                    <div className="h-full rounded-full bg-[var(--app-accent,#c86018)]" style={{ width: `${(count / segmentTotal) * 100}%` }} />
                  </div>
                </li>
              ))}
          </ul>
        )}
      </section>
    </div>
  );
}
