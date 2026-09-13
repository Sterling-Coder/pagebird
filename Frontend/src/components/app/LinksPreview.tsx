"use client";

import { useEffect, useRef, useState } from "react";
import type { PDFDocumentProxy } from "pdfjs-dist";
import { loadPdfjs } from "@/lib/pdfjs";
import { authHeaders, downloadAuthed } from "@/lib/supabase/authFetch";
import { listLinkFiles, linkFileUrl, type LinkFile } from "@/lib/translate";

/** Finder-style preview for a "links" batch job: every translated linked
 * graphic listed on the left, the selected one previewed full-size on the
 * right — mirrors macOS Finder's column view instead of forcing a
 * download-and-open round trip per file.
 *
 * Deliberately does NOT reuse the shared `PdfPreview` component: that one
 * always renders a full thumbnail rail (re-rendering every page a second
 * time into a small canvas), which is pure overhead here since a links
 * batch is a flat list of mostly single-page graphics, not a paginated
 * document you thumb through. This viewer also caches parsed pdf.js
 * documents per file name so flipping back to something already opened is
 * instant instead of re-fetching + re-parsing it. */
export function LinksPreview({ jobId, jobName }: { jobId: string; jobName: string }) {
  const [files, setFiles] = useState<LinkFile[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [downloading, setDownloading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    listLinkFiles(jobId)
      .then((list) => {
        if (cancelled) return;
        setFiles(list);
        setSelected(list[0]?.name ?? null);
      })
      .catch((err) => {
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load files");
      });
    return () => {
      cancelled = true;
    };
  }, [jobId]);

  const selectedFile = files?.find((f) => f.name === selected) ?? null;

  function extIcon(name: string) {
    return name.includes(".") ? name.split(".").pop()!.toUpperCase() : "FILE";
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <div className="flex w-72 shrink-0 flex-col overflow-hidden border-r border-rule bg-paper">
        <div className="border-b border-rule px-3 py-2">
          <p className="truncate font-mono text-[11px] uppercase tracking-widest text-muted">
            {jobName}
          </p>
          {files ? (
            <p className="mt-0.5 font-mono text-[10px] text-muted">{files.length} files</p>
          ) : null}
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">
          {error ? (
            <p className="p-3 text-xs text-red">{error}</p>
          ) : !files ? (
            <p className="p-3 text-xs text-muted">Loading…</p>
          ) : files.length === 0 ? (
            <p className="p-3 text-xs text-muted">No translated files.</p>
          ) : (
            files.map((f) => (
              <button
                key={f.name}
                type="button"
                onClick={() => setSelected(f.name)}
                className={`flex w-full items-center gap-2 border-b border-rule px-3 py-2 text-left transition-colors ${
                  selected === f.name ? "bg-paper-dim" : "hover:bg-paper-dim/60"
                }`}
              >
                <span className="flex h-8 w-8 shrink-0 items-center justify-center border border-rule font-mono text-[8px] text-ink-soft">
                  {extIcon(f.name)}
                </span>
                <span className="min-w-0 flex-1">
                  <span className="block truncate text-xs text-ink">{f.name}</span>
                  <span className="block font-mono text-[9px] uppercase tracking-widest text-muted">
                    {f.translated ? "Translated" : "Untranslated"}
                  </span>
                </span>
              </button>
            ))
          )}
        </div>
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex shrink-0 items-center justify-between border-b border-rule px-3 py-1.5">
          <p className="truncate font-mono text-[11px] text-ink">{selectedFile?.name ?? "—"}</p>
          {selectedFile ? (
            <button
              type="button"
              disabled={downloading}
              onClick={() => {
                setDownloading(true);
                downloadAuthed(linkFileUrl(jobId, selectedFile.name), selectedFile.name).finally(() =>
                  setDownloading(false)
                );
              }}
              className="bg-ink px-3 py-1 font-mono text-[10px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80 disabled:opacity-50"
            >
              {downloading ? "Preparing…" : "Download"}
            </button>
          ) : null}
        </div>
        <div className="flex min-h-0 min-w-0 flex-1">
          {selectedFile?.previewable ? (
            <LinkFileCanvas key="preview" jobId={jobId} name={selectedFile.name} />
          ) : selectedFile ? (
            <div className="flex flex-1 flex-col items-center justify-center gap-2 p-8 text-center">
              <p className="font-mono text-[11px] text-ink-soft">
                No inline preview for .{selectedFile.name.split(".").pop()} — download to view.
              </p>
            </div>
          ) : (
            <div className="flex flex-1 items-center justify-center text-muted">
              Select a file to preview
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

// Module-scoped so the cache survives switching the selected file (and
// re-mounting the preview pane) without surviving a full page navigation —
// exactly the lifetime a "don't re-fetch what I already opened" cache wants.
const docCache = new Map<string, Promise<PDFDocumentProxy>>();

function LinkFileCanvas({ jobId, name }: { jobId: string; name: string }) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [page, setPage] = useState(1);
  const [zoom, setZoom] = useState(0.5);
  const [error, setError] = useState<string | null>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const cacheKey = `${jobId}/${name}`;

  useEffect(() => {
    let cancelled = false;
    setDoc(null);
    setNumPages(0);
    setPage(1);
    setZoom(0.5);
    setError(null);

    (async () => {
      try {
        let pending = docCache.get(cacheKey);
        if (!pending) {
          pending = (async () => {
            const pdfjsLib = await loadPdfjs();
            const loadingTask = pdfjsLib.getDocument({
              url: linkFileUrl(jobId, name),
              httpHeaders: await authHeaders(),
            });
            return loadingTask.promise;
          })();
          docCache.set(cacheKey, pending);
        }
        const pdf = await pending;
        if (cancelled) return;
        setDoc(pdf);
        setNumPages(pdf.numPages);
      } catch (err) {
        docCache.delete(cacheKey);
        if (!cancelled) setError(err instanceof Error ? err.message : "Failed to load preview");
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [cacheKey, jobId, name]);

  useEffect(() => {
    if (!doc || !canvasRef.current) return;
    let cancelled = false;
    let renderTask: { cancel: () => void } | null = null;

    (async () => {
      const pdfPage = await doc.getPage(page);
      if (cancelled || !canvasRef.current) return;
      const dpr = window.devicePixelRatio || 1;
      const containerWidth = containerRef.current?.clientWidth || 600;
      const unscaledWidth = pdfPage.getViewport({ scale: 1 }).width;
      const fitScale = ((containerWidth - 32) / unscaledWidth) * zoom;
      const viewport = pdfPage.getViewport({ scale: fitScale * dpr });
      const canvas = canvasRef.current;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width / dpr}px`;
      canvas.style.height = `${viewport.height / dpr}px`;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const task = pdfPage.render({ canvas, canvasContext: ctx, viewport });
      renderTask = task;
      await task.promise.catch(() => {});
    })();

    return () => {
      cancelled = true;
      renderTask?.cancel();
    };
  }, [doc, page, zoom]);

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-center">
        <p className="font-mono text-[11px] uppercase tracking-widest text-red">{error}</p>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1 flex-col">
      {doc ? (
        <div className="flex items-center justify-center gap-3 border-b border-rule py-1.5">
          {numPages > 1 ? (
            <>
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={page <= 1}
                className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
              >
                ←
              </button>
              <span className="font-mono text-[11px] text-muted">
                {page} / {numPages}
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(numPages, p + 1))}
                disabled={page >= numPages}
                className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
              >
                →
              </button>
              <span className="mx-1 h-4 w-px bg-rule" />
            </>
          ) : null}
          <button
            type="button"
            onClick={() => setZoom((z) => Math.max(0.5, +(z - 0.1).toFixed(2)))}
            disabled={zoom <= 0.5}
            aria-label="Zoom out"
            className="flex h-6 w-6 items-center justify-center border border-rule font-mono text-[12px] text-ink-soft transition-colors hover:border-ink hover:text-ink disabled:opacity-30"
          >
            −
          </button>
          <span className="w-9 text-center font-mono text-[11px] text-muted">
            {Math.round(zoom * 100)}%
          </span>
          <button
            type="button"
            onClick={() => setZoom((z) => Math.min(3, +(z + 0.1).toFixed(2)))}
            disabled={zoom >= 3}
            aria-label="Zoom in"
            className="flex h-6 w-6 items-center justify-center border border-rule font-mono text-[12px] text-ink-soft transition-colors hover:border-ink hover:text-ink disabled:opacity-30"
          >
            +
          </button>
        </div>
      ) : null}
      <div ref={containerRef} className="flex flex-1 items-start justify-center overflow-auto p-4">
        {doc ? (
          <canvas ref={canvasRef} className="shadow-sm" />
        ) : (
          <div className="flex flex-1 items-center justify-center text-muted">Loading…</div>
        )}
      </div>
    </div>
  );
}
