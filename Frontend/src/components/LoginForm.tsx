"use client";

import { useState } from "react";
import Link from "next/link";
import { Fraunces } from "next/font/google";
import { createClient } from "@/lib/supabase/client";

const fraunces = Fraunces({
  variable: "--font-login-display",
  subsets: ["latin"],
  weight: ["500", "600"],
  style: ["normal", "italic"],
});

export function LoginForm() {
  const [email, setEmail] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [sent, setSent] = useState(false);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setLoading(true);
    const supabase = createClient();

    try {
      const { error: otpError } = await supabase.auth.signInWithOtp({
        email,
        options: { emailRedirectTo: `${window.location.origin}/auth/callback` },
      });
      if (otpError) throw otpError;
      setSent(true);
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

  function handleApple() {
    setError("Apple sign-in is coming soon — use email or Google for now.");
  }

  return (
    <div
      className={`${fraunces.variable} relative min-h-screen overflow-hidden bg-[#153a2e] text-[#f2ede0]`}
    >
      <svg
        className="pointer-events-none absolute inset-0 h-full w-full opacity-40"
        viewBox="0 0 1600 1000"
        preserveAspectRatio="xMidYMid slice"
        fill="none"
        aria-hidden="true"
      >
        <path
          d="M420 -50 C 700 150, 250 500, 550 850 C 800 1080, 1200 900, 1350 650"
          stroke="#8a9a5b"
          strokeWidth="2.5"
        />
        <path
          d="M950 -80 C 650 200, 1450 350, 1150 700 C 950 950, 500 950, 150 780"
          stroke="#8a9a5b"
          strokeWidth="2.5"
        />
        <path
          d="M-100 700 C 300 550, 400 900, 750 1000"
          stroke="#8a9a5b"
          strokeWidth="2.5"
        />
      </svg>

      <Link
        href="/"
        className="relative z-10 mt-6 ml-6 inline-flex items-center gap-2 text-[11px] font-semibold tracking-widest text-[#c9c4b0] uppercase transition-colors hover:text-[#f2ede0] sm:mt-8 sm:ml-10"
      >
        ← Back
      </Link>

      <section className="relative z-10 mx-auto flex w-full max-w-md flex-col px-6 pt-16 pb-24 sm:ml-10 sm:px-0">
        <span
          className="text-3xl italic"
          style={{ fontFamily: "var(--font-login-display), Georgia, serif" }}
        >
          pagebird
        </span>

        <h1
          className="mt-10 text-5xl font-medium"
          style={{ fontFamily: "var(--font-login-display), Georgia, serif" }}
        >
          Welcome <span className="text-[#e08a6f] italic">back.</span>
        </h1>
        <p className="mt-3 text-[15px] text-[#c9c4b0]">
          Three ways in. No password to remember.
        </p>

        {sent ? (
          <div className="mt-10 border border-[#3d5847] bg-[#1b4436] px-5 py-4 text-sm text-[#f2ede0]">
            Check <span className="font-semibold">{email}</span> for a link to sign in.
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="mt-10">
            <label htmlFor="email" className="text-[11px] font-semibold tracking-widest uppercase">
              Email
            </label>
            <input
              id="email"
              type="email"
              autoComplete="email"
              required
              placeholder="you@somewhere"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-2 w-full rounded-lg border border-[#3d5847] bg-[#1e4536] px-4 py-3 text-sm text-[#f2ede0] placeholder-[#8fa090] outline-none focus-visible:border-[#e08a6f]"
            />

            {error ? (
              <p className="mt-3 text-xs text-[#e08a6f]" role="alert">
                {error}
              </p>
            ) : null}

            <button
              type="submit"
              disabled={loading}
              className="mt-4 w-full rounded-full bg-[#e08a6f] px-6 py-3.5 text-sm font-bold text-[#153a2e] transition-opacity hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "Sending…" : "Send the link"}
            </button>

            <div className="mt-7 flex items-center gap-3">
              <span className="h-px flex-1 bg-[#3d5847]" />
              <span className="text-[10px] font-semibold tracking-widest text-[#8fa090] uppercase">
                Or, faster
              </span>
              <span className="h-px flex-1 bg-[#3d5847]" />
            </div>

            <div className="mt-5 flex flex-col gap-3">
              <button
                type="button"
                onClick={handleApple}
                className="flex items-center justify-center gap-2.5 rounded-full bg-[#f2ede0] px-6 py-3.5 text-sm font-semibold text-[#153a2e] transition-opacity hover:opacity-90"
              >
                <svg viewBox="0 0 384 512" className="h-4 w-4" fill="currentColor">
                  <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
                </svg>
                Continue with Apple
              </button>
              <button
                type="button"
                onClick={handleGoogle}
                className="flex items-center justify-center gap-2.5 rounded-full bg-[#f2ede0] px-6 py-3.5 text-sm font-semibold text-[#153a2e] transition-opacity hover:opacity-90"
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
            </div>
          </form>
        )}
      </section>
    </div>
  );
}
