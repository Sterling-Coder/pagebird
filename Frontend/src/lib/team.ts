import { API_BASE_URL } from "./translate";
import { authHeaders } from "@/lib/supabase/authFetch";

export type Me = {
  id: string;
  email: string | null;
  created_at: string | null;
  trial_ends_at: string | null;
};

export type TeamMember = {
  member_id: string;
  email: string;
  created_at: number;
};

export type TeamInfo = {
  members: TeamMember[];
  owner: { owner_id: string; email: string; created_at: number } | null;
};

export async function getMe(): Promise<Me> {
  const res = await fetch(`${API_BASE_URL}/api/me`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load account (${res.status})`);
  return res.json();
}

export async function getTeam(): Promise<TeamInfo> {
  const res = await fetch(`${API_BASE_URL}/api/team`, { headers: await authHeaders() });
  if (!res.ok) throw new Error(`Failed to load team (${res.status})`);
  return res.json();
}

export async function inviteTeamMember(email: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/team/invite`, {
    method: "POST",
    headers: { "Content-Type": "application/json", ...(await authHeaders()) },
    body: JSON.stringify({ email }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Invite failed (${res.status})`);
  }
}

export async function removeTeamMember(memberId: string): Promise<void> {
  const res = await fetch(`${API_BASE_URL}/api/team/${memberId}`, {
    method: "DELETE",
    headers: await authHeaders(),
  });
  if (!res.ok) throw new Error(`Failed to remove member (${res.status})`);
}
