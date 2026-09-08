"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject, listAllProjectFiles, type Project, type JobSummary } from "@/lib/projects";
import { getJobEval, evalDownloadUrl, type EvalReport } from "@/lib/translate";

export default function ProjectSettingsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [files, setFiles] = useState<JobSummary[]>([]);
  const [checking, setChecking] = useState(false);
  const [results, setResults] = useState<Record<string, EvalReport | { error: string }>>({});
  const [downloading, setDownloading] = useState(false);

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
          next[f.id] = await getJobEval(f.id, true);
        } catch (err) {
          next[f.id] = { error: err instanceof Error ? err.message : "Failed" };
        }
      })
    );
    setResults(next);
    setChecking(false);
  }

  function handleLqaReport() {
    setDownloading(true);
    for (const f of files) {
      const a = document.createElement("a");
      a.href = evalDownloadUrl(f.id, "pdf");
      a.download = "";
      document.body.appendChild(a);
      a.click();
      a.remove();
    }
    setDownloading(false);
  }

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
          <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-muted">
            QA results
          </p>
          <table className="w-full max-w-2xl border-collapse text-sm">
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
                const score = r.overall?.score;
                const passed = r.overall?.gates_passed;
                return (
                  <tr key={f.id} className="border-b border-rule">
                    <td className="py-2 text-ink">{f.original_filename ?? f.id}</td>
                    <td className="py-2 text-ink-soft">
                      {typeof score === "number" ? `${Math.round(score * 100)}%` : "—"}
                    </td>
                    <td className={passed ? "py-2 text-ink" : "py-2 text-red"}>
                      {passed === undefined ? "—" : passed ? "Passed" : "Failed"}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      ) : null}
    </div>
  );
}
