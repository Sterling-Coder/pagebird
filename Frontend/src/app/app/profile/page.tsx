"use client";

import { useEffect, useMemo, useRef, useState, useSyncExternalStore, type ChangeEvent, type FormEvent, type ReactNode } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AppTopBar } from "@/components/app/AppTopBar";
import { Avatar } from "@/components/app/Avatar";
import { ICON, PageHeader, PrimaryButton } from "@/components/app/ui";
import { createClient } from "@/lib/supabase/client";
import { AVATAR_MAX_BYTES, AVATAR_TYPES, deleteAvatar, getMe, updateMe, uploadAvatar, type Me } from "@/lib/team";
import { listJobs, type JobRow } from "@/lib/agents";
import { listLanguages, type Language } from "@/lib/translate";
import { languageName } from "@/lib/languageNames";
import {
  DEFAULT_LANG_KEY,
  PREFS_KEY,
  desktopPermission,
  parsePrefs,
  readRaw,
  requestDesktopPermission,
  setDefaultLang,
  setPrefs,
  subscribeLocal,
  type NotifyPrefs,
} from "@/lib/notifications";

const DAY = 86_400_000;
const WEEK_SEC = 7 * 86400;

/** A localStorage value that re-renders on change and is null during SSR. */
function useLocal(key: string): string | null {
  return useSyncExternalStore(subscribeLocal, () => readRaw(key), () => null);
}

const inputCls =
  "w-full rounded-xl border border-[var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2 text-[13px] text-[var(--app-ink)] outline-none transition-colors focus:border-[var(--app-accent)] disabled:opacity-60";
const ghostBtn =
  "rounded-full border border-[var(--app-border)] bg-[var(--app-surface)] px-4 py-2 text-[12.5px] font-medium text-[var(--app-ink-soft)] transition-colors hover:border-[var(--app-ink-soft)] hover:text-[var(--app-ink)] disabled:opacity-40";

const SECTIONS = [
  { id: "account", label: "Account" },
  { id: "plan", label: "Plan" },
  { id: "preferences", label: "Preferences" },
  { id: "usage", label: "Usage" },
  { id: "security", label: "Security" },
] as const;

/** One settings group: a heading over a bordered list of rows. */
function Section({ id, title, desc, children }: { id: string; title: string; desc?: string; children: ReactNode }) {
  return (
    <section id={id} aria-labelledby={`${id}-title`} className="scroll-mt-4">
      <div className="mb-2 px-1">
        <h2 id={`${id}-title`} className="text-[14px] font-semibold text-[var(--app-ink)]">{title}</h2>
        {desc ? <p className="text-[12.5px] text-[var(--app-muted)]">{desc}</p> : null}
      </div>
      <div className="divide-y divide-[var(--app-border)] rounded-2xl border border-[var(--app-border)]">{children}</div>
    </section>
  );
}

/** Label and hint on the left, the control on the right; stacks on phones. */
function Row({ label, hint, htmlFor, children }: { label: string; hint?: ReactNode; htmlFor?: string; children?: ReactNode }) {
  return (
    <div className="flex flex-col gap-3 px-5 py-4 sm:flex-row sm:items-center sm:justify-between">
      <div className="min-w-0">
        {htmlFor ? (
          <label htmlFor={htmlFor} className="block text-[13px] text-[var(--app-ink)]">{label}</label>
        ) : (
          <p className="text-[13px] text-[var(--app-ink)]">{label}</p>
        )}
        {hint ? <div className="text-[12px] text-[var(--app-muted)]">{hint}</div> : null}
      </div>
      {children ? <div className="flex shrink-0 flex-wrap items-center gap-2">{children}</div> : null}
    </div>
  );
}

function Toggle({ id, label, hint, checked, onChange }: {
  id: string; label: string; hint: string; checked: boolean; onChange: (v: boolean) => void;
}) {
  return (
    <div className="flex items-center justify-between gap-4 px-5 py-4">
      <div className="min-w-0">
        <label htmlFor={id} className="block text-[13px] text-[var(--app-ink)]">{label}</label>
        <p id={`${id}-hint`} className="text-[12px] text-[var(--app-muted)]">{hint}</p>
      </div>
      <button
        id={id}
        type="button"
        role="switch"
        aria-checked={checked}
        aria-describedby={`${id}-hint`}
        onClick={() => onChange(!checked)}
        className={`relative h-6 w-10 shrink-0 rounded-full transition-colors focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent)] ${
          checked ? "bg-[var(--app-accent)]" : "bg-[var(--app-border)]"
        }`}
      >
        <span
          className={`absolute top-0.5 left-0.5 h-5 w-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-4" : ""
          }`}
        />
      </button>
    </div>
  );
}

