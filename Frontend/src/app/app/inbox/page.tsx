"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, PageHeader, StatusBadge, Empty, timeAgo } from "@/components/app/ui";
import { listJobs, jobKind, type JobRow } from "@/lib/agents";
import { getTeam, acceptTeamInvite, declineTeamInvite, epochSec, type TeamInfo } from "@/lib/team";

type Item =
  | { kind: "job"; at: number; job: JobRow }
  | { kind: "invite"; at: number; ownerId: string; email: string };

const WEEK = 7 * 86400;

export default function InboxPage() {
  const [jobs, setJobs] = useState<JobRow[] | null>(null);
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [busy, setBusy] = useState<string | null>(null);

  function load() {
    listJobs().then(setJobs).catch(() => setJobs([]));
    getTeam().then(setTeam).catch(() => setTeam(null));
  }
  useEffect(() => {
    load();
    const poll = setInterval(load, 15000);
    return () => clearInterval(poll);
  }, []);

  const [now] = useState(() => Date.now() / 1000);
  const items: Item[] = [
    ...(jobs ?? [])
      .filter((j) => j.status !== "processing" && now - j.created_at < WEEK)
      .map((job) => ({ kind: "job" as const, at: job.created_at, job })),
    ...(team?.pending_invitations ?? []).map((inv) => ({
      kind: "invite" as const, at: epochSec(inv.created_at), ownerId: inv.owner_id, email: inv.email,
    })),
  ].sort((a, b) => b.at - a.at);

  async function answer(ownerId: string, accept: boolean) {
    setBusy(ownerId);
    try {
      await (accept ? acceptTeamInvite(ownerId) : declineTeamInvite(ownerId));
      load();
    } finally {
      setBusy(null);
    }
  }

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.inbox} title="Inbox" count={items.length}
        desc="Finished and failed translations from the last week, and team invitations." />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-8">
        <div className="mx-auto max-w-[760px] space-y-2">
          {jobs === null ? <p className="text-[13px] text-muted">Loading…</p> : null}
          {jobs !== null && items.length === 0 ? <Empty>Nothing new. Finished translations show up here.</Empty> : null}
          {items.map((it) =>
            it.kind === "invite" ? (
              <div key={`inv-${it.ownerId}`} className="flex items-center gap-3 rounded-2xl bg-[var(--app-surface-2)] px-4 py-3">
                <span className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-[#8b6fbf] text-[12px] font-bold text-white">
                  {it.email.charAt(0).toUpperCase()}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="text-[13px] font-semibold text-ink">{it.email}</div>
                  <div className="text-[12.5px] text-ink-soft">invited you to their workspace</div>
                </div>
                <button type="button" disabled={busy === it.ownerId} onClick={() => answer(it.ownerId, false)}
                  className="rounded-full border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-1 text-[12px] text-ink-soft">Decline</button>
                <button type="button" disabled={busy === it.ownerId} onClick={() => answer(it.ownerId, true)}
                  className="rounded-full bg-[var(--app-accent)] px-3 py-1 text-[12px] font-semibold text-white">Accept</button>
              </div>
            ) : (
              <Link key={it.job.id}
                href={it.job.project_id ? `/app/jobs/${it.job.project_id}/files/${it.job.id}` : `/app/jobs`}
                className="flex items-center gap-3 rounded-2xl bg-[var(--app-surface-2)] px-4 py-3 hover:bg-[var(--app-surface-3)]">
                <span className={`flex h-9 w-9 shrink-0 items-center justify-center rounded-full text-[11px] font-bold text-white ${
                  it.job.status === "failed" ? "bg-[#d9534f]" : "bg-[#4caf50]"}`}>
                  {jobKind(it.job).slice(0, 2).toUpperCase()}
                </span>
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="truncate text-[13px] font-semibold text-ink">{it.job.original_filename ?? it.job.id}</span>
                    <StatusBadge status={it.job.status} />
                  </div>
                  <div className="truncate text-[12.5px] text-ink-soft">
                    {it.job.status === "failed"
                      ? it.job.error ?? "Translation failed"
                      : `Translated to ${it.job.meta?.target_language ?? it.job.meta?.target_lang ?? "the target language"}`}
                  </div>
                </div>
                <span className="shrink-0 text-[11.5px] text-muted">{timeAgo(it.at)}</span>
              </Link>
            ),
          )}
        </div>
      </div>
    </div>
  );
}
