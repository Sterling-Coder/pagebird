"use client";

import { useCallback, useEffect, useId, useRef, useState } from "react";
import { createPortal } from "react-dom";
import Link from "next/link";

/** localStorage flag set once the welcome/tour has been finished or skipped. */
export const TOUR_STORAGE_KEY = "pb-tour-done";
const START_EVENT = "pb-tour:start";

/** Start the tour from anywhere (help menu, help page), even if it was done. */
export function replayTour() {
  if (typeof window !== "undefined") window.dispatchEvent(new Event(START_EVENT));
}

function isDone(): boolean {
  try {
    return window.localStorage.getItem(TOUR_STORAGE_KEY) === "1";
  } catch {
    return false;
  }
}

function markDone() {
  try {
    window.localStorage.setItem(TOUR_STORAGE_KEY, "1");
  } catch {
    /* storage blocked: the tour may show again next visit, which is harmless */
  }
}

type Step = {
  /** `data-tour` value of the element to highlight. None = centred card. */
  anchor?: string;
  title: string;
  body: string;
  /** Shown when the anchor lives in the sidebar but isn't on screen. */
  inSidebar?: boolean;
  final?: boolean;
};

const STEPS: Step[] = [
  {
    anchor: "nav-home",
    inSidebar: true,
    title: "Home",
    body: "Your starting point. Name a project to create it, follow the suggested next steps, and pick up recent projects or anything that needs your attention.",
  },
  {
    anchor: "nav-agents",
    inSidebar: true,
    title: "Agents do the translating",
    body: "One agent per kind of input: Document & Office (PDF, IDML, Word, PowerPoint, Excel, text), OCR for images (PNG, JPEG, WEBP, PSD, AI), Web for a public page by URL, and Quick Translate for pasted text.",
  },
  {
    anchor: "nav-jobs",
    inSidebar: true,
    title: "Jobs: every translation",
    body: "Translations run in the background, so you can leave the page. The board groups them into Translating, Needs attention and Delivered, and you can filter by type.",
  },
  {
    anchor: "nav-projects",
    inSidebar: true,
    title: "Projects keep work together",
    body: "Group files into a project. Each one has Files (review segments and download), Settings, Linguistic assets and Statistics tabs.",
  },
  {
    anchor: "nav-inbox",
    inSidebar: true,
    title: "Inbox",
    body: "Translations that finished or failed in the last week, plus invitations to join a team, all in one list.",
  },
  {
    anchor: "nav-glossary",
    inSidebar: true,
    title: "Glossary and Workflows",
    body: "The glossary holds locked terms per language that every translation must use. Workflows (Beta) shows the steps each agent runs, in order.",
  },
  {
    anchor: "nav-extension",
    inSidebar: true,
    title: "Chrome extension",
    body: "Translate a selection or a whole page while you browse, using this account. Install steps are on the Extension page.",
  },
  {
    anchor: "notifications",
    title: "Notifications",
    body: "The bell shows job updates as they happen. Switch between light and dark next to your name at the bottom of the sidebar.",
  },
  {
    anchor: "nav-user",
    inSidebar: true,
    title: "You and your team",
    body: "Click your name to open your Profile: plan, usage, and which notifications you get. Team (bottom of the sidebar) is where you invite teammates, and Settings holds your account and sign-out.",
  },
  {
    final: true,
    title: "Try it: translate your first file",
    body: "Upload a document, pick a language and press Translate. You get the same file type back with the layout intact. InDesign users: export IDML, as .indd isn't supported. Right-to-left languages are mirrored for you.",
  },
];

const PAD = 6; // space between anchor and highlight ring
const GAP = 12; // space between highlight and card
const EDGE = 12; // minimum distance from the viewport edge

type Rect = { top: number; left: number; width: number; height: number };

function findAnchor(name?: string): HTMLElement | null {
  if (!name) return null;
  const el = document.querySelector<HTMLElement>(`[data-tour="${name}"]`);
  if (!el) return null;
  const r = el.getBoundingClientRect();
  if (r.width === 0 || r.height === 0) return null;
  if (r.bottom < 0 || r.right < 0 || r.top > window.innerHeight || r.left > window.innerWidth) return null;
  return el;
}

