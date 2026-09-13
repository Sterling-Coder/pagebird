import { API_BASE_URL } from "./translate";
import { authHeaders } from "./supabase/authFetch";

export type LogLine = {
  id: number;
  level: string;
  logger: string;
  line: string;
};

export async function getLogs(since = 0): Promise<LogLine[]> {
  const url = new URL(`${API_BASE_URL}/api/logs`);
  url.searchParams.set("since", String(since));
  // /api/logs now scopes lines to the caller's own activity (see backend
  // api.py) — needs auth to know who's asking, same as every other job route.
  const res = await fetch(url, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load logs (${res.status})`);
  const body = await res.json();
  return body.lines;
}
