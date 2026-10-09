"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { listLanguages, type Language } from "@/lib/translate";
import { getImageConfig, listFormats } from "@/lib/agents";
import { getDefaultLang } from "@/lib/notifications";
import {
  FALLBACK_DOCUMENT_EXTS,
  FALLBACK_IMAGE_EXTS,
  getJobType,
  rejectReason,
  type JobTypeId,
} from "@/lib/jobTypes";
import { startProjectJob } from "@/lib/projects";
import { PdfPreview } from "./PdfPreview";

/** Theme-following class names shared by the project pages. Each colour is a
 * CSS variable with the light value as its fallback. */
export const T = {
  surface: "bg-[var(--app-surface,#fff)]",
  surface2: "bg-[var(--app-surface-2,#f6f2ea)]",
  border: "border-[var(--app-border,#ebe5da)]",
  accentBg: "bg-[var(--app-accent,#c86018)]",
  accentText: "text-[var(--app-accent,#c86018)]",
  accentBorder: "border-[var(--app-accent,#c86018)]",
  primaryBtn:
    "rounded-full bg-[var(--app-accent,#c86018)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40",
  secondaryBtn:
    "rounded-full border border-[var(--app-border,#ebe5da)] bg-[var(--app-surface,#fff)] px-4 py-2 text-[12.5px] text-ink-soft transition-colors hover:text-ink disabled:opacity-40",
  input:
    "w-full rounded-xl border border-[var(--app-border,#ebe5da)] bg-[var(--app-surface,#fff)] px-3 py-2 text-[13px] text-ink outline-none placeholder:text-muted focus:border-[var(--app-accent,#c86018)]",
  card: "rounded-2xl border border-[var(--app-border,#ebe5da)] bg-[var(--app-surface,#fff)]",
  error: "text-[#b3261e]",
};

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/** A success or error line that sits above the content it is about. */
export function Notice({
  kind,
  children,
  onClose,
}: {
  kind: "success" | "error" | "info";
  children: ReactNode;
  onClose?: () => void;
}) {
  const tone =
    kind === "success"
      ? "border-[#cfe6d0] bg-[#e8f5e9] text-[#2e7d32]"
      : kind === "error"
        ? "border-[#f3c9c5] bg-[#fdecea] text-[#b3261e]"
        : `${T.border} ${T.surface2} text-ink-soft`;
  return (
    <div role={kind === "error" ? "alert" : "status"} className={`flex items-start gap-3 rounded-xl border px-3.5 py-2.5 text-[12.5px] ${tone}`}>
      <div className="min-w-0 flex-1">{children}</div>
      {onClose ? (
        <button type="button" onClick={onClose} aria-label="Dismiss" className="shrink-0 opacity-60 hover:opacity-100">
          ×
        </button>
      ) : null}
    </div>
  );
}

/** Target-language picker. Starts from `preferred` (the project's language),
 * then the person's saved default, then the server's default. */
