"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  listProjectFiles,
  getProject,
  listFolders,
  listAllFolders,
  createFolder,
  deleteFolder,
  type JobSummary,
  type Folder,
} from "@/lib/projects";
import {
  listLanguages, translateDocument, translateLinks, deleteJob, getJobEval,
  API_BASE_URL, type Language, type EvalReport,
} from "@/lib/translate";
import { downloadAuthed } from "@/lib/supabase/authFetch";
import { languageName } from "@/lib/languageNames";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { QaDetail } from "@/components/app/QaDetail";

const TRANSLATE_STAGES = ["Uploading", "Extracting text", "Translating", "Rebuilding document"];
const STAGE_DURATION_MS = 4000;

export default function ProjectFilesPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const folderId = searchParams.get("folder") ?? undefined;
  const inputRef = useRef<HTMLInputElement>(null);
  const linksInputRef = useRef<HTMLInputElement>(null);
  const linksFolderInputRef = useRef<HTMLInputElement>(null);
  const [uploadMenuOpen, setUploadMenuOpen] = useState(false);
  const uploadMenuRef = useRef<HTMLDivElement>(null);
  const uploadButtonRef = useRef<HTMLButtonElement>(null);
  const uploadMenuItemRefs = useRef<(HTMLButtonElement | null)[]>([]);
  const [files, setFiles] = useState<JobSummary[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [allFolders, setAllFolders] = useState<Folder[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<Folder[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [targetLanguage, setTargetLanguage] = useState("es");
  const [projectTargetLang, setProjectTargetLang] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [pendingLinkFiles, setPendingLinkFiles] = useState<File[]>([]);
  // Set synchronously so a double-click can't fire the links translation twice.
  const submittingLinksRef = useRef(false);
  const [error, setError] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState(false);
  // Set synchronously (unlike state) so a double-click or Enter+click landing
  // in the same tick doesn't both pass the disabled check and create two
  // identical folders — the button had no in-flight guard at all before.
  const creatingFolderRef = useRef(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [deletingItems, setDeletingItems] = useState(false);
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [inFlight, setInFlight] = useState<
    { id: string; name: string; startedAt: number | null }[]
  >([]);
  const [, setTick] = useState(0);
  const [qaScores, setQaScores] = useState<Record<string, EvalReport>>({});
  const [qaModalId, setQaModalId] = useState<string | null>(null);

  function refresh() {
    listProjectFiles(params.projectId, folderId)
      .then((fetched) => {
        setFiles(fetched);
        // The backend now persists a "processing" row the moment upload
        // starts (survives navigating away / a closed tab, visible from any
        // tab polling this list) — once that real row shows up here, drop
        // this tab's own optimistic placeholder for the same file so it
        // doesn't render twice.
        const known = new Set(fetched.map((f) => f.original_filename));
        setInFlight((prev) => prev.filter((f) => !known.has(f.name)));

        // Never computes anything here — `cache_only` just reads whatever a
        // prior "QA check" (on the project's Settings page) already wrote to
        // disk, or reports "not computed". Layout scoring re-renders every
        // page of the document, so triggering it for every row just because
        // the list loaded would make opening this page expensive for no
        // reason nobody asked for yet.
        const done = fetched.filter((f) => f.status === "complete");
        Promise.all(
          done.map((f) =>
            getJobEval(f.id, { cacheOnly: true }).then(
              (r) => [f.id, r] as const,
              () => [f.id, { not_computed: true } as EvalReport] as const
            )
          )
        ).then((pairs) => setQaScores(Object.fromEntries(pairs)));
      })
      .catch(() => setFiles([]));
    listFolders(params.projectId, folderId).then(setFolders).catch(() => setFolders([]));
    // Every folder in the project, fetched once (not per breadcrumb level) —
    // building the breadcrumb used to walk the parent chain one `getFolder`
    // round trip at a time, so opening a folder 4 levels deep meant 4
    // sequential network calls before the breadcrumb could even render.
    listAllFolders(params.projectId).then(setAllFolders).catch(() => setAllFolders([]));
  }

  useEffect(() => {
    refresh();
    setSelectedFolders(new Set());
    setSelectedFiles(new Set());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId, folderId]);

  // Closes the Upload menu on an outside click or Escape — a menu that only
  // closes by picking an item traps anyone who opened it by mistake.
  useEffect(() => {
    if (!uploadMenuOpen) return;
    function handlePointerDown(e: MouseEvent) {
      const target = e.target as Node;
      if (uploadMenuRef.current?.contains(target) || uploadButtonRef.current?.contains(target)) {
        return;
      }
      setUploadMenuOpen(false);
    }
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") {
        setUploadMenuOpen(false);
        uploadButtonRef.current?.focus();
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    document.addEventListener("keydown", handleKeyDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [uploadMenuOpen]);

  useEffect(() => {
    if (!folderId) {
      setBreadcrumb([]);
      return;
    }
    const byId = new Map(allFolders.map((f) => [f.id, f]));
    const chain: Folder[] = [];
    let current: string | undefined = folderId;
    while (current) {
      const folder = byId.get(current);
      if (!folder) break;  // allFolders hasn't loaded yet, or folder was deleted
      chain.unshift(folder);
      current = folder.parent_folder_id ?? undefined;
    }
    setBreadcrumb(chain);
  }, [folderId, allFolders]);

  // Always poll while this page is open — not just while this tab kicked off
  // an upload. A reload, a return visit, or an upload started elsewhere all
  // used to mean the list froze until a manual refresh.
  useEffect(() => {
    const pollInterval = setInterval(refresh, 5000);
    return () => clearInterval(pollInterval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId, folderId]);

  useEffect(() => {
    if (inFlight.length === 0) return;
    const tickInterval = setInterval(() => setTick((t) => t + 1), 1000);
    return () => clearInterval(tickInterval);
  }, [inFlight.length]);

  useEffect(() => {
    listLanguages()
      .then((res) => {
        setLanguages(res.languages);
        setTargetLanguage(res.default || res.languages[0]?.code || "es");
      })
      .catch(() => setLanguages([]));
    getProject(params.projectId)
      .then((p) => setProjectTargetLang(p.target_lang))
      .catch(() => setProjectTargetLang(null));
  }, [params.projectId]);

  function handleFilePicked(fileList: FileList | null) {
    if (!fileList || fileList.length === 0) return;
    const all = Array.from(fileList);
    const picked = all.filter((f) => !f.name.toLowerCase().endsWith(".indd"));
    setError(
      picked.length < all.length
        ? ".indd files aren't supported. In InDesign, use File → Export → InDesign Markup (IDML) and upload the .idml."
        : null
    );
    if (picked.length) setPendingFiles(picked);
  }

  const LINK_EXTENSIONS = [".ai", ".eps", ".pdf", ".psd"];

  function handleLinksPicked(fileList: FileList | null, filterByExtension = false) {
    if (!fileList || fileList.length === 0) return;
    let picked = Array.from(fileList);
    if (filterByExtension) {
      picked = picked.filter((f) =>
        LINK_EXTENSIONS.some((ext) => f.name.toLowerCase().endsWith(ext))
      );
    }
    if (picked.length) {
      setError(null);
      setPendingLinkFiles(picked);
    }
  }

  function removePendingLinkFile(index: number) {
    setPendingLinkFiles((prev) => prev.filter((_, i) => i !== index));
  }

  async function handleConfirmTranslate() {
    if (pendingFiles.length === 0) return;
    const filesToTranslate = pendingFiles;
    setPendingFiles([]);
    setError(null);

    // Show every file as queued immediately, so the list doesn't look like
    // it silently dropped documents 2..N while document 1 is still running.
    const tempIds = filesToTranslate.map((file, i) => `pending-${Date.now()}-${i}-${file.name}`);
    setInFlight((prev) => [
      ...prev,
      ...filesToTranslate.map((file, i) => ({ id: tempIds[i], name: file.name, startedAt: null })),
    ]);

    async function runOne(file: File, tempId: string) {
      setInFlight((prev) =>
        prev.map((f) => (f.id === tempId ? { ...f, startedAt: Date.now() } : f))
      );
      try {
        await translateDocument({ file, targetLanguage, projectId: params.projectId, folderId });
        refresh();
      } catch (err) {
        setError(err instanceof Error ? err.message : `Upload failed: ${file.name}`);
      } finally {
        setInFlight((prev) => prev.filter((f) => f.id !== tempId));
      }
    }

    // Fully parallel: documents no longer share anything that benefits from
    // sequencing (no TM, and Links are their own independent upload/job now,
    // not attached to a document batch), so there's nothing left to protect
    // by staggering these.
    await Promise.all(
      filesToTranslate.map((file, i) => runOne(file, tempIds[i]))
    );
  }

  async function handleConfirmTranslateLinks() {
    if (pendingLinkFiles.length === 0 || submittingLinksRef.current) return;
    submittingLinksRef.current = true;
    const filesToTranslate = pendingLinkFiles;
    setPendingLinkFiles([]);
    setError(null);

    // Matches the backend's own display-name choice (translate_links_upload)
    // so this placeholder's name lines up with the real job row `refresh()`
    // replaces it with — a batch of one shows its real filename, not a
    // "1 linked graphic" label with nothing left to disambiguate.
    const linksDisplayName =
      filesToTranslate.length === 1
        ? filesToTranslate[0].name
        : `${filesToTranslate.length} linked graphics`;
    const tempId = `pending-links-${Date.now()}`;
    setInFlight((prev) => [
      ...prev,
      { id: tempId, name: linksDisplayName, startedAt: Date.now() },
    ]);
    // The guard only needs to stop a double-click on this batch, and the
    // modal is already closed by now. Holding it until the request returns
    // (minutes) silently swallowed every batch picked while one was running.
    submittingLinksRef.current = false;

    try {
      await translateLinks({
        files: filesToTranslate,
        targetLanguage,
        projectId: params.projectId,
        folderId,
      });
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Links upload failed");
    } finally {
      setInFlight((prev) => prev.filter((f) => f.id !== tempId));
    }
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim() || creatingFolderRef.current) return;
    creatingFolderRef.current = true;
    try {
      await createFolder(params.projectId, newFolderName.trim(), folderId);
      setNewFolderName("");
      setCreatingFolder(false);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create folder");
    } finally {
      creatingFolderRef.current = false;
    }
  }

  function toggleFolderSelected(id: string) {
    setSelectedFolders((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleFileSelected(id: string) {
    setSelectedFiles((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  const allSelected =
    (folders.length > 0 || files.length > 0) &&
    selectedFolders.size === folders.length &&
    selectedFiles.size === files.length;

  function toggleSelectAll() {
    if (allSelected) {
      setSelectedFolders(new Set());
      setSelectedFiles(new Set());
    } else {
      setSelectedFolders(new Set(folders.map((f) => f.id)));
      setSelectedFiles(new Set(files.map((f) => f.id)));
    }
  }

  async function handleConfirmDeleteSelected() {
    setDeletingItems(true);
    try {
      await Promise.all([
        ...[...selectedFolders].map((id) => deleteFolder(id)),
        ...[...selectedFiles].map((id) => deleteJob(id)),
      ]);
      setSelectedFolders(new Set());
      setSelectedFiles(new Set());
      setConfirmDeleteOpen(false);
      refresh();
    } finally {
      setDeletingItems(false);
    }
  }

  const selectedNames = [
    ...folders.filter((f) => selectedFolders.has(f.id)).map((f) => f.name),
    ...files
      .filter((f) => selectedFiles.has(f.id))
      .map((f) => f.original_filename ?? f.id),
  ];

  function goToFolder(id?: string) {
    router.push(
      id
        ? `/app/jobs/${params.projectId}/files?folder=${id}`
        : `/app/jobs/${params.projectId}/files`
    );
  }

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-auto p-6">
      <div className="mb-4">
        <h2 className="text-lg font-bold text-ink">Files</h2>
        <p className="mt-1 font-mono text-[11px] uppercase tracking-widest">
          <button
            type="button"
            onClick={() => goToFolder()}
            className="text-ink-soft underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
          >
            Files
          </button>
          {breadcrumb.map((f, i) => {
            const isLast = i === breadcrumb.length - 1;
            return (
              <span key={f.id}>
                {" "}
                / {" "}
                {isLast ? (
                  <span className="text-ink">{f.name}</span>
                ) : (
                  <button
                    type="button"
                    onClick={() => goToFolder(f.id)}
                    className="text-ink-soft underline decoration-rule underline-offset-4 hover:text-ink hover:decoration-ink"
                  >
                    {f.name}
                  </button>
                )}
              </span>
            );
          })}
        </p>
      </div>

      <div className="mb-4 flex items-center gap-3">
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.idml"
          multiple
          className="hidden"
          onChange={(e) => handleFilePicked(e.target.files)}
        />
        <input
          ref={linksInputRef}
          type="file"
          multiple
          accept=".ai,.eps,.pdf,.psd"
          className="hidden"
          onChange={(e) => {
            handleLinksPicked(e.target.files);
            e.target.value = "";
          }}
        />
        <input
          ref={linksFolderInputRef}
          type="file"
          multiple
          // @ts-expect-error non-standard attrs, Chrome/Safari/Firefox support them
          webkitdirectory=""
          directory=""
          className="hidden"
          onChange={(e) => {
            handleLinksPicked(e.target.files, true);
            e.target.value = "";
          }}
        />

        <div className="relative">
          <button
            ref={uploadButtonRef}
            type="button"
            aria-haspopup="menu"
            aria-expanded={uploadMenuOpen}
            onClick={() => setUploadMenuOpen((v) => !v)}
            onKeyDown={(e) => {
              if (e.key === "ArrowDown") {
                e.preventDefault();
                setUploadMenuOpen(true);
                requestAnimationFrame(() => uploadMenuItemRefs.current[0]?.focus());
              }
            }}
            className="flex items-center gap-2 bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90"
          >
            Upload
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className={`h-3 w-3 transition-transform ${uploadMenuOpen ? "rotate-180" : ""}`}>
              <path d="M6 9l6 6 6-6" />
            </svg>
          </button>
          {uploadMenuOpen ? (
            <div
              ref={uploadMenuRef}
              role="menu"
              aria-label="Upload"
              className="absolute left-0 top-full z-40 mt-1 w-72 border border-ink bg-paper py-1 shadow-lg"
            >
              {[
                {
                  label: "Document(s)",
                  hint: ".pdf, .idml — single or multiple",
                  onSelect: () => inputRef.current?.click(),
                },
                {
                  label: "Linked graphic(s)",
                  hint: ".ai, .eps, .pdf, .psd — single or multiple",
                  onSelect: () => linksInputRef.current?.click(),
                },
                {
                  label: "Linked graphics folder",
                  hint: ".ai, .eps, .pdf, .psd — whole Links folder at once",
                  onSelect: () => linksFolderInputRef.current?.click(),
                },
              ].map((item, i, arr) => (
                <button
                  key={item.label}
                  ref={(el) => {
                    uploadMenuItemRefs.current[i] = el;
                  }}
                  type="button"
                  role="menuitem"
                  onClick={() => {
                    setUploadMenuOpen(false);
                    item.onSelect();
                  }}
                  onKeyDown={(e) => {
                    if (e.key === "ArrowDown") {
                      e.preventDefault();
                      uploadMenuItemRefs.current[(i + 1) % arr.length]?.focus();
                    } else if (e.key === "ArrowUp") {
                      e.preventDefault();
                      uploadMenuItemRefs.current[(i - 1 + arr.length) % arr.length]?.focus();
                    }
                  }}
                  className="block w-full px-4 py-2 text-left hover:bg-paper-dim"
                >
                  <span className="block font-mono text-[11px] uppercase tracking-widest text-ink">
                    {item.label}
                  </span>
                  <span className="block text-xs text-muted">{item.hint}</span>
                </button>
              ))}
            </div>
          ) : null}
        </div>

        <button
          type="button"
          onClick={() => setCreatingFolder(true)}
          className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
        >
          Create folder
        </button>
        {selectedFolders.size + selectedFiles.size > 0 ? (
          <button
            type="button"
            onClick={() => setConfirmDeleteOpen(true)}
            disabled={deletingItems}
            aria-label="Delete selected items"
            className="border border-rule p-2 text-ink-soft transition-colors hover:border-red hover:text-red disabled:opacity-40"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
              <path d="M3 6h18" />
              <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
              <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
            </svg>
          </button>
        ) : null}
      </div>

      {error ? <p className="mb-3 text-sm text-red">{error}</p> : null}

      <table className="w-full border-collapse text-sm">
        <thead>
          <tr className="border-b border-rule text-left font-mono text-[11px] uppercase tracking-widest text-muted">
            <th className="w-8 py-2">
              {folders.length + files.length > 0 ? (
                <input
                  type="checkbox"
                  checked={allSelected}
                  onChange={toggleSelectAll}
                  aria-label="Select all"
                />
              ) : null}
            </th>
            <th className="py-2">Document</th>
            <th className="py-2">Type</th>
            <th className="py-2">Progress</th>
            <th className="py-2">Target</th>
            <th className="py-2">Created by</th>
            <th className="py-2">Created</th>
            <th className="py-2">QA</th>
            <th className="py-2">Download</th>
          </tr>
        </thead>
        <tbody>
          {folders.map((f) => (
            <tr
              key={f.id}
              onClick={() => goToFolder(f.id)}
              className="cursor-pointer border-b border-rule hover:bg-paper-dim"
            >
              <td className="py-2" onClick={(e) => e.stopPropagation()}>
                <input
                  type="checkbox"
                  checked={selectedFolders.has(f.id)}
                  onChange={() => toggleFolderSelected(f.id)}
                  aria-label={`Select ${f.name}`}
                />
              </td>
              <td className="py-2">
                <span className="flex items-center gap-2 text-ink">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4 shrink-0 text-ink-soft">
                    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  </svg>
                  {f.name}
                </span>
              </td>
              <td className="py-2 text-muted" colSpan={3}>
                —
              </td>
              <td className="py-2 text-ink-soft">{f.created_by_name ?? "—"}</td>
              <td className="py-2 text-ink-soft">
                {new Date(f.created_at * 1000).toLocaleDateString()}
              </td>
              <td className="py-2 text-muted" colSpan={2}>
                —
              </td>
            </tr>
          ))}
          {inFlight.map((f) => {
            const stage =
              f.startedAt === null
                ? "Queued"
                : TRANSLATE_STAGES[
                    Math.min(
                      Math.floor((Date.now() - f.startedAt) / STAGE_DURATION_MS),
                      TRANSLATE_STAGES.length - 1
                    )
                  ];
            return (
              <tr key={f.id} className="border-b border-rule">
                <td className="py-2" />
                <td className="py-2 text-ink">{f.name}</td>
                <td className="py-2 text-ink-soft">—</td>
                <td className="py-2">
                  <div className="h-4 w-24 overflow-hidden border border-rule">
                    <div
                      className={`progress-indeterminate h-full w-full ${f.startedAt === null ? "opacity-20" : "opacity-50"}`}
                    />
                  </div>
                </td>
                <td className="py-2 font-mono text-[10px] uppercase tracking-widest text-muted" colSpan={5}>
                  {stage}…
                </td>
              </tr>
            );
          })}
          {files.map((f) => {
            const name = f.original_filename ?? f.id;
            // A "links" job's own filename is a display label ("3 linked
            // graphics"), not a real name with an extension — its actual
            // file type(s) come from the batch's own extensions instead.
            const linkExtensions = Array.isArray(f.meta?.extensions) ? f.meta.extensions : null;
            const ext = linkExtensions?.length
              ? linkExtensions.join(", ").toUpperCase()
              : name.includes(".")
                ? name.split(".").pop()
                : "—";
            const processing = f.status === "processing";
            return (
              <tr
                key={f.id}
                onClick={() =>
                  !processing && router.push(`/app/jobs/${params.projectId}/files/${f.id}`)
                }
                className={`border-b border-rule ${processing ? "" : "cursor-pointer hover:bg-paper-dim"}`}
              >
                <td className="py-2" onClick={(e) => e.stopPropagation()}>
                  <input
                    type="checkbox"
                    checked={selectedFiles.has(f.id)}
                    onChange={() => toggleFileSelected(f.id)}
                    aria-label={`Select ${name}`}
                  />
                </td>
                <td className="py-2">
                  <span className="text-ink">{name}</span>
                  {f.status === "failed" ? (
                    <span className="ml-2 text-xs text-red">Error</span>
                  ) : null}
                </td>
                <td className="py-2 text-ink-soft">{ext}</td>
                <td className="py-2">
                  {processing && typeof f.meta?.progress === "number" ? (
                    <div className="flex flex-col gap-1">
                      <div className="h-4 w-24 overflow-hidden border border-rule">
                        <div
                          className="h-full bg-red transition-[width] duration-500"
                          style={{ width: `${f.meta.progress}%` }}
                        />
                      </div>
                      <span className="font-mono text-[10px] text-muted">
                        {f.meta.progress}%{f.meta.stage ? ` · ${f.meta.stage}` : ""}
                      </span>
                    </div>
                  ) : (
                    <div className="h-4 w-24 overflow-hidden border border-rule">
                      <div
                        className={
                          processing
                            ? "progress-indeterminate h-full w-full opacity-50"
                            : `h-full ${f.status === "failed" ? "bg-red/40" : "bg-red"}`
                        }
                        style={
                          processing
                            ? undefined
                            : { width: f.status === "complete" || f.status === "failed" ? "100%" : "0%" }
                        }
                      />
                    </div>
                  )}
                </td>
                <td className="py-2 text-ink-soft">{languageName(projectTargetLang) ?? "—"}</td>
                <td className="py-2 text-ink-soft">{f.created_by_name ?? "—"}</td>
                <td className="py-2 text-ink-soft">
                  {new Date(f.created_at * 1000).toLocaleDateString()}
                </td>
                {(() => {
                  const qa = qaScores[f.id];
                  if (!qa || qa.not_computed) {
                    return (
                      <td className="py-2 text-muted" title="Run QA check on the project's Settings page">
                        —
                      </td>
                    );
                  }
                  if (qa.not_applicable) {
                    return <td className="py-2 text-muted">N/A</td>;
                  }
                  const score = qa.overall?.score;
                  const passed = qa.overall?.gates_passed;
                  return (
                    <td className="py-2" onClick={(e) => e.stopPropagation()}>
                      <button
                        type="button"
                        onClick={() => setQaModalId(f.id)}
                        className={`underline decoration-dotted underline-offset-2 hover:no-underline ${
                          passed ? "text-ink" : "text-red"
                        }`}
                      >
                        {typeof score === "number" ? `${Math.round(score * 100)}%` : "—"}
                      </button>
                    </td>
                  );
                })()}
                <td className="py-2" onClick={(e) => e.stopPropagation()}>
                  {f.status === "complete" ? (
                    <button
                      type="button"
                      disabled={downloadingIds.has(f.id)}
                      onClick={() => {
                        const isIdml = (ext ?? "").toLowerCase() === "idml";
                        const url = `${API_BASE_URL}/api/jobs/${f.id}/download${isIdml ? "?format=idml" : ""}`;
                        setDownloadingIds((prev) => new Set(prev).add(f.id));
                        downloadAuthed(url, name)
                          .catch((err) =>
                            setError(err instanceof Error ? err.message : `Download failed: ${name}`)
                          )
                          .finally(() =>
                            setDownloadingIds((prev) => {
                              const next = new Set(prev);
                              next.delete(f.id);
                              return next;
                            })
                          );
                      }}
                      aria-label={`Download ${name}`}
                      aria-busy={downloadingIds.has(f.id)}
                      title="Download translated document"
                      className="inline-flex h-6 w-6 items-center justify-center border border-rule text-ink-soft hover:border-ink hover:text-ink disabled:opacity-50"
                    >
                      {downloadingIds.has(f.id) ? (
                        <svg viewBox="0 0 24 24" fill="none" className="h-3.5 w-3.5 animate-spin">
                          <circle cx="12" cy="12" r="9" stroke="currentColor" strokeWidth="1.75" opacity="0.25" />
                          <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" />
                        </svg>
                      ) : (
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5">
                          <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" />
                        </svg>
                      )}
                    </button>
                  ) : (
                    <span className="text-muted">—</span>
                  )}
                </td>
              </tr>
            );
          })}
          {files.length === 0 && folders.length === 0 && inFlight.length === 0 ? (
            <tr>
              <td colSpan={9} className="py-8 text-center text-muted">
                No files yet. Upload one to get started.
              </td>
            </tr>
          ) : null}
        </tbody>
      </table>

      {pendingFiles.length > 0 ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40">
          <div className="w-full max-w-sm border border-ink bg-paper p-6">
            <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
              Translate {pendingFiles.length > 1 ? `${pendingFiles.length} documents` : "document"}
            </p>
            <ul className="mt-3 max-h-32 space-y-1 overflow-auto text-sm text-ink">
              {pendingFiles.map((f, i) => (
                <li key={`${f.name}-${i}`} className="flex items-center justify-between">
                  <span className="truncate">{f.name}</span>
                  <button
                    type="button"
                    onClick={() =>
                      setPendingFiles((prev) => prev.filter((_, idx) => idx !== i))
                    }
                    aria-label={`Remove ${f.name}`}
                    className="ml-2 shrink-0 text-ink-soft hover:text-red"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>

            <label className="mt-4 block">
              <span className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-muted">
                Translate to
              </span>
              <select
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                className="w-full border border-rule bg-paper px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-ink"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setPendingFiles([])}
                className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmTranslate}
                disabled={pendingFiles.length === 0}
                className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90 disabled:opacity-40"
              >
                Translate
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {pendingLinkFiles.length > 0 ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40">
          <div className="w-full max-w-sm border border-ink bg-paper p-6">
            <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
              Translate {pendingLinkFiles.length} linked graphic{pendingLinkFiles.length !== 1 ? "s" : ""}
            </p>
            <p className="mt-2 text-xs text-muted">
              OCR + translate each file on its own — no document, no relinking.
              Download the translated set as its own zip when done.
            </p>
            <ul className="mt-3 max-h-32 space-y-1 overflow-auto text-sm text-ink">
              {pendingLinkFiles.map((f, i) => (
                <li key={`${f.name}-${i}`} className="flex items-center justify-between">
                  <span className="truncate">{f.name}</span>
                  <button
                    type="button"
                    onClick={() => removePendingLinkFile(i)}
                    aria-label={`Remove ${f.name}`}
                    className="ml-2 shrink-0 text-ink-soft hover:text-red"
                  >
                    ×
                  </button>
                </li>
              ))}
            </ul>

            <label className="mt-4 block">
              <span className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-muted">
                Translate to
              </span>
              <select
                value={targetLanguage}
                onChange={(e) => setTargetLanguage(e.target.value)}
                className="w-full border border-rule bg-paper px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-ink"
              >
                {languages.map((lang) => (
                  <option key={lang.code} value={lang.code}>
                    {lang.name}
                  </option>
                ))}
              </select>
            </label>

            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => setPendingLinkFiles([])}
                className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleConfirmTranslateLinks}
                disabled={pendingLinkFiles.length === 0}
                className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90 disabled:opacity-40"
              >
                Translate
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {creatingFolder ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40">
          <div className="w-full max-w-sm border border-ink bg-paper p-6">
            <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
              New folder
            </p>
            <input
              autoFocus
              value={newFolderName}
              onChange={(e) => setNewFolderName(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()}
              placeholder="Folder name"
              className="mt-4 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink"
            />
            <div className="mt-6 flex justify-end gap-3">
              <button
                type="button"
                onClick={() => {
                  setCreatingFolder(false);
                  setNewFolderName("");
                }}
                className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleCreateFolder}
                disabled={!newFolderName.trim()}
                className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90 disabled:opacity-40"
              >
                Create
              </button>
            </div>
          </div>
        </div>
      ) : null}

      <ConfirmDialog
        open={confirmDeleteOpen}
        title="Delete"
        message={`Delete ${selectedNames.length} item${selectedNames.length > 1 ? "s" : ""} (${selectedNames.join(", ")})? Folders also delete their files and subfolders. This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        busy={deletingItems}
        onConfirm={handleConfirmDeleteSelected}
        onCancel={() => setConfirmDeleteOpen(false)}
      />

      {qaModalId && qaScores[qaModalId] ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40"
          onClick={() => setQaModalId(null)}
        >
          <div
            className="max-h-[80vh] w-full max-w-2xl overflow-auto border border-ink bg-paper"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between border-b border-rule px-4 py-3">
              <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
                QA detail — {files.find((f) => f.id === qaModalId)?.original_filename ?? qaModalId}
              </p>
              <button
                type="button"
                onClick={() => setQaModalId(null)}
                aria-label="Close"
                className="text-ink-soft hover:text-ink"
              >
                ×
              </button>
            </div>
            <QaDetail report={qaScores[qaModalId]} />
          </div>
        </div>
      ) : null}
    </div>
  );
}
