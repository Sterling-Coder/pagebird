"use client";

import { useEffect, useState } from "react";
import { AppTopBar } from "@/components/app/AppTopBar";
import { Avatar } from "@/components/app/Avatar";
import { ICON, PageHeader } from "@/components/app/ui";
import {
  acceptTeamInvite,
  declineTeamInvite,
  epochSec,
  getMe,
  getTeam,
  inviteTeamMember,
  removeTeamMember,
  type Me,
  type TeamInfo,
} from "@/lib/team";

const inputCls =
  "w-full min-w-0 rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2 text-[13px] text-[var(--app-ink)] outline-none transition-colors placeholder:text-[var(--app-muted)] focus:border-[var(--app-accent)]";
const primaryBtn =
  "shrink-0 rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40";
const ghostBtn =
  "shrink-0 rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-4 py-2 text-[12.5px] font-medium text-[var(--app-ink-soft)] transition-colors hover:border-[var(--app-ink-soft)] hover:text-[var(--app-ink)] disabled:opacity-40";
const linkBtn =
  "text-[12px] text-[var(--app-muted)] underline-offset-4 transition-colors hover:text-[var(--app-ink)] hover:underline disabled:opacity-40";

function RolePill({ kind }: { kind: "owner" | "joined" | "pending" }) {
  const style =
    kind === "joined"
      ? { color: "var(--app-success)", background: "var(--app-success-bg)", label: "Joined" }
      : kind === "pending"
        ? { color: "var(--app-warn)", background: "var(--app-warn-bg)", label: "Invite sent" }
        : { color: "var(--app-ink-soft)", background: "var(--app-neutral-bg)", label: "Owner" };
  return (
    <span className="inline-block rounded-full px-2 py-0.5 text-[11px] font-medium" style={{ color: style.color, background: style.background }}>
      {style.label}
    </span>
  );
}

function formatDate(value: number | string | null | undefined): string {
  const sec = epochSec(value);
  return sec ? new Date(sec * 1000).toLocaleDateString(undefined, { month: "short", day: "numeric", year: "numeric" }) : "—";
}

