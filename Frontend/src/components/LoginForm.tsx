"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { PunchCardPanel } from "./login-panels/PunchCardPanel";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export function LoginForm() {
  const [mode, setMode] = useState<Mode>("login");
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const router = useRouter();

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();

    try {
      if (mode === "signup") {
        const { error: signUpError } = await supabase.auth.signUp({
          email,
          password,
          options: { data: { name } },
        });
        if (signUpError) throw signUpError;
      } else {
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email,
          password,
        });
        if (signInError) throw signInError;
      }
      router.push("/app");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleGoogle() {
    setError(null);
    const supabase = createClient();
    const { error: oauthError } = await supabase.auth.signInWithOAuth({
      provider: "google",
      options: { redirectTo: `${window.location.origin}/auth/callback` },
    });
    if (oauthError) setError(oauthError.message);
  }

  return (
    <div className="relative grid w-full flex-1 lg:grid-cols-2">
      <Link
        href="/"
        aria-label="Back to Pagebird"
        className="fixed right-6 top-6 z-20 flex h-9 w-9 items-center justify-center border border-ink bg-paper text-ink-soft transition-colors hover:border-ink hover:text-ink sm:right-8 sm:top-8 lg:border-paper/30 lg:bg-transparent lg:text-paper/70 lg:hover:border-paper lg:hover:text-paper"
      >
        <svg
          viewBox="0 0 24 24"
          fill="none"
          stroke="currentColor"
          strokeWidth="2"
          strokeLinecap="round"
          strokeLinejoin="round"
          className="h-4 w-4"
          aria-hidden="true"
        >
          <path d="M19 12H5" />
          <path d="M11 18l-6-6 6-6" />
        </svg>
      </Link>

      <section className="mx-auto flex w-full max-w-md flex-col items-center justify-center px-6 py-16 text-center sm:px-8">
        <span className="font-mono text-[11px] uppercase tracking-widest text-red">
          {mode === "login" ? "Welcome back" : "Create account"}
        </span>
        <h1 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
          {mode === "login" ? "Log in to Pagebird" : "Sign up for Pagebird"}
        </h1>
        {mode === "signup" ? (
          <p className="mt-2 text-sm text-ink-soft">
            14-day free trial, no card required.
          </p>
        ) : null}

        <div className="relative mt-8 w-full">
          <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
          <form
            onSubmit={handleSubmit}
            className="relative z-10 space-y-5 border-2 border-ink bg-paper p-6 text-left"
          >
            <button
              type="button"
              onClick={handleGoogle}
              className="flex w-full items-center justify-center gap-2.5 border border-ink bg-paper px-6 py-3 text-sm font-semibold text-ink transition-colors hover:bg-paper-dim"
            >
              <svg viewBox="0 0 24 24" className="h-4 w-4">
                <path
                  fill="#4285F4"
                  d="M23.5 12.27c0-.79-.07-1.54-.2-2.27H12v4.3h6.47c-.28 1.5-1.13 2.77-2.4 3.62v3h3.87c2.27-2.09 3.56-5.17 3.56-8.65z"
                />
                <path
                  fill="#34A853"
                  d="M12 24c3.24 0 5.96-1.07 7.94-2.9l-3.87-3c-1.08.72-2.45 1.15-4.07 1.15-3.13 0-5.78-2.11-6.73-4.96H1.28v3.09C3.25 21.3 7.31 24 12 24z"
                />
                <path
                  fill="#FBBC05"
                  d="M5.27 14.29a7.2 7.2 0 0 1 0-4.58V6.62H1.28a12 12 0 0 0 0 10.76l3.99-3.09z"
                />
                <path
                  fill="#EA4335"
                  d="M12 4.75c1.76 0 3.34.6 4.59 1.79l3.44-3.44C17.95 1.19 15.24 0 12 0 7.31 0 3.25 2.7 1.28 6.62l3.99 3.09C6.22 6.86 8.87 4.75 12 4.75z"
                />
              </svg>
              Continue with Google
            </button>

            <div className="flex items-center gap-3">
              <span className="h-px flex-1 bg-rule" />
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted">or</span>
              <span className="h-px flex-1 bg-rule" />
            </div>

            {mode === "signup" ? (
              <div>
                <label
                  htmlFor="name"
                  className="font-mono text-[10px] uppercase tracking-widest text-muted"
                >
                  Name
                </label>
                <input
                  id="name"
                  type="text"
                  autoComplete="name"
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="mt-2 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
                />
              </div>
            ) : null}

            <div>
              <label
                htmlFor="email"
                className="font-mono text-[10px] uppercase tracking-widest text-muted"
              >
                Email
              </label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-2 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
              />
            </div>

            <div>
              <label
                htmlFor="password"
                className="font-mono text-[10px] uppercase tracking-widest text-muted"
              >
                Password
              </label>
              <input
                id="password"
                type="password"
                autoComplete={mode === "login" ? "current-password" : "new-password"}
                required
                minLength={6}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="mt-2 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
              />
            </div>

            {error ? (
              <p className="text-xs text-red" role="alert">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Please wait…" : mode === "login" ? "Log in" : "Start free trial"}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-ink-soft">
          {mode === "login" ? "New to Pagebird?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => {
              setError(null);
              setMode(mode === "login" ? "signup" : "login");
            }}
            className="font-mono text-[11px] uppercase tracking-widest text-ink underline decoration-rule underline-offset-4 hover:decoration-ink"
          >
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </p>
      </section>

      <PunchCardPanel />
    </div>
  );
}
