import { createClient } from "./client";

async function getAccessToken(): Promise<string | null> {
  const supabase = createClient();
  const { data } = await supabase.auth.getSession();
  return data.session?.access_token ?? null;
}

/** Authorization header for fetch() calls to the FastAPI backend. */
export async function authHeaders(): Promise<Record<string, string>> {
  const token = await getAccessToken();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Fetches a protected file with the Authorization header and saves it via a
 * short-lived blob URL — used instead of putting the session token in the
 * URL (query-string tokens leak into browser history and server logs). */
export async function downloadAuthed(url: string, filename: string): Promise<void> {
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Download failed (${res.status})`);
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = blobUrl;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  URL.revokeObjectURL(blobUrl);
}
