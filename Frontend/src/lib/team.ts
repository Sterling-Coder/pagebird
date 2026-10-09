import { API_BASE_URL } from "./translate";
import { authHeaders } from "@/lib/supabase/authFetch";

export type Me = {
  id: string;
  email: string | null;
  created_at: string | null;
  trial_ends_at: string | null;
  first_name: string | null;
  last_name: string | null;
  full_name: string | null;
  avatar_url?: string | null;
};

export type TeamMember = {
  member_id: string;
  email: string;
  status: "pending" | "accepted";
  created_at: string | number;
};

export type PendingInvitation = {
  owner_id: string;
  email: string;
  status: "pending";
  created_at: string | number;
};

export type Workspace = {
  owner_id: string;
  email: string;
  status: "accepted";
  created_at: string | number;
};

export type TeamInfo = {
  members: TeamMember[];
  pending_invitations: PendingInvitation[];
  workspaces: Workspace[];
};

async function post(path: string, body: unknown) {
  const res = await fetch(`${API_BASE_URL}${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Request failed"));
}

export async function getMe(): Promise<Me> {
  const res = await fetch(`${API_BASE_URL}/api/me`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load account (${res.status})`);
  return res.json();
}

/** Team rows carry Postgres timestamptz values (ISO strings); jobs use epoch
 * seconds. Normalise to epoch seconds so the two sort and compare together. */
export function epochSec(value: string | number | null | undefined): number {
  if (typeof value === "number") return value;
  const ms = value ? Date.parse(value) : NaN;
  return Number.isNaN(ms) ? 0 : ms / 1000;
}

/** Fired on window after the signed-in user's profile changes, so the sidebar
 * and other open views can refresh without a reload. */
export const ME_UPDATED_EVENT = "pb-me-updated";

function announceMe(me: Partial<Me>) {
  window.dispatchEvent(new CustomEvent(ME_UPDATED_EVENT, { detail: me }));
}

async function errorDetail(res: Response, fallback: string): Promise<string> {
  const body = await res.json().catch(() => null);
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail) && detail[0]?.msg) return String(detail[0].msg);
  return `${fallback} (${res.status})`;
}

export async function updateMe(names: { first_name: string; last_name: string }): Promise<Me> {
  const res = await fetch(`${API_BASE_URL}/api/me`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify(names),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Could not save your name"));
  const me: Me = await res.json();
  announceMe(me);
  return me;
}

export const AVATAR_MAX_BYTES = 2 * 1024 * 1024;
export const AVATAR_TYPES = ["image/png", "image/jpeg", "image/webp", "image/gif"];

export async function uploadAvatar(file: File): Promise<string> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE_URL}/api/me/avatar`, {
    method: "POST",
    headers: await authHeaders(),
    body: form,
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Upload failed"));
  const { avatar_url } = (await res.json()) as { avatar_url: string };
  announceMe({ avatar_url });
  return avatar_url;
}

export async function deleteAvatar(): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/me/avatar`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Could not remove the photo"));
  announceMe({ avatar_url: null });
}

export async function getTeam(): Promise<TeamInfo> {
  const res = await fetch(`${API_BASE_URL}/api/team`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load team (${res.status})`);
  return res.json();
}

export async function inviteTeamMember(email: string): Promise<void> {
  await post("/api/team/invite", { email });
}

export async function acceptTeamInvite(ownerId: string): Promise<void> {
  await post("/api/team/accept", { owner_id: ownerId });
}

export async function declineTeamInvite(ownerId: string): Promise<void> {
  await post("/api/team/decline", { owner_id: ownerId });
}

export async function removeTeamMember(otherUserId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/team/${otherUserId}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(await errorDetail(res, "Failed to remove"));
}
