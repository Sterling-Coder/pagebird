"use client";

import {
  forwardRef,
  useEffect,
  useImperativeHandle,
  useRef,
  useState,
  type ReactNode,
  type RefObject,
} from "react";
import type { PDFDocumentProxy, PDFPageProxy } from "pdfjs-dist";
import { loadPdfjs } from "@/lib/pdfjs";
import { rebuildJob, updateSegment, type Segment } from "@/lib/translate";

type Source = { kind: "file"; file: File } | { kind: "url"; url: string };

export function PdfPreview({ source }: { source: Source }) {
  const { doc, numPages, thumbs, error } = usePdfDocument(source);
  const [page, setPage] = useState(1);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const pageContainerRef = useRef<HTMLDivElement>(null);
  const renderTaskRef = useRef<{ cancel: () => void } | null>(null);

  // eslint-disable-next-line react-hooks/set-state-in-effect
  useEffect(() => setPage(1), [doc]);

  // Render the current page at full size.
  useEffect(() => {
    if (!doc || !canvasRef.current) return;
    let cancelled = false;

    (async () => {
      renderTaskRef.current?.cancel();
      const pdfPage = await doc.getPage(page);
      if (cancelled || !canvasRef.current) return;
      const dpr = window.devicePixelRatio || 1;
      const containerWidth = pageContainerRef.current?.clientWidth || 600;
      const unscaledWidth = pdfPage.getViewport({ scale: 1 }).width;
      const fitScale = (containerWidth - 32) / unscaledWidth; // 32 = pane padding
      const viewport = pdfPage.getViewport({ scale: fitScale * dpr });
      const canvas = canvasRef.current;
      canvas.width = viewport.width;
      canvas.height = viewport.height;
      canvas.style.width = `${viewport.width / dpr}px`;
      canvas.style.height = `${viewport.height / dpr}px`;
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const task = pdfPage.render({ canvas, canvasContext: ctx, viewport });
      renderTaskRef.current = task;
      await task.promise.catch(() => {});
    })();

    return () => {
      cancelled = true;
    };
  }, [doc, page]);

  if (error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-center">
        <p className="font-mono text-[11px] uppercase tracking-widest text-red">
          {error}
        </p>
      </div>
    );
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <div className="flex w-20 shrink-0 flex-col gap-2 overflow-y-auto border-r border-rule bg-paper-dim p-2">
        {Array.from({ length: numPages }).map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => setPage(i + 1)}
            className={`flex flex-col items-center gap-1 border p-1 transition-colors ${
              page === i + 1
                ? "border-ink"
                : "border-transparent hover:border-rule"
            }`}
          >
            {thumbs[i] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={thumbs[i]} alt={`Page ${i + 1}`} className="w-full" />
            ) : (
              <div className="aspect-[3/4] w-full animate-pulse bg-rule/40" />
            )}
            <span className="font-mono text-[9px] text-muted">{i + 1}</span>
          </button>
        ))}
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex items-center justify-center gap-3 border-b border-rule py-1.5">
          <button
            type="button"
            onClick={() => setPage((p) => Math.max(1, p - 1))}
            disabled={page <= 1}
            className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
          >
            ←
          </button>
          <span className="font-mono text-[11px] text-muted">
            {page} / {numPages || "…"}
          </span>
          <button
            type="button"
            onClick={() => setPage((p) => Math.min(numPages, p + 1))}
            disabled={page >= numPages}
            className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
          >
            →
          </button>
        </div>
        <div
          ref={pageContainerRef}
          className="flex flex-1 items-start justify-center overflow-auto p-4"
        >
          <canvas ref={canvasRef} className="shadow-sm" />
        </div>
      </div>
    </div>
  );
}

type RenderedPage = {
  page: PDFPageProxy;
  scale: number;
};

function sourceKey(source: Source) {
  return source.kind === "file"
    ? `${source.file.name}-${source.file.size}-${source.file.lastModified}`
    : source.url;
}

