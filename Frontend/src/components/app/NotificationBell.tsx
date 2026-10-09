"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { Icon, timeAgo } from "@/components/app/ui";
import {
  NOTIFY_EVENT,
  SEEN_KEY,
  PREFS_KEY,
  getPrefs,
  jobHref,
  loadNotifications,
  markAllRead,
  showDesktop,
  type Notification,
} from "@/lib/notifications";

const POLL_MS = 20_000;
const MAX_ITEMS = 10;

const BELL = "M18 8a6 6 0 0 0-12 0c0 7-3 9-3 9h18s-3-2-3-9M13.73 21a2 2 0 0 1-3.46 0";
const CHECK = "M20 6L9 17l-5-5";
const CROSS = "M18 6L6 18M6 6l12 12";
const PERSON = "M16 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M10 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM20 8v6M23 11h-6";

const KIND_STYLE: Record<Notification["kind"], { icon: string; tone: string; label: string }> = {
  "job-finished": { icon: CHECK, tone: "bg-[#4caf50]", label: "Translation finished" },
  "job-failed": { icon: CROSS, tone: "bg-[#d9534f]", label: "Translation failed" },
  invite: { icon: PERSON, tone: "bg-[#8b6fbf]", label: "Team invitation" },
};

export default function NotificationBell() {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState<Notification[] | null>(null);
  const [unread, setUnread] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  /** Job id → last status we saw, to detect jobs finishing while the app is open. */
  const statusRef = useRef<Map<string, string> | null>(null);
  const panelId = useId();

  const load = useCallback(() => {
    loadNotifications()
      .then((feed) => {
        setItems(feed.items);
        setUnread(feed.unread);
        setError(null);

        const prev = statusRef.current;
        const next = new Map(feed.jobs.map((j) => [j.id, String(j.status)]));
        if (prev) {
          const prefs = getPrefs();
          for (const job of feed.jobs) {
            if (prev.get(job.id) !== "processing") continue;
            const name = job.original_filename || "Your file";
            if (job.status === "complete" && prefs.jobFinished) {
              showDesktop("Translation finished", name, jobHref(job));
            } else if (job.status === "failed" && prefs.jobFailed) {
              showDesktop("Translation failed", name, jobHref(job));
            }
          }
        }
        statusRef.current = next;
      })
      .catch((e: unknown) => setError(e instanceof Error ? e.message : "Could not load notifications"));
  }, []);

  // Poll while the tab is visible; refresh straight away when it comes back.
  useEffect(() => {
    load();
    const tick = setInterval(() => {
      if (document.visibilityState === "visible") load();
    }, POLL_MS);
    const onVisible = () => {
      if (document.visibilityState === "visible") load();
    };
    const onStorage = (e: StorageEvent) => {
      if (e.key === SEEN_KEY || e.key === PREFS_KEY) load();
    };
    document.addEventListener("visibilitychange", onVisible);
    window.addEventListener(NOTIFY_EVENT, load);
    window.addEventListener("storage", onStorage);
    return () => {
      clearInterval(tick);
      document.removeEventListener("visibilitychange", onVisible);
      window.removeEventListener(NOTIFY_EVENT, load);
      window.removeEventListener("storage", onStorage);
    };
  }, [load]);

  const close = useCallback((restoreFocus: boolean) => {
    setOpen(false);
    if (restoreFocus) buttonRef.current?.focus();
  }, []);

  // Click outside / Escape close; focus moves into the panel on open.
  useEffect(() => {
    if (!open) return;
    const first = panelRef.current?.querySelector<HTMLElement>("a, button");
    (first ?? panelRef.current)?.focus();

    const onPointer = (e: PointerEvent) => {
      const t = e.target as Node;
      if (panelRef.current?.contains(t) || buttonRef.current?.contains(t)) return;
      close(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close(true);
      }
    };
    document.addEventListener("pointerdown", onPointer);
    document.addEventListener("keydown", onKey);
    return () => {
      document.removeEventListener("pointerdown", onPointer);
      document.removeEventListener("keydown", onKey);
    };
  }, [open, close]);

  function toggle() {
    if (!open) load();
    setOpen((o) => !o);
  }

  function readAll() {
    const newest = items?.reduce((m, i) => Math.max(m, i.at), 0) ?? 0;
    markAllRead(Math.max(Date.now() / 1000, newest));
  }

  const shown = (items ?? []).slice(0, MAX_ITEMS);
  const badge = unread > 9 ? "9+" : String(unread);

  return (
    <div className="relative">
      <button
        ref={buttonRef}
        type="button"
        onClick={toggle}
        aria-haspopup="dialog"
        aria-expanded={open}
        aria-controls={open ? panelId : undefined}
        aria-label={unread > 0 ? `Notifications, ${unread} unread` : "Notifications"}
        className="relative flex h-8 w-8 items-center justify-center rounded-full text-[var(--app-ink-soft)] transition-colors hover:bg-[var(--app-nav-hover)] hover:text-[var(--app-ink)] focus-visible:outline-2 focus-visible:outline-[var(--app-accent)]"
      >
        <Icon d={BELL} className="h-[17px] w-[17px]" />
        {unread > 0 ? (
          <span
            aria-hidden="true"
            className="absolute -top-0.5 -right-0.5 flex h-[16px] min-w-[16px] items-center justify-center rounded-full bg-[var(--app-accent)] px-1 text-[10px] leading-none font-semibold text-white ring-2 ring-[var(--app-surface)]"
          >
            {badge}
          </span>
        ) : null}
      </button>

      {open ? (
        <div
          ref={panelRef}
          id={panelId}
          role="dialog"
          aria-label="Notifications"
          tabIndex={-1}
          className="absolute top-full right-0 z-50 mt-2 w-[min(360px,calc(100vw-24px))] overflow-hidden rounded-2xl border border-[var(--app-border)] bg-[var(--app-surface)] shadow-[0_12px_40px_rgba(0,0,0,0.18)] outline-none"
        >
          <div className="flex items-center justify-between border-b border-[var(--app-border)] px-4 py-3">
            <h2 className="text-[13px] font-semibold text-[var(--app-ink)]">
              Notifications
              {unread > 0 ? <span className="ml-1.5 font-normal text-[var(--app-muted)]">{unread} new</span> : null}
            </h2>
            <button
              type="button"
              onClick={readAll}
              disabled={unread === 0}
              className="rounded-md px-1.5 py-0.5 text-[12px] text-[var(--app-accent)] hover:underline disabled:cursor-default disabled:text-[var(--app-muted)] disabled:no-underline"
            >
              Mark all as read
            </button>
          </div>

          <div className="max-h-[min(420px,60vh)] overflow-y-auto">
            {items === null && !error ? (
              <p className="px-4 py-6 text-center text-[12.5px] text-[var(--app-muted)]" role="status">Loading…</p>
            ) : null}
            {error && items === null ? (
              <p className="px-4 py-6 text-center text-[12.5px] text-[var(--app-muted)]" role="alert">{error}</p>
            ) : null}
            {items !== null && shown.length === 0 ? (
              <p className="px-4 py-8 text-center text-[12.5px] text-[var(--app-muted)]">
                You&apos;re all caught up.
              </p>
            ) : null}
            {shown.length > 0 ? (
              <ul className="py-1">
                {shown.map((n) => {
                  const k = KIND_STYLE[n.kind];
                  return (
                    <li key={n.id}>
                      <Link
                        href={n.href}
                        onClick={() => close(false)}
                        className="flex items-start gap-3 px-4 py-2.5 transition-colors hover:bg-[var(--app-nav-hover)] focus-visible:bg-[var(--app-nav-hover)] focus-visible:outline-none"
                      >
                        <span className={`mt-0.5 flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-white ${k.tone}`}>
                          <Icon d={k.icon} className="h-[13px] w-[13px]" />
                        </span>
                        <span className="min-w-0 flex-1">
                          <span className="sr-only">{k.label}: </span>
                          <span className="block truncate text-[13px] font-medium text-[var(--app-ink)]">{n.title}</span>
                          <span className="block truncate text-[12px] text-[var(--app-ink-soft)]">{n.detail}</span>
                          <span className="mt-0.5 block text-[11px] text-[var(--app-muted)]">{timeAgo(n.at)}</span>
                        </span>
                        {n.unread ? (
                          <span className="mt-2 h-2 w-2 shrink-0 rounded-full bg-[var(--app-accent)]">
                            <span className="sr-only">Unread</span>
                          </span>
                        ) : null}
                      </Link>
                    </li>
                  );
                })}
              </ul>
            ) : null}
          </div>

          <div className="flex items-center justify-between border-t border-[var(--app-border)] px-4 py-2.5 text-[12px]">
            <Link href="/app/inbox" onClick={() => close(false)} className="font-medium text-[var(--app-ink)] hover:underline">
              View inbox
            </Link>
            <Link href="/app/profile#preferences" onClick={() => close(false)} className="text-[var(--app-muted)] hover:text-[var(--app-ink)] hover:underline">
              Settings
            </Link>
          </div>
        </div>
      ) : null}
    </div>
  );
}
