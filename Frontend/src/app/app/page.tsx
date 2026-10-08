"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppTopBar } from "@/components/app/AppTopBar";
import { createProject, listProjects, type Project } from "@/lib/projects";
import { getMe } from "@/lib/team";
import { languageName } from "@/lib/languageNames";
import { JOB_TYPES } from "@/lib/jobTypes";

const ARROW = "M7 17L17 7M8 7h9v9";
const SURFACE = "#f6f2ea";
const LINE = "#e8e2d8";

function Arrow({ className = "" }: { className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"
      strokeLinejoin="round" className={`h-3 w-3 shrink-0 text-muted ${className}`}>
      <path d={ARROW} />
    </svg>
  );
}

function greeting(): string {
  const hour = new Date().getHours();
  if (hour < 12) return "Good morning";
  if (hour < 18) return "Good afternoon";
  return "Good evening";
}

function firstName(me: { first_name: string | null; full_name: string | null; email: string | null }): string | null {
  if (me.first_name) return me.first_name;
  if (me.full_name) return me.full_name.split(" ")[0];
  return me.email ? me.email.split("@")[0] : null;
}

function attention(p: Project): string | null {
  const failed = p.status_counts?.failed ?? 0;
  const review = p.status_counts?.needs_human ?? 0;
  const parts = [
    failed ? `${failed} failed` : "",
    review ? `${review} need${review === 1 ? "s" : ""} review` : "",
  ].filter(Boolean);
  return parts.length ? parts.join(" · ") : null;
}

