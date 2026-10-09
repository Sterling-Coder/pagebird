"use client";

import { Suspense, useEffect, useRef, useState } from "react";
import { useParams, useRouter, useSearchParams } from "next/navigation";
import {
  listProjectFiles,
  getProject,
  listAllFolders,
  createFolder,
  deleteFolder,
  startProjectJob,
  downloadJobOutput,
  type JobSummary,
  type Folder,
  type Project,
} from "@/lib/projects";
import { translateLinks, deleteJob, getJobEval, listProjectEvals, type EvalReport } from "@/lib/translate";
import { languageName } from "@/lib/languageNames";
import { fileKind, fileKindLabel, getJobType, stageLabel, type JobTypeId } from "@/lib/jobTypes";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { QaDetail } from "@/components/app/QaDetail";
import { Notice, ProjectUploader, T, TargetLanguageSelect } from "@/components/app/UploadPane";

// Last list seen per project/folder, so returning to a page shows it at once
// and refreshes behind it instead of starting from an empty screen.
const filesCache = new Map<string, JobSummary[]>();
const foldersCache = new Map<string, Folder[]>();
const POLL_ACTIVE_MS = 3000; // while something is translating
const POLL_IDLE_MS = 30000; // otherwise: just notice work started elsewhere
const LINK_EXTENSIONS = [".ai", ".eps", ".pdf", ".psd"];

const EMPTY_HINT: Record<string, string> = {
  document: "No files yet — drop a PDF, IDML or Office file above to translate it.",
  image: "No images yet — drop a PNG, JPEG, WEBP, Photoshop or Illustrator file above.",
  website: "No pages yet — paste a public page URL above to translate it.",
};

type Toast = { kind: "success" | "error" | "info"; text: string; id: number };

export default function ProjectFilesPage() {
  return (
    <Suspense fallback={<div className="p-6 text-[13px] text-muted">Loading…</div>}>
      <KeyedProjectFiles />
    </Suspense>
  );
}

/** One fresh list per project/folder: moving between folders remounts it, so
 * selections and per-visit state reset without effects that copy state. */
function KeyedProjectFiles() {
  const params = useParams<{ projectId: string }>();
  const folderId = useSearchParams().get("folder") ?? undefined;
  return <ProjectFiles key={`${params.projectId}:${folderId ?? ""}`} folderId={folderId} />;
}

