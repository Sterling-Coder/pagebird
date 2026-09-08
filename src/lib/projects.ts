import { API_BASE_URL } from "./translate";

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
  original_filename: string | null;
  created_at: number;
  project_id?: string | null;
  job_type?: string;
  folder_id?: string | null;
};

export type Folder = {
  id: string;
  project_id: string;
  name: string;
  parent_folder_id: string | null;
  created_at: number;
};

export async function createProject(input: {
  name: string;
  jobType: string;
  targetLanguage?: string;
  sourceLanguage?: string;
}): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
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
  const res = await fetch(`${API_BASE_URL}/api/projects`);
  if (!res.ok) throw new Error(`Failed to load projects (${res.status})`);
  return res.json();
}

export async function getProject(projectId: string): Promise<Project> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`);
  if (!res.ok) throw new Error(`Failed to load project (${res.status})`);
  return res.json();
}

export async function deleteProject(projectId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/projects/${projectId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete project (${res.status})`);
}

export async function listProjectFiles(
  projectId: string,
  folderId?: string
): Promise<JobSummary[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/files`);
  if (folderId) url.searchParams.set("folder_id", folderId);
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load files (${res.status})`);
  return res.json();
}

export async function listAllProjectFiles(projectId: string): Promise<JobSummary[]> {
  const url = new URL(`${API_BASE_URL}/api/projects/${projectId}/files`);
  url.searchParams.set("all", "true");
  const res = await fetch(url);
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
    headers: { "Content-Type": "application/json" },
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
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load folders (${res.status})`);
  return res.json();
}

export async function getFolder(folderId: string): Promise<Folder> {
  const res = await fetch(`${API_BASE_URL}/api/folders/${folderId}`);
  if (!res.ok) throw new Error(`Failed to load folder (${res.status})`);
  return res.json();
}

export async function deleteFolder(folderId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/folders/${folderId}`, {
    method: "DELETE",
  });
  if (!res.ok) throw new Error(`Failed to delete folder (${res.status})`);
}
