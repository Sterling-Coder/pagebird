"use client";

import { Fragment, useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject, listAllProjectFiles, type Project, type JobSummary } from "@/lib/projects";
import { getJobEval, evalDownloadUrl, type EvalReport } from "@/lib/translate";
import { downloadAuthed } from "@/lib/supabase/authFetch";
import { QaDetail } from "@/components/app/QaDetail";

export default function ProjectSettingsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<JobSummary[]>([]);
  const [checking, setChecking] = useState(false);
  const [results, setResults] = useState<Record<string, EvalReport | { error: string }>>({});
  const [downloading, setDownloading] = useState(false);
  const [expanded, setExpanded] = useState<Set<string>>(new Set());

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
    listAllProjectFiles(params.projectId).then(setFiles).catch(() => setFiles([]));
  }, [params.projectId]);

  async function handleQaCheck() {
    setChecking(true);
    const next: Record<string, EvalReport | { error: string }> = {};
    await Promise.all(
      files.map(async (f) => {
        try {
          next[f.id] = await getJobEval(f.id, { refresh: true });
        } catch (err) {
          next[f.id] = { error: err instanceof Error ? err.message : "Failed" };
        }
      })
    );
    setResults(next);
    setChecking(false);
  }

  async function handleLqaReport() {
    setDownloading(true);
    try {
      await Promise.all(
        files.map((f) =>
          downloadAuthed(evalDownloadUrl(f.id, "pdf"), `${f.original_filename ?? f.id}-accuracy.pdf`)
        )
      );
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

  return (
    <div className="p-6 text-sm text-ink-soft">
      <div className="mb-6 flex items-center gap-3">
        <button
          type="button"
          onClick={handleQaCheck}
          disabled={checking || files.length === 0}
          className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90 disabled:opacity-40"
        >
          {checking ? "Checking…" : "QA check"}
        </button>
        <button
          type="button"
          onClick={handleLqaReport}
          disabled={downloading || files.length === 0}
          className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink disabled:opacity-40"
        >
          {downloading ? "Downloading…" : "LQA report"}
        </button>
      </div>

      <dl className="grid max-w-md grid-cols-2 gap-y-2">
        <dt className="text-muted">Source</dt>
        <dd className="text-ink">
          {project?.source_lang ?? "—"} → {project?.target_lang ?? "—"}
        </dd>
        <dt className="text-muted">Created</dt>
        <dd className="text-ink">
          {project ? new Date(project.created_at * 1000).toLocaleDateString() : "—"}
        </dd>
        <dt className="text-muted">Status</dt>
        <dd className="text-red">{project?.status ?? "—"}</dd>
        <dt className="text-muted">Client</dt>
        <dd>{project?.client ?? "—"}</dd>
        <dt className="text-muted">Vendor</dt>
        <dd>{project?.vendor ?? "—"}</dd>
      </dl>

      {Object.keys(results).length > 0 ? (
        <div className="mt-6">
          <div className="mb-2 flex items-center justify-between">
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted">QA results</p>
            <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
              {summaryCounts.passed} passed · {summaryCounts.failed} failed
              {summaryCounts.na > 0 ? ` · ${summaryCounts.na} not applicable` : ""}
            </p>
          </div>
          <table className="w-full max-w-4xl border-collapse text-sm">
            <thead>
              <tr className="border-b border-rule text-left font-mono text-[11px] uppercase tracking-widest text-muted">
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
                    <tr key={f.id} className="border-b border-rule">
                      <td className="py-2 text-ink">{f.original_filename ?? f.id}</td>
                      <td className="py-2 text-red" colSpan={2}>
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
                      className="cursor-pointer border-b border-rule hover:bg-paper-dim"
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
                              : "py-2 text-red"
                        }
                      >
                        {notApplicable ? "Not applicable" : passed === undefined ? "—" : passed ? "Passed" : "Failed"}
                      </td>
                    </tr>
                    {isOpen ? (
                      <tr>
                        <td colSpan={3} className="border-t border-rule bg-paper-dim p-0">
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
