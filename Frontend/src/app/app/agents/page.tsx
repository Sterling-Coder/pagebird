"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, Icon, PageHeader } from "@/components/app/ui";
import { listJobs, jobKind, type JobRow } from "@/lib/agents";

const AGENTS = [
  { id: "document", name: "Layout Agent", tag: "system", kinds: ["Document"], color: "#e0527a",
    desc: "InDesign and PDF, rebuilt with every frame, style and master in place.", formats: ".idml .pdf" },
  { id: "document", name: "Office Agent", tag: "", kinds: ["Office"], color: "#f5b942",
    desc: "Word, PowerPoint, Excel and text. Styles, links and formulas stay put.", formats: ".docx .pptx .xlsx .txt" },
  { id: "image", name: "OCR Agent", tag: "", kinds: ["Image"], color: "#4fc4a8",
    desc: "Reads the words in an image and paints the translation back in.", formats: ".png .jpg .webp .psd .ai" },
  { id: "website", name: "Web Agent", tag: "", kinds: ["Website"], color: "#6f9cff",
    desc: "Translates a public page into a safe, read-only copy.", formats: "URL" },
  { id: "text", name: "Quick Translate", tag: "", kinds: [], color: "#a98bf0",
    desc: "Paste a sentence or a paragraph and get it back translated.", formats: "text" },
];

/** Jobs per day for the last 7 days. */
function activity(jobs: JobRow[], kinds: string[], now: number): number[] {
  const days = Array.from({ length: 7 }, () => 0);
  for (const j of jobs) {
    if (!kinds.includes(jobKind(j))) continue;
    const d = Math.floor((now - j.created_at) / 86400);
    if (d >= 0 && d < 7) days[6 - d] += 1;
  }
  return days;
}

export default function AgentsPage() {
  const [jobs, setJobs] = useState<JobRow[]>([]);
  const [now] = useState(() => Date.now() / 1000);
  useEffect(() => { listJobs().then(setJobs).catch(() => setJobs([])); }, []);

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.agents} title="Agents" count={AGENTS.length}
        desc="One agent per kind of file. Pick one to start a translation." />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-8">
        <div className="grid items-center px-2 pb-2 text-[12px] text-muted"
          style={{ gridTemplateColumns: "minmax(0,1fr) 150px 110px 70px" }}>
          <span>Agent</span><span className="hidden sm:block">Formats</span>
          <span className="hidden sm:block">Activity 7d</span><span className="text-right">Runs</span>
        </div>
        {AGENTS.map((a) => {
          const bars = activity(jobs, a.kinds, now);
          const runs = jobs.filter((j) => a.kinds.includes(jobKind(j))).length;
          const max = Math.max(1, ...bars);
          return (
            <Link key={a.name} href={`/app/agents/${a.id}`}
              className="grid items-center rounded-xl px-2 py-3 hover:bg-[var(--app-surface-2)]"
              style={{ gridTemplateColumns: "minmax(0,1fr) 150px 110px 70px", borderTop: "1px solid var(--app-border)" }}>
              <div className="flex min-w-0 items-center gap-3">
                <span className="h-8 w-8 shrink-0" style={{ background: a.color, borderRadius: "50% 50% 46% 46%" }} />
                <div className="min-w-0">
                  <div className="flex items-center gap-2 text-[13.5px] font-semibold text-ink">
                    {a.name}
                    {a.tag ? <span className="rounded-md bg-[var(--app-surface-3)] px-1.5 text-[10.5px] font-normal text-ink-soft">{a.tag}</span> : null}
                  </div>
                  <div className="truncate text-[12.5px] text-ink-soft">{a.desc}</div>
                </div>
              </div>
              <span className="hidden font-mono text-[11.5px] text-ink-soft sm:block">{a.formats}</span>
              <svg viewBox="0 0 56 16" className="hidden h-4 w-14 sm:block" aria-label={`${bars.reduce((x, y) => x + y, 0)} runs this week`}>
                {bars.map((h, i) => (
                  <rect key={i} x={i * 8} y={16 - Math.max(1, (h / max) * 16)} width="6" height={Math.max(1, (h / max) * 16)} style={{ fill: "var(--app-border-hover)" }} rx="1" />
                ))}
              </svg>
              <span className="flex items-center justify-end gap-2 text-[12.5px] text-ink-soft">
                {a.kinds.length ? runs : "—"}
                <span className="text-muted"><Icon d={ICON.arrow} className="h-3 w-3" /></span>
              </span>
            </Link>
          );
        })}
      </div>
    </div>
  );
}
