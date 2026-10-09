"use client";

import { useEffect, useState } from "react";
import { getJobRow, type JobRow } from "@/lib/agents";
import { StatusBadge } from "@/components/app/ui";

/** Follows one job until it finishes, then hands the finished row back. */
export function useJob(jobId: string | null, intervalMs = 2500): JobRow | null {
  const [job, setJob] = useState<JobRow | null>(null);
  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const row = await getJobRow(jobId);
        if (stop) return;
        setJob(row);
        if (row.status === "processing") timer = setTimeout(tick, intervalMs);
      } catch {
        if (!stop) timer = setTimeout(tick, intervalMs * 2);
      }
    };
    tick();
    return () => { stop = true; clearTimeout(timer); };
  }, [jobId, intervalMs]);
  return jobId ? job : null;
}

export function JobProgress({ job }: { job: JobRow }) {
  const pct = job.meta?.progress;
  return (
    <div className="rounded-xl bg-[var(--app-surface-2)] p-4">
      <div className="flex items-center gap-2">
        <span className="truncate text-[13px] font-semibold text-ink">{job.original_filename ?? job.id}</span>
        <StatusBadge status={job.status} />
      </div>
      {job.status === "processing" ? (
        <>
          <p className="mt-2 text-[12.5px] text-ink-soft">{job.meta?.stage ? `Working: ${job.meta.stage}` : "Queued…"}</p>
          <div className="mt-2 h-1.5 overflow-hidden rounded-full bg-[var(--app-surface-3)]">
            {typeof pct === "number" ? (
              <div className="h-full rounded-full bg-[#e08a2c] transition-[width]" style={{ width: `${Math.max(4, pct)}%` }} />
            ) : (
              <div className="progress-indeterminate h-full w-full opacity-60" />
            )}
          </div>
        </>
      ) : null}
      {job.status === "failed" ? <p className="mt-2 text-[12.5px] text-[color:var(--app-danger)]">{job.error ?? "Translation failed."}</p> : null}
    </div>
  );
}

/** The job id in `?job=` when the page was opened from the Jobs board. */
export function useJobParam(): [string | null, (id: string | null) => void] {
  const [id, setId] = useState<string | null>(null);
  useEffect(() => {
    // Read once after mount; the URL is the only source and never changes underneath.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setId(new URLSearchParams(window.location.search).get("job"));
  }, []);
  const update = (next: string | null) => {
    setId(next);
    const url = new URL(window.location.href);
    if (next) url.searchParams.set("job", next); else url.searchParams.delete("job");
    window.history.replaceState(null, "", url);
  };
  return [id, update];
}
