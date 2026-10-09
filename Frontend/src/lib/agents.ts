import { API_BASE_URL } from "./translate";
import { authHeaders } from "@/lib/supabase/authFetch";

/** Any job row, as GET /api/jobs returns it. */
export type JobRow = {
  id: string;
  status: "processing" | "complete" | "failed" | string;
  error?: string | null;
  original_filename: string | null;
  created_at: number;
  duration_sec?: number | null;
  project_id?: string | null;
  job_type?: string;
  download_available?: boolean;
  meta?: {
    format?: string;
    target_lang?: string;
    target_language?: string;
    stage?: string;
    progress?: number;
    source_url?: string;
  } | null;
};

async function json<T>(res: Response, what: string): Promise<T> {
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(typeof body?.detail === "string" ? body.detail : `${what} failed (${res.status})`);
  }
  return res.json();
}

export async function listJobs(): Promise<JobRow[]> {
  const res = await fetch(`${API_BASE_URL}/api/jobs`, { headers: await authHeaders() });
  return json(res, "Loading jobs");
}

export async function getJobRow(jobId: string): Promise<JobRow> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, { headers: await authHeaders() });
  return json(res, "Loading the job");
}

export type Formats = { documents: { ext: string; label: string; mime: string }[] };

export async function listFormats(): Promise<Formats> {
  const res = await fetch(`${API_BASE_URL}/api/formats`);
  return json(res, "Loading formats");
}

/** Upload any document format the backend accepts (PDF, IDML, Word,
 * PowerPoint, Excel, text). Returns the new job id; the job runs in the
 * background. */
export async function startDocumentJob(file: File, targetLang: string, projectId?: string): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_lang", targetLang);
  if (projectId) form.append("project_id", projectId);
  const res = await fetch(`${API_BASE_URL}/api/translate`, { method: "POST", headers: await authHeaders(), body: form });
  const body = await json<{ job_id: string }>(res, "Upload");
  return body.job_id;
}

export type ImageConfig = {
  formats: { format: string; extensions: string[] }[] | unknown;
  max_bytes: number;
  ocr_available: boolean;
  stages: { key: string; label: string }[];
};

export async function getImageConfig(): Promise<ImageConfig> {
  const res = await fetch(`${API_BASE_URL}/api/image-translation/config`);
  return json(res, "Loading image settings");
}

export async function startImageJob(file: File, targetLang: string, projectId?: string): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  form.append("target_lang", targetLang);
  if (projectId) form.append("project_id", projectId);
  const res = await fetch(`${API_BASE_URL}/api/image-translation`, {
    method: "POST", headers: await authHeaders(), body: form,
  });
  const body = await json<{ job_id: string }>(res, "Upload");
  return body.job_id;
}

export type ImageJob = {
  job_id: string;
  status: string;
  error: string | null;
  stage: string | null;
  failed_stage: string | null;
  stage_progress: Record<string, number>;
  original_filename: string | null;
  target_language: string | null;
  report?: { warnings?: { message: string }[]; output_format?: string };
};

export async function getImageJob(jobId: string): Promise<ImageJob> {
  const res = await fetch(`${API_BASE_URL}/api/image-translation/${jobId}`, { headers: await authHeaders() });
  return json(res, "Loading the image job");
}

/** A protected file as an object URL the page can show or save. */
export async function authedBlobUrl(url: string): Promise<string> {
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`File not available (${res.status})`);
  return URL.createObjectURL(await res.blob());
}

export function imageFileUrl(jobId: string, which: "source" | "result", download = false): string {
  return `${API_BASE_URL}/api/image-translation/${jobId}/${which}${download ? "?download=true" : ""}`;
}

export async function startWebsiteJob(url: string, targetLang: string, projectId?: string): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/api/translate/website`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ url, target_lang: targetLang, project_id: projectId ?? "" }),
  });
  const body = await json<{ job_id: string }>(res, "Website translation");
  return body.job_id;
}

/** The translated (or original) page as HTML text, for a sandboxed frame. */
export async function getWebsiteHtml(jobId: string, which: "result" | "source"): Promise<string> {
  const res = await fetch(`${API_BASE_URL}/api/translate/website/${jobId}/${which}`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Page not available (${res.status})`);
  return res.text();
}

export async function translateText(texts: string[], targetLang: string): Promise<{ translations: string[]; direction: string }> {
  const res = await fetch(`${API_BASE_URL}/api/translate/text`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ texts, target_lang: targetLang }),
  });
  return json(res, "Translation");
}

export type Glossary = { code: string; name: string; terms: { source: string; target: string }[] };

export async function listGlossaries(): Promise<Glossary[]> {
  const res = await fetch(`${API_BASE_URL}/api/glossary`, { headers: await authHeaders() });
  return (await json<{ glossaries: Glossary[] }>(res, "Loading glossaries")).glossaries;
}

/** What a job is, in a word the UI can show. */
export function jobKind(job: JobRow): string {
  const f = job.meta?.format ?? "";
  if (job.job_type === "links") return "Links";
  if (f === "image") return "Image";
  if (f === "website") return "Website";
  if (["docx", "pptx", "xlsx", "txt"].includes(f)) return "Office";
  return "Document";
}
