"use client";

import { Fragment, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject, updateProject, listAllProjectFiles, type Project, type JobSummary } from "@/lib/projects";
import { getJobEval, evalDownloadUrl, type EvalReport } from "@/lib/translate";
import { downloadAuthed } from "@/lib/supabase/authFetch";
import { QaDetail } from "@/components/app/QaDetail";
import { Notice, T } from "@/components/app/UploadPane";
import { fileKind, getJobType } from "@/lib/jobTypes";
import { languageName } from "@/lib/languageNames";

/** A dd value that turns into a text input on click, saves on blur/Enter,
 * reverts on Escape. Lets "Client"/"Vendor" hold whatever free text the
 * user wants instead of being permanently stuck at "—" — there was no way
 * to set either after a project's creation until this existed. */
function EditableField({
  value,
  placeholder,
  onSave,
}: {
  value: string | null;
  placeholder: string;
  onSave: (next: string) => Promise<void>;
}) {
  const [editing, setEditing] = useState(false);
  const [draft, setDraft] = useState(value ?? "");
  const [saving, setSaving] = useState(false);

  if (!editing) {
    return (
      <button
        type="button"
        onClick={() => {
          setDraft(value ?? "");
          setEditing(true);
        }}
        className="text-left text-ink hover:underline"
      >
        {value || <span className="text-muted">{placeholder}</span>}
      </button>
    );
  }

  async function commit() {
    setSaving(true);
    try {
      if (draft !== (value ?? "")) await onSave(draft);
    } finally {
      setSaving(false);
      setEditing(false);
    }
  }

  return (
    <input
      autoFocus
      value={draft}
      disabled={saving}
      placeholder={placeholder}
      onChange={(e) => setDraft(e.target.value)}
      onBlur={commit}
      onKeyDown={(e) => {
        if (e.key === "Enter") (e.target as HTMLInputElement).blur();
        if (e.key === "Escape") {
          setDraft(value ?? "");
          setEditing(false);
        }
      }}
      className={`${T.input} py-1 disabled:opacity-50`}
    />
  );
}

