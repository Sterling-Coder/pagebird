"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, PageHeader, Pill, PrimaryButton, STATUS_STYLE, Empty, timeAgo } from "@/components/app/ui";
import { listJobs, jobKind, type JobRow } from "@/lib/agents";
import { languageName } from "@/lib/languageNames";

const COLUMNS: { status: string; title: string }[] = [
  { status: "processing", title: "Translating" },
  { status: "failed", title: "Needs attention" },
  { status: "complete", title: "Delivered" },
];
const KINDS = ["All", "Document", "Office", "Image", "Website", "Links"];

function jobHref(job: JobRow): string {
  if (job.project_id) return `/app/jobs/${job.project_id}/files/${job.id}`;
  return `/app/agents/${jobKind(job) === "Image" ? "image" : jobKind(job) === "Website" ? "website" : "document"}?job=${job.id}`;
}

function JobCard({ job }: { job: JobRow }) {
  const lang = languageName(job.meta?.target_lang ?? null) ?? job.meta?.target_language;
  const progress = job.status === "processing" ? job.meta?.progress : undefined;
  return (
    <Link href={jobHref(job)} className="block rounded-xl border border-[color:var(--app-border)] bg-[var(--app-surface)] p-3 shadow-[0_1px_2px_var(--app-shadow)] transition-colors hover:border-[color:var(--app-border-hover)]">
      <div className="flex items-center gap-2 text-[11.5px] text-muted">
        <span className="rounded bg-[var(--app-surface-3)] px-1.5 py-0.5 text-[10.5px] text-ink-soft">{jobKind(job)}</span>
        <span className="ml-auto">{timeAgo(job.created_at)}</span>
      </div>
      <div className="mt-2 truncate text-[13px] font-medium text-ink" title={job.original_filename ?? job.id}>
        {job.original_filename ?? job.id}
      </div>
      <div className="mt-1.5 flex items-center gap-2 text-[11.5px] text-ink-soft">
        {lang ? <span className="rounded-md border border-[color:var(--app-border)] px-1.5 py-0.5">{lang}</span> : null}
        {job.status === "processing" && job.meta?.stage ? <span className="truncate text-muted">{job.meta.stage}</span> : null}
      </div>
      {job.status === "failed" && job.error ? (
        <p className="mt-2 line-clamp-2 text-[11.5px] text-[color:var(--app-danger)]">{job.error}</p>
      ) : null}
      {typeof progress === "number" ? (
        <div className="mt-2 h-1 rounded-full bg-[var(--app-surface-3)]">
          <div className="h-1 rounded-full bg-[#e08a2c]" style={{ width: `${Math.max(4, progress)}%` }} />
        </div>
      ) : null}
    </Link>
  );
}

export default function JobsBoardPage() {
  const [jobs, setJobs] = useState<JobRow[] | null>(null);
  const [kind, setKind] = useState("All");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = () => listJobs().then((j) => { setJobs(j); setError(null); }).catch((e) => setError(e.message));
    load();
    const poll = setInterval(load, 6000);
    return () => clearInterval(poll);
  }, []);

  const shown = (jobs ?? []).filter((j) => kind === "All" || jobKind(j) === kind)
    .sort((a, b) => b.created_at - a.created_at);

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.jobs} title="Jobs" count={jobs?.length}
        desc="Every translation across your projects and agents."
        right={<Link href="/app/agents"><PrimaryButton>+ New translation</PrimaryButton></Link>} />
      <div className="flex flex-wrap gap-2 px-6 pb-4">
        {KINDS.map((k) => <Pill key={k} active={kind === k} onClick={() => setKind(k)}>{k}</Pill>)}
      </div>
      {error ? <p className="px-6 pb-3 text-[12.5px] text-[color:var(--app-danger)]">{error}</p> : null}
      <div className="min-h-0 flex-1 overflow-auto bg-[var(--app-surface-2)] px-6 py-5">
        {jobs !== null && jobs.length === 0 ? (
          <Empty>No translations yet. Start one from <Link href="/app/agents" className="underline">Agents</Link>.</Empty>
        ) : (
          <div className="grid min-w-[720px] grid-cols-3 gap-4">
            {COLUMNS.map((col) => {
              const items = shown.filter((j) => j.status === col.status);
              return (
                <div key={col.status} className="flex flex-col gap-2">
                  <div className="flex items-center gap-2 px-1 pb-1 text-[13px] font-semibold text-ink">
                    <span className="h-2 w-2 rounded-full" style={{ background: STATUS_STYLE[col.status].dot }} />
                    {col.title}
                    <span className="font-normal text-muted">{items.length}</span>
                  </div>
                  {jobs === null ? <p className="px-1 text-[12.5px] text-muted">Loading…</p> : null}
                  {items.map((j) => <JobCard key={j.id} job={j} />)}
                </div>
              );
            })}
          </div>
        )}
      </div>
    </div>
  );
}