function usePdfDocument(source: Source, keepPrevious = false) {
  const [doc, setDoc] = useState<PDFDocumentProxy | null>(null);
  const [numPages, setNumPages] = useState(0);
  const [thumbs, setThumbs] = useState<string[]>([]);
  const [error, setError] = useState<string | null>(null);
  const key = sourceKey(source);

  useEffect(() => {
    let cancelled = false;
    // keepPrevious: an edit-triggered rebuild swaps in a new PDF behind the
    // same URL. Clearing `doc` here unmounts every rendered page for the gap
    // between requests, which resets the pane's scroll position and reads as
    // a jarring full refresh. Leaving the old doc on screen until the new one
    // is ready keeps the DOM (and its scroll offset) untouched.
    if (!keepPrevious) {
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setDoc(null);
      setNumPages(0);
      setThumbs([]);
    }
    setError(null);

    (async () => {
      try {
        const pdfjsLib = await loadPdfjs();
        const data =
          source.kind === "file" ? await source.file.arrayBuffer() : undefined;
        const loadingTask =
          source.kind === "file"
            ? pdfjsLib.getDocument({ data })
            : pdfjsLib.getDocument({ url: source.url });
        const pdf = await loadingTask.promise;
        if (cancelled) return;
        setDoc(pdf);
        setNumPages(pdf.numPages);
      } catch (err) {
        if (!cancelled) {
          setError(err instanceof Error ? err.message : "Failed to load PDF");
        }
      }
    })();

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [key]);

  useEffect(() => {
    if (!doc) return;
    let cancelled = false;

    (async () => {
      const urls: string[] = [];
      for (let i = 1; i <= doc.numPages; i++) {
        if (cancelled) return;
        const pdfPage = await doc.getPage(i);
        const viewport = pdfPage.getViewport({ scale: 0.22 });
        const canvas = document.createElement("canvas");
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        const ctx = canvas.getContext("2d");
        if (!ctx) continue;
        await pdfPage.render({ canvas, canvasContext: ctx, viewport }).promise;
        urls.push(canvas.toDataURL());
        if (!cancelled) setThumbs([...urls]);
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [doc]);

  return { doc, numPages, thumbs, error };
}

type SyncedPaneHandle = {
  setScrollTop: (px: number) => void;
  scrollToPage: (pageNumber: number, smooth?: boolean) => void;
};

function packedColorToCss(color: number): string {
  const r = (color >> 16) & 255;
  const g = (color >> 8) & 255;
  const b = color & 255;
  return `rgb(${r}, ${g}, ${b})`;
}

/** An in-place text edit that reads as "the same word, now editable" rather
 * than a form control dropped on the page: it samples the rendered canvas
 * pixel just outside its own box for a background that matches whatever is
 * actually behind it (a purple banner, a tinted callout, plain paper), and
 * uses the segment's own PDF text colour — so it covers the glyph it is
 * replacing instead of doubling it, and doesn't relayer the design in
 * generic black-on-white. */
function SegmentEditor({
  canvasRef,
  left,
  top,
  width,
  height,
  color,
  value,
  onChange,
  onCommit,
  onCancel,
  error,
}: {
  canvasRef: RefObject<HTMLCanvasElement | null>;
  left: number;
  top: number;
  width: number;
  height: number;
  color?: number;
  value: string;
  onChange: (text: string) => void;
  onCommit: () => void;
  onCancel: () => void;
  error?: string | null;
}) {
  const cancellingRef = useRef(false);
  const [bg, setBg] = useState<string | null>(null);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext("2d");
    if (!ctx) return;
    const scaleX = canvas.width / canvas.clientWidth;
    const scaleY = canvas.height / canvas.clientHeight;
    // Sample just above-left of the box: outside the glyphs it covers, still
    // inside whatever fill (page, banner, callout) sits behind them.
    const sx = Math.max(0, Math.min(canvas.width - 1, Math.round((left - 3) * scaleX)));
    const sy = Math.max(0, Math.min(canvas.height - 1, Math.round((top - 3) * scaleY)));
    try {
      const [r, g, b] = ctx.getImageData(sx, sy, 1, 1).data;
      setBg(`rgb(${r}, ${g}, ${b})`);
    } catch {
      setBg(null);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [left, top]);

  const fontSize = Math.min(16, Math.max(9, height * 0.68));

  return (
    <div
      className="absolute z-10"
      style={{ left, top, width, height, backgroundColor: bg ?? undefined }}
    >
      <textarea
        autoFocus
        value={value}
        onChange={(event) => onChange(event.target.value)}
        onFocus={(event) => {
          const el = event.currentTarget;
          el.selectionStart = el.selectionEnd = el.value.length;
        }}
        onKeyDown={(event) => {
          if (event.key === "Escape") {
            cancellingRef.current = true;
            event.currentTarget.blur();
          }
          if (event.key === "Enter" && !event.shiftKey) {
            event.preventDefault();
            event.currentTarget.blur();
          }
        }}
        onBlur={() => {
          if (cancellingRef.current) {
            cancellingRef.current = false;
            onCancel();
          } else {
            onCommit();
          }
        }}
        style={{
          fontSize,
          color: color !== undefined ? packedColorToCss(color) : undefined,
        }}
        className="h-full w-full resize-none overflow-hidden border-none bg-transparent p-0 leading-tight outline-none"
      />
      {error ? (
        <p className="absolute left-0 top-full z-20 mt-0.5 whitespace-nowrap bg-paper font-mono text-[9px] uppercase tracking-widest text-red">
          {error}
        </p>
      ) : null}
    </div>
  );
}

type PdfPageBlockProps = {
  doc: PDFDocumentProxy;
  pageNumber: number;
  segments: Segment[];
  activeSegmentId: string | null;
  onSegmentSelect: (segmentId: string | null) => void;
  zoom: number;
  editable?: boolean;
  onSegmentClick?: (segment: Segment) => void;
  editingSegmentId?: string | null;
  editText?: string;
  onEditTextChange?: (text: string) => void;
  onEditCommit?: () => void;
  onEditCancel?: () => void;
  editSaving?: boolean;
  editError?: string | null;
};

const PdfPageBlock = forwardRef<HTMLDivElement, PdfPageBlockProps>(
  function PdfPageBlock(
    {
      doc,
      pageNumber,
      segments,
      activeSegmentId,
      onSegmentSelect,
      zoom,
      editable,
      onSegmentClick,
      editingSegmentId,
      editText,
      onEditTextChange,
      onEditCommit,
      onEditCancel,
      editSaving,
      editError,
    },
    wrapperRef
  ) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const innerRef = useRef<HTMLDivElement>(null);
    const [rendered, setRendered] = useState<RenderedPage | null>(null);

    useEffect(() => {
      let cancelled = false;

      (async () => {
        const pdfPage = await doc.getPage(pageNumber);
        if (cancelled || !canvasRef.current) return;
        const dpr = window.devicePixelRatio || 1;
        const availableWidth = innerRef.current?.clientWidth || 640;
        const unscaled = pdfPage.getViewport({ scale: 1 });
        const cssScale = Math.max(0.25, (availableWidth / unscaled.width) * zoom);
        const viewport = pdfPage.getViewport({ scale: cssScale * dpr });
        const canvas = canvasRef.current;
        canvas.width = viewport.width;
        canvas.height = viewport.height;
        canvas.style.width = `${viewport.width / dpr}px`;
        canvas.style.height = `${viewport.height / dpr}px`;
        const ctx = canvas.getContext("2d");
        if (!ctx) return;
        await pdfPage.render({ canvas, canvasContext: ctx, viewport }).promise.catch(() => {});
        if (!cancelled) setRendered({ page: pdfPage, scale: cssScale });
      })();

      return () => {
        cancelled = true;
      };
    }, [doc, pageNumber, zoom]);

    const pageSegments = rendered
      ? segments.filter((segment) => segment.page === pageNumber - 1)
      : [];

    return (
      <div ref={wrapperRef} data-page={pageNumber} className="flex justify-center px-4 pt-4">
        <div ref={innerRef} className="relative w-full max-w-3xl shrink-0">
          <canvas ref={canvasRef} className="w-full shadow-sm" />
          {rendered
            ? pageSegments.map((segment) => {
                const [x1, y1, x2, y2] = segment.bbox;
                const left = Math.min(x1, x2) * rendered.scale;
                const top = Math.min(y1, y2) * rendered.scale;
                const width = Math.abs(x2 - x1) * rendered.scale;
                const height = Math.abs(y2 - y1) * rendered.scale;
                const active = activeSegmentId === segment.seg_id;

                if (editable && segment.seg_id === editingSegmentId) {
                  return (
                    <SegmentEditor
                      key={segment.seg_id}
                      canvasRef={canvasRef}
                      left={left}
                      top={top}
                      width={width}
                      height={height}
                      color={segment.color}
                      value={editText ?? ""}
                      onChange={(text) => onEditTextChange?.(text)}
                      onCommit={() => onEditCommit?.()}
                      onCancel={() => onEditCancel?.()}
                      error={editError}
                    />
                  );
                }

                return (
                  <button
                    key={segment.seg_id}
                    type="button"
                    title={
                      editable
                        ? "Click to edit"
                        : segment.source_restored ?? segment.target_restored ?? ""
                    }
                    onMouseEnter={() => onSegmentSelect(segment.seg_id)}
                    onFocus={() => onSegmentSelect(segment.seg_id)}
                    onMouseLeave={() => onSegmentSelect(null)}
                    onBlur={() => onSegmentSelect(null)}
                    onClick={() => editable && onSegmentClick?.(segment)}
                    className={`absolute border transition-colors ${
                      active
                        ? "border-blue-500 bg-blue-500/20"
                        : "border-transparent bg-blue-400/0"
                    }`}
                    style={{
                      left,
                      top,
                      width,
                      height,
                      cursor: editable ? "text" : undefined,
                    }}
                  />
                );
              })
            : null}
          <p className="py-1 text-center font-mono text-[10px] text-muted">
            {pageNumber}
          </p>
        </div>
      </div>
    );
  }
);

type SyncedPdfPaneProps = {
  title: string;
  doc: PDFDocumentProxy | null;
  numPages: number;
  segments: Segment[];
  activeSegmentId: string | null;
  onSegmentSelect: (segmentId: string | null) => void;
  onScroll: (topPx: number) => void;
  onCurrentPageChange?: (pageNumber: number) => void;
  zoom: number;
  editable?: boolean;
  onSegmentClick?: (segment: Segment) => void;
  editingSegmentId?: string | null;
  editText?: string;
  onEditTextChange?: (text: string) => void;
  onEditCommit?: () => void;
  onEditCancel?: () => void;
  editSaving?: boolean;
  editError?: string | null;
  titleExtra?: ReactNode;
};

const SyncedPdfPane = forwardRef<SyncedPaneHandle, SyncedPdfPaneProps>(
  function SyncedPdfPane(
    {
      title,
      doc,
      numPages,
      segments,
      activeSegmentId,
      onSegmentSelect,
      onScroll,
      onCurrentPageChange,
      zoom,
      editable,
      onSegmentClick,
      editingSegmentId,
      editText,
      onEditTextChange,
      onEditCommit,
      onEditCancel,
      editSaving,
      editError,
      titleExtra,
    },
    ref
  ) {
    const scrollRef = useRef<HTMLDivElement>(null);
    const blockRefs = useRef<(HTMLDivElement | null)[]>([]);

    useImperativeHandle(
      ref,
      () => ({
        setScrollTop: (px) => {
          if (scrollRef.current) scrollRef.current.scrollTop = px;
        },
        scrollToPage: (pageNumber, smooth = true) => {
          const el = blockRefs.current[pageNumber - 1];
          el?.scrollIntoView({
            block: "start",
            behavior: smooth ? "smooth" : "auto",
          });
        },
      }),
      []
    );

    return (
      <div className="flex min-h-0 min-w-0 flex-1 flex-col border-r border-rule last:border-r-0">
        <div className="flex items-center justify-between border-b border-rule px-3 py-2">
          <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
            {title}
          </p>
          {titleExtra}
        </div>
        <div
          ref={scrollRef}
          onScroll={(event) => {
            const node = event.currentTarget;
            onScroll(node.scrollTop);
            if (!onCurrentPageChange) return;
            const containerTop = node.getBoundingClientRect().top;
            let current = 1;
            for (let i = 0; i < blockRefs.current.length; i++) {
              const el = blockRefs.current[i];
              if (!el) continue;
              if (el.getBoundingClientRect().top - containerTop <= 24) {
                current = i + 1;
              } else {
                break;
              }
            }
            onCurrentPageChange(current);
          }}
          className="flex min-h-0 flex-1 flex-col overflow-auto pb-4"
        >
          {doc
            ? Array.from({ length: numPages }).map((_, i) => (
                <PdfPageBlock
                  key={i}
                  ref={(el) => {
                    blockRefs.current[i] = el;
                  }}
                  doc={doc}
                  pageNumber={i + 1}
                  segments={segments}
                  activeSegmentId={activeSegmentId}
                  onSegmentSelect={onSegmentSelect}
                  zoom={zoom}
                  editable={editable}
                  onSegmentClick={onSegmentClick}
                  editingSegmentId={editingSegmentId}
                  editText={editText}
                  onEditTextChange={onEditTextChange}
                  onEditCommit={onEditCommit}
                  onEditCancel={onEditCancel}
                  editSaving={editSaving}
                  editError={editError}
                />
              ))
            : null}
        </div>
      </div>
    );
  }
);

export function SyncedDocumentPair({
  source,
  target,
  segments: initialSegments,
  downloadUrl,
  fileName,
  language,
  languages,
  onLanguageChange,
  onTranslate,
  translating,
  jobId,
}: {
  source: Source;
  target: Source;
  segments: Segment[];
  downloadUrl: string;
  fileName: string;
  language?: string;
  languages?: { code: string; name: string }[];
  onLanguageChange?: (lang: string) => void;
  onTranslate?: () => void;
  translating?: boolean;
  jobId?: string;
}) {
  const [segments, setSegments] = useState(initialSegments);
  useEffect(() => setSegments(initialSegments), [initialSegments]);
  const [targetVersion, setTargetVersion] = useState(0);
  const versionedTarget: Source =
    target.kind === "url"
      ? {
          kind: "url",
          url: `${target.url}${target.url.includes("?") ? "&" : "?"}v=${targetVersion}`,
        }
      : target;
  const sourcePdf = usePdfDocument(source);
  const targetPdf = usePdfDocument(versionedTarget, true);
  const [page, setPage] = useState(1);
  const [editMode, setEditMode] = useState(false);
  const [editingSegmentId, setEditingSegmentId] = useState<string | null>(null);
  const [editText, setEditText] = useState("");
  const [editError, setEditError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const editingSegment = segments.find((s) => s.seg_id === editingSegmentId) ?? null;
  const [lastEdit, setLastEdit] = useState<{ segId: string; previousText: string } | null>(null);
  const [undoing, setUndoing] = useState(false);
  const [zoom, setZoom] = useState(1);
  const [activeSegmentId, setActiveSegmentId] = useState<string | null>(null);
  const sourcePaneRef = useRef<SyncedPaneHandle | null>(null);
  const targetPaneRef = useRef<SyncedPaneHandle | null>(null);
  const syncingRef = useRef(false);
  const numPages = sourcePdf.numPages || targetPdf.numPages;

  if (sourcePdf.error || targetPdf.error) {
    return (
      <div className="flex flex-1 items-center justify-center p-8 text-center">
        <p className="font-mono text-[11px] uppercase tracking-widest text-red">
          {sourcePdf.error ?? targetPdf.error}
        </p>
      </div>
    );
  }

  function syncScroll(side: "source" | "target", top: number) {
    if (syncingRef.current) return;
    syncingRef.current = true;
    const peer = side === "source" ? targetPaneRef.current : sourcePaneRef.current;
    peer?.setScrollTop(top);
    window.requestAnimationFrame(() => {
      syncingRef.current = false;
    });
  }

  function goToPage(pageNumber: number) {
    sourcePaneRef.current?.scrollToPage(pageNumber);
  }

  function openEdit(segment: Segment) {
    setEditingSegmentId(segment.seg_id);
    // "**word**" is our own bold marker baked into the raw target text, not
    // something a person should see or retype — show the plain sentence.
    setEditText((segment.target_restored ?? "").replace(/\*\*(.+?)\*\*/g, "$1"));
    setEditError(null);
  }

  function cancelEdit() {
    setEditingSegmentId(null);
    setEditError(null);
  }

  function toggleEditMode() {
    setEditMode((v) => !v);
    cancelEdit();
  }

  async function saveEdit() {
    if (!editingSegment || !jobId) return;
    const previousText = editingSegment.target_restored ?? "";
    setSaving(true);
    setEditError(null);
    try {
      const updated = await updateSegment(jobId, editingSegment.seg_id, editText, true);
      setSegments((prev) =>
        prev.map((s) => (s.seg_id === updated.seg_id ? { ...s, ...updated } : s))
      );
      await rebuildJob(jobId);
      setTargetVersion((v) => v + 1);
      setEditingSegmentId(null);
      setLastEdit({ segId: editingSegment.seg_id, previousText });
    } catch (err) {
      setEditError(err instanceof Error ? err.message : "Failed to save");
    } finally {
      setSaving(false);
    }
  }

  async function undoLastEdit() {
    if (!lastEdit || !jobId) return;
    setUndoing(true);
    try {
      const updated = await updateSegment(jobId, lastEdit.segId, lastEdit.previousText, true);
      setSegments((prev) =>
        prev.map((s) => (s.seg_id === updated.seg_id ? { ...s, ...updated } : s))
      );
      await rebuildJob(jobId);
      setTargetVersion((v) => v + 1);
      setLastEdit(null);
    } catch {
      // best-effort — leave lastEdit in place so the user can try again
    } finally {
      setUndoing(false);
    }
  }

  return (
    <div className="flex min-h-0 min-w-0 flex-1">
      <div className="flex w-20 shrink-0 flex-col gap-2 overflow-y-auto border-r border-rule bg-paper-dim p-2">
        {Array.from({ length: numPages }).map((_, i) => (
          <button
            key={i}
            type="button"
            onClick={() => goToPage(i + 1)}
            className={`flex flex-col items-center gap-1 border p-1 transition-colors ${
              page === i + 1
                ? "border-ink"
                : "border-transparent hover:border-rule"
            }`}
          >
            {sourcePdf.thumbs[i] ? (
              // eslint-disable-next-line @next/next/no-img-element
              <img src={sourcePdf.thumbs[i]} alt={`Page ${i + 1}`} className="w-full" />
            ) : (
              <div className="aspect-[3/4] w-full animate-pulse bg-rule/40" />
            )}
            <span className="font-mono text-[9px] text-muted">{i + 1}</span>
          </button>
        ))}
      </div>

      <div className="flex min-h-0 min-w-0 flex-1 flex-col">
        <div className="flex flex-wrap items-center gap-x-4 gap-y-1.5 border-b border-rule px-3 py-1.5">
          <p className="truncate font-mono text-[11px] text-ink">{fileName}</p>

          <div className="flex items-center gap-2">
            <button
              type="button"
              onClick={() => goToPage(page - 1)}
              disabled={page <= 1}
              className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
            >
              ←
            </button>
            <p className="font-mono text-[11px] text-muted">
              {page} / {numPages || "..."}
            </p>
            <button
              type="button"
              onClick={() => goToPage(page + 1)}
              disabled={page >= numPages}
              className="font-mono text-[11px] text-ink-soft disabled:opacity-30"
            >
              →
            </button>
          </div>

          <div className="flex items-center gap-1.5">
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

          <div className="ml-auto flex items-center gap-2">
            {onLanguageChange && onTranslate ? (
              <>
                <select
                  value={language}
                  onChange={(event) => onLanguageChange(event.target.value)}
                  className="border border-rule bg-paper px-2 py-1 font-mono text-[11px] uppercase tracking-widest text-ink"
                >
                  {(languages ?? []).map((lang) => (
                    <option key={lang.code} value={lang.code}>
                      {lang.name}
                    </option>
                  ))}
                </select>
                <button
                  type="button"
                  onClick={onTranslate}
                  disabled={translating}
                  className="bg-red px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-40"
                >
                  {translating ? "Translating…" : "Translate"}
                </button>
              </>
            ) : null}
            {jobId ? (
              <button
                type="button"
                onClick={undoLastEdit}
                disabled={!lastEdit || undoing}
                title={lastEdit ? "Undo last edit" : "No edit to undo"}
                className="border border-rule px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-ink-soft transition-colors hover:border-ink hover:text-ink disabled:opacity-40"
              >
                {undoing ? "Undoing…" : "Undo Edit"}
              </button>
            ) : null}
            <a
              href={downloadUrl}
              className="bg-ink px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
            >
              Download
            </a>
          </div>
        </div>
        <div className="flex min-h-0 min-w-0 flex-1">
          <SyncedPdfPane
            ref={sourcePaneRef}
            title="Original"
            doc={sourcePdf.doc}
            numPages={numPages}
            segments={segments}
            activeSegmentId={activeSegmentId}
            onSegmentSelect={setActiveSegmentId}
            onScroll={(top) => syncScroll("source", top)}
            onCurrentPageChange={setPage}
            zoom={zoom}
          />
          <SyncedPdfPane
            ref={targetPaneRef}
            title="Translated"
            doc={targetPdf.doc}
            numPages={numPages}
            segments={segments}
            activeSegmentId={activeSegmentId}
            onSegmentSelect={setActiveSegmentId}
            onScroll={(top) => syncScroll("target", top)}
            zoom={zoom}
            editable={editMode && Boolean(jobId)}
            onSegmentClick={openEdit}
            editingSegmentId={editingSegmentId}
            editText={editText}
            onEditTextChange={setEditText}
            onEditCommit={saveEdit}
            onEditCancel={cancelEdit}
            editSaving={saving}
            editError={editError}
            titleExtra={
              jobId ? (
                <button
                  type="button"
                  onClick={toggleEditMode}
                  aria-pressed={editMode}
                  className={`font-mono text-[10px] uppercase tracking-widest transition-colors ${
                    editMode
                      ? "border border-ink bg-ink px-2 py-0.5 text-paper"
                      : "border border-rule px-2 py-0.5 text-ink-soft hover:border-ink hover:text-ink"
                  }`}
                >
                  {editMode ? "Done" : "Edit"}
                </button>
              ) : null
            }
          />
        </div>
      </div>
    </div>
  );
}
