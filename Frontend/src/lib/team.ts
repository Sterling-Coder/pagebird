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
  status: "pending" | "accepted";
  created_at: number;
};

export type PendingInvitation = {
  owner_id: string;
  email: string;
  status: "pending";
  created_at: number;
};

export type Workspace = {
  owner_id: string;
  email: string;
  status: "accepted";
  created_at: number;
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
  if (!res.ok) {
    const errBody = await res.json().catch(() => null);
    throw new Error(errBody?.detail ?? `Request failed (${res.status})`);
  }
}

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
  if (!res.ok) throw new Error(`Failed to remove (${res.status})`);
}