/** Place the card beside the highlight, trying right, left, below, above, then clamp. */
function placeCard(target: Rect, card: { width: number; height: number }) {
  const vw = window.innerWidth;
  const vh = window.innerHeight;
  const clampX = (x: number) => Math.min(Math.max(x, EDGE), Math.max(EDGE, vw - card.width - EDGE));
  const clampY = (y: number) => Math.min(Math.max(y, EDGE), Math.max(EDGE, vh - card.height - EDGE));
  const midY = target.top + target.height / 2 - card.height / 2;
  const midX = target.left + target.width / 2 - card.width / 2;

  const right = target.left + target.width + GAP;
  if (right + card.width <= vw - EDGE) return { top: clampY(midY), left: right };
  const left = target.left - GAP - card.width;
  if (left >= EDGE) return { top: clampY(midY), left };
  const below = target.top + target.height + GAP;
  if (below + card.height <= vh - EDGE) return { top: below, left: clampX(midX) };
  const above = target.top - GAP - card.height;
  if (above >= EDGE) return { top: above, left: clampX(midX) };
  return { top: clampY(midY), left: clampX(midX) };
}

const FOCUSABLE = 'a[href], button:not([disabled]), [tabindex]:not([tabindex="-1"])';

/** Keep Tab / Shift+Tab inside `root`. */
function trapTab(e: KeyboardEvent, root: HTMLElement | null) {
  if (e.key !== "Tab" || !root) return;
  const items = Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE));
  if (items.length === 0) return;
  const first = items[0];
  const last = items[items.length - 1];
  const active = document.activeElement;
  if (e.shiftKey && (active === first || !root.contains(active))) {
    e.preventDefault();
    last.focus();
  } else if (!e.shiftKey && (active === last || !root.contains(active))) {
    e.preventDefault();
    first.focus();
  }
}

const btnGhost =
  "rounded-full px-3 py-1.5 text-[12.5px] text-[var(--app-ink-soft,#57524b)] transition-colors hover:bg-[var(--app-surface-2,#f6f2ea)] hover:text-[var(--app-ink,#1d1b18)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent,#c86018)]";
const btnPrimary =
  "rounded-full bg-[var(--app-accent,#c86018)] px-4 py-1.5 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent,#c86018)]";
const cardBase =
  "fixed z-[101] w-[min(340px,calc(100vw-24px))] rounded-2xl border border-[var(--app-border,#e2dccf)] bg-[var(--app-surface,#ffffff)] p-5 text-[var(--app-ink,#1d1b18)] shadow-[0_18px_50px_rgba(10,9,8,0.28)] outline-none";

type Phase = "idle" | "welcome" | "steps";

