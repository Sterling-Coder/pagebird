"use client";

import { useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  listProjectFiles,
  getProject,
  listFolders,
  createFolder,
  deleteFolder,
  getFolder,
  type JobSummary,
  type Folder,
} from "@/lib/projects";
import { listLanguages, translateDocument, deleteJob, API_BASE_URL, type Language } from "@/lib/translate";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";

const TRANSLATE_STAGES = ["Uploading", "Extracting text", "Translating", "Rebuilding document"];
const STAGE_DURATION_MS = 4000;

export default function ProjectFilesPage() {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const folderId = searchParams.get("folder") ?? undefined;
  const inputRef = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<JobSummary[]>([]);
  const [folders, setFolders] = useState<Folder[]>([]);
  const [breadcrumb, setBreadcrumb] = useState<Folder[]>([]);
  const [languages, setLanguages] = useState<Language[]>([]);
  const [targetLanguage, setTargetLanguage] = useState("es");
  const [projectTargetLang, setProjectTargetLang] = useState<string | null>(null);
  const [pendingFiles, setPendingFiles] = useState<File[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [creatingFolder, setCreatingFolder] = useState(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [deletingItems, setDeletingItems] = useState(false);
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [inFlight, setInFlight] = useState<{ id: string; name: string; startedAt: number }[]>([]);
  const [, setTick] = useState(0);

  function refresh() {
    listProjectFiles(params.projectId, folderId).then(setFiles).catch(() => setFiles([]));
    listFolders(params.projectId, folderId).then(setFolders).catch(() => setFolders([]));
  }

  useEffect(() => {
    refresh();
    setSelectedFolders(new Set());
    setSelectedFiles(new Set());
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId, folderId]);

  useEffect(() => {
    let cancelled = false;
    async function buildBreadcrumb() {
      if (!folderId) {
        setBreadcrumb([]);
        return;
      }
      const chain: Folder[] = [];
      let current: string | undefined = folderId;
      while (current) {
        const folder: Folder = await getFolder(current);
        chain.unshift(folder);
        current = folder.parent_folder_id ?? undefined;
      }
      if (!cancelled) setBreadcrumb(chain);
    }
    buildBreadcrumb().catch(() => setBreadcrumb([]));
    return () => {
      cancelled = true;
    };
  }, [folderId]);

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
    setError(null);
    setPendingFiles(Array.from(fileList));
  }

  function handleConfirmTranslate() {
    if (pendingFiles.length === 0) return;
    const filesToTranslate = pendingFiles;
    setPendingFiles([]);
    setError(null);

    for (const file of filesToTranslate) {
      const tempId = `pending-${Date.now()}-${file.name}`;
      setInFlight((prev) => [...prev, { id: tempId, name: file.name, startedAt: Date.now() }]);

      translateDocument({ file, targetLanguage, projectId: params.projectId, folderId })
        .then(() => refresh())
        .catch((err) => {
          setError(err instanceof Error ? err.message : `Upload failed: ${file.name}`);
        })
        .finally(() => {
          setInFlight((prev) => prev.filter((f) => f.id !== tempId));
        });
    }
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim()) return;
    try {
      await createFolder(params.projectId, newFolderName.trim(), folderId);
      setNewFolderName("");
      setCreatingFolder(false);
      refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create folder");
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
          accept=".pdf,.indd,.idml"
          multiple
          className="hidden"
          onChange={(e) => handleFilePicked(e.target.files)}
        />
        <button
          type="button"
          onClick={() => inputRef.current?.click()}
          className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90"
        >
          Upload
        </button>
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
              <td className="py-2" colSpan={7}>
                <span className="flex items-center gap-2 text-ink">
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4 shrink-0 text-ink-soft">
                    <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                  </svg>
                  {f.name}
                </span>
              </td>
            </tr>
          ))}
          {inFlight.map((f) => {
            const stageIndex = Math.min(
              Math.floor((Date.now() - f.startedAt) / STAGE_DURATION_MS),
              TRANSLATE_STAGES.length - 1
            );
            return (
              <tr key={f.id} className="border-b border-rule">
                <td className="py-2" />
                <td className="py-2 text-ink">{f.name}</td>
                <td className="py-2 text-ink-soft">—</td>
                <td className="py-2">
                  <div className="h-4 w-24 overflow-hidden border border-rule">
                    <div className="progress-indeterminate h-full w-full opacity-50" />
                  </div>
                </td>
                <td className="py-2 font-mono text-[10px] uppercase tracking-widest text-muted" colSpan={5}>
                  {TRANSLATE_STAGES[stageIndex]}…
                </td>
              </tr>
            );
          })}
          {files.map((f) => {
            const name = f.original_filename ?? f.id;
            const ext = name.includes(".") ? name.split(".").pop() : "—";
            return (
              <tr
                key={f.id}
                onClick={() => router.push(`/app/jobs/${params.projectId}/files/${f.id}`)}
                className="cursor-pointer border-b border-rule hover:bg-paper-dim"
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
                  <div className="h-4 w-24 overflow-hidden border border-rule">
                    <div
                      className={`h-full ${f.status === "failed" ? "bg-red/40" : "bg-red"}`}
                      style={{ width: f.status === "complete" || f.status === "failed" ? "100%" : "0%" }}
                    />
                  </div>
                </td>
                <td className="py-2 text-ink-soft">{projectTargetLang ?? "—"}</td>
                <td className="py-2 text-ink-soft">—</td>
                <td className="py-2 text-ink-soft">
                  {new Date(f.created_at * 1000).toLocaleDateString()}
                </td>
                <td className="py-2 text-ink-soft">0</td>
                <td className="py-2" onClick={(e) => e.stopPropagation()}>
                  {f.status === "complete" ? (
                    <a
                      href={`${API_BASE_URL}/api/jobs/${f.id}/download`}
                      download
                      aria-label={`Download ${name}`}
                      className="inline-flex h-6 w-6 items-center justify-center border border-rule text-ink-soft hover:border-ink hover:text-ink"
                    >
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5">
                        <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" />
                      </svg>
                    </a>
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
    </div>
  );
}
