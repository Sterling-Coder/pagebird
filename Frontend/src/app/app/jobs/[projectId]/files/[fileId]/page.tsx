"use client";

import { useEffect, useMemo, useState } from "react";
import { useParams, useRouter } from "next/navigation";
import {
  API_BASE_URL,
  getJobHistory,
  getSegments,
  listLanguages,
  rebuildJob,
  updateSegment,
  type Language,
  type Segment,
  type SegmentEvent,
} from "@/lib/translate";
import { authedBlobUrl, getJobRow, getWebsiteHtml, imageFileUrl, type JobRow } from "@/lib/agents";
import { downloadJobOutput, jobDownloadUrl } from "@/lib/projects";
import { fileKind, fileKindLabel, stageLabel, supportsRebuild, type FileKind } from "@/lib/jobTypes";
import { languageName } from "@/lib/languageNames";
import { SyncedDocumentPair } from "@/components/app/PdfPreview";
import { LinksPreview } from "@/components/app/LinksPreview";
import { Notice, T } from "@/components/app/UploadPane";

/** Back to wherever the person came from (keeps the folder they were in);
 * falls back to the project's Files list when the page was opened directly. */
function BackBar({ projectId, children }: { projectId: string; children?: React.ReactNode }) {
  const router = useRouter();
  return (
    <div className={`flex shrink-0 flex-wrap items-center gap-3 border-b ${T.border} px-6 py-2.5`}>
      <button
        type="button"
        onClick={() => (window.history.length > 1 ? router.back() : router.push(`/app/jobs/${projectId}/files`))}
        className="flex items-center gap-1.5 text-[12.5px] text-ink-soft transition-colors hover:text-ink"
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5">
          <path d="M19 12H5M11 6l-6 6 6 6" />
        </svg>
        Back to files
      </button>
      <div className="ml-auto flex flex-wrap items-center gap-2">{children}</div>
    </div>
  );
}

export default function FileViewerPage() {
  const params = useParams<{ projectId: string; fileId: string }>();
  const [job, setJob] = useState<JobRow | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);
  const [notice, setNotice] = useState<{ kind: "success" | "error"; text: string } | null>(null);

  // Follow the job until it finishes, so opening a running file still works.
  useEffect(() => {
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const row = await getJobRow(params.fileId);
        if (stop) return;
        setJob(row);
        if (row.status === "processing") timer = setTimeout(tick, 3000);
      } catch (err) {
        if (!stop) setError(err instanceof Error ? err.message : "Could not load this file.");
      }
    };
    tick();
    return () => {
      stop = true;
      clearTimeout(timer);
    };
  }, [params.fileId]);

  function download() {
    if (!job) return;
    setDownloading(true);
    downloadJobOutput(job)
      .catch((err) => setNotice({ kind: "error", text: err instanceof Error ? err.message : "Download failed." }))
      .finally(() => setDownloading(false));
  }

  const kind: FileKind | null = job ? fileKind(job) : null;
  const done = job?.status === "complete";
  const downloadButton = done ? (
    <button type="button" onClick={download} disabled={downloading || job?.download_available === false} className={T.primaryBtn}>
      {downloading ? "Preparing…" : "Download translation"}
    </button>
  ) : null;

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col">
      <BackBar projectId={params.projectId}>
        {job ? (
          <span className="mr-2 truncate text-[12.5px] text-muted">
            {fileKindLabel(job)} · {job.meta?.target_language ?? languageName(job.meta?.target_lang) ?? ""}
          </span>
        ) : null}
        {downloadButton}
      </BackBar>
      {notice ? (
        <div className="px-6 pt-3">
          <Notice kind={notice.kind} onClose={() => setNotice(null)}>{notice.text}</Notice>
        </div>
      ) : null}
      {error ? (
        <Centered><Notice kind="error">{error}</Notice></Centered>
      ) : !job || !kind ? (
        <Centered><p className="text-[13px] text-muted">Loading…</p></Centered>
      ) : job.status === "processing" ? (
        <Centered>
          <div className={`${T.card} w-full max-w-md p-5`}>
            <p className="truncate text-[13.5px] font-semibold text-ink">{job.original_filename}</p>
            <p className="mt-1 text-[12.5px] text-ink-soft">{stageLabel(job.meta?.stage) ?? "Queued"}…</p>
            <div className="mt-3 h-1.5 overflow-hidden rounded-full bg-[var(--app-surface-2,#f0ece3)]">
              {typeof job.meta?.progress === "number" ? (
                <div className="h-full rounded-full bg-[var(--app-accent,#c86018)] transition-[width]" style={{ width: `${Math.max(4, job.meta.progress)}%` }} />
              ) : (
                <div className="progress-indeterminate h-full w-full opacity-60" />
              )}
            </div>
            <p className="mt-3 text-[11.5px] text-muted">This page updates on its own. You can leave — the translation keeps running.</p>
          </div>
        </Centered>
      ) : job.status === "failed" ? (
        <Centered>
          <div className="w-full max-w-md">
            <Notice kind="error">
              <p className="font-medium">This translation failed.</p>
              <p className="mt-1">{job.error || "No reason was recorded."}</p>
              <p className="mt-2 opacity-80">Go back to Files and upload it again{kind === "website" ? " (or press retry on its row)" : ""}.</p>
            </Notice>
          </div>
        </Centered>
      ) : kind === "links" ? (
        <div className={`flex min-h-0 min-w-0 flex-1 flex-col ${T.surface2}`}>
          <LinksPreview jobId={job.id} jobName={job.original_filename ?? job.id} />
        </div>
      ) : kind === "image" ? (
        <ImageView job={job} />
      ) : kind === "idml" ? (
        <Centered>
          <div className={`${T.card} max-w-md p-6 text-center`}>
            <p className="text-[13.5px] font-semibold text-ink">{job.original_filename}</p>
            <p className="mt-2 text-[12.5px] leading-relaxed text-ink-soft">
              There&apos;s no in-browser preview for InDesign files. Download it and open it in InDesign — the download includes
              its translated Links when there are any.
            </p>
            <div className="mt-4 flex justify-center">{downloadButton}</div>
          </div>
        </Centered>
      ) : kind === "pdf" ? (
        <PdfView job={job} />
      ) : (
        <SegmentReview job={job} kind={kind} onNotice={setNotice} />
      )}
    </div>
  );
}

