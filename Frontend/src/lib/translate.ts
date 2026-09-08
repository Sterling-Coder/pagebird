import { authHeaders } from "@/lib/supabase/authFetch";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";

export type Language = {
  code: string;
  name: string;
  direction: "ltr" | "rtl";
  supported: boolean;
  note: string;
};

export type TranslateRequest = {
  file: File;
  targetLanguage: string; // language code, e.g. "es"
  projectId?: string;
  folderId?: string;
};

export type TranslateResult = {
  jobId: string;
  translatedFileName: string;
  pages: number | null;
  downloadUrl: string;
  previewUrl: string | null;
};

export type Segment = {
  seg_id: string;
  page: number; // 0-indexed, matches PyMuPDF page numbers
  bbox: [number, number, number, number];
  source_restored: string | null;
  target_restored: string | null;
  status?: string;
  notes?: string[];
  color?: number; // packed 0xRRGGBB, the segment's original PDF text colour
};

export type SegmentEvent = {
  seg_id: string;
  action: string;
  reviewer: string;
  old_target: string | null;
  new_target: string | null;
  created_at: number;
};

export async function getJobHistory(jobId: string): Promise<SegmentEvent[]> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/history`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to load history (${res.status})`);
  return res.json();
}

export type EvalReport = {
  overall?: {
    score: number | null;
    gates_passed: boolean;
    gates_failed: string[];
  };
  gates?: {
    passed: boolean;
    failed: string[];
    skipped: string[];
  };
  needs_human_count?: number;
};

export async function getJobEval(jobId: string, refresh = false): Promise<EvalReport> {
  const url = new URL(`${API_BASE_URL}/api/jobs/${jobId}/eval`);
  if (refresh) url.searchParams.set("refresh", "true");
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load eval (${res.status})`);
  return res.json();
}

export function evalDownloadUrl(jobId: string, format: "pdf" | "md" | "json" = "pdf"): string {
  return `${API_BASE_URL}/api/jobs/${jobId}/eval/download?format=${format}`;
}

export async function getSegments(jobId: string): Promise<Segment[]> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/segments`, {
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to load segments (${res.status})`);
  return res.json();
}

export async function updateSegment(
  jobId: string,
  segId: string,
  target: string,
  approve = true
): Promise<Segment> {
  const res = await fetch(`${API_BASE_URL}/api/segments/${jobId}/${segId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ target, approve }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to save edit (${res.status})`);
  }
  return res.json();
}

export async function rebuildJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}/rebuild`, {
    method: "POST",
    headers: await authHeaders(),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Rebuild failed (${res.status})`);
  }
}

export async function listLanguages(): Promise<{
  languages: Language[];
  default: string;
}> {
  const res = await fetch(`${API_BASE_URL}/api/languages`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load languages (${res.status})`);
  return res.json();
}

function jobToResult(job: {
  job_id?: string;
  id?: string;
  output?: string;
  original_filename?: string | null;
  format?: string;
  has_output_pdf?: boolean;
}): TranslateResult {
  const jobId = (job.job_id ?? job.id) as string;
  if (!jobId) throw new Error("Backend did not return a job id.");
  const format = job.format === "idml" ? "idml" : "pdf";
  return {
    jobId,
    translatedFileName: `${job.output ?? job.original_filename ?? jobId}`
      .split("/")
      .pop()!,
    pages: null,
    downloadUrl: `${API_BASE_URL}/api/jobs/${jobId}/download?format=${format}`,
    previewUrl:
      job.has_output_pdf ?? Boolean(job.output)
        ? `${API_BASE_URL}/api/jobs/${jobId}/output`
        : null,
  };
}

export async function getJob(jobId: string): Promise<TranslateResult> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load job (${res.status})`);
  const job = await res.json();
  return jobToResult({ ...job, id: jobId });
}

export async function deleteJob(jobId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/jobs/${jobId}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to delete file (${res.status})`);
}

export async function translateDocument(
  request: TranslateRequest
): Promise<TranslateResult> {
  const formData = new FormData();
  formData.append("file", request.file);
  formData.append("target_lang", request.targetLanguage);
  if (request.projectId) {
    formData.append("project_id", request.projectId);
  }
  if (request.folderId) {
    formData.append("folder_id", request.folderId);
  }

  const res = await fetch(`${API_BASE_URL}/api/translate`, {
    method: "POST",
    headers: await authHeaders(),
    body: formData,
  });

  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Translation failed (${res.status})`);
  }

  const report = await res.json();
  const result = jobToResult(report);
  return {
    ...result,
    pages: typeof report.pages === "number" ? report.pages : null,
  };
}
