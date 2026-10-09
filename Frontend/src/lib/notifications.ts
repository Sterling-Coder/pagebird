/**
 * In-app notifications, derived on the client from the job list and team
 * invitations. Nothing is stored server-side: read state is one
 * "last seen" timestamp in localStorage, and which kinds show up is a
 * per-browser preference set on the Profile page.
 */
import { listJobs, type JobRow } from "@/lib/agents";
import { epochSec, getTeam } from "@/lib/team";
import { languageName } from "@/lib/languageNames";

export const PREFS_KEY = "pb-notify-prefs";
export const SEEN_KEY = "pb-notify-seen";
export const DEFAULT_LANG_KEY = "pb-default-lang";
/** Fired on window whenever prefs or read state change in this tab. */
export const NOTIFY_EVENT = "pb-notify-change";

export type NotifyPrefs = { jobFinished: boolean; jobFailed: boolean; teamInvites: boolean };
export const DEFAULT_PREFS: NotifyPrefs = { jobFinished: true, jobFailed: true, teamInvites: true };

export type Notification = {
  id: string;
  kind: "job-finished" | "job-failed" | "invite";
  title: string;
  detail: string;
  /** Epoch seconds. */
  at: number;
  href: string;
  unread: boolean;
};

/** Only look this far back, so a long job history does not flood the bell. */
const WINDOW_SEC = 14 * 86400;

function readJSON<T>(key: string): T | null {
  try {
    const raw = window.localStorage.getItem(key);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

function write(key: string, value: string) {
  try {
    window.localStorage.setItem(key, value);
  } catch {
    /* storage blocked: preferences just don't persist */
  }
  window.dispatchEvent(new Event(NOTIFY_EVENT));
}

export function getPrefs(): NotifyPrefs {
  return parsePrefs(readRaw(PREFS_KEY));
}

export function setPrefs(prefs: NotifyPrefs) {
  write(PREFS_KEY, JSON.stringify(prefs));
}

/** Epoch seconds of the last "mark all as read" (0 if never). */
export function getSeen(): number {
  const v = readJSON<number>(SEEN_KEY);
  return typeof v === "number" && Number.isFinite(v) ? v : 0;
}

export function markAllRead(at: number = Date.now() / 1000) {
  write(SEEN_KEY, JSON.stringify(Math.ceil(at)));
}

export function getDefaultLang(): string {
  try {
    return window.localStorage.getItem(DEFAULT_LANG_KEY) ?? "";
  } catch {
    return "";
  }
}

export function setDefaultLang(code: string) {
  try {
    if (code) window.localStorage.setItem(DEFAULT_LANG_KEY, code);
    else window.localStorage.removeItem(DEFAULT_LANG_KEY);
  } catch {
    /* ignore */
  }
  window.dispatchEvent(new Event(NOTIFY_EVENT));
}

/** Subscribe to local changes of prefs, read state or default language (this tab and others). */
export function subscribeLocal(onChange: () => void): () => void {
  window.addEventListener(NOTIFY_EVENT, onChange);
  window.addEventListener("storage", onChange);
  return () => {
    window.removeEventListener(NOTIFY_EVENT, onChange);
    window.removeEventListener("storage", onChange);
  };
}

/** Raw localStorage string (stable between calls, so safe as a useSyncExternalStore snapshot). */
export function readRaw(key: string): string | null {
  try {
    return window.localStorage.getItem(key);
  } catch {
    return null;
  }
}

export function parsePrefs(raw: string | null): NotifyPrefs {
  if (!raw) return DEFAULT_PREFS;
  try {
    return { ...DEFAULT_PREFS, ...(JSON.parse(raw) as Partial<NotifyPrefs>) };
  } catch {
    return DEFAULT_PREFS;
  }
}

export function jobHref(job: Pick<JobRow, "id" | "project_id">): string {
  return job.project_id ? `/app/jobs/${job.project_id}/files/${job.id}` : "/app/jobs";
}

/** Rough finish time: the API only has created_at plus an optional duration. */
function finishedAt(job: JobRow): number {
  return job.created_at + (job.duration_sec && job.duration_sec > 0 ? job.duration_sec : 0);
}

function jobName(job: JobRow): string {
  return job.original_filename || job.meta?.source_url || "Untitled file";
}

function targetOf(job: JobRow): string | null {
  return languageName(job.meta?.target_language ?? job.meta?.target_lang ?? null);
}

export type NotificationFeed = {
  items: Notification[];
  unread: number;
  /** The raw jobs, so callers can spot status transitions. */
  jobs: JobRow[];
};

/**
 * Fetch jobs and team, and turn them into notifications (newest first).
 * Throws only if both sources fail.
 */
export async function loadNotifications(): Promise<NotificationFeed> {
  const [jobsRes, teamRes] = await Promise.allSettled([listJobs(), getTeam()]);
  if (jobsRes.status === "rejected" && teamRes.status === "rejected") {
    throw jobsRes.reason instanceof Error ? jobsRes.reason : new Error("Could not load notifications");
  }
  const jobs = jobsRes.status === "fulfilled" ? jobsRes.value : [];
  const team = teamRes.status === "fulfilled" ? teamRes.value : null;
  const prefs = getPrefs();
  const seen = getSeen();
  const now = Date.now() / 1000;
  const items: Notification[] = [];

  for (const job of jobs) {
    const at = finishedAt(job);
    if (now - at > WINDOW_SEC) continue;
    const lang = targetOf(job);
    if (job.status === "complete" && prefs.jobFinished) {
      items.push({
        id: `job-${job.id}`, kind: "job-finished", at, href: jobHref(job), unread: at > seen,
        title: jobName(job),
        detail: lang ? `Translated into ${lang}` : "Translation delivered",
      });
    } else if (job.status === "failed" && prefs.jobFailed) {
      items.push({
        id: `job-${job.id}`, kind: "job-failed", at, href: jobHref(job), unread: at > seen,
        title: jobName(job),
        detail: job.error ? `Failed: ${job.error}` : "Translation failed",
      });
    }
  }

  if (prefs.teamInvites) {
    for (const inv of team?.pending_invitations ?? []) {
      items.push({
        id: `invite-${inv.owner_id}`, kind: "invite", at: epochSec(inv.created_at), href: "/app/inbox",
        unread: epochSec(inv.created_at) > seen,
        title: inv.email,
        detail: "invited you to their workspace",
      });
    }
  }

  items.sort((a, b) => b.at - a.at);
  return { items, unread: items.filter((i) => i.unread).length, jobs };
}

/** Browser Notification support and current permission ("unsupported" if absent). */
export function desktopPermission(): NotificationPermission | "unsupported" {
  if (typeof window === "undefined" || !("Notification" in window)) return "unsupported";
  return window.Notification.permission;
}

/** Must be called from a user gesture (a click). */
export async function requestDesktopPermission(): Promise<NotificationPermission | "unsupported"> {
  if (desktopPermission() === "unsupported") return "unsupported";
  try {
    return await window.Notification.requestPermission();
  } catch {
    return desktopPermission();
  }
}

/** Show a desktop notification if allowed; silently does nothing otherwise. */
export function showDesktop(title: string, body: string, href?: string) {
  if (desktopPermission() !== "granted") return;
  try {
    const n = new window.Notification(title, { body, icon: "/favicon.ico", tag: href });
    if (href) {
      n.onclick = () => {
        window.focus();
        window.location.assign(href);
        n.close();
      };
    }
  } catch {
    /* some browsers only allow notifications from a service worker */
  }
}
