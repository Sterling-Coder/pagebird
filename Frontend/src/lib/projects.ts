import { API_BASE_URL } from "./translate";
import { authHeaders } from "@/lib/supabase/authFetch";
import { fileKind } from "./jobTypes";

export type Project = {
  id: string;
  name: string;
  job_type: string;
  source_lang: string | null;
  target_lang: string | null;
  client: string | null;
  vendor: string | null;
  deadline: number | null;
  status: string;
  created_at: number;
  created_by: string | null;
  file_count: number;
  status_counts: Record<string, number>;
};

export type JobSummary = {
  id: string;
  status: string;
  error?: string | null;
  original_filename: string | null;
  created_at: number;
  project_id?: string | null;
  job_type?: string;
  folder_id?: string | null;
  created_by?: string | null;
  created_by_name?: string | null;
  download_available?: boolean;
  meta?: {
    progress?: number;
    stage?: string;
    failed_stage?: string;
    extensions?: string[];
    format?: string;
    target_lang?: string;
    target_language?: string;
    source_url?: string;
  } | null;
};

export type Folder = {
  id: string;
  project_id: string;
  name: string;
  parent_folder_id: string | null;
  created_at: number;
  created_by?: string | null;
  created_by_name?: string | null;
};

export async function createProject(input: {
  name: string;
  jobType: string;
  targetLanguage?: string;
  sourceLanguage?: string;
}): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({
      name: input.name,
      job_type: input.jobType,
      target_lang: input.targetLanguage,
      source_lang: input.sourceLanguage,
    }),
  });
  if (!res.ok) throw new Error(`Failed to create project (${res.status})`);
  return res.json();
}

export async function listProjects(): Promise<Project[]> {
  const res = await fetch(`${API_BASE_URL}/api/projects`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load projects (${res.status})`);
  return res.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to load project (${res.status})`);
  return res.json();
}

export async function updateProject(
  projectId: string,
  fields: { client?: string; vendor?: string; deadline?: number }
): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
    method: "PATCH",
    headers: { ...(await authHeaders()), "Content-Type": "application/json" },
    body: JSON.stringify(fields),
  });
  if (!res.ok) throw new Error(`Failed to update project (${res.status})`);
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete project (${res.status})`);
}

export async function listProjectFiles(
  projectId: string,
  folderId?: string
): Promise<JobSummary[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/files`);
  if (folderId) url.searchParams.set("folder_id", folderId);
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load files (${res.status})`);
  return res.json();
}

export async function listAllProjectFiles(projectId: string): Promise<JobSummary[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/files`);
  url.searchParams.set("all", "true");
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load files (${res.status})`);
  return res.json();
}

export async function createFolder(
  projectId: string,
  name: string,
  parentFolderId?: string
): Promise<Folder> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}/folders`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ name, parent_folder_id: parentFolderId ?? null }),
  });
  if (!res.ok) throw new Error(`Failed to create folder (${res.status})`);
  return res.json();
}

export async function listFolders(
  projectId: string,
  parentFolderId?: string
): Promise<Folder[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/folders`);
  if (parentFolderId) url.searchParams.set("parent_folder_id", parentFolderId);
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load folders (${res.status})`);
  return res.json();
}

export async function listAllFolders(projectId: string): Promise<Folder[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/folders`);
  url.searchParams.set("all", "true");
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load folders (${res.status})`);
  return res.json();
}

export async function getFolder(folderId: string): Promise<Folder> {
  const res = await fetch(`${API_BASE_URL}/api/folders/${folderId}`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to load folder (${res.status})`);
  return res.json();
}

export async function deleteFolder(folderId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/folders/${folderId}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete folder (${res.status})`);
}

/** The backend's error text for a failed request (FastAPI `detail`), or a
 * plain fallback that still names what went wrong. */
async function failure(res: Response, what: string): Promise<Error> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return new Error(detail);
  if (Array.isArray(detail) && typeof detail[0]?.msg === "string") return new Error(detail[0].msg);
  return new Error(`${what} failed (${res.status})`);
}

/** Start one translation inside a project (and folder). Documents and Office
 * files go to /api/translate, images to /api/image-translation, a page URL to
 * /api/translate/website. Every one returns 202 + a job id and runs in the
 * background; the Files list follows it from there. The helpers in
 * `lib/agents.ts` do the same without a folder. */