export default function AppHomePage() {
  const router = useRouter();
  const [name, setName] = useState<string | null>(null);
  const [projects, setProjects] = useState<Project[] | null>(null);
  const [title, setTitle] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Set synchronously so a double Enter cannot create two identical projects.
  const submittingRef = useRef(false);
  const jobType = JOB_TYPES.find((t) => t.enabled) ?? JOB_TYPES[0];

  useEffect(() => {
    getMe().then((me) => setName(firstName(me))).catch(() => setName(null));
    const load = () => listProjects().then(setProjects).catch(() => setProjects([]));
    load();
    const poll = setInterval(load, 15000);
    return () => clearInterval(poll);
  }, []);

  async function start() {
    const projectName = title.trim();
    if (!projectName || submittingRef.current) return;
    submittingRef.current = true;
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({ name: projectName, jobType: jobType.id, sourceLanguage: "English" });
      router.push(`/app/jobs/${project.id}/files`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the project.");
      submittingRef.current = false;
      setCreating(false);
    }
  }

  const recent = [...(projects ?? [])].sort((a, b) => b.created_at - a.created_at);
  const latest = recent[0];
  const flagged = recent.filter((p) => attention(p));

  const steps = [
    ...(latest ? [{ label: `Continue “${latest.name}”`, href: `/app/jobs/${latest.id}/files` }] : []),
    { label: "See all your jobs", href: "/app/jobs" },
    { label: "Invite a teammate to your workspace", href: "/app/team" },
  ];

  return (
    <div className="flex h-full w-full flex-col bg-white">
      <AppTopBar breadcrumb="Home" />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-10">
        <div className="mx-auto w-full max-w-[600px] pt-14">
          <h1 className="text-center text-[22px] font-medium text-ink">
            {greeting()}{name ? `, ${name}` : ""}
          </h1>

          <form
            onSubmit={(e) => { e.preventDefault(); start(); }}
            className="mt-7 rounded-2xl p-4"
            style={{ background: SURFACE, border: `1px solid ${LINE}` }}
          >
            <input
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Name a project to start translating…"
              aria-label="Project name"
              className="w-full bg-transparent text-[14px] text-ink outline-none placeholder:text-muted"
            />
            <div className="mt-6 flex items-center gap-3 text-[12px] text-ink-soft">
              <span className="inline-block h-3.5 w-3.5 rounded-full bg-[#e8ac2e]" />
              <span>{jobType.label}</span>
              <span className="ml-auto text-muted">English → choose in project</span>
              <button
                type="submit"
                disabled={!title.trim() || creating}
                aria-label="Create project"
                className="flex h-7 w-7 items-center justify-center rounded-full bg-[#c86018] text-white transition-opacity disabled:opacity-40"
              >
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"
                  strokeLinejoin="round" className="h-3.5 w-3.5">
                  <path d="M12 19V5M5 12l7-7 7 7" />
                </svg>
              </button>
            </div>
          </form>
          {error ? <p className="mt-2 text-[12px] text-red">{error}</p> : null}

          <p className="mt-7 text-[11px] text-muted">Suggested next steps</p>
          {steps.map((s) => (
            <Link
              key={s.label}
              href={s.href}
              className="flex items-center justify-between py-2.5 text-[13px] text-ink-soft hover:text-ink"
              style={{ borderBottom: `1px solid ${LINE}` }}
            >
              <span className="truncate">{s.label}</span>
              <Arrow />
            </Link>
          ))}
        </div>

        <div className="mx-auto mt-12 grid w-full max-w-[980px] grid-cols-1 gap-6 lg:grid-cols-2">
          <section>
            <p className="mb-2 text-[10.5px] uppercase tracking-[0.08em] text-muted">Widgets</p>
            <Link href="/app/jobs" className="mb-2 flex items-center justify-between text-[13px] font-semibold text-ink">
              Recent jobs <Arrow />
            </Link>
            {projects === null ? (
              <p className="text-[12.5px] text-muted">Loading…</p>
            ) : recent.length === 0 ? (
              <p className="rounded-xl px-3 py-3 text-[12.5px] text-muted" style={{ background: SURFACE }}>
                No jobs yet. Name a project above to create your first one.
              </p>
            ) : (
              recent.slice(0, 4).map((p) => (
                <Link
                  key={p.id}
                  href={`/app/jobs/${p.id}/files`}
                  className="mb-1.5 flex items-center gap-3 rounded-xl px-3 py-2.5 hover:brightness-[0.98]"
                  style={{ background: SURFACE }}
                >
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13px] font-semibold text-ink">{p.name}</div>
                    <div className="truncate text-[12px] text-ink-soft">
                      {languageName(p.source_lang) ?? "—"} → {languageName(p.target_lang) ?? "—"} · {p.file_count}{" "}
                      file{p.file_count === 1 ? "" : "s"}
                    </div>
                  </div>
                  <span className="shrink-0 text-[11.5px] text-red">{p.status}</span>
                </Link>
              ))
            )}
          </section>

          <section className="lg:pt-[22px]">
            <div className="mb-2 flex items-center justify-between text-[13px] font-semibold text-ink">
              Needs your attention
            </div>
            {projects === null ? (
              <p className="text-[12.5px] text-muted">Loading…</p>
            ) : flagged.length === 0 ? (
              <p className="rounded-xl px-3 py-3 text-[12.5px] text-muted" style={{ background: SURFACE }}>
                Nothing needs your attention.
              </p>
            ) : (
              flagged.slice(0, 4).map((p) => (
                <Link
                  key={p.id}
                  href={`/app/jobs/${p.id}/files`}
                  className="mb-1.5 flex items-center gap-3 rounded-xl px-3 py-2.5 hover:brightness-[0.98]"
                  style={{ background: SURFACE }}
                >
                  <span className="h-2 w-2 shrink-0 rounded-full bg-red" />
                  <div className="min-w-0 flex-1">
                    <div className="truncate text-[13px] font-semibold text-ink">{p.name}</div>
                    <div className="truncate text-[12px] text-ink-soft">{attention(p)}</div>
                  </div>
                  <Arrow />
                </Link>
              ))
            )}
          </section>
        </div>
      </div>
    </div>
  );
}
