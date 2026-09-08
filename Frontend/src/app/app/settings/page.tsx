"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";
import { createClient } from "@/lib/supabase/client";

type Profile = {
  email: string | null;
  createdAt: string | null;
  trialEndsAt: string | null;
};

export default function AccountSettingsPage() {
  const [navOpen, setNavOpen] = useState(true);
  const [profile, setProfile] = useState<Profile | null>(null);
  const [signingOut, setSigningOut] = useState(false);
  const router = useRouter();

  useEffect(() => {
    const supabase = createClient();
    supabase.auth.getUser().then(({ data }) => {
      const user = data.user;
      if (!user) return;
      supabase
        .from("profiles")
        .select("trial_ends_at")
        .single()
        .then(({ data: row }) => {
          setProfile({
            email: user.email ?? null,
            createdAt: user.created_at ?? null,
            trialEndsAt: row?.trial_ends_at ?? null,
          });
        });
    });
  }, []);

  async function handleSignOut() {
    setSigningOut(true);
    const supabase = createClient();
    await supabase.auth.signOut();
    router.push("/login");
    router.refresh();
  }

  const trialDaysLeft = profile?.trialEndsAt
    ? Math.ceil((new Date(profile.trialEndsAt).getTime() - Date.now()) / 86_400_000)
    : null;

  return (
    <div className="flex min-h-screen w-full bg-paper">
      {navOpen ? <AppNavRail /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar navOpen={navOpen} onToggleNav={() => setNavOpen((v) => !v)} breadcrumb="Settings" />
        <div className="flex min-h-0 flex-1 overflow-auto p-6">
          <div className="w-full max-w-md">
            <h1 className="mb-6 text-lg font-bold text-ink">Account</h1>

            {profile ? (
              <div className="flex flex-col gap-6">
                <div className="flex items-center gap-4 border border-rule bg-paper-dim p-5">
                  <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-full bg-red font-mono text-lg font-bold text-paper">
                    {profile.email?.[0]?.toUpperCase() ?? "?"}
                  </div>
                  <div>
                    <p className="text-sm font-semibold text-ink">{profile.email}</p>
                    {profile.createdAt ? (
                      <p className="mt-0.5 text-xs text-muted">
                        Member since {new Date(profile.createdAt).toLocaleDateString()}
                      </p>
                    ) : null}
                  </div>
                </div>

                <div className="border border-rule p-5">
                  <span className="font-mono text-[11px] font-bold tracking-widest text-muted uppercase">
                    Trial status
                  </span>
                  <p className="mt-2 text-sm text-ink-soft">
                    {trialDaysLeft === null
                      ? "—"
                      : trialDaysLeft > 0
                        ? `${trialDaysLeft} day${trialDaysLeft === 1 ? "" : "s"} left in your free trial.`
                        : "Your trial has ended."}
                  </p>
                </div>

                <button
                  type="button"
                  onClick={handleSignOut}
                  disabled={signingOut}
                  className="flex h-11 items-center justify-center border border-rule font-mono text-[11px] uppercase tracking-widest text-ink-soft transition-colors hover:border-red hover:text-red disabled:opacity-40"
                >
                  {signingOut ? "Signing out…" : "Sign out"}
                </button>
              </div>
            ) : (
              <p className="text-sm text-muted">Loading…</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
