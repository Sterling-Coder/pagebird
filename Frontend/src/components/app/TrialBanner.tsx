"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { TalkToUsPanel } from "./TalkToUsPanel";

type TrialState =
  | { status: "loading" }
  | { status: "none" }
  | { status: "active"; daysLeft: number }
  | { status: "expired" };

const DISMISS_KEY = "pb-trial-banner-dismissed";

function readDismissed(): boolean {
  try {
    return window.sessionStorage.getItem(DISMISS_KEY) === "1";
  } catch {
    // storage blocked (private mode, sandbox) or no window during SSR
    return false;
  }
}

function DismissButton({ onClick }: { onClick: () => void }) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label="Dismiss"
      className="absolute right-3 top-1/2 -translate-y-1/2 p-1 opacity-70 transition-opacity hover:opacity-100"
    >
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3.5 w-3.5">
        <path d="M6 6l12 12M18 6L6 18" />
      </svg>
    </button>
  );
}

export function TrialBanner() {
  const [trial, setTrial] = useState<TrialState>({ status: "loading" });
  const [panelOpen, setPanelOpen] = useState(false);
  // Banner is null while loading, so reading storage at init can't cause a
  // visible hydration mismatch.
  const [dismissed, setDismissed] = useState(readDismissed);

  function dismiss() {
    setDismissed(true);
    try {
      window.sessionStorage.setItem(DISMISS_KEY, "1");
    } catch {
      // keep the in-memory dismissal for this page view
    }
  }

  useEffect(() => {
    let cancelled = false;
    const supabase = createClient();

    async function load() {
      try {
        const { data } = await supabase.from("profiles").select("trial_ends_at").single();
        if (cancelled) return;
        if (!data?.trial_ends_at) {
          setTrial({ status: "none" });
          return;
        }
        const msLeft = new Date(data.trial_ends_at).getTime() - Date.now();
        if (msLeft <= 0) {
          setTrial({ status: "expired" });
        } else {
          setTrial({ status: "active", daysLeft: Math.ceil(msLeft / 86_400_000) });
        }
      } catch {
        if (!cancelled) setTrial({ status: "none" });
      }
    }

    load();
    return () => {
      cancelled = true;
    };
  }, []);

  if (dismissed || trial.status === "loading" || trial.status === "none") return null;

  if (trial.status === "expired") {
    return (
      <>
        <div className="relative flex items-center justify-center gap-2 bg-red px-10 py-2 text-center text-sm text-paper">
          <span>Your 14-day trial has ended — new translations are paused.</span>
          <button
            type="button"
            onClick={() => setPanelOpen(true)}
            className="font-semibold underline underline-offset-2"
          >
            Contact us to keep going
          </button>
          <DismissButton onClick={dismiss} />
        </div>
        {panelOpen && <TalkToUsPanel onClose={() => setPanelOpen(false)} />}
      </>
    );
  }

  const urgent = trial.daysLeft <= 3;
  return (
    <>
      <div
        className={`relative flex items-center justify-center gap-2 px-10 py-2 text-center text-sm ${
          urgent ? "bg-red text-paper" : "bg-paper-dim text-ink-soft"
        }`}
      >
        {trial.daysLeft} {trial.daysLeft === 1 ? "day" : "days"} left in your free trial.
        {urgent ? (
          <button
            type="button"
            onClick={() => setPanelOpen(true)}
            className="font-semibold underline underline-offset-2"
          >
            Talk to us
          </button>
        ) : null}
        <DismissButton onClick={dismiss} />
      </div>
      {panelOpen && <TalkToUsPanel onClose={() => setPanelOpen(false)} />}
    </>
  );
}
