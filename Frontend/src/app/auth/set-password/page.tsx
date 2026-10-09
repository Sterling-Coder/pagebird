"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { createClient } from "@/lib/supabase/client";

type Stage = "checking" | "ready" | "saving" | "invalid";

const MIN_LENGTH = 8;

/** Landing page for two email links: a team invite (the admin invite uses the
 * implicit flow, so the session arrives in the URL #hash, which only the
 * browser can read) and a password reset (PKCE, exchanged by /auth/callback
 * before it redirects here). Either way the visitor ends up signed in and
 * chooses a password. */
export default function SetPasswordPage() {
  const router = useRouter();
  const [stage, setStage] = useState<Stage>("checking");
  const [invited, setInvited] = useState(false);
  const [email, setEmail] = useState<string | null>(null);
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let cancelled = false;
    const url = new URL(window.location.href);
    const hash = new URLSearchParams(url.hash.slice(1));

    async function check() {
      const supabase = createClient();
      const linkError = hash.get("error_description") ?? url.searchParams.get("error_description");
      const code = url.searchParams.get("code");
      if (code) await supabase.auth.exchangeCodeForSession(code).catch(() => null);
      // getSession waits for the client to finish reading any #access_token in the URL.
      const { data } = await supabase.auth.getSession();
      if (cancelled) return;
      setInvited(url.searchParams.get("invited") === "1");
      if (data.session) {
        setEmail(data.session.user.email ?? null);
        setStage("ready");
        // Drop the tokens from the address bar.
        window.history.replaceState(null, "", url.pathname + (url.searchParams.get("invited") ? "?invited=1" : ""));
      } else {
        setError(linkError ? linkError.replace(/\+/g, " ") : null);
        setStage("invalid");
      }
    }
    check();
    return () => {
      cancelled = true;
    };
  }, []);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    if (password.length < MIN_LENGTH) {
      setError(`Use at least ${MIN_LENGTH} characters.`);
      return;
    }
    if (password !== confirm) {
      setError("The two passwords don't match.");
      return;
    }
    setStage("saving");
    const { error: updateError } = await createClient().auth.updateUser({ password });
    if (updateError) {
      setError(updateError.message);
      setStage("ready");
      return;
    }
    router.replace(invited ? "/app/team" : "/app");
    router.refresh();
  }

  const inputCls =
    "mt-2 w-full rounded-xl border border-[#e2dccf] bg-[#f6f2ea] px-3.5 py-2.5 text-[15px] text-ink outline-none transition-colors focus:border-[#c86018]";

  return (
    <div className="flex min-h-screen flex-col bg-[#e2ddd6] p-2 text-ink">
      <div className="flex flex-1 flex-col rounded-[14px] bg-white">
        <section className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-10 sm:px-0">
          <span className="text-2xl tracking-[0.04em]" style={{ fontFamily: "var(--font-mono), monospace" }}>
            <span className="text-[#3a3630]">page</span>
            <span className="text-[#e08a6f]">birdy</span>
          </span>

          {stage === "checking" ? (
            <p className="mt-10 text-[15px] text-[#6b6560]" role="status">Checking your link…</p>
          ) : stage === "invalid" ? (
            <>
              <h1 className="mt-10 text-[34px] leading-[1.1] font-medium tracking-tight">This link has expired.</h1>
              <p className="mt-3 text-[15px] text-[#6b6560]">
                {error ?? "Email links work once and only for a limited time."} Sign in, or ask for a new link from your
                profile or from the person who invited you.
              </p>
              <Link href="/login" className="mt-8 inline-flex self-start rounded-full bg-[#c86018] px-5 py-2.5 text-[14px] font-semibold text-white hover:opacity-90">
                Go to sign in
              </Link>
            </>
          ) : (
            <>
              <h1 className="mt-10 text-[34px] leading-[1.1] font-medium tracking-tight">
                {invited ? "Welcome to the team." : "Choose a new password."}
              </h1>
              <p className="mt-3 text-[15px] text-[#6b6560]">
                {invited ? "Set a password to finish creating your account" : "Set the password you'll use to sign in"}
                {email ? <> for <span className="font-semibold text-ink">{email}</span></> : null}.
              </p>
              <form onSubmit={handleSubmit} className="mt-8 flex flex-col gap-4">
                <div>
                  <label htmlFor="new-password" className="text-[12px] font-semibold tracking-widest uppercase">New password</label>
                  <input id="new-password" type="password" autoComplete="new-password" required minLength={MIN_LENGTH}
                    value={password} onChange={(e) => setPassword(e.target.value)} className={inputCls} />
                </div>
                <div>
                  <label htmlFor="confirm-password" className="text-[12px] font-semibold tracking-widest uppercase">Confirm password</label>
                  <input id="confirm-password" type="password" autoComplete="new-password" required minLength={MIN_LENGTH}
                    value={confirm} onChange={(e) => setConfirm(e.target.value)} className={inputCls} />
                </div>
                {error ? <p role="alert" className="text-[13px] text-[#b3261e]">{error}</p> : null}
                <button type="submit" disabled={stage === "saving"}
                  className="mt-2 rounded-full bg-[#c86018] py-3 text-[14px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-50">
                  {stage === "saving" ? "Saving…" : invited ? "Set password and continue" : "Save password"}
                </button>
              </form>
            </>
          )}
        </section>
      </div>
    </div>
  );
}