export function TargetLanguageSelect({
  value,
  onChange,
  preferred,
  className = "",
}: {
  value: string;
  onChange: (code: string) => void;
  preferred?: string | null;
  className?: string;
}) {
  const [langs, setLangs] = useState<Language[]>([]);
  const seeded = useRef(false);
  useEffect(() => {
    let cancelled = false;
    listLanguages()
      .then((r) => {
        if (cancelled) return;
        setLangs(r.languages);
        if (!seeded.current && !value) {
          seeded.current = true;
          const known = (code: string | null | undefined) =>
            code ? r.languages.find((l) => l.code === code || l.name.toLowerCase() === code.toLowerCase())?.code : undefined;
          onChange(known(preferred) ?? known(getDefaultLang()) ?? r.default ?? r.languages[0]?.code ?? "");
        }
      })
      .catch(() => setLangs([]));
    return () => {
      cancelled = true;
    };
    // Load once; `onChange` only seeds the first value.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <select
      value={value}
      onChange={(e) => onChange(e.target.value)}
      aria-label="Target language"
      className={`${T.input} ${className}`}
    >
      {langs.length === 0 ? <option value={value}>{value || "Loading languages…"}</option> : null}
      {langs.map((l) => (
        <option key={l.code} value={l.code}>
          {l.name}
          {l.direction === "rtl" ? " (right-to-left)" : ""}
        </option>
      ))}
    </select>
  );
}

/** Extensions the server accepts for this kind of project. */
export function useAcceptedExtensions(kind: "document" | "image"): string[] {
  const [exts, setExts] = useState<string[]>(kind === "image" ? FALLBACK_IMAGE_EXTS : FALLBACK_DOCUMENT_EXTS);
  useEffect(() => {
    let cancelled = false;
    if (kind === "document") {
      listFormats()
        .then((f) => {
          const list = f.documents.map((d) => d.ext.toLowerCase());
          if (!cancelled && list.length) setExts(list);
        })
        .catch(() => {});
    } else {
      getImageConfig()
        .then((c) => {
          if (!Array.isArray(c.formats)) return;
          const list = (c.formats as { extensions?: string[] }[])
            .flatMap((f) => f.extensions ?? [])
            .map((e) => (e.startsWith(".") ? e : `.${e}`).toLowerCase());
          if (!cancelled && list.length) setExts(Array.from(new Set(list)));
        })
        .catch(() => {});
    }
    return () => {
      cancelled = true;
    };
  }, [kind]);
  return exts;
}

type Picked = { key: string; file: File; state: "ready" | "uploading" | "failed"; error?: string };

/**
 * Where work enters a project: a drag-and-drop zone for several files at
 * once (documents/Office or images, by project type) or a page URL for a
 * website project. Each file is uploaded on its own; a file that fails stays
 * in the list with the reason so it can be fixed or retried, and the others
 * carry on. The Files list follows each started job from there.
 */
export function ProjectUploader({
  projectId,
  projectType,
  folderId,
  projectLang,
  onStarted,
  onClose,
}: {
  projectId: string;
  projectType: JobTypeId;
  folderId?: string;
  projectLang?: string | null;
  /** Called with the job ids that started and how many files were sent. */
  onStarted: (jobIds: string[], label: string) => void;
  onClose?: () => void;
}) {
  const type = getJobType(projectType);
  const isWebsite = type?.input === "url";
  const kind: "document" | "image" = projectType === "image" ? "image" : "document";
  const accepted = useAcceptedExtensions(kind);
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [picked, setPicked] = useState<Picked[]>([]);
  const [rejected, setRejected] = useState<string[]>([]);
  const [lang, setLang] = useState("");
  const [url, setUrl] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function addFiles(list: FileList | File[] | null) {
    if (!list) return;
    const ok: Picked[] = [];
    const bad: string[] = [];
    for (const file of Array.from(list)) {
      const reason = rejectReason(file.name, accepted);
      if (reason) bad.push(`${file.name}: ${reason}`);
      else ok.push({ key: `${file.name}-${file.size}-${file.lastModified}`, file, state: "ready" });
    }
    setRejected(bad);
    setError(null);
    setPicked((prev) => {
      const seen = new Set(prev.map((p) => p.key));
      return [...prev, ...ok.filter((p) => !seen.has(p.key))];
    });
  }

  async function uploadAll() {
    const todo = picked.filter((p) => p.state !== "uploading");
    if (!todo.length || !lang || busy) return;
    setBusy(true);
    setError(null);
    setPicked((prev) => prev.map((p) => (todo.includes(p) ? { ...p, state: "uploading", error: undefined } : p)));
    const results = await Promise.all(
      todo.map(async (p) => {
        try {
          const id = await startProjectJob({ kind, file: p.file, targetLang: lang, projectId, folderId });
          return { key: p.key, id };
        } catch (err) {
          return { key: p.key, error: err instanceof Error ? err.message : "Upload failed." };
        }
      })
    );
    const started = results.filter((r) => r.id).map((r) => r.id as string);
    const failed = new Map(results.filter((r) => r.error).map((r) => [r.key, r.error as string]));
    // Started files leave the list (their rows appear in Files); failures stay.
    setPicked((prev) =>
      prev
        .filter((p) => !started.length || failed.has(p.key) || !todo.some((t) => t.key === p.key))
        .map((p) => (failed.has(p.key) ? { ...p, state: "failed", error: failed.get(p.key) } : p))
    );
    setBusy(false);
    if (started.length) onStarted(started, `${started.length} file${started.length === 1 ? "" : "s"}`);
    if (failed.size) setError(`${failed.size} file${failed.size === 1 ? "" : "s"} didn't upload. Fix the reason shown and press Translate again.`);
  }

  async function submitUrl(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || !lang || busy) return;
    setBusy(true);
    setError(null);
    try {
      const id = await startProjectJob({ kind: "website", url: url.trim(), targetLang: lang, projectId, folderId });
      setUrl("");
      onStarted([id], url.trim());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the translation.");
    } finally {
      setBusy(false);
    }
  }

  const header = (
    <div className="mb-3 flex items-start gap-3">
      <div className="min-w-0 flex-1">
        <p className="text-[13.5px] font-semibold text-ink">
          {isWebsite ? "Translate a web page" : kind === "image" ? "Add images" : "Add documents"}
        </p>
        <p className="mt-0.5 text-[12px] text-muted">
          {isWebsite
            ? "Paste a public English page. You get a translated, read-only copy with scripts removed."
            : kind === "image"
              ? "Text in each image is read and redrawn in the target language. Illustrator files stay vector."
              : "Layout is preserved and the same file type comes back. Add several files at once."}
        </p>
      </div>
      {onClose ? (
        <button type="button" onClick={onClose} className="shrink-0 text-[12px] text-muted hover:text-ink">
          Close
        </button>
      ) : null}
    </div>
  );

  if (isWebsite) {
    return (
      <form onSubmit={submitUrl} className={`${T.card} p-5`}>
        {header}
        <div className="grid gap-3 md:grid-cols-[minmax(0,1fr)_220px_auto]">
          <input
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://example.com/pricing"
            aria-label="Page URL"
            inputMode="url"
            className={T.input}
          />
          <TargetLanguageSelect value={lang} onChange={setLang} preferred={projectLang} />
          <button type="submit" disabled={!url.trim() || !lang || busy} className={T.primaryBtn}>
            {busy ? "Starting…" : "Translate page"}
          </button>
        </div>
        <p className="mt-3 text-[11.5px] text-muted">
          Only public pages on standard ports. Pages that need a login or JavaScript to show their text can&apos;t be translated.
        </p>
        {error ? <div className="mt-3"><Notice kind="error">{error}</Notice></div> : null}
      </form>
    );
  }

  const readable = accepted.map((e) => e.replace(".", "").toUpperCase()).join(" · ");

  return (
    <div className={`${T.card} p-5`}>
      {header}
      <input
        ref={inputRef}
        type="file"
        multiple
        accept={accepted.join(",")}
        className="hidden"
        onChange={(e) => {
          addFiles(e.target.files);
          e.target.value = "";
        }}
      />
      <div
        role="button"
        tabIndex={0}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") {
            e.preventDefault();
            inputRef.current?.click();
          }
        }}
        onDragOver={(e) => {
          e.preventDefault();
          setDragOver(true);
        }}
        onDragLeave={() => setDragOver(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragOver(false);
          addFiles(e.dataTransfer.files);
        }}
        onClick={() => inputRef.current?.click()}
        className={`flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-8 text-center transition-colors ${
          dragOver ? `${T.accentBorder} ${T.surface2}` : `${T.border} hover:border-[var(--app-accent,#c86018)]`
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className={`h-6 w-6 ${T.accentText}`}>
          <path d="M12 16V4m0 0l-4 4m4-4l4 4M4 16v3a1 1 0 0 0 1 1h14a1 1 0 0 0 1-1v-3" />
        </svg>
        <p className="mt-2 text-[13px] font-medium text-ink">
          Drop {kind === "image" ? "images" : "files"} here, or <span className={T.accentText}>browse</span>
        </p>
        <p className="mt-1 text-[11.5px] text-muted">{readable}</p>
      </div>

      {rejected.length ? (
        <div className="mt-3">
          <Notice kind="error" onClose={() => setRejected([])}>
            <ul className="space-y-1">
              {rejected.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </Notice>
        </div>
      ) : null}

      {picked.length ? (
        <>
          <ul className={`mt-4 divide-y rounded-xl border ${T.border} divide-[var(--app-border,#ebe5da)]`}>
            {picked.map((p) => (
              <li key={p.key} className="flex items-center gap-3 px-3 py-2">
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[13px] text-ink">{p.file.name}</p>
                  <p className={`text-[11.5px] ${p.state === "failed" ? T.error : "text-muted"}`}>
                    {p.state === "uploading"
                      ? "Uploading…"
                      : p.state === "failed"
                        ? p.error
                        : formatBytes(p.file.size)}
                  </p>
                </div>
                {p.state === "uploading" ? (
                  <span className="h-1.5 w-16 overflow-hidden rounded-full bg-[var(--app-surface-2,#f6f2ea)]">
                    <span className="progress-indeterminate block h-full w-full opacity-60" />
                  </span>
                ) : (
                  <button
                    type="button"
                    onClick={() => setPicked((prev) => prev.filter((x) => x.key !== p.key))}
                    aria-label={`Remove ${p.file.name}`}
                    className="text-[13px] text-muted hover:text-ink"
                  >
                    ×
                  </button>
                )}
              </li>
            ))}
          </ul>
          <div className="mt-4 flex flex-wrap items-center gap-3">
            <span className="text-[12px] text-muted">Translate into</span>
            <div className="w-56">
              <TargetLanguageSelect value={lang} onChange={setLang} preferred={projectLang} />
            </div>
            <button
              type="button"
              onClick={uploadAll}
              disabled={busy || !lang || picked.every((p) => p.state === "uploading")}
              className={`${T.primaryBtn} ml-auto`}
            >
              {busy ? "Uploading…" : `Translate ${picked.length} file${picked.length === 1 ? "" : "s"}`}
            </button>
          </div>
        </>
      ) : null}
      {error ? <div className="mt-3"><Notice kind="error">{error}</Notice></div> : null}
      {kind === "document" ? (
        <p className="mt-3 text-[11.5px] text-muted">
          .indd isn&apos;t supported. Export IDML from InDesign instead. Old .doc, .ppt and .xls files need re-saving as .docx, .pptx or .xlsx.
        </p>
      ) : null}
    </div>
  );
}

/** Single-document picker for the standalone translate workspace. */
export function UploadPane({
  file,
  onFileChange,
  language,
  onLanguageChange,
  onTranslate,
  status,
}: {
  file: File | null;
  onFileChange: (file: File | null) => void;
  language: string;
  onLanguageChange: (lang: string) => void;
  onTranslate: () => void;
  status: "idle" | "translating" | "error";
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [rejected, setRejected] = useState<string | null>(null);
  const accepted = useAcceptedExtensions("document");

  function handleFiles(files: FileList | null) {
    const f = files?.[0];
    if (!f) return;
    const reason = rejectReason(f.name, accepted);
    setRejected(reason);
    if (!reason) onFileChange(f);
  }

  return (
    <div className={`flex min-w-[320px] flex-1 flex-col border-r ${T.border} p-6`}>
      <p className="text-[13px] font-semibold text-ink">Source document</p>
      <label className="mt-4 block">
        <span className="mb-1.5 block text-[12px] text-muted">Translate to</span>
        <TargetLanguageSelect value={language} onChange={onLanguageChange} />
      </label>

      <input
        ref={inputRef}
        type="file"
        accept={accepted.join(",")}
        className="hidden"
        onChange={(e) => {
          handleFiles(e.target.files);
          e.target.value = "";
        }}
      />

      {file ? (
        <div className={`mt-4 flex min-h-0 flex-1 flex-col overflow-hidden rounded-xl border ${T.border}`}>
          <div className={`flex items-center justify-between border-b ${T.border} px-3 py-2`}>
            <div>
              <p className="text-[13px] text-ink">{file.name}</p>
              <p className="text-xs text-muted">{formatBytes(file.size)}</p>
            </div>
            <button type="button" onClick={() => onFileChange(null)} className="text-[12px] text-ink-soft hover:text-ink">
              Remove
            </button>
          </div>
          {file.type === "application/pdf" ? (
            <PdfPreview source={{ kind: "file", file }} />
          ) : (
            <div className="flex flex-1 items-center justify-center p-8 text-center">
              <p className="text-[12px] text-muted">No inline preview for this file type</p>
            </div>
          )}
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => inputRef.current?.click()}
          className={`mt-4 flex flex-1 cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed p-8 text-center transition-colors ${
            dragOver ? `${T.accentBorder} ${T.surface2}` : `${T.border} hover:border-[var(--app-accent,#c86018)]`
          }`}
        >
          <p className="text-[13px] text-ink-soft">Drop a file, or click to browse</p>
          <p className="mt-2 text-xs text-muted">{accepted.map((e) => e.replace(".", "").toUpperCase()).join(" · ")}</p>
        </div>
      )}
      {rejected ? <p className={`mt-3 text-[12px] ${T.error}`}>{rejected}</p> : null}

      <button
        type="button"
        onClick={onTranslate}
        disabled={!file || status === "translating"}
        className={`mt-6 w-full ${T.primaryBtn} py-3`}
      >
        {status === "translating" ? "Translating…" : "Translate document"}
      </button>
    </div>
  );
}
