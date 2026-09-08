"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject } from "@/lib/projects";
import {
  API_BASE_URL,
  getJob,
  getJobHistory,
  getSegments,
  listLanguages,
  type Language,
  type Segment,
  type SegmentEvent,
  type TranslateResult,
} from "@/lib/translate";
import { SyncedDocumentPair } from "@/components/app/PdfPreview";
import { ComingSoonWorkspace } from "@/components/app/ComingSoonWorkspace";
import { getJobType } from "@/lib/jobTypes";

export default function FileEditorPage() {
  const params = useParams<{ projectId: string; fileId: string }>();
  const [jobType, setJobType] = useState<string | null>(null);
  const [result, setResult] = useState<TranslateResult | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<SegmentEvent[]>([]);
  const [historyLoading, setHistoryLoading] = useState(false);

  function toggleHistory() {
    setHistoryOpen((open) => {
      const next = !open;
      if (next) {
        setHistoryLoading(true);
        getJobHistory(params.fileId)
          .then(setHistory)
          .catch(() => setHistory([]))
          .finally(() => setHistoryLoading(false));
      }
      return next;
    });
  }

  useEffect(() => {
    let cancelled = false;
    async function load() {
      try {
        const project = await getProject(params.projectId);
        if (cancelled) return;
        setJobType(project.job_type);
        if (project.job_type !== "document") {
          setLoading(false);
          return;
        }
        const [job, segs, langs] = await Promise.all([
          getJob(params.fileId),
          getSegments(params.fileId).catch(() => []),
          listLanguages().catch(() => ({ languages: [], default: "es" })),
        ]);
        if (cancelled) return;
        setResult(job);
        setSegments(segs);
        setLanguages(langs.languages);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load file");
        }
      } finally {
        if (!cancelled) setLoading(false);
      }
    }
    load();
    return () => {
      cancelled = true;
    };
  }, [params.projectId, params.fileId]);

  if (loading) {
    return (
      <div className="flex flex-1 items-center justify-center text-muted">
        Loading…
      </div>
    );
  }

  if (jobType && jobType !== "document") {
    const config = getJobType(jobType);
    return <ComingSoonWorkspace label={config?.label ?? jobType} />;
  }

  if (error || !result) {
    return (
      <div className="flex flex-1 items-center justify-center text-red">
        {error ?? "File not found"}
      </div>
    );
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-rule bg-paper-dim">
      <div className="flex shrink-0 items-center justify-end border-b border-rule bg-paper px-4 py-1.5">
        <button
          type="button"
          onClick={toggleHistory}
          aria-pressed={historyOpen}
          className={`flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest transition-colors ${
            historyOpen ? "text-red" : "text-ink-soft hover:text-ink"
          }`}
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5">
            <circle cx="12" cy="12" r="9" />
            <path d="M12 7v5l3 3" />
          </svg>
          History
        </button>
      </div>
      <div className="flex min-h-0 min-w-0 flex-1">
        <SyncedDocumentPair
          source={{ kind: "url", url: `${API_BASE_URL}/api/jobs/${params.fileId}/source` }}
          target={
            result.previewUrl
              ? { kind: "url", url: result.previewUrl }
              : { kind: "url", url: `${API_BASE_URL}/api/jobs/${params.fileId}/output` }
          }
          segments={segments}
          downloadUrl={result.downloadUrl}
          fileName={result.translatedFileName}
          languages={languages}
          jobId={result.jobId}
        />
        {historyOpen ? (
          <div className="flex w-80 shrink-0 flex-col overflow-auto border-l border-rule bg-paper p-4">
            <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-muted">
              Edit history
            </p>
            {historyLoading ? (
              <p className="text-sm text-muted">Loading…</p>
            ) : history.length === 0 ? (
              <p className="text-sm text-muted">No edits yet.</p>
            ) : (
              <ul className="space-y-3">
                {history.map((h, i) => (
                  <li key={i} className="border-b border-rule pb-3 text-sm">
                    <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
                      {h.action} · {h.reviewer} · seg {h.seg_id}
                    </p>
                    <p className="mt-1 text-xs text-ink-soft line-through">
                      {h.old_target ?? "—"}
                    </p>
                    <p className="text-ink">{h.new_target ?? "—"}</p>
                    <p className="mt-1 text-xs text-muted">
                      {new Date(h.created_at * 1000).toLocaleString()}
                    </p>
                  </li>
                ))}
              </ul>
            )}
          </div>
        ) : null}
      </div>
    </div>
  );
}
