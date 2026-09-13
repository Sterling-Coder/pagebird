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
import { LinksPreview } from "@/components/app/LinksPreview";
import { ComingSoonWorkspace } from "@/components/app/ComingSoonWorkspace";
import { getJobType } from "@/lib/jobTypes";
import { downloadAuthed } from "@/lib/supabase/authFetch";

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
  const [downloading, setDownloading] = useState(false);

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
        const job = await getJob(params.fileId);
        if (cancelled) return;
        setResult(job);
        // A links batch job has its own job_type regardless of the project
        // it lives in ("document" projects can hold a links upload too) —
        // check the job itself, not the parent project.
        if (job.jobType === "links") {
          setJobType("links");
          setLoading(false);
          return;
        }
        const project = await getProject(params.projectId);
        if (cancelled) return;
        setJobType(project.job_type);
        if (project.job_type !== "document") {
          setLoading(false);
          return;
        }
        const [segs, langs] = await Promise.all([
          getSegments(params.fileId).catch(() => []),
          listLanguages().catch(() => ({ languages: [], default: "es" })),
        ]);
        if (cancelled) return;
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

  if (jobType === "links" && result) {
    return (
      <div className="flex min-h-0 min-w-0 flex-1 flex-col border-t border-rule bg-paper-dim">
        <LinksPreview jobId={result.jobId} jobName={result.translatedFileName} />
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

  // .idml only opens in InDesign — there's no faithful in-browser render to
  // compare it against, so skip the synced source/target preview and just
  // offer the download.
  const isIdml = result.translatedFileName.toLowerCase().endsWith(".idml");
  if (isIdml) {
    return (
      <div className="flex min-h-0 flex-1 flex-col items-center justify-center border-t border-rule bg-paper-dim p-8 text-center">
        <p className="font-mono text-[12px] text-ink">{result.translatedFileName}</p>
        <p className="mt-2 max-w-sm text-xs leading-relaxed text-ink-soft">
          No inline preview for .idml — open it in InDesign to view it.
        </p>
        <button
          type="button"
          disabled={downloading}
          onClick={() => {
            setDownloading(true);
            downloadAuthed(result.downloadUrl, result.translatedFileName)
              .catch((err) => setError(err instanceof Error ? err.message : "Download failed"))
              .finally(() => setDownloading(false));
          }}
          className="mt-4 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80 disabled:opacity-50"
        >
          {downloading ? "Preparing download…" : "Download →"}
        </button>
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