function Centered({ children }: { children: React.ReactNode }) {
  return <div className="flex min-h-0 flex-1 items-center justify-center p-8">{children}</div>;
}

/** PDF: the synced source/translation pair with in-place edits and rebuild. */
function PdfView({ job }: { job: JobRow }) {
  const [segments, setSegments] = useState<Segment[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [history, setHistory] = useState<SegmentEvent[] | null>(null);

  useEffect(() => {
    getSegments(job.id).then(setSegments).catch(() => setSegments([]));
    listLanguages().then((r) => setLanguages(r.languages)).catch(() => setLanguages([]));
  }, [job.id]);

  function toggleHistory() {
    const next = !historyOpen;
    setHistoryOpen(next);
    if (next) {
      setHistory(null);
      getJobHistory(job.id).then(setHistory).catch(() => setHistory([]));
    }
  }

  return (
    <div className={`flex min-h-0 min-w-0 flex-1 flex-col ${T.surface2}`}>
      <div className={`flex shrink-0 items-center gap-3 border-b ${T.border} ${T.surface} px-6 py-1.5`}>
        <p className="text-[12px] text-muted">Click a sentence in the translation to edit it — the PDF is rebuilt with your change.</p>
        <button type="button" onClick={toggleHistory} aria-pressed={historyOpen}
          className={`ml-auto text-[12px] ${historyOpen ? T.accentText : "text-ink-soft hover:text-ink"}`}>
          Edit history
        </button>
      </div>
      <div className="flex min-h-0 min-w-0 flex-1">
        <SyncedDocumentPair
          source={{ kind: "url", url: `${API_BASE_URL}/api/jobs/${job.id}/source` }}
          target={{ kind: "url", url: `${API_BASE_URL}/api/jobs/${job.id}/output` }}
          segments={segments}
          downloadUrl={jobDownloadUrl(job)}
          fileName={job.original_filename ?? job.id}
          languages={languages}
          jobId={job.id}
        />
        {historyOpen ? (
          <div className={`flex w-80 shrink-0 flex-col overflow-auto border-l ${T.border} ${T.surface} p-4`}>
            <p className="mb-3 text-[12px] font-medium text-muted">Edit history</p>
            <HistoryList history={history} />
          </div>
        ) : null}
      </div>
    </div>
  );
}

function HistoryList({ history }: { history: SegmentEvent[] | null }) {
  if (history === null) return <p className="text-[12.5px] text-muted">Loading…</p>;
  if (history.length === 0) return <p className="text-[12.5px] text-muted">No edits yet.</p>;
  return (
    <ul className="space-y-3">
      {history.map((h, i) => (
        <li key={i} className={`border-b ${T.border} pb-3 text-[12.5px]`}>
          <p className="text-[11px] text-muted">{h.action} · {h.reviewer} · {new Date(h.created_at * 1000).toLocaleString()}</p>
          <p className="mt-1 text-ink-soft line-through">{h.old_target ?? "—"}</p>
          <p className="text-ink">{h.new_target ?? "—"}</p>
        </li>
      ))}
    </ul>
  );
}

/** Images: original and translation side by side. No segment edits — the
 * backend has no rebuild for image jobs. */
function ImageView({ job }: { job: JobRow }) {
  const [views, setViews] = useState<{ source?: string; result?: string; failed?: boolean }>({});
  useEffect(() => {
    let stop = false;
    const made: string[] = [];
    Promise.all([
      authedBlobUrl(imageFileUrl(job.id, "source")).catch(() => undefined),
      authedBlobUrl(imageFileUrl(job.id, "result")).catch(() => undefined),
    ]).then(([source, result]) => {
      if (source) made.push(source);
      if (result) made.push(result);
      if (!stop) setViews({ source, result, failed: !source && !result });
    });
    return () => {
      stop = true;
      made.forEach((u) => URL.revokeObjectURL(u));
    };
  }, [job.id]);
  return (
    <div className="min-h-0 flex-1 overflow-auto p-6">
      <p className="mb-3 text-[12px] text-muted">
        Images can&apos;t be edited sentence by sentence. To change a translation, upload the image again.
      </p>
      {views.failed ? <Notice kind="error">The previews couldn&apos;t be loaded. The download may still work.</Notice> : null}
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
        {(["source", "result"] as const).map((w) => (
          <figure key={w} className={`overflow-hidden ${T.card}`}>
            {views[w] ? (
              // eslint-disable-next-line @next/next/no-img-element -- a blob URL from the API, not a static asset
              <img src={views[w]} alt={w === "source" ? "Original image" : "Translated image"} className="w-full" />
            ) : (
              <div className="p-10 text-center text-[12px] text-muted">{views.failed ? "No preview" : "Loading preview…"}</div>
            )}
            <figcaption className={`border-t ${T.border} px-3 py-2 text-[12px] text-muted`}>
              {w === "source" ? "Original" : `Translated · ${job.meta?.target_language ?? languageName(job.meta?.target_lang) ?? ""}`}
            </figcaption>
          </figure>
        ))}
      </div>
    </div>
  );
}

/** Office files and web pages: edit any translated segment, then rebuild the
 * file once with every change applied. */
function SegmentReview({ job, kind, onNotice }: {
  job: JobRow;
  kind: FileKind;
  onNotice: (n: { kind: "success" | "error"; text: string }) => void;
}) {
  const [segments, setSegments] = useState<Segment[] | null>(null);
  const [drafts, setDrafts] = useState<Record<string, string>>({});
  const [savedSinceRebuild, setSavedSinceRebuild] = useState(0);
  const [saving, setSaving] = useState<string | null>(null);
  const [rebuilding, setRebuilding] = useState(false);
  const [query, setQuery] = useState("");
  const [html, setHtml] = useState<string | null>(null);
  const [view, setView] = useState<"result" | "source">("result");
  const [htmlVersion, setHtmlVersion] = useState(0);
  const rebuildable = supportsRebuild(kind);

  useEffect(() => {
    getSegments(job.id).then(setSegments).catch(() => setSegments([]));
  }, [job.id]);

  useEffect(() => {
    if (kind !== "website") return;
    let stop = false;
    getWebsiteHtml(job.id, view)
      .then((h) => { if (!stop) setHtml(h); })
      .catch(() => { if (!stop) setHtml(null); });
    return () => { stop = true; };
  }, [job.id, kind, view, htmlVersion]);

  const shown = useMemo(() => {
    const q = query.trim().toLowerCase();
    const list = (segments ?? []).filter((s) => s.source_restored || s.target_restored);
    if (!q) return list;
    return list.filter((s) =>
      `${s.source_restored ?? ""} ${s.target_restored ?? ""}`.toLowerCase().includes(q));
  }, [segments, query]);

  async function save(seg: Segment) {
    const text = drafts[seg.seg_id];
    if (text === undefined || text === (seg.target_restored ?? "")) return;
    setSaving(seg.seg_id);
    try {
      const updated = await updateSegment(job.id, seg.seg_id, text, true);
      setSegments((prev) => (prev ?? []).map((s) => (s.seg_id === seg.seg_id ? { ...s, ...updated } : s)));
      setDrafts((prev) => {
        const next = { ...prev };
        delete next[seg.seg_id];
        return next;
      });
      setSavedSinceRebuild((n) => n + 1);
    } catch (err) {
      onNotice({ kind: "error", text: err instanceof Error ? err.message : "Could not save the edit." });
    } finally {
      setSaving(null);
    }
  }

  async function rebuild() {
    setRebuilding(true);
    try {
      await rebuildJob(job.id);
      setSavedSinceRebuild(0);
      setHtmlVersion((v) => v + 1);
      onNotice({ kind: "success", text: "Your edits are applied. The download now includes them." });
    } catch (err) {
      onNotice({ kind: "error", text: err instanceof Error ? err.message : "Rebuild failed." });
    } finally {
      setRebuilding(false);
    }
  }

  const unsaved = Object.entries(drafts).filter(([id, text]) =>
    (segments ?? []).some((s) => s.seg_id === id && (s.target_restored ?? "") !== text)).length;

  const editor = (
    <div className="flex min-h-0 flex-1 flex-col">
      <div className={`flex shrink-0 flex-wrap items-center gap-3 border-b ${T.border} px-6 py-2.5`}>
        <input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Find text…" aria-label="Find text"
          className={`${T.input} max-w-xs py-1.5`} />
        <span className="text-[12px] text-muted">
          {segments === null ? "Loading segments…" : `${shown.length} segment${shown.length === 1 ? "" : "s"}`}
          {unsaved ? ` · ${unsaved} unsaved` : ""}
        </span>
        {rebuildable ? (
          <button type="button" onClick={rebuild} disabled={rebuilding || savedSinceRebuild === 0}
            title={savedSinceRebuild ? "Write your saved edits into the file" : "Edit a segment first"}
            className={`${T.primaryBtn} ml-auto`}>
            {rebuilding ? "Applying…" : savedSinceRebuild ? `Apply ${savedSinceRebuild} edit${savedSinceRebuild === 1 ? "" : "s"} to the file` : "No edits to apply"}
          </button>
        ) : null}
      </div>
      <div className="min-h-0 flex-1 overflow-auto px-6 py-4">
        {segments !== null && shown.length === 0 ? (
          <p className={`rounded-xl ${T.surface2} px-4 py-6 text-center text-[13px] text-muted`}>
            {query ? "No segment matches that text." : "No editable text was found in this file. You can still download it."}
          </p>
        ) : (
          <ul className="space-y-2">
            {shown.map((s) => {
              const draft = drafts[s.seg_id] ?? s.target_restored ?? "";
              const dirty = draft !== (s.target_restored ?? "");
              return (
                <li key={s.seg_id} className={`grid gap-3 rounded-xl border ${T.border} p-3 md:grid-cols-2`}>
                  <p className="whitespace-pre-wrap text-[13px] text-ink-soft">{s.source_restored}</p>
                  <div>
                    <textarea
                      value={draft}
                      onChange={(e) => setDrafts((prev) => ({ ...prev, [s.seg_id]: e.target.value }))}
                      onBlur={() => save(s)}
                      rows={Math.min(6, Math.max(2, Math.ceil(draft.length / 60)))}
                      aria-label={`Translation of segment ${s.seg_id}`}
                      className={`${T.input} resize-y`}
                    />
                    <p className="mt-1 h-4 text-[11px] text-muted">
                      {saving === s.seg_id ? "Saving…" : dirty ? "Saves when you leave the box" : s.status === "approved" ? "Edited" : ""}
                    </p>
                  </div>
                </li>
              );
            })}
          </ul>
        )}
      </div>
    </div>
  );

  if (kind !== "website") return editor;

  return (
    <div className="grid min-h-0 flex-1 grid-cols-1 lg:grid-cols-2">
      <div className={`flex min-h-0 flex-col border-r ${T.border}`}>{editor}</div>
      <div className="flex min-h-[420px] flex-col p-4">
        <div className="mb-3 flex gap-2">
          {(["result", "source"] as const).map((v) => (
            <button key={v} type="button" onClick={() => setView(v)}
              className={`rounded-full border px-3 py-1 text-[12.5px] ${view === v ? `${T.accentBorder} text-ink` : `${T.border} text-ink-soft`}`}>
              {v === "result" ? "Translated" : "Original"}
            </button>
          ))}
          {job.meta?.source_url ? (
            <a href={job.meta.source_url} target="_blank" rel="noreferrer" className="ml-auto self-center truncate text-[12px] text-muted hover:text-ink">
              {job.meta.source_url}
            </a>
          ) : null}
        </div>
        {html !== null ? (
          // No allow-scripts, no allow-same-origin: the copy can't run code or reach the app.
          <iframe title={view === "result" ? "Translated page" : "Original page"} sandbox="" srcDoc={html}
            className={`min-h-0 w-full flex-1 rounded-xl border ${T.border} bg-white`} />
        ) : (
          <p className="text-[12.5px] text-muted">Loading the page…</p>
        )}
      </div>
    </div>
  );
}
