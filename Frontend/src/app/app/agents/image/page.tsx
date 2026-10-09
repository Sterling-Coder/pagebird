"use client";

import { useEffect, useState } from "react";
import { AgentShell, Field, FilePicker } from "../AgentShell";
import { useJobParam } from "../JobStatus";
import { LanguageSelect, PrimaryButton, Empty, StatusBadge } from "@/components/app/ui";
import {
  authedBlobUrl, getImageConfig, getImageJob, imageFileUrl, startImageJob,
  type ImageConfig, type ImageJob,
} from "@/lib/agents";
import { downloadAuthed } from "@/lib/supabase/authFetch";

export default function ImageAgentPage() {
  const [file, setFile] = useState<File | null>(null);
  const [lang, setLang] = useState("");
  const [config, setConfig] = useState<ImageConfig | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useJobParam();
  const [job, setJob] = useState<ImageJob | null>(null);
  const [views, setViews] = useState<{ source?: string; result?: string }>({});

  useEffect(() => { getImageConfig().then(setConfig).catch(() => setConfig(null)); }, []);

  // Follow the job; once it is done, fetch both images through the auth header.
  useEffect(() => {
    if (!jobId) return;
    let stop = false;
    let timer: ReturnType<typeof setTimeout>;
    const tick = async () => {
      try {
        const j = await getImageJob(jobId);
        if (stop) return;
        setJob(j);
        if (j.status === "processing") { timer = setTimeout(tick, 2000); return; }
        if (j.status === "complete") {
          const [source, result] = await Promise.all([
            authedBlobUrl(imageFileUrl(jobId, "source")).catch(() => undefined),
            authedBlobUrl(imageFileUrl(jobId, "result")).catch(() => undefined),
          ]);
          if (!stop) setViews({ source, result });
        }
      } catch (e) {
        if (!stop) setError(e instanceof Error ? e.message : "Could not load the job.");
      }
    };
    tick();
    return () => { stop = true; clearTimeout(timer); };
  }, [jobId]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !lang) return;
    setBusy(true);
    setError(null);
    setViews({});
    setJob(null);
    try {
      setJobId(await startImageJob(file, lang));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  const stages = config?.stages ?? [];
  const current = job?.stage;

  return (
    <AgentShell
      name="OCR Agent"
      desc="Reads the text in an image and redraws the translation in the same place, colour and size."
      form={
        <form onSubmit={start}>
          <Field label="Image">
            <FilePicker accept=".png,.jpg,.jpeg,.webp,.psd,.psb,.ai" file={file} onFile={setFile}
              hint="PNG, JPEG, WEBP, Photoshop or Illustrator" />
          </Field>
          <Field label="Translate into"><LanguageSelect value={lang} onChange={setLang} /></Field>
          {config && !config.ocr_available ? (
            <p className="mb-3 text-[12px] text-[color:var(--app-warn)]">No OCR engine is set up on the server, so only Illustrator files with live text will work.</p>
          ) : null}
          {error ? <p className="mb-3 text-[12.5px] text-[color:var(--app-danger)]">{error}</p> : null}
          <PrimaryButton type="submit" disabled={!file || !lang || busy}>{busy ? "Uploading…" : "Translate image"}</PrimaryButton>
          <p className="mt-3 text-[11.5px] text-muted">Illustrator files stay vector. Photoshop files come back as PNG.</p>
        </form>
      }
      result={
        !job ? (
          <Empty>The original and the translated image appear here side by side.</Empty>
        ) : (
          <div className="space-y-4">
            <div className="flex items-center gap-2">
              <span className="truncate text-[13px] font-semibold text-ink">{job.original_filename}</span>
              <StatusBadge status={job.status} />
            </div>
            {job.status === "processing" && stages.length ? (
              <ol className="flex flex-wrap gap-2">
                {stages.map((s) => {
                  const pct = job.stage_progress?.[s.key] ?? 0;
                  return (
                    <li key={s.key} className={`rounded-full px-2.5 py-1 text-[11.5px] ${
                      s.key === current ? "bg-[var(--app-warn-bg)] text-[color:var(--app-warn)]" : pct >= 100 ? "bg-[var(--app-success-bg)] text-[color:var(--app-success)]" : "bg-[var(--app-surface-3)] text-muted"}`}>
                      {s.label}
                    </li>
                  );
                })}
              </ol>
            ) : null}
            {job.status === "failed" ? <p className="text-[12.5px] text-[color:var(--app-danger)]">{job.error}</p> : null}
            {job.status === "complete" ? (
              <>
                <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
                  {(["source", "result"] as const).map((w) => (
                    <figure key={w} className="overflow-hidden rounded-xl border border-[color:var(--app-border)] bg-[var(--app-surface-2)]">
                      {views[w] ? (
                        // eslint-disable-next-line @next/next/no-img-element -- a blob URL from the API, not a static asset
                        <img src={views[w]} alt={w === "source" ? "Original image" : "Translated image"} className="w-full" />
                      ) : <div className="p-6 text-center text-[12px] text-muted">Loading preview…</div>}
                      <figcaption className="px-3 py-2 text-[11.5px] text-muted">{w === "source" ? "Original" : `Translated · ${job.target_language ?? ""}`}</figcaption>
                    </figure>
                  ))}
                </div>
                {job.report?.warnings?.length ? (
                  <ul className="space-y-1 text-[12px] text-[color:var(--app-warn)]">
                    {job.report.warnings.slice(0, 4).map((w, i) => <li key={i}>• {w.message}</li>)}
                  </ul>
                ) : null}
                <button type="button"
                  onClick={() => downloadAuthed(imageFileUrl(job.job_id, "result", true), job.original_filename ?? "translated-image")}
                  className="rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white">Download translated image</button>
              </>
            ) : null}
          </div>
        )
      }
    />
  );
}
