"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

type TrialState =
  | { status: "loading" }
  | { status: "none" }
  | { status: "active"; daysLeft: number }
  | { status: "expired" };

export function TrialBanner() {
  const [trial, setTrial] = useState<TrialState>({ status: "loading" });

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

  if (trial.status === "loading" || trial.status === "none") return null;

  if (trial.status === "expired") {
    return (
      <div className="flex items-center justify-center gap-2 bg-red px-4 py-2 text-center text-sm text-paper">
        <span>Your 14-day trial has ended — new translations are paused.</span>
        <Link href="/contact" className="font-semibold underline underline-offset-2">
          Contact us to keep going
        </Link>
      </div>
    );
  }

  const urgent = trial.daysLeft <= 3;
  return (
    <div
      className={`flex items-center justify-center gap-2 px-4 py-2 text-center text-sm ${
        urgent ? "bg-red text-paper" : "bg-paper-dim text-ink-soft"
      }`}
    >
      {trial.daysLeft} {trial.daysLeft === 1 ? "day" : "days"} left in your free trial.
      {urgent ? (
        <Link href="/contact" className="font-semibold underline underline-offset-2">
          Talk to us
        </Link>
      ) : null}
    </div>
  );
}