function Stat({ label, value }: { label: string; value: number | string }) {
  return (
    <div className="rounded-xl bg-[var(--app-surface-2)] px-4 py-3">
      <div className="text-[20px] font-semibold text-[var(--app-ink)] tabular-nums">{value}</div>
      <div className="text-[12px] text-[var(--app-muted)]">{label}</div>
    </div>
  );
}

function Alert({ tone, children }: { tone: "ok" | "error"; children: ReactNode }) {
  return (
    <p role={tone === "error" ? "alert" : "status"}
      className={`text-[12.5px] ${tone === "error" ? "text-[var(--app-danger)]" : "text-[var(--app-ink-soft)]"}`}>
      {children}
    </p>
  );
}

export default function ProfilePage() {
  const router = useRouter();
  const [me, setMe] = useState<Me | null>(null);
  const [meError, setMeError] = useState<string | null>(null);
  const [jobs, setJobs] = useState<JobRow[] | null>(null);
  const [jobsError, setJobsError] = useState<string | null>(null);
  const [langs, setLangs] = useState<Language[] | null>(null);
  const [now] = useState(() => Date.now());

  // Identity form
  const [first, setFirst] = useState("");
  const [last, setLast] = useState("");
  const [saving, setSaving] = useState(false);
  const [saveMsg, setSaveMsg] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  // Photo
  const fileRef = useRef<HTMLInputElement>(null);
  const [photoBusy, setPhotoBusy] = useState<"uploading" | "removing" | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [photoMsg, setPhotoMsg] = useState<{ tone: "ok" | "error"; text: string } | null>(null);

  // Security
  const [resetState, setResetState] = useState<"idle" | "sending" | "sent" | "error">("idle");
  const [resetError, setResetError] = useState<string | null>(null);
  const [signingOut, setSigningOut] = useState(false);

  // Preferences (localStorage-backed)
  const defaultLang = useLocal(DEFAULT_LANG_KEY) ?? "";
  const prefsRaw = useLocal(PREFS_KEY);
  const prefs = useMemo(() => parsePrefs(prefsRaw), [prefsRaw]);
  const permSnapshot = useSyncExternalStore(subscribeLocal, desktopPermission, () => "unsupported" as const);
  const [permOverride, setPermOverride] = useState<NotificationPermission | "unsupported" | null>(null);
  const permission = permOverride ?? permSnapshot;

  useEffect(() => {
    getMe()
      .then((m) => {
        setMe(m);
        setFirst(m.first_name ?? "");
        setLast(m.last_name ?? "");
      })
      .catch((e: unknown) => setMeError(e instanceof Error ? e.message : "Could not load your account."));
    listJobs()
      .then(setJobs)
      .catch((e: unknown) => setJobsError(e instanceof Error ? e.message : "Could not load usage."));
    listLanguages()
      .then((r) => setLangs(r.languages))
      .catch(() => setLangs([]));
  }, []);

  const displayName = me?.full_name || [me?.first_name, me?.last_name].filter(Boolean).join(" ") || null;
  const dirty = me !== null && (first.trim() !== (me.first_name ?? "") || last.trim() !== (me.last_name ?? ""));

  async function saveName(e: FormEvent) {
    e.preventDefault();
    if (!me) return;
    setSaving(true);
    setSaveMsg(null);
    try {
      // The server writes the profile row (what /api/me reads) and the auth metadata together.
      const saved = await updateMe({ first_name: first.trim(), last_name: last.trim() });
      setMe((prev) => ({ ...(prev ?? saved), ...saved }));
      setFirst(saved.first_name ?? "");
      setLast(saved.last_name ?? "");
      setSaveMsg({ tone: "ok", text: saved.full_name ? `Saved. You appear as ${saved.full_name}.` : "Saved." });
    } catch (err) {
      setSaveMsg({ tone: "error", text: err instanceof Error ? err.message : "Could not save your name." });
    } finally {
      setSaving(false);
    }
  }

  async function onPhotoPicked(e: ChangeEvent<HTMLInputElement>) {
    const file = e.target.files?.[0];
    e.target.value = ""; // let the same file be picked again after an error
    if (!file) return;
    setPhotoMsg(null);
    if (!AVATAR_TYPES.includes(file.type)) {
      setPhotoMsg({ tone: "error", text: "Use a PNG, JPG, WebP or GIF image." });
      return;
    }
    if (file.size > AVATAR_MAX_BYTES) {
      setPhotoMsg({ tone: "error", text: `That image is ${(file.size / 1048576).toFixed(1)} MB. The limit is 2 MB.` });
      return;
    }
    const preview = URL.createObjectURL(file);
    setPhotoPreview(preview);
    setPhotoBusy("uploading");
    try {
      const avatar_url = await uploadAvatar(file);
      setMe((prev) => (prev ? { ...prev, avatar_url } : prev));
      setPhotoMsg({ tone: "ok", text: "Photo updated." });
    } catch (err) {
      setPhotoMsg({ tone: "error", text: err instanceof Error ? err.message : "Upload failed." });
    } finally {
      URL.revokeObjectURL(preview);
      setPhotoPreview(null);
      setPhotoBusy(null);
    }
  }

  async function removePhoto() {
    setPhotoMsg(null);
    setPhotoBusy("removing");
    try {
      await deleteAvatar();
      setMe((prev) => (prev ? { ...prev, avatar_url: null } : prev));
      setPhotoMsg({ tone: "ok", text: "Photo removed." });
    } catch (err) {
      setPhotoMsg({ tone: "error", text: err instanceof Error ? err.message : "Could not remove the photo." });
    } finally {
      setPhotoBusy(null);
    }
  }

  async function sendReset() {
    if (!me?.email) return;
    setResetState("sending");
    setResetError(null);
    try {
      const { error } = await createClient().auth.resetPasswordForEmail(me.email, {
        // PKCE: /auth/callback exchanges the code, then the set-password page takes over.
        redirectTo: `${window.location.origin}/auth/callback?next=/auth/set-password`,
      });
      if (error) throw error;
      setResetState("sent");
    } catch (err) {
      setResetState("error");
      setResetError(err instanceof Error ? err.message : "Could not send the email.");
    }
  }

  async function signOut() {
    setSigningOut(true);
    await createClient().auth.signOut();
    router.push("/login");
    router.refresh();
  }

  function updatePrefs(patch: Partial<NotifyPrefs>) {
    setPrefs({ ...prefs, ...patch });
  }

  async function enableDesktop() {
    setPermOverride(await requestDesktopPermission());
  }

  // Plan
  const trialEnd = me?.trial_ends_at ? new Date(me.trial_ends_at).getTime() : null;
  const trialStart = me?.created_at ? new Date(me.created_at).getTime() : null;
  const daysLeft = trialEnd !== null ? Math.ceil((trialEnd - now) / DAY) : null;
  const trialPct =
    trialEnd !== null && trialStart !== null && trialEnd > trialStart
      ? Math.min(100, Math.max(0, ((now - trialStart) / (trialEnd - trialStart)) * 100))
      : null;

  // Usage
  const usage = useMemo(() => {
    if (!jobs) return null;
    const nowSec = now / 1000;
    const counts = new Map<string, number>();
    for (const j of jobs) {
      const code = j.meta?.target_language ?? j.meta?.target_lang;
      if (code) counts.set(code, (counts.get(code) ?? 0) + 1);
    }
    const top = [...counts.entries()].sort((a, b) => b[1] - a[1]).slice(0, 5);
    return {
      total: jobs.length,
      delivered: jobs.filter((j) => j.status === "complete").length,
      failed: jobs.filter((j) => j.status === "failed").length,
      week: jobs.filter((j) => nowSec - j.created_at < WEEK_SEC).length,
      top,
      topMax: top[0]?.[1] ?? 1,
    };
  }, [jobs, now]);

  const langLabel = (code: string) => langs?.find((l) => l.code === code)?.name ?? languageName(code) ?? code;

  const planLabel =
    daysLeft === null ? "Free trial" : daysLeft > 0 ? `Free trial · ${daysLeft} day${daysLeft === 1 ? "" : "s"} left` : "Trial ended";
  const memberSince = me?.created_at
    ? new Date(me.created_at).toLocaleDateString(undefined, { year: "numeric", month: "long", day: "numeric" })
    : null;
  const photoUrl = photoPreview ?? me?.avatar_url ?? null;

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.user} title="Profile" desc="Your account, plan, preferences and usage." />
      <div className="min-h-0 flex-1 overflow-auto px-4 pb-12 sm:px-6">
        <div className="mx-auto flex max-w-[920px] flex-col gap-6">
          {meError ? (
            <div role="alert" className="rounded-2xl border border-[var(--app-border)] px-5 py-4 text-[13px] text-[var(--app-ink-soft)]">
              {meError}{" "}
              <button type="button" className="text-[var(--app-accent)] underline" onClick={() => location.reload()}>
                Try again
              </button>
            </div>
          ) : null}

          {/* Summary (hidden when the account failed to load; the alert above explains) */}
          <div className={`flex-col gap-4 rounded-2xl bg-[var(--app-surface-2)] p-5 sm:flex-row sm:items-center ${meError && !me ? "hidden" : "flex"}`}>
            {me === null && !meError ? (
              <div className="flex animate-pulse items-center gap-4" role="status" aria-label="Loading profile">
                <div className="h-16 w-16 rounded-full bg-[var(--app-surface-3)]" />
                <div className="space-y-2">
                  <div className="h-3 w-40 rounded bg-[var(--app-surface-3)]" />
                  <div className="h-3 w-56 rounded bg-[var(--app-surface-3)]" />
                </div>
              </div>
            ) : me ? (
              <>
                <button type="button" onClick={() => fileRef.current?.click()} disabled={photoBusy !== null}
                  aria-label={me.avatar_url ? "Change profile photo" : "Add profile photo"}
                  className="group relative self-start rounded-full focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent)] sm:self-center">
                  <Avatar url={photoUrl} name={displayName || me.email || "?"} seed={me.email ?? undefined} size={64} />
                  <span className={`absolute inset-0 flex items-center justify-center rounded-full bg-black/45 text-[11px] font-medium text-white transition-opacity ${
                    photoBusy ? "opacity-100" : "opacity-0 group-hover:opacity-100"}`}>
                    {photoBusy === "uploading" ? "Uploading…" : photoBusy === "removing" ? "Removing…" : "Change"}
                  </span>
                </button>
                <div className="min-w-0 flex-1">
                  <p className="truncate text-[17px] font-semibold text-[var(--app-ink)]">{displayName || "Add your name"}</p>
                  <p className="truncate text-[12.5px] text-[var(--app-muted)]">{me.email}</p>
                  <div className="mt-2 flex flex-wrap gap-1.5 text-[11.5px]">
                    <span className={`rounded-full px-2.5 py-0.5 font-medium ${
                      daysLeft !== null && daysLeft <= 0
                        ? "bg-[var(--app-danger-bg)] text-[var(--app-danger)]"
                        : daysLeft !== null && daysLeft <= 3
                          ? "bg-[var(--app-warn-bg)] text-[var(--app-warn)]"
                          : "bg-[var(--app-surface)] text-[var(--app-ink-soft)]"}`}>
                      {planLabel}
                    </span>
                    {memberSince ? (
                      <span className="rounded-full bg-[var(--app-surface)] px-2.5 py-0.5 text-[var(--app-ink-soft)]">Member since {memberSince}</span>
                    ) : null}
                  </div>
                </div>
                <Link href="/pricing"
                  className="self-start rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90 sm:self-center">
                  {daysLeft !== null && daysLeft <= 0 ? "Choose a plan" : "See plans"}
                </Link>
              </>
            ) : null}
          </div>

          <div className="grid gap-8 md:grid-cols-[160px_minmax(0,1fr)]">
            <nav aria-label="Profile sections" className="hidden md:block">
              <ul className="sticky top-2 flex flex-col gap-0.5">
                {SECTIONS.map((sec) => (
                  <li key={sec.id}>
                    <a href={`#${sec.id}`}
                      className="block rounded-lg px-3 py-1.5 text-[13px] text-[var(--app-nav-ink)] transition-colors hover:bg-[var(--app-surface-2)] hover:text-[var(--app-ink)]">
                      {sec.label}
                    </a>
                  </li>
                ))}
              </ul>
            </nav>

            <div className="flex min-w-0 flex-col gap-8">
              <Section id="account" title="Account" desc="How you appear to teammates.">
                <Row label="Photo" hint="PNG, JPG, WebP or GIF, up to 2 MB.">
                  <input ref={fileRef} type="file" accept={AVATAR_TYPES.join(",")} className="sr-only"
                    onChange={onPhotoPicked} aria-label="Upload profile photo" tabIndex={-1} />
                  <button type="button" className={ghostBtn} disabled={!me || photoBusy !== null}
                    onClick={() => fileRef.current?.click()}>
                    {photoBusy === "uploading" ? "Uploading…" : me?.avatar_url ? "Change photo" : "Upload photo"}
                  </button>
                  {me?.avatar_url ? (
                    <button type="button" onClick={removePhoto} disabled={photoBusy !== null}
                      className="text-[12.5px] text-[var(--app-muted)] transition-colors hover:text-[var(--app-danger)] disabled:opacity-40">
                      {photoBusy === "removing" ? "Removing…" : "Remove"}
                    </button>
                  ) : null}
                </Row>
                {photoMsg ? <div className="px-5 py-3"><Alert tone={photoMsg.tone}>{photoMsg.text}</Alert></div> : null}

                <form onSubmit={saveName} className="flex flex-col gap-3 px-5 py-4">
                  <p className="text-[13px] text-[var(--app-ink)]">Name</p>
                  <div className="grid gap-3 sm:grid-cols-2">
                    <div>
                      <label htmlFor="first-name" className="mb-1 block text-[12px] text-[var(--app-muted)]">First name</label>
                      <input id="first-name" className={inputCls} value={first} autoComplete="given-name"
                        onChange={(e) => setFirst(e.target.value)} disabled={!me || saving} maxLength={80} />
                    </div>
                    <div>
                      <label htmlFor="last-name" className="mb-1 block text-[12px] text-[var(--app-muted)]">Last name</label>
                      <input id="last-name" className={inputCls} value={last} autoComplete="family-name"
                        onChange={(e) => setLast(e.target.value)} disabled={!me || saving} maxLength={80} />
                    </div>
                  </div>
                  <div className="flex flex-wrap items-center gap-3">
                    <PrimaryButton type="submit" disabled={!dirty || saving}>{saving ? "Saving…" : "Save name"}</PrimaryButton>
                    {dirty && !saving && me ? (
                      <button type="button" className="text-[12.5px] text-[var(--app-muted)] hover:text-[var(--app-ink)]"
                        onClick={() => { setFirst(me.first_name ?? ""); setLast(me.last_name ?? ""); }}>
                        Cancel
                      </button>
                    ) : null}
                    {saveMsg ? <Alert tone={saveMsg.tone}>{saveMsg.text}</Alert> : null}
                  </div>
                </form>

                <Row label="Email" hint="Used to sign in. Contact us to change it.">
                  <span className="text-[13px] text-[var(--app-ink-soft)]">{me?.email ?? "—"}</span>
                </Row>
              </Section>

              <Section id="plan" title="Plan">
                {me === null && !meError ? (
                  <p className="px-5 py-4 text-[13px] text-[var(--app-muted)]" role="status">Loading…</p>
                ) : (
                  <div className="flex flex-col gap-3 px-5 py-4">
                    <div className="flex flex-wrap items-baseline justify-between gap-2">
                      <p className="text-[13px] text-[var(--app-ink)]">
                        <span className="font-semibold">Free trial</span>
                        <span className="text-[var(--app-ink-soft)]">
                          {" · "}
                          {daysLeft === null
                            ? "No trial end date on file"
                            : daysLeft > 0
                              ? `${daysLeft} day${daysLeft === 1 ? "" : "s"} left`
                              : "Your trial has ended"}
                        </span>
                      </p>
                      {trialEnd !== null ? (
                        <span className="text-[12px] text-[var(--app-muted)]">
                          {daysLeft !== null && daysLeft > 0 ? "Ends" : "Ended"} {new Date(trialEnd).toLocaleDateString()}
                        </span>
                      ) : null}
                    </div>
                    {trialPct !== null ? (
                      <div className="h-2 overflow-hidden rounded-full bg-[var(--app-surface-2)]" role="progressbar"
                        aria-label="Trial used" aria-valuemin={0} aria-valuemax={100} aria-valuenow={Math.round(trialPct)}>
                        <div className="h-full rounded-full bg-[var(--app-accent)] transition-[width]" style={{ width: `${trialPct}%` }} />
                      </div>
                    ) : null}
                  </div>
                )}
              </Section>

              <Section id="preferences" title="Preferences" desc="Saved in this browser.">
                <Row label="Default target language" hint="Pre-selected when you start a translation." htmlFor="default-lang">
                  <select id="default-lang" value={defaultLang} onChange={(e) => setDefaultLang(e.target.value)}
                    className={`${inputCls} sm:w-[240px]`} disabled={langs === null}>
                    <option value="">{langs === null ? "Loading…" : "No default (ask each time)"}</option>
                    {defaultLang && langs !== null && !langs.some((l) => l.code === defaultLang) ? (
                      <option value={defaultLang}>{langLabel(defaultLang)}</option>
                    ) : null}
                    {(langs ?? []).map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
                  </select>
                </Row>
                <Toggle id="pref-finished" label="Job finished" hint="Notify me when a translation is delivered."
                  checked={prefs.jobFinished} onChange={(v) => updatePrefs({ jobFinished: v })} />
                <Toggle id="pref-failed" label="Job failed" hint="Notify me when a translation could not be completed."
                  checked={prefs.jobFailed} onChange={(v) => updatePrefs({ jobFailed: v })} />
                <Toggle id="pref-invites" label="Team invites" hint="Notify me when someone invites me to their workspace."
                  checked={prefs.teamInvites} onChange={(v) => updatePrefs({ teamInvites: v })} />
                <Row label="Desktop notifications" hint={
                  permission === "granted"
                    ? "On. You'll get a system notification when a job finishes while Pagebirdy is open."
                    : permission === "denied"
                      ? "Blocked in your browser. Allow notifications for this site in the browser settings."
                      : permission === "unsupported"
                        ? "Not supported in this browser."
                        : "Get a system notification when a job finishes while Pagebirdy is open."
                }>
                  {permission === "default" ? (
                    <button type="button" onClick={enableDesktop} className={ghostBtn}>Turn on</button>
                  ) : null}
                </Row>
              </Section>

              <Section id="usage" title="Usage" desc="All translations in your account.">
                <div className="px-5 py-4">
                  {jobsError ? (
                    <p role="alert" className="text-[13px] text-[var(--app-ink-soft)]">{jobsError}</p>
                  ) : usage === null ? (
                    <p className="text-[13px] text-[var(--app-muted)]" role="status">Loading…</p>
                  ) : (
                    <>
                      <div className="grid grid-cols-2 gap-3 sm:grid-cols-4">
                        <Stat label="Total jobs" value={usage.total} />
                        <Stat label="Delivered" value={usage.delivered} />
                        <Stat label="Failed" value={usage.failed} />
                        <Stat label="This week" value={usage.week} />
                      </div>
                      <h3 className="mt-5 text-[12px] font-medium text-[var(--app-ink-soft)]">Top target languages</h3>
                      {usage.top.length === 0 ? (
                        <p className="mt-2 text-[12.5px] text-[var(--app-muted)]">
                          No translations yet. <Link href="/app" className="text-[var(--app-accent)] hover:underline">Start one</Link>.
                        </p>
                      ) : (
                        <ul className="mt-2 space-y-2">
                          {usage.top.map(([code, n]) => (
                            <li key={code} className="flex items-center gap-3 text-[12.5px]">
                              <span className="w-28 shrink-0 truncate text-[var(--app-ink)]">{langLabel(code)}</span>
                              <span className="h-1.5 flex-1 overflow-hidden rounded-full bg-[var(--app-surface-2)]" aria-hidden="true">
                                <span className="block h-full rounded-full bg-[var(--app-accent)]" style={{ width: `${(n / usage.topMax) * 100}%` }} />
                              </span>
                              <span className="w-8 shrink-0 text-right text-[var(--app-muted)] tabular-nums">{n}</span>
                            </li>
                          ))}
                        </ul>
                      )}
                    </>
                  )}
                </div>
              </Section>

              <Section id="security" title="Security">
                <Row label="Password" hint={`We'll email ${me?.email ?? "you"} a link to set a new password.`}>
                  <button type="button" onClick={sendReset} className={ghostBtn}
                    disabled={!me?.email || resetState === "sending" || resetState === "sent"}>
                    {resetState === "sending" ? "Sending…" : resetState === "sent" ? "Email sent" : "Send reset email"}
                  </button>
                </Row>
                {resetState === "sent" ? <div className="px-5 py-3"><Alert tone="ok">Check your inbox for the reset link.</Alert></div> : null}
                {resetState === "error" && resetError ? <div className="px-5 py-3"><Alert tone="error">{resetError}</Alert></div> : null}
                <Row label="Sign out" hint="End your session on this device.">
                  <button type="button" onClick={signOut} disabled={signingOut}
                    className="rounded-full border border-[var(--app-border)] px-4 py-2 text-[12.5px] font-medium text-[var(--app-danger)] transition-colors hover:border-[var(--app-danger)] disabled:opacity-40">
                    {signingOut ? "Signing out…" : "Sign out"}
                  </button>
                </Row>
              </Section>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
