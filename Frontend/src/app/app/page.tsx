"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, PageHeader } from "@/components/app/ui";
import { createProject, listProjects, type Project } from "@/lib/projects";
import { getMe } from "@/lib/team";
import { languageName } from "@/lib/languageNames";
import { ENABLED_JOB_TYPES, JOB_TYPES, getJobType, type JobTypeId } from "@/lib/jobTypes";
import { T, TargetLanguageSelect, Notice } from "@/components/app/UploadPane";
import { defaultProjectName } from "@/components/app/CreateJobModal";

const ARROW = "M7 17L17 7M8 7h9v9";
const SURFACE = "var(--app-surface-2, #f6f2ea)";
const LINE = "var(--app-border, #ebe5da)";

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
    failed ? `${failed} segment${failed === 1 ? "" : "s"} failed` : "",
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
  const [jobTypeId, setJobTypeId] = useState<JobTypeId>("document");
  const [lang, setLang] = useState("");
  const jobType = getJobType(jobTypeId) ?? JOB_TYPES[0];

  useEffect(() => {
    getMe().then((me) => setName(firstName(me))).catch(() => setName(null));
    const load = () => listProjects().then(setProjects).catch(() => setProjects([]));
    load();
    const poll = setInterval(load, 15000);
    return () => clearInterval(poll);
  }, []);

  async function start() {
    const projectName = title.trim() || defaultProjectName();
    if (submittingRef.current) return;
    submittingRef.current = true;
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({
        name: projectName,
        jobType: jobType.id,
        sourceLanguage: "en",
        targetLanguage: lang || undefined,
      });
      // Straight to the project's Files tab with the upload area open.
      router.push(`/app/jobs/${project.id}/files?upload=1`);
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
    { label: "Translate an image, a web page or a sentence", href: "/app/agents" },
    { label: "See every translation on the Jobs board", href: "/app/jobs" },
    { label: "Invite a teammate to your workspace", href: "/app/team" },
  ];

  return (
    <div className={`flex h-full w-full flex-col ${T.surface}`}>
      <AppTopBar />
      <PageHeader icon={ICON.home} title="Home" />
      <div className="flex min-h-0 flex-1 flex-col overflow-auto px-6 pb-10">
        {/* Auto margins centre the content vertically and collapse to 0 once it overflows. */}
        <div className="mx-auto mt-auto w-full max-w-[600px] pt-6">
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
              placeholder="Name a project to start translating (optional)…"
              aria-label="Project name"
              className="w-full bg-transparent text-[14px] text-ink outline-none placeholder:text-muted"
            />
            <div className="mt-4 flex flex-wrap items-center gap-1.5" role="radiogroup" aria-label="Project type">
              {ENABLED_JOB_TYPES.map((t) => {
                const active = t.id === jobTypeId;
                return (
                  <button
                    key={t.id}
                    type="button"
                    role="radio"
                    aria-checked={active}
                    title={`${t.description} ${t.formats}`}
                    onClick={() => setJobTypeId(t.id)}
                    className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[12px] transition-colors ${
                      active
                        ? `${T.accentBorder} ${T.surface} text-ink`
                        : `border-transparent text-ink-soft hover:text-ink`
                    }`}
                  >
                    <span className="h-2 w-2 rounded-full" style={{ background: t.color }} />
                    {t.label}
                  </button>
                );
              })}
            </div>
            <p className="mt-2 text-[11.5px] text-muted">{jobType.formats}</p>
            <div className="mt-3 flex flex-wrap items-center gap-3 text-[12px] text-ink-soft">
              <span className="text-muted">English →</span>
              <div className="w-48">
                <TargetLanguageSelect value={lang} onChange={setLang} className="py-1.5 text-[12.5px]" />
              </div>
              <button
                type="submit"
                disabled={creating}
                className={`${T.primaryBtn} ml-auto inline-flex items-center gap-1.5`}
              >
                {creating ? "Creating…" : jobType.input === "url" ? "Create and add a page" : "Create and upload"}
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round"
                  strokeLinejoin="round" className="h-3.5 w-3.5">
                  <path d="M5 12h14M13 6l6 6-6 6" />
                </svg>
              </button>
            </div>
          </form>
          {error ? <div className="mt-2"><Notice kind="error" onClose={() => setError(null)}>{error}</Notice></div> : null}

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

        <div className="mx-auto mb-auto mt-12 grid w-full max-w-[980px] grid-cols-1 gap-6 lg:grid-cols-2">
          <section>
            <p className="mb-2 text-[10.5px] uppercase tracking-[0.08em] text-muted">Widgets</p>
            <Link href="/app/projects" className="mb-2 flex items-center justify-between text-[13px] font-semibold text-ink">
              Recent projects <Arrow />
            </Link>
            {projects === null ? (
              <p className="text-[12.5px] text-muted">Loading…</p>
            ) : recent.length === 0 ? (
              <p className="rounded-xl px-3 py-3 text-[12.5px] text-muted" style={{ background: SURFACE }}>
                No projects yet. Pick a type above and press “Create and upload” to translate your first file.
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
                  <span className="shrink-0 text-[11.5px] text-muted">{getJobType(p.job_type)?.label ?? p.status}</span>
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
                  <span className="h-2 w-2 shrink-0 rounded-full bg-[#d9534f]" />
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