/** First-run welcome and spotlight tour of /app. Mount once in the /app layout. */
export function Tour() {
  const [phase, setPhase] = useState<Phase>("idle");
  const [index, setIndex] = useState(0);
  const [hole, setHole] = useState<Rect | null>(null);
  const [pos, setPos] = useState<{ top: number; left: number } | null>(null);
  const cardRef = useRef<HTMLDivElement>(null);
  const returnFocus = useRef<HTMLElement | null>(null);
  const titleId = useId();
  const bodyId = useId();

  const step = STEPS[index];

  // First visit: show the welcome once the page has had a moment to render.
  useEffect(() => {
    const t = window.setTimeout(() => {
      if (!isDone()) {
        returnFocus.current = document.activeElement as HTMLElement | null;
        setPhase("welcome");
      }
    }, 700);
    const onStart = () => {
      returnFocus.current = document.activeElement as HTMLElement | null;
      setIndex(0);
      setPhase("welcome");
    };
    window.addEventListener(START_EVENT, onStart);
    return () => {
      window.clearTimeout(t);
      window.removeEventListener(START_EVENT, onStart);
    };
  }, []);

  const close = useCallback(() => {
    markDone();
    setPhase("idle");
    setHole(null);
    setPos(null);
    const el = returnFocus.current;
    if (el && document.contains(el)) el.focus();
  }, []);

  const next = useCallback(() => {
    setIndex((i) => {
      if (i >= STEPS.length - 1) return i;
      return i + 1;
    });
  }, []);
  const back = useCallback(() => setIndex((i) => Math.max(0, i - 1)), []);

  // Measure the anchor and the card, then place both. Runs on step change,
  // resize, any scroll (capture catches inner scroll panes) and size changes.
  useEffect(() => {
    if (phase !== "steps") return;
    let raf = 0;
    const anchorEl = findAnchor(STEPS[index].anchor);
    anchorEl?.scrollIntoView({ block: "nearest", inline: "nearest" });

    const measure = () => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = findAnchor(STEPS[index].anchor);
        const card = cardRef.current;
        const cw = card?.offsetWidth ?? 340;
        const ch = card?.offsetHeight ?? 200;
        if (!el) {
          setHole(null);
          setPos({
            top: Math.max(EDGE, (window.innerHeight - ch) / 2),
            left: Math.max(EDGE, (window.innerWidth - cw) / 2),
          });
          return;
        }
        const r = el.getBoundingClientRect();
        const h = { top: r.top - PAD, left: r.left - PAD, width: r.width + PAD * 2, height: r.height + PAD * 2 };
        setHole(h);
        setPos(placeCard(h, { width: cw, height: ch }));
      });
    };

    measure();
    window.addEventListener("resize", measure);
    window.addEventListener("scroll", measure, true);
    const ro = new ResizeObserver(measure);
    if (anchorEl) ro.observe(anchorEl);
    if (cardRef.current) ro.observe(cardRef.current);
    return () => {
      cancelAnimationFrame(raf);
      window.removeEventListener("resize", measure);
      window.removeEventListener("scroll", measure, true);
      ro.disconnect();
    };
  }, [phase, index]);

  // Move focus into the card whenever it opens or the step changes.
  useEffect(() => {
    if (phase === "idle") return;
    const id = requestAnimationFrame(() => {
      const card = cardRef.current;
      const primary = card?.querySelector<HTMLElement>("[data-tour-primary]");
      (primary ?? card)?.focus();
    });
    return () => cancelAnimationFrame(id);
  }, [phase, index]);

  // Keyboard: Esc skips, arrows step, Tab stays inside the card.
  useEffect(() => {
    if (phase === "idle") return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        e.preventDefault();
        close();
      } else if (phase === "steps" && e.key === "ArrowRight") {
        e.preventDefault();
        next();
      } else if (phase === "steps" && e.key === "ArrowLeft") {
        e.preventDefault();
        back();
      } else {
        trapTab(e, cardRef.current);
      }
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [phase, close, next, back]);

  if (phase === "idle" || typeof document === "undefined") return null;

  if (phase === "welcome") {
    return createPortal(
      <>
        <div className="fixed inset-0 z-[100] bg-[rgba(10,9,8,0.55)]" aria-hidden="true" />
        <div
          ref={cardRef}
          role="dialog"
          aria-modal="true"
          aria-labelledby={titleId}
          aria-describedby={bodyId}
          tabIndex={-1}
          className={`${cardBase} left-1/2 top-1/2 w-[min(420px,calc(100vw-32px))] -translate-x-1/2 -translate-y-1/2 p-6 motion-safe:animate-[pb-tour-in_180ms_ease-out]`}
        >
          <TourKeyframes />
          <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-full bg-[var(--app-surface-2,#f6f2ea)] text-[var(--app-accent,#c86018)]">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round" strokeLinejoin="round" className="h-[18px] w-[18px]" aria-hidden="true">
              <path d="M12 3l1.9 5.1L19 10l-5.1 1.9L12 17l-1.9-5.1L5 10l5.1-1.9z" />
            </svg>
          </div>
          <h2 id={titleId} className="text-[17px] font-semibold">Welcome to Pagebirdy</h2>
          <div id={bodyId} className="mt-2 space-y-1 text-[13px] leading-relaxed text-[var(--app-ink-soft,#57524b)]">
            <p>Translate documents, images and web pages without losing the layout.</p>
            <p>Pick an agent, upload a file, and it runs in the background.</p>
            <p>Finished work lands in Jobs, Projects and your Inbox, ready to review and download.</p>
          </div>
          <div className="mt-5 flex items-center justify-end gap-2">
            <button type="button" onClick={close} className={btnGhost}>Skip</button>
            <button type="button" data-tour-primary onClick={() => { setIndex(0); setPhase("steps"); }} className={btnPrimary}>
              Start tour
            </button>
          </div>
        </div>
      </>,
      document.body,
    );
  }

  const missingAnchor = !hole;
  const total = STEPS.length;

  return createPortal(
    <>
      <TourKeyframes />
      {/* Click shield + dim. With a target, the dim is the ring's huge shadow so the target shows through. */}
      <div
        className={`fixed inset-0 z-[100] ${missingAnchor ? "bg-[rgba(10,9,8,0.55)]" : ""}`}
        aria-hidden="true"
      />
      {hole ? (
        <div
          aria-hidden="true"
          className="pointer-events-none fixed z-[100] rounded-xl ring-2 ring-[var(--app-accent,#c86018)] motion-safe:transition-all motion-safe:duration-200 motion-safe:ease-out"
          style={{
            top: hole.top,
            left: hole.left,
            width: hole.width,
            height: hole.height,
            boxShadow: "0 0 0 9999px rgba(10,9,8,0.55)",
          }}
        />
      ) : null}
      <div
        ref={cardRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={bodyId}
        tabIndex={-1}
        className={`${cardBase} motion-safe:transition-[top,left] motion-safe:duration-200 motion-safe:ease-out`}
        style={{ top: pos?.top ?? -9999, left: pos?.left ?? -9999, visibility: pos ? "visible" : "hidden" }}
      >
        <div className="mb-2 flex items-center justify-between">
          <span className="font-mono text-[10.5px] uppercase tracking-widest text-[var(--app-muted,#8f8778)]" aria-live="polite">
            {index + 1} of {total}
          </span>
          {!step.final ? (
            <button type="button" onClick={close} className="text-[12px] text-[var(--app-muted,#8f8778)] hover:text-[var(--app-ink,#1d1b18)] hover:underline">
              Skip tour
            </button>
          ) : null}
        </div>
        <h2 id={titleId} className="text-[15px] font-semibold">{step.title}</h2>
        <div id={bodyId}>
          <p className="mt-1.5 text-[13px] leading-relaxed text-[var(--app-ink-soft,#57524b)]">{step.body}</p>
          {missingAnchor && step.inSidebar ? (
            <p className="mt-2 rounded-lg bg-[var(--app-surface-2,#f6f2ea)] px-2.5 py-1.5 text-[12px] text-[var(--app-muted,#8f8778)]">
              This lives in the sidebar, which is hidden right now. Use the sidebar button at the top left, or a wider window, to see it.
            </p>
          ) : null}
        </div>

        {/* Progress dots */}
        <div className="mt-4 flex gap-1" aria-hidden="true">
          {STEPS.map((_, i) => (
            <span
              key={i}
              className={`h-1 flex-1 rounded-full ${i <= index ? "bg-[var(--app-accent,#c86018)]" : "bg-[var(--app-border,#e2dccf)]"}`}
            />
          ))}
        </div>

        {step.final ? (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            <Link href="/app/agents/document" data-tour-primary onClick={close} className={btnPrimary}>
              Translate a file
            </Link>
            <Link href="/app/help" onClick={close} className={btnGhost}>
              Read the getting started guide
            </Link>
            <button type="button" onClick={back} className={`${btnGhost} ml-auto`}>Back</button>
          </div>
        ) : (
          <div className="mt-4 flex items-center justify-between gap-2">
            <button type="button" onClick={back} disabled={index === 0} className={`${btnGhost} disabled:invisible`}>
              Back
            </button>
            <button type="button" data-tour-primary onClick={next} className={btnPrimary}>
              Next
            </button>
          </div>
        )}
      </div>
    </>,
    document.body,
  );
}

function TourKeyframes() {
  return (
    <style>{`@keyframes pb-tour-in{from{opacity:0;transform:translateY(6px)}to{opacity:1;transform:none}}`}</style>
  );
}

/** Small button for pages (e.g. /app/help) that restarts the tour. */
export function ReplayTourButton({ className }: { className?: string }) {
  return (
    <button type="button" onClick={replayTour} className={className ?? btnPrimary}>
      Replay the tour
    </button>
  );
}