export default function TeamPage() {
  const [team, setTeam] = useState<TeamInfo | null>(null);
  const [me, setMe] = useState<Me | null>(null);
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
    getMe().then(setMe).catch(() => setMe(null));
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
    setError(null);
    try {
      await acceptTeamInvite(ownerId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not accept the invitation");
    } finally {
      setBusyId(null);
    }
  }

  async function handleDecline(ownerId: string) {
    setBusyId(ownerId);
    setError(null);
    try {
      await declineTeamInvite(ownerId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not decline the invitation");
    } finally {
      setBusyId(null);
    }
  }

  async function handleRemove(otherUserId: string) {
    setBusyId(otherUserId);
    setError(null);
    try {
      await removeTeamMember(otherUserId);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not update the team");
    } finally {
      setBusyId(null);
    }
  }

  const members = team?.members ?? [];
  const thClass = "px-4 py-2.5 text-left text-[11.5px] font-medium text-[var(--app-muted)]";
  const tdClass = "px-4 py-3 align-middle";

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader
        icon={ICON.team}
        title="Team"
        count={team ? members.length + 1 : undefined}
        desc="People who share your projects."
      />
      <div className="min-h-0 flex-1 overflow-auto px-4 pb-10 sm:px-6">
        <div className="mx-auto flex max-w-[680px] flex-col gap-4">
          {team?.pending_invitations.map((inv) => (
            <div
              key={inv.owner_id}
              className="flex flex-wrap items-center gap-3 rounded-2xl bg-[var(--app-warn-bg)] px-4 py-3 text-[13px]"
            >
              <span className="min-w-0 flex-1 text-[var(--app-ink)]">
                <span className="font-semibold">{inv.email}</span> invited you to their workspace.
              </span>
              <button
                type="button"
                onClick={() => handleAccept(inv.owner_id)}
                disabled={busyId === inv.owner_id}
                className={primaryBtn}
              >
                Accept
              </button>
              <button
                type="button"
                onClick={() => handleDecline(inv.owner_id)}
                disabled={busyId === inv.owner_id}
                className={ghostBtn}
              >
                Decline
              </button>
            </div>
          ))}

          <form onSubmit={handleInvite} className="flex items-center gap-2">
            <label htmlFor="invite-email" className="sr-only">
              Invite by email
            </label>
            <input
              id="invite-email"
              type="email"
              required
              placeholder="teammate@company.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={inputCls}
            />
            <button type="submit" disabled={inviting} className={primaryBtn}>
              {inviting ? "Inviting…" : "Invite"}
            </button>
          </form>

          {error ? (
            <p className="text-[12.5px] text-[var(--app-danger)]" role="alert">
              {error}
            </p>
          ) : null}

          <div className="overflow-x-auto rounded-2xl border border-[var(--app-border)]">
            <table className="w-full border-collapse text-[13px] tabular-nums">
              <thead>
                <tr className="border-b border-[var(--app-border)]">
                  <th scope="col" className={thClass}>Person</th>
                  <th scope="col" className={thClass}>Status</th>
                  <th scope="col" className={thClass}>Added</th>
                  <th scope="col" className={thClass}><span className="sr-only">Actions</span></th>
                </tr>
              </thead>
              <tbody>
                <tr className="border-b border-[var(--app-border)] last:border-b-0">
                  <td className={tdClass}>
                    <span className="flex items-center gap-2.5">
                      <Avatar url={me?.avatar_url} name={me?.full_name || me?.email || "?"} seed={me?.email ?? undefined} />
                      <span className="truncate text-[var(--app-ink)]">
                        {me?.email ?? "You"} <span className="text-[var(--app-muted)]">(you)</span>
                      </span>
                    </span>
                  </td>
                  <td className={tdClass}><RolePill kind="owner" /></td>
                  <td className={`${tdClass} whitespace-nowrap text-[var(--app-muted)]`}>{formatDate(me?.created_at)}</td>
                  <td className={tdClass} />
                </tr>
                {members.map((m) => {
                  const pending = m.status === "pending";
                  const busy = busyId === m.member_id;
                  return (
                    <tr key={m.member_id} className="border-b border-[var(--app-border)] last:border-b-0">
                      <td className={tdClass}>
                        <span className="flex items-center gap-2.5">
                          <Avatar name={m.email} seed={m.email} pending={pending} />
                          <span className="truncate text-[var(--app-ink)]">{m.email}</span>
                        </span>
                      </td>
                      <td className={tdClass}><RolePill kind={pending ? "pending" : "joined"} /></td>
                      <td className={`${tdClass} whitespace-nowrap text-[var(--app-muted)]`}>{formatDate(m.created_at)}</td>
                      <td className={`${tdClass} text-right`}>
                        <button
                          type="button"
                          onClick={() => handleRemove(m.member_id)}
                          disabled={busy}
                          className={linkBtn}
                        >
                          {busy ? (pending ? "Cancelling…" : "Removing…") : pending ? "Cancel invite" : "Remove"}
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
            {team && members.length === 0 ? (
              <p className="border-t border-[var(--app-border)] px-4 py-5 text-center text-[12.5px] text-[var(--app-muted)]">
                No teammates yet. Invite someone above and they&rsquo;ll see the same projects you do.
              </p>
            ) : null}
          </div>

          {team?.workspaces.map((w) => (
            <p key={w.owner_id} className="text-[12.5px] text-[var(--app-muted)]">
              You&rsquo;re also a member of <span className="font-semibold text-[var(--app-ink)]">{w.email}</span>&rsquo;s
              workspace.{" "}
              <button
                type="button"
                onClick={() => handleRemove(w.owner_id)}
                disabled={busyId === w.owner_id}
                className="underline underline-offset-4 transition-colors hover:text-[var(--app-ink)] disabled:opacity-40"
              >
                {busyId === w.owner_id ? "Leaving…" : "Leave"}
              </button>
            </p>
          ))}
        </div>
      </div>
    </div>
  );
}