export async function startProjectJob(input: {
  kind: "document" | "image" | "website";
  file?: File;
  url?: string;
  targetLang: string;
  projectId: string;
  folderId?: string;
}): Promise<string> {
  let res: Response;
  if (input.kind === "website") {
    res = await fetch(`${API_BASE_URL}/api/translate/website`, {
      method: "POST",
      headers: { "Content-Type": "application/json", ...(await authHeaders()) },
      body: JSON.stringify({
        url: input.url ?? "",
        target_lang: input.targetLang,
        project_id: input.projectId,
        folder_id: input.folderId ?? "",
      }),
    });
  } else {
    if (!input.file) throw new Error("Choose a file first.");
    const form = new FormData();
    form.append("file", input.file);
    form.append("target_lang", input.targetLang);
    form.append("project_id", input.projectId);
    if (input.folderId) form.append("folder_id", input.folderId);
    const path = input.kind === "image" ? "/api/image-translation" : "/api/translate";
    res = await fetch(`${API_BASE_URL}${path}`, { method: "POST", headers: await authHeaders(), body: form });
  }
  if (!res.ok) throw await failure(res, input.kind === "website" ? "Website translation" : "Upload");
  const body = await res.json();
  const id = body.job_id ?? body.id;
  if (!id) throw new Error("The server did not return a job id.");
  return id as string;
}

/** Where a finished job's translated file is served from. */
export function jobDownloadUrl(job: Pick<JobSummary, "id" | "job_type" | "original_filename" | "meta">): string {
  switch (fileKind(job)) {
    case "image":
      return `${API_BASE_URL}/api/image-translation/${job.id}/result?download=true`;
    case "website":
      return `${API_BASE_URL}/api/translate/website/${job.id}/result?download=true`;
    case "idml":
      return `${API_BASE_URL}/api/jobs/${job.id}/download?format=idml`;
    default:
      return `${API_BASE_URL}/api/jobs/${job.id}/download`;
  }
}

function filenameFrom(disposition: string | null): string | null {
  if (!disposition) return null;
  const star = /filename\*=UTF-8''([^;]+)/i.exec(disposition);
  if (star) {
    try {
      return decodeURIComponent(star[1].trim());
    } catch {
      /* fall through to the plain name */
    }
  }
  const plain = /filename="?([^";]+)"?/i.exec(disposition);
  return plain ? plain[1].trim() : null;
}

const EXT_BY_TYPE: Record<string, string> = {
  "application/zip": ".zip", "application/x-zip-compressed": ".zip",
  "image/png": ".png", "image/jpeg": ".jpg", "image/webp": ".webp",
  "application/illustrator": ".ai", "image/vnd.adobe.photoshop": ".psd",
  "text/html": ".html", "application/pdf": ".pdf",
};

/** "brochure.pdf" + "es" → "brochure.es.pdf", with the extension switched to
 * what actually came back (an IDML with Links is a .zip, a Photoshop file a .png). */
function translatedName(job: Pick<JobSummary, "id" | "original_filename" | "meta">, kind: string, contentType: string): string {
  const original = (job.original_filename ?? job.id).split("/").pop() || job.id;
  const lang = job.meta?.target_lang ? `.${job.meta.target_lang}` : "";
  if (kind === "website") {
    let host = "page";
    try {
      host = new URL(job.meta?.source_url ?? original).hostname || host;
    } catch {
      /* not a URL; keep the generic name */
    }
    return `${host}${lang}.html`;
  }
  const dot = original.lastIndexOf(".");
  const stem = dot > 0 ? original.slice(0, dot) : original;
  const ext = dot > 0 ? original.slice(dot) : "";
  const served = EXT_BY_TYPE[contentType.split(";")[0].trim().toLowerCase()];
  const keepOriginal = !served || served === ext.toLowerCase() || (served === ".jpg" && ext.toLowerCase() === ".jpeg");
  return `${stem}${lang}${keepOriginal ? ext : served}`;
}

/** Saves a finished job's translation, named after the original file plus the
 * target language. */
export async function downloadJobOutput(
  job: Pick<JobSummary, "id" | "job_type" | "original_filename" | "meta">
): Promise<void> {
  const res = await fetch(jobDownloadUrl(job), { headers: await authHeaders() });
  if (!res.ok) throw await failure(res, "Download");
  const blob = await res.blob();
  const name =
    filenameFrom(res.headers.get("Content-Disposition")) ??
    translatedName(job, fileKind(job), res.headers.get("Content-Type") ?? blob.type ?? "");
  const href = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = href;
  a.download = name;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(href), 60_000);
}
