"use client";

import { useEffect, useState } from "react";
import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";
import {
  acceptTeamInvite,
  declineTeamInvite,
  getTeam,
  inviteTeamMember,
  removeTeamMember,
  type TeamInfo,
} from "@/lib/team";

export default function TeamPage() {
  const [navOpen, setNavOpen] = useState(true);
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [email, setEmail] = useState("");
  const [inviting, setInviting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);

  function refresh() {
    return getTeam()
      .then(setTeam)
      .catch(() => setTeam({ members: [], pending_invitations: [], workspaces: [] }));
  }

  useEffect(() => {
    refresh();
  }, []);

  async function handleInvite(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setInviting(true);
    try {
      await inviteTeamMember(email);
      setEmail("");
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invite failed");
    } finally {
      setInviting(false);
    }
  }

  async function handleAccept(ownerId: string) {
    setBusyId(ownerId);
    try {
      await acceptTeamInvite(ownerId);
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  async function handleDecline(ownerId: string) {
    setBusyId(ownerId);
    try {
      await declineTeamInvite(ownerId);
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemove(otherUserId: string) {
    setBusyId(otherUserId);
    try {
      await removeTeamMember(otherUserId);
      await refresh();
    } finally {
      setBusyId(null);
    }
  }

  return (
    <div className="flex h-full w-full bg-paper">
      {navOpen ? <AppNavRail /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar navOpen={navOpen} onToggleNav={() => setNavOpen((v) => !v)} breadcrumb="Team" />
        <div className="flex min-h-0 flex-1 overflow-auto p-6">
          <div className="w-full max-w-xl">
            <h1 className="mb-1 text-lg font-bold text-ink">Team</h1>
            <p className="mb-6 text-sm text-muted">
              Invite people to work in your workspace — once they accept, they&rsquo;ll see
              and translate the same projects you do.
            </p>

            {team && team.pending_invitations.length > 0 ? (
              <div className="mb-6 flex flex-col gap-2">
                {team.pending_invitations.map((inv) => (
                  <div
                    key={inv.owner_id}
                    className="flex items-center justify-between border border-red bg-red-dim/40 px-4 py-3 text-sm"
                  >
                    <span className="text-ink">
                      <span className="font-semibold">{inv.email}</span> invited you to their
                      workspace.
                    </span>
                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => handleAccept(inv.owner_id)}
                        disabled={busyId === inv.owner_id}
                        className="bg-red px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90 disabled:opacity-40"
                      >
                        Accept
                      </button>
                      <button
                        type="button"
                        onClick={() => handleDecline(inv.owner_id)}
                        disabled={busyId === inv.owner_id}
                        className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 hover:decoration-ink disabled:opacity-40"
                      >
                        Decline
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            ) : null}

            {team && team.workspaces.length > 0 ? (
              <div className="mb-6 flex flex-col gap-2">
                {team.workspaces.map((w) => (
                  <div
                    key={w.owner_id}
                    className="flex items-center justify-between border border-rule bg-paper-dim px-4 py-3 text-sm"
                  >
                    <span className="text-ink-soft">
                      You&rsquo;re a member of <span className="font-semibold text-ink">{w.email}</span>&rsquo;s
                      workspace.
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemove(w.owner_id)}
                      disabled={busyId === w.owner_id}
                      className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 hover:decoration-ink disabled:opacity-40"
                    >
                      {busyId === w.owner_id ? "Leaving…" : "Leave"}
                    </button>
                  </div>
                ))}
              </div>
            ) : null}

            <form onSubmit={handleInvite} className="mb-8 flex items-end gap-3">
              <div className="flex-1">
                <label htmlFor="invite-email" className="font-mono text-[10px] uppercase tracking-widest text-muted">
                  Invite by email
                </label>
                <input
                  id="invite-email"
                  type="email"
                  required
                  placeholder="teammate@company.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="mt-2 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
                />
              </div>
              <button
                type="submit"
                disabled={inviting}
                className="h-9 shrink-0 bg-red px-5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-40"
              >
                {inviting ? "Inviting…" : "Invite"}
              </button>
            </form>

            {error ? (
              <p className="mb-6 text-xs text-red" role="alert">
                {error}
              </p>
            ) : null}

            <div className="border border-rule">
              <div className="border-b border-rule px-4 py-2.5 font-mono text-[11px] font-bold uppercase tracking-widest text-muted">
                People you&rsquo;ve invited
              </div>
              {!team || team.members.length === 0 ? (
                <p className="px-4 py-6 text-center text-sm text-muted">
                  No one invited yet.
                </p>
              ) : (
                team.members.map((m) => (
                  <div
                    key={m.member_id}
                    className="flex items-center justify-between border-b border-rule px-4 py-3 text-sm last:border-b-0"
                  >
                    <span className="text-ink">
                      {m.email}{" "}
                      {m.status === "pending" ? (
                        <span className="ml-1 font-mono text-[10px] uppercase tracking-widest text-muted">
                          pending
                        </span>
                      ) : null}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleRemove(m.member_id)}
                      disabled={busyId === m.member_id}
                      className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 hover:decoration-ink disabled:opacity-40"
                    >
                      {busyId === m.member_id ? "Removing…" : "Remove"}
                    </button>
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
