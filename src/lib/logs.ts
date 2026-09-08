import { API_BASE_URL } from "./translate";

export type LogLine = {
  id: number;
  level: string;
  logger: string;
  line: string;
};

export async function getLogs(since = 0): Promise<LogLine[]> {
  const url = new URL(`${API_BASE_URL}/api/logs`);
  url.searchParams.set("since", String(since));
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Failed to load logs (${res.status})`);
  const body = await res.json();
  return body.lines;
}