export default function ProjectSettingsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<JobSummary[]>([]);
  const [checking, setChecking] = useState(false);
  const [results, setResults] = useState<Record<string, EvalReport | { error: string }>>({});
  const [downloading, setDownloading] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());
  const [notice, setNotice] = useState<{ kind: "success" | "error"; text: string } | null>(null);
  // QA scores layout fidelity, which only PDF, IDML and linked-graphics jobs have.
  const checkable = files.filter((f) => f.status === "complete" && ["pdf", "idml", "links"].includes(fileKind(f)));

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
    listAllProjectFiles(params.projectId).then(setFiles).catch(() => setFiles([]));
  }, [params.projectId]);

  async function handleQaCheck() {
    setChecking(true);
    const next: Record<string, EvalReport | { error: string }> = {};
    await Promise.all(
      checkable.map(async (f) => {
        try {
          next[f.id] = await getJobEval(f.id, { refresh: true });
        } catch (err) {
          next[f.id] = { error: err instanceof Error ? err.message : "Failed" };
        }
      })
    );
    setResults(next);
    setChecking(false);
    const failures = Object.values(next).filter((r) => "error" in r).length;
    setNotice(
      failures
        ? { kind: "error", text: `QA finished, but ${failures} file${failures === 1 ? "" : "s"} couldn't be checked. See below.` }
        : { kind: "success", text: `QA checked ${checkable.length} file${checkable.length === 1 ? "" : "s"}.` }
    );
  }

  async function handleLqaReport() {
    setDownloading(true);
    try {
      await Promise.all(
        checkable.map((f) =>
          downloadAuthed(evalDownloadUrl(f.id, "pdf"), `${f.original_filename ?? f.id}-accuracy.pdf`)
        )
      );
      setNotice({ kind: "success", text: "LQA reports downloaded." });
    } catch (err) {
      setNotice({ kind: "error", text: err instanceof Error ? err.message : "Could not download the reports." });
    } finally {
      setDownloading(false);
    }
  }

  function toggleExpanded(id: string) {
    setExpanded((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const summaryCounts = (() => {
    let passed = 0, failed = 0, na = 0;
    for (const r of Object.values(results)) {
      if ("error" in r) continue;
      if (r.not_applicable) na += 1;
      else if (r.overall?.gates_passed) passed += 1;
      else failed += 1;
    }
    return { passed, failed, na };
  })();

  const type = getJobType(project?.job_type);

  return (
    <div className="overflow-auto px-6 py-5 text-[13px] text-ink-soft">
      {notice ? (
        <div className="mb-4 max-w-2xl">
          <Notice kind={notice.kind} onClose={() => setNotice(null)}>{notice.text}</Notice>
        </div>
      ) : null}

      <section className={`max-w-2xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Project details</h2>
        <p className="mt-0.5 text-[12px] text-muted">Click Client or Vendor to edit. Changes save when you leave the field.</p>
        <dl className="mt-4 grid grid-cols-[140px_minmax(0,1fr)] gap-y-2.5">
          <dt className="text-muted">Type</dt>
          <dd className="text-ink">{type?.label ?? project?.job_type ?? "—"}</dd>
          <dt className="text-muted">Languages</dt>
          <dd className="text-ink">
            {languageName(project?.source_lang) ?? "English"} → {languageName(project?.target_lang) ?? "chosen per upload"}
          </dd>
          <dt className="text-muted">Created</dt>
          <dd className="text-ink">{project ? new Date(project.created_at * 1000).toLocaleDateString() : "—"}</dd>
          <dt className="text-muted">Files</dt>
          <dd className="text-ink">{files.length}</dd>
          <dt className="text-muted">Client</dt>
          <dd>
            <EditableField
              value={project?.client ?? null}
              placeholder="Add client"
              onSave={async (next) => {
                try {
                  setProject(await updateProject(params.projectId, { client: next }));
                  setNotice({ kind: "success", text: "Client saved." });
                } catch (err) {
                  setNotice({ kind: "error", text: err instanceof Error ? err.message : "Could not save." });
                }
              }}
            />
          </dd>
          <dt className="text-muted">Vendor</dt>
          <dd>
            <EditableField
              value={project?.vendor ?? null}
              placeholder="Add vendor"
              onSave={async (next) => {
                try {
                  setProject(await updateProject(params.projectId, { vendor: next }));
                  setNotice({ kind: "success", text: "Vendor saved." });
                } catch (err) {
                  setNotice({ kind: "error", text: err instanceof Error ? err.message : "Could not save." });
                }
              }}
            />
          </dd>
        </dl>
      </section>

      <section className={`mt-4 max-w-2xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Quality checks</h2>
        <p className="mt-0.5 text-[12px] text-muted">
          Scores how faithfully each translated PDF or InDesign file keeps its layout and text. Office files, images and web pages
          aren&apos;t scored — review them in the file viewer instead.
        </p>
        <div className="mt-4 flex flex-wrap items-center gap-2">
          <button type="button" onClick={handleQaCheck} disabled={checking || checkable.length === 0} className={T.primaryBtn}>
            {checking ? "Checking…" : `Run QA on ${checkable.length} file${checkable.length === 1 ? "" : "s"}`}
          </button>
          <button type="button" onClick={handleLqaReport} disabled={downloading || checkable.length === 0} className={T.secondaryBtn}>
            {downloading ? "Downloading…" : "Download LQA reports"}
          </button>
        </div>
        {checkable.length === 0 ? (
          <p className="mt-3 text-[12px] text-muted">Nothing to check yet — QA becomes available once a PDF or IDML file in this project is translated.</p>
        ) : null}
      </section>

      {Object.keys(results).length > 0 ? (
        <div className={`mt-4 max-w-4xl ${T.card} p-5`}>
          <div className="mb-2 flex items-center justify-between">
            <p className="text-[14px] font-semibold text-ink">QA results</p>
            <p className="text-[12px] text-muted">
              {summaryCounts.passed} passed · {summaryCounts.failed} failed
              {summaryCounts.na > 0 ? ` · ${summaryCounts.na} not applicable` : ""}
            </p>
          </div>
          <table className="w-full max-w-4xl border-collapse text-sm">
            <thead>
              <tr className={`border-b ${T.border} text-left text-[11.5px] text-muted`}>
                <th className="py-2">File</th>
                <th className="py-2">Score</th>
                <th className="py-2">Gates</th>
              </tr>
            </thead>
            <tbody>
              {files.map((f) => {
                const r = results[f.id];
                if (!r) return null;
                if ("error" in r) {
                  return (
                    <tr key={f.id} className={`border-b ${T.border}`}>
                      <td className="py-2 text-ink">{f.original_filename ?? f.id}</td>
                      <td className={`py-2 ${T.error}`} colSpan={2}>
                        {r.error}
                      </td>
                    </tr>
                  );
                }
                const notApplicable = r.not_applicable;
                const score = r.overall?.score;
                const passed = r.overall?.gates_passed;
                const isOpen = expanded.has(f.id);
                return (
                  <Fragment key={f.id}>
                    <tr
                      onClick={() => toggleExpanded(f.id)}
                      className={`cursor-pointer border-b ${T.border} hover:bg-[var(--app-surface-2,#f6f2ea)]`}
                    >
                      <td className="py-2 text-ink">
                        <span className="mr-2 inline-block w-3 text-muted">{isOpen ? "▾" : "▸"}</span>
                        {f.original_filename ?? f.id}
                      </td>
                      <td className="py-2 text-ink-soft">
                        {notApplicable
                          ? "—"
                          : typeof score === "number"
                            ? `${Math.round(score * 100)}%`
                            : "—"}
                      </td>
                      <td
                        className={
                          notApplicable
                            ? "py-2 text-muted"
                            : passed
                              ? "py-2 text-ink"
                              : "py-2 text-[#b3261e]"
                        }
                      >
                        {notApplicable ? "Not applicable" : passed === undefined ? "—" : passed ? "Passed" : "Failed"}
                      </td>
                    </tr>
                    {isOpen ? (
                      <tr>
                        <td colSpan={3} className={`border-t ${T.border} ${T.surface2} p-0`}>
                          <QaDetail report={r} />
                        </td>
                      </tr>
                    ) : null}
                  </Fragment>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