function ProjectFiles({ folderId }: { folderId?: string }) {
  const params = useParams<{ projectId: string }>();
  const router = useRouter();
  const searchParams = useSearchParams();
  const linksInputRef = useRef<HTMLInputElement>(null);
  const linksFolderInputRef = useRef<HTMLInputElement>(null);
  const [project, setProject] = useState<Project | null>(null);
  const [projectReady, setProjectReady] = useState(false);
  const [files, setFiles] = useState<JobSummary[]>(() => filesCache.get(`${params.projectId}:${folderId ?? ""}`) ?? []);
  const [allFolders, setAllFolders] = useState<Folder[]>(() => foldersCache.get(params.projectId) ?? []);
  // The current level is just the project's folders filtered by parent — one
  // request for the whole tree serves both this list and the breadcrumb.
  const folders = allFolders.filter((f) => (f.parent_folder_id ?? null) === (folderId ?? null));
  const [loaded, setLoaded] = useState(() => filesCache.has(`${params.projectId}:${folderId ?? ""}`));
  const [listError, setListError] = useState(false);
  const processingRef = useRef(false);
  const qaAskedRef = useRef<Set<string>>(new Set());
  // Last status seen per job, so a finish or failure during this visit is announced.
  const lastStatusRef = useRef<Map<string, string>>(new Map());
  const [uploaderOpen, setUploaderOpen] = useState(searchParams.get("upload") === "1");
  const [toast, setToast] = useState<Toast | null>(null);
  const [pendingLinkFiles, setPendingLinkFiles] = useState<File[]>([]);
  const [linksLang, setLinksLang] = useState("");
  const [linksInFlight, setLinksInFlight] = useState<{ id: string; name: string }[]>([]);
  const [creatingFolder, setCreatingFolder] = useState(false);
  // Set synchronously so a double-click or Enter+click can't create two folders.
  const creatingFolderRef = useRef(false);
  const submittingLinksRef = useRef(false);
  const [newFolderName, setNewFolderName] = useState("");
  const [selectedFolders, setSelectedFolders] = useState<Set<string>>(new Set());
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set());
  const [deletingItems, setDeletingItems] = useState(false);
  const [downloadingIds, setDownloadingIds] = useState<Set<string>>(new Set());
  const [retryingIds, setRetryingIds] = useState<Set<string>>(new Set());
  const [confirmDeleteOpen, setConfirmDeleteOpen] = useState(false);
  const [qaScores, setQaScores] = useState<Record<string, EvalReport>>({});
  const [qaModalId, setQaModalId] = useState<string | null>(null);
  const [qaRunning, setQaRunning] = useState<Set<string>>(new Set());
  const [qaErrors, setQaErrors] = useState<Record<string, string>>({});

  const projectType = (project?.job_type ?? "document") as JobTypeId;
  const typeConfig = getJobType(projectType);

  function notify(kind: Toast["kind"], text: string) {
    setToast({ kind, text, id: Date.now() });
  }

  // Successes fade on their own; errors stay until dismissed.
  useEffect(() => {
    if (!toast || toast.kind === "error") return;
    const t = setTimeout(() => setToast((cur) => (cur?.id === toast.id ? null : cur)), 6000);
    return () => clearTimeout(t);
  }, [toast]);

  function setBusy(setter: typeof setDownloadingIds, id: string, on: boolean) {
    setter((prev) => {
      const next = new Set(prev);
      if (on) next.add(id);
      else next.delete(id);
      return next;
    });
  }

  // Runs the full evaluation for one file, then opens its report. The list
  // itself only ever reads cached results, so this is the explicit opt-in.
  function runQa(jobId: string) {
    if (qaRunning.has(jobId)) return;
    setBusy(setQaRunning, jobId, true);
    setQaErrors((prev) => {
      const next = { ...prev };
      delete next[jobId];
      return next;
    });
    getJobEval(jobId, { refresh: true })
      .then((report) => {
        setQaScores((prev) => ({ ...prev, [jobId]: report }));
        setQaModalId(jobId);
      })
      .catch((err) =>
        setQaErrors((prev) => ({ ...prev, [jobId]: err instanceof Error ? err.message : "QA failed" }))
      )
      .finally(() => setBusy(setQaRunning, jobId, false));
  }

  function refreshQa() {
    listProjectEvals(params.projectId)
      .then((reports) => setQaScores((prev) => ({ ...prev, ...reports })))
      .catch(() => {});
  }

  function refreshFiles() {
    const cacheKey = `${params.projectId}:${folderId ?? ""}`;
    return listProjectFiles(params.projectId, folderId)
      .then((fetched) => {
        filesCache.set(cacheKey, fetched);
        setFiles(fetched);
        setLoaded(true);
        setListError(false);
        processingRef.current = fetched.some((f) => f.status === "processing");
        const known = new Set(fetched.map((f) => f.original_filename));
        setLinksInFlight((prev) => prev.filter((f) => !known.has(f.name)));

        // Announce jobs that finished or failed while this page was open.
        const last = lastStatusRef.current;
        const finishedNow = fetched.filter((f) => last.get(f.id) === "processing" && f.status === "complete");
        const failedNow = fetched.filter((f) => last.get(f.id) === "processing" && f.status === "failed");
        fetched.forEach((f) => last.set(f.id, f.status));
        if (failedNow.length) {
          const f = failedNow[0];
          notify("error", `${f.original_filename ?? "A file"} failed${f.error ? `: ${f.error}` : "."}`);
        } else if (finishedNow.length) {
          notify(
            "success",
            finishedNow.length === 1
              ? `${finishedNow[0].original_filename ?? "Your file"} is translated. Download it or open it to review.`
              : `${finishedNow.length} files are translated.`
          );
        }

        // QA scores come from one cached-only request, made only when a file
        // has newly finished — never one request per file per poll.
        const finished = fetched.filter((f) => f.status === "complete" && !qaAskedRef.current.has(f.id));
        if (finished.length > 0) {
          finished.forEach((f) => qaAskedRef.current.add(f.id));
          refreshQa();
        }
        return fetched;
      })
      .catch(() => {
        setListError(true); // keep what is on screen; the next poll retries
        return null;
      });
  }

  function refreshFolders() {
    listAllFolders(params.projectId)
      .then((fetched) => {
        foldersCache.set(params.projectId, fetched);
        setAllFolders(fetched);
      })
      .catch(() => setListError(true));
  }

  function refresh() {
    refreshFiles();
    refreshFolders();
  }

  useEffect(() => {
    refresh();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId, folderId]);

  useEffect(() => {
    getProject(params.projectId)
      .then(setProject)
      .catch(() => setProject(null))
      .finally(() => setProjectReady(true));
  }, [params.projectId]);

  // Poll quickly only while something is translating; otherwise check rarely
  // (so work started in another tab still shows up) and again whenever the
  // tab becomes visible. A hidden tab makes no requests at all.
  useEffect(() => {
    let cancelled = false;
    let timer: ReturnType<typeof setTimeout>;
    function schedule() {
      timer = setTimeout(async () => {
        if (!cancelled && !document.hidden) await refreshFiles();
        if (!cancelled) schedule();
      }, processingRef.current ? POLL_ACTIVE_MS : POLL_IDLE_MS);
    }
    function onVisible() {
      if (!document.hidden) refreshFiles();
    }
    schedule();
    document.addEventListener("visibilitychange", onVisible);
    return () => {
      cancelled = true;
      clearTimeout(timer);
      document.removeEventListener("visibilitychange", onVisible);
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [params.projectId, folderId]);

  // Drop `?upload=1` once read, so a reload or Back doesn't reopen the panel.
  useEffect(() => {
    if (searchParams.get("upload") !== "1") return;
    const url = new URL(window.location.href);
    url.searchParams.delete("upload");
    window.history.replaceState(null, "", url);
  }, [searchParams]);

  function handleStarted(jobIds: string[], label: string) {
    // The backend writes each job's row before answering, so the next list
    // already shows them as Translating.
    jobIds.forEach((id) => lastStatusRef.current.set(id, "processing"));
    processingRef.current = true;
    refreshFiles();
    notify("success", `Started translating ${label}. Progress shows below — you can leave this page, it keeps running.`);
    setUploaderOpen(false);
  }

  async function retry(f: JobSummary) {
    const kind = fileKind(f);
    if (kind !== "website" || !f.meta?.source_url) {
      setUploaderOpen(true);
      notify("info", `Drop ${f.original_filename ?? "the file"} again above to retry.`);
      return;
    }
    setBusy(setRetryingIds, f.id, true);
    try {
      const id = await startProjectJob({
        kind: "website",
        url: f.meta.source_url,
        targetLang: f.meta.target_lang ?? project?.target_lang ?? "",
        projectId: params.projectId,
        folderId,
      });
      handleStarted([id], f.meta.source_url);
    } catch (err) {
      notify("error", err instanceof Error ? err.message : "Could not retry.");
    } finally {
      setBusy(setRetryingIds, f.id, false);
    }
  }

  function download(f: JobSummary) {
    if (f.download_available === false) return;
    setBusy(setDownloadingIds, f.id, true);
    downloadJobOutput(f)
      .catch((err) => notify("error", err instanceof Error ? err.message : `Download failed: ${f.original_filename}`))
      .finally(() => setBusy(setDownloadingIds, f.id, false));
  }

  function handleLinksPicked(fileList: FileList | null, filterByExtension = false) {
    if (!fileList || fileList.length === 0) return;
    let picked = Array.from(fileList);
    if (filterByExtension) {
      picked = picked.filter((f) => LINK_EXTENSIONS.some((ext) => f.name.toLowerCase().endsWith(ext)));
    }
    if (picked.length) setPendingLinkFiles(picked);
    else notify("error", "That folder has no .ai, .eps, .pdf or .psd files.");
  }

  async function handleConfirmTranslateLinks() {
    if (pendingLinkFiles.length === 0 || !linksLang || submittingLinksRef.current) return;
    submittingLinksRef.current = true;
    const filesToTranslate = pendingLinkFiles;
    setPendingLinkFiles([]);
    // Matches the backend's own display name so the real row replaces this one.
    const name =
      filesToTranslate.length === 1 ? filesToTranslate[0].name : `${filesToTranslate.length} linked graphics`;
    const tempId = `pending-links-${filesToTranslate.length}-${name}`;
    setLinksInFlight((prev) => [...prev, { id: tempId, name }]);
    submittingLinksRef.current = false;
    try {
      const { jobId } = await translateLinks({
        files: filesToTranslate,
        targetLanguage: linksLang,
        projectId: params.projectId,
        folderId,
      });
      handleStarted([jobId], name);
    } catch (err) {
      notify("error", err instanceof Error ? err.message : "Linked graphics upload failed.");
    } finally {
      setLinksInFlight((prev) => prev.filter((f) => f.id !== tempId));
    }
  }

  async function handleCreateFolder() {
    if (!newFolderName.trim() || creatingFolderRef.current) return;
    creatingFolderRef.current = true;
    try {
      await createFolder(params.projectId, newFolderName.trim(), folderId);
      notify("success", `Folder “${newFolderName.trim()}” created.`);
      setNewFolderName("");
      setCreatingFolder(false);
      refresh();
    } catch (err) {
      notify("error", err instanceof Error ? err.message : "Failed to create folder");
    } finally {
      creatingFolderRef.current = false;
    }
  }

  function toggle(setter: typeof setSelectedFiles, id: string) {
    setter((prev) => {
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
  const hasLegacyDownloadIssue = files.some((f) => f.download_available === false && f.status === "complete");
  const isEmpty = loaded && files.length === 0 && folders.length === 0 && linksInFlight.length === 0;
  const showUploader = uploaderOpen || isEmpty;

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
    const count = selectedFolders.size + selectedFiles.size;
    try {
      await Promise.all([
        ...[...selectedFolders].map((id) => deleteFolder(id)),
        ...[...selectedFiles].map((id) => deleteJob(id)),
      ]);
      setSelectedFolders(new Set());
      setSelectedFiles(new Set());
      notify("success", `Deleted ${count} item${count === 1 ? "" : "s"}.`);
    } catch (err) {
      notify("error", err instanceof Error ? err.message : "Some items couldn't be deleted.");
    } finally {
      setConfirmDeleteOpen(false);
      setDeletingItems(false);
      refresh();
    }
  }

  const selectedNames = [
    ...folders.filter((f) => selectedFolders.has(f.id)).map((f) => f.name),
    ...files.filter((f) => selectedFiles.has(f.id)).map((f) => f.original_filename ?? f.id),
  ];

  function goToFolder(id?: string) {
    router.push(id ? `/app/jobs/${params.projectId}/files?folder=${id}` : `/app/jobs/${params.projectId}/files`);
  }

  const breadcrumb: Folder[] = (() => {
    if (!folderId) return [];
    const byId = new Map(allFolders.map((f) => [f.id, f]));
    const chain: Folder[] = [];
    let current: string | undefined = folderId;
    while (current) {
      const folder = byId.get(current);
      if (!folder) break; // not loaded yet, or deleted
      chain.unshift(folder);
      current = folder.parent_folder_id ?? undefined;
    }
    return chain;
  })();

  const th = "px-3 py-2.5 text-left text-[11.5px] font-medium text-muted";
  const td = "px-3 py-2.5";

  return (
    <div className="flex min-h-0 flex-1 flex-col overflow-auto px-6 py-5">
      <div className="mb-4 flex flex-wrap items-center gap-2">
        <nav className="mr-auto flex flex-wrap items-center gap-1 text-[13px]" aria-label="Folders">
          <button type="button" onClick={() => goToFolder()} className={breadcrumb.length ? "text-ink-soft hover:text-ink" : "font-medium text-ink"}>
            All files
          </button>
          {breadcrumb.map((f, i) => (
            <span key={f.id} className="flex items-center gap-1">
              <span className="text-muted">/</span>
              {i === breadcrumb.length - 1 ? (
                <span className="font-medium text-ink">{f.name}</span>
              ) : (
                <button type="button" onClick={() => goToFolder(f.id)} className="text-ink-soft hover:text-ink">
                  {f.name}
                </button>
              )}
            </span>
          ))}
        </nav>
        {selectedFolders.size + selectedFiles.size > 0 ? (
          <button type="button" onClick={() => setConfirmDeleteOpen(true)} disabled={deletingItems}
            className={`${T.secondaryBtn} hover:!text-[#b3261e]`}>
            Delete {selectedFolders.size + selectedFiles.size} selected
          </button>
        ) : null}
        <button type="button" onClick={() => setCreatingFolder(true)} className={T.secondaryBtn}>
          New folder
        </button>
        {!isEmpty ? (
          <button type="button" onClick={() => setUploaderOpen((v) => !v)} aria-expanded={showUploader} className={T.primaryBtn}>
            {showUploader ? "Hide upload" : typeConfig?.input === "url" ? "Translate a page" : "Upload files"}
          </button>
        ) : null}
      </div>

      {toast ? (
        <div className="mb-3">
          <Notice kind={toast.kind} onClose={() => setToast(null)}>{toast.text}</Notice>
        </div>
      ) : null}
      {hasLegacyDownloadIssue ? (
        <div className="mb-3">
          <Notice kind="error">
            Some translations were created before durable file storage was enabled and can&apos;t be downloaded. Upload the original file again.
          </Notice>
        </div>
      ) : null}
      {listError ? (
        <div className="mb-3">
          <Notice kind="info">
            Couldn&apos;t refresh this list — retrying automatically.{" "}
            <button type="button" onClick={refresh} className="underline hover:no-underline">Retry now</button>
          </Notice>
        </div>
      ) : null}

      {showUploader && projectReady ? (
        <div className="mb-5">
          <ProjectUploader
            projectId={params.projectId}
            projectType={projectType}
            folderId={folderId}
            projectLang={project?.target_lang}
            onStarted={handleStarted}
            onClose={isEmpty ? undefined : () => setUploaderOpen(false)}
          />
          {projectType === "document" ? (
            <p className="mt-2 text-[12px] text-muted">
              Translating an InDesign Links folder on its own?{" "}
              <button type="button" onClick={() => linksInputRef.current?.click()} className={`${T.accentText} hover:underline`}>
                Pick linked graphics
              </button>{" "}
              or{" "}
              <button type="button" onClick={() => linksFolderInputRef.current?.click()} className={`${T.accentText} hover:underline`}>
                a whole Links folder
              </button>{" "}
              (.ai, .eps, .pdf, .psd).
            </p>
          ) : null}
        </div>
      ) : null}

      <input ref={linksInputRef} type="file" multiple accept={LINK_EXTENSIONS.join(",")} className="hidden"
        onChange={(e) => { handleLinksPicked(e.target.files); e.target.value = ""; }} />
      <input
        ref={linksFolderInputRef}
        type="file"
        multiple
        // @ts-expect-error non-standard attrs, Chrome/Safari/Firefox support them
        webkitdirectory=""
        directory=""
        className="hidden"
        onChange={(e) => { handleLinksPicked(e.target.files, true); e.target.value = ""; }}
      />

      {!loaded && files.length === 0 && folders.length === 0 ? (
        <p className={`rounded-2xl ${T.surface2} px-4 py-8 text-center text-[13px] text-muted`}>Loading files…</p>
      ) : isEmpty ? (
        <p className={`rounded-2xl ${T.surface2} px-4 py-6 text-center text-[13px] text-muted`}>
          {folderId ? "This folder is empty. Upload files above while you're in it to keep them here." : EMPTY_HINT[projectType] ?? EMPTY_HINT.document}
        </p>
      ) : (
        <div className={`overflow-x-auto ${T.card}`}>
          <table className="w-full min-w-[820px] border-collapse text-[13px]">
            <thead>
              <tr className={`border-b ${T.border}`}>
                <th className={`${th} w-8`}>
                  <input type="checkbox" checked={allSelected} onChange={toggleSelectAll} aria-label="Select all" />
                </th>
                <th className={th}>Name</th>
                <th className={th}>Type</th>
                <th className={th}>Status</th>
                <th className={th}>Target</th>
                <th className={th}>Created by</th>
                <th className={th}>Created</th>
                <th className={th}>QA</th>
                <th className={`${th} text-right`}>Download</th>
              </tr>
            </thead>
            <tbody>
              {folders.map((f) => (
                <tr key={f.id} onClick={() => goToFolder(f.id)}
                  className={`cursor-pointer border-b ${T.border} last:border-0 hover:bg-[var(--app-surface-2,#f6f2ea)]`}>
                  <td className={td} onClick={(e) => e.stopPropagation()}>
                    <input type="checkbox" checked={selectedFolders.has(f.id)} onChange={() => toggle(setSelectedFolders, f.id)}
                      aria-label={`Select ${f.name}`} />
                  </td>
                  <td className={td}>
                    <span className="flex items-center gap-2 text-ink">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4 shrink-0 text-ink-soft">
                        <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                      </svg>
                      {f.name}
                    </span>
                  </td>
                  <td className={`${td} text-muted`}>Folder</td>
                  <td className={`${td} text-muted`} colSpan={2}>—</td>
                  <td className={`${td} text-ink-soft`}>{f.created_by_name ?? "—"}</td>
                  <td className={`${td} text-ink-soft`}>{new Date(f.created_at * 1000).toLocaleDateString()}</td>
                  <td className={`${td} text-muted`} colSpan={2}>—</td>
                </tr>
              ))}
              {linksInFlight.map((f) => (
                <tr key={f.id} className={`border-b ${T.border} last:border-0`}>
                  <td className={td} />
                  <td className={`${td} text-ink`}>{f.name}</td>
                  <td className={`${td} text-ink-soft`}>Linked graphics</td>
                  <td className={td} colSpan={6}>
                    <ProgressCell stage="Uploading…" />
                  </td>
                </tr>
              ))}
              {files.map((f) => {
                const kind = fileKind(f);
                const name = kind === "website" ? f.meta?.source_url ?? f.original_filename ?? f.id : f.original_filename ?? f.id;
                const processing = f.status === "processing";
                const failed = f.status === "failed";
                const complete = f.status === "complete";
                const canOpen = complete;
                return (
                  <tr key={f.id}
                    onClick={() => canOpen && router.push(`/app/jobs/${params.projectId}/files/${f.id}`)}
                    className={`border-b ${T.border} align-top last:border-0 ${canOpen ? "cursor-pointer hover:bg-[var(--app-surface-2,#f6f2ea)]" : ""}`}>
                    <td className={td} onClick={(e) => e.stopPropagation()}>
                      <input type="checkbox" checked={selectedFiles.has(f.id)} onChange={() => toggle(setSelectedFiles, f.id)}
                        aria-label={`Select ${name}`} />
                    </td>
                    <td className={`${td} max-w-[320px]`}>
                      <span className="block truncate text-ink" title={name}>{name}</span>
                      {failed ? (
                        <div className="mt-1 text-[12px]" onClick={(e) => e.stopPropagation()}>
                          <p className={T.error}>{f.error || "Translation failed."}</p>
                          <p className="mt-0.5 text-muted">
                            {kind === "website" ? "Check the page is public, then " : "Fix the file if the reason above says so, then "}
                            <button type="button" disabled={retryingIds.has(f.id)} onClick={() => retry(f)} className={`${T.accentText} hover:underline disabled:opacity-50`}>
                              {retryingIds.has(f.id) ? "retrying…" : kind === "website" ? "retry" : "upload it again"}
                            </button>
                            .
                          </p>
                        </div>
                      ) : null}
                      {complete ? <span className="text-[11.5px] text-muted">Open to review{kind === "image" ? "" : " and edit"}</span> : null}
                    </td>
                    <td className={`${td} whitespace-nowrap text-ink-soft`}>
                      {kind === "links" && f.meta?.extensions?.length ? f.meta.extensions.join(", ").toUpperCase() : fileKindLabel(f)}
                    </td>
                    <td className={td}>
                      {processing ? (
                        <ProgressCell progress={f.meta?.progress} stage={stageLabel(f.meta?.stage) ?? "Queued"} />
                      ) : (
                        <StatusPill status={f.status} />
                      )}
                    </td>
                    <td className={`${td} text-ink-soft`}>
                      {f.meta?.target_language ?? languageName(f.meta?.target_lang ?? project?.target_lang) ?? "—"}
                    </td>
                    <td className={`${td} text-ink-soft`}>{f.created_by_name ?? "—"}</td>
                    <td className={`${td} whitespace-nowrap text-ink-soft`}>{new Date(f.created_at * 1000).toLocaleDateString()}</td>
                    <td className={td} onClick={(e) => e.stopPropagation()}>
                      <QaCell
                        report={qaScores[f.id]}
                        applicable={complete && (kind === "pdf" || kind === "idml" || kind === "links")}
                        running={qaRunning.has(f.id)}
                        failure={qaErrors[f.id]}
                        onRun={() => runQa(f.id)}
                        onOpen={() => setQaModalId(f.id)}
                      />
                    </td>
                    <td className={`${td} text-right`} onClick={(e) => e.stopPropagation()}>
                      {complete ? (
                        <button type="button" disabled={f.download_available === false || downloadingIds.has(f.id)}
                          onClick={() => download(f)} aria-label={`Download ${name}`} aria-busy={downloadingIds.has(f.id)}
                          title={f.download_available === false ? "This translation needs to be uploaded again." : "Download the translation"}
                          className={`inline-flex items-center gap-1.5 rounded-full border ${T.border} px-3 py-1 text-[12px] text-ink-soft hover:text-ink disabled:cursor-not-allowed disabled:opacity-40`}>
                          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75"
                            className={`h-3.5 w-3.5 ${downloadingIds.has(f.id) ? "animate-pulse" : ""}`}>
                            <path d="M12 3v12m0 0l-4-4m4 4l4-4M4 21h16" />
                          </svg>
                          {downloadingIds.has(f.id) ? "Preparing…" : "Download"}
                        </button>
                      ) : (
                        <span className="text-muted">—</span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      )}

      {pendingLinkFiles.length > 0 ? (
        <Modal title={`Translate ${pendingLinkFiles.length} linked graphic${pendingLinkFiles.length !== 1 ? "s" : ""}`}
          onClose={() => setPendingLinkFiles([])}>
          <p className="text-[12.5px] text-muted">
            Each file is read and translated on its own — no document, no relinking. Download the set as a zip when done.
          </p>
          <ul className="mt-3 max-h-32 space-y-1 overflow-auto text-[13px] text-ink">
            {pendingLinkFiles.map((f, i) => (
              <li key={`${f.name}-${i}`} className="flex items-center justify-between">
                <span className="truncate">{f.name}</span>
                <button type="button" onClick={() => setPendingLinkFiles((prev) => prev.filter((_, idx) => idx !== i))}
                  aria-label={`Remove ${f.name}`} className="ml-2 shrink-0 text-muted hover:text-ink">×</button>
              </li>
            ))}
          </ul>
          <label className="mt-4 block">
            <span className="mb-1.5 block text-[12px] text-muted">Translate into</span>
            <TargetLanguageSelect value={linksLang} onChange={setLinksLang} preferred={project?.target_lang} />
          </label>
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={() => setPendingLinkFiles([])} className={T.secondaryBtn}>Cancel</button>
            <button type="button" onClick={handleConfirmTranslateLinks} disabled={!linksLang} className={T.primaryBtn}>Translate</button>
          </div>
        </Modal>
      ) : null}

      {creatingFolder ? (
        <Modal title="New folder" onClose={() => { setCreatingFolder(false); setNewFolderName(""); }}>
          <input autoFocus value={newFolderName} onChange={(e) => setNewFolderName(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleCreateFolder()} placeholder="Folder name" className={T.input} />
          <div className="mt-6 flex justify-end gap-2">
            <button type="button" onClick={() => { setCreatingFolder(false); setNewFolderName(""); }} className={T.secondaryBtn}>Cancel</button>
            <button type="button" onClick={handleCreateFolder} disabled={!newFolderName.trim()} className={T.primaryBtn}>Create</button>
          </div>
        </Modal>
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
        <Modal wide title={`QA detail — ${files.find((f) => f.id === qaModalId)?.original_filename ?? qaModalId}`}
          onClose={() => setQaModalId(null)}>
          <QaDetail report={qaScores[qaModalId]} />
        </Modal>
      ) : null}
    </div>
  );
}

function Modal({ title, children, onClose, wide = false }: {
  title: string; children: React.ReactNode; onClose: () => void; wide?: boolean;
}) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => { if (e.target === e.currentTarget) onClose(); }}>
      <div role="dialog" aria-modal="true" aria-label={title}
        className={`max-h-[85vh] w-full overflow-auto ${wide ? "max-w-2xl" : "max-w-sm"} ${T.card} p-6 shadow-xl`}>
        <div className="mb-3 flex items-start justify-between gap-3">
          <p className="text-[14.5px] font-semibold text-ink">{title}</p>
          <button type="button" onClick={onClose} aria-label="Close" className="text-muted hover:text-ink">×</button>
        </div>
        {children}
      </div>
    </div>
  );
}

function ProgressCell({ progress, stage }: { progress?: number; stage: string }) {
  const known = typeof progress === "number";
  return (
    <div className="w-36">
      <div className="h-1.5 overflow-hidden rounded-full bg-[var(--app-surface-2,#f0ece3)]">
        {known ? (
          <div className="h-full rounded-full bg-[var(--app-accent,#c86018)] transition-[width] duration-500"
            style={{ width: `${Math.max(4, Math.min(100, progress))}%` }} />
        ) : (
          <div className="progress-indeterminate h-full w-full opacity-60" />
        )}
      </div>
      <p className="mt-1 truncate text-[11.5px] text-muted">{known ? `${Math.round(progress)}% · ` : ""}{stage}</p>
    </div>
  );
}

const STATUS: Record<string, { label: string; cls: string }> = {
  complete: { label: "Translated", cls: "bg-[#e8f5e9] text-[#2e7d32]" },
  failed: { label: "Failed", cls: "bg-[#fdecea] text-[#b3261e]" },
  processing: { label: "Translating", cls: "bg-[#fbefe1] text-[#9a5a14]" },
};

function StatusPill({ status }: { status: string }) {
  const s = STATUS[status] ?? { label: status, cls: "bg-[var(--app-surface-2,#f6f2ea)] text-muted" };
  return <span className={`inline-flex rounded-full px-2 py-0.5 text-[11.5px] ${s.cls}`}>{s.label}</span>;
}

function QaCell({ report, applicable, running, failure, onRun, onOpen }: {
  report?: EvalReport; applicable: boolean; running: boolean; failure?: string; onRun: () => void; onOpen: () => void;
}) {
  if (!report || report.not_computed) {
    if (!applicable) return <span className="text-muted">—</span>;
    return (
      <button type="button" disabled={running} onClick={onRun} aria-busy={running}
        title={failure ? `${failure} — click to retry` : "Run a QA check and open the report"}
        className={`rounded-full border px-2.5 py-0.5 text-[11.5px] disabled:opacity-60 ${
          failure ? "border-[#f3c9c5] text-[#b3261e]" : "border-[var(--app-border,#ebe5da)] text-ink-soft hover:text-ink"
        }`}>
        {running ? "Running…" : failure ? "Retry QA" : "Run QA"}
      </button>
    );
  }
  if (report.not_applicable) return <span className="text-muted">N/A</span>;
  const score = report.overall?.score;
  return (
    <button type="button" onClick={onOpen}
      className={`underline decoration-dotted underline-offset-2 hover:no-underline ${report.overall?.gates_passed ? "text-ink" : "text-[#b3261e]"}`}>
      {typeof score === "number" ? `${Math.round(score * 100)}%` : "—"}
    </button>
  );
}
