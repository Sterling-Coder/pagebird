"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";

type Mode = "login" | "signup";

export function LoginForm() {
  const [mode, setMode] = useState<Mode>("login");
  const [firstName, setFirstName] = useState("");
  const [lastName, setLastName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);
  const [awaitingOtp, setAwaitingOtp] = useState(false);
  const [otp, setOtp] = useState("");
  const [verifying, setVerifying] = useState(false);
  const [resending, setResending] = useState(false);
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
          options: {
            data: {
              first_name: firstName,
              last_name: lastName,
              full_name: `${firstName} ${lastName}`.trim(),
            },
          },
        });
        if (signUpError) throw signUpError;
        setAwaitingOtp(true);
        return;
      }
      const { error: signInError } = await supabase.auth.signInWithPassword({
        email,
        password,
      });
      if (signInError) throw signInError;
      router.push("/app");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Something went wrong");
    } finally {
      setLoading(false);
    }
  }

  async function handleVerifyOtp(event: React.FormEvent) {
    event.preventDefault();
    setError(null);
    setVerifying(true);
    const supabase = createClient();
    try {
      const { error: otpError } = await supabase.auth.verifyOtp({
        email,
        token: otp,
        type: "signup",
      });
      if (otpError) throw otpError;
      router.push("/app");
      router.refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Invalid or expired code");
    } finally {
      setVerifying(false);
    }
  }

  async function handleResendOtp() {
    setError(null);
    setResending(true);
    const supabase = createClient();
    try {
      const { error: resendError } = await supabase.auth.resend({ type: "signup", email });
      if (resendError) throw resendError;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to resend code");
    } finally {
      setResending(false);
    }
  }

  function handleGoogle() {
    setError("Google sign-in is coming soon — use email for now.");
  }

  function handleApple() {
    setError("Apple sign-in is coming soon — use email for now.");
  }

  return (
    <div className="flex min-h-screen flex-col bg-[#e2ddd6] p-2 text-ink">
      <div className="flex flex-1 flex-col gap-2 lg:flex-row">
      <div className="flex flex-1 flex-col rounded-[14px] bg-white">
      <Link
        href="/"
        className="mt-6 ml-6 inline-flex items-center gap-2 text-[11px] font-semibold tracking-widest text-[#6b6560] uppercase transition-colors hover:text-ink sm:mt-8 sm:ml-10"
      >
        ← Back
      </Link>

      <section className="mx-auto flex w-full max-w-md flex-1 flex-col justify-center px-6 py-10 sm:px-0">
        <span className="text-2xl tracking-[0.04em]" style={{ fontFamily: "var(--font-mono), monospace" }}>
          <span className="text-[#3a3630]">page</span>
          <span className="text-[#e08a6f]">birdy</span>
        </span>

        {awaitingOtp ? (
          <>
            <h1 className="mt-10 text-[40px] leading-[1.1] font-medium tracking-tight">
              Check your <span className="text-[#e08a6f] italic">email.</span>
            </h1>
            <p className="mt-3 text-[15px] text-[#6b6560]">
              We sent a 6-digit code to <span className="font-semibold text-ink">{email}</span>.
            </p>

            <form onSubmit={handleVerifyOtp} className="mt-10">
              <label htmlFor="otp" className="text-[11px] font-semibold tracking-widest uppercase">
                Verification code
              </label>
              <input
                id="otp"
                type="text"
                inputMode="numeric"
                autoComplete="one-time-code"
                required
                maxLength={6}
                placeholder="000000"
                value={otp}
                onChange={(e) => setOtp(e.target.value.replace(/\D/g, ""))}
                className="mt-2 w-full rounded-lg border border-[#e2d6c8] bg-[#f6f2ea] px-4 py-3 text-center text-lg tracking-[0.5em] text-ink placeholder-[#a39b8d] outline-none focus-visible:border-[#c86018]"
              />

              {error ? (
                <p className="mt-3 text-xs text-[#a8321a]" role="alert">
                  {error}
                </p>
              ) : null}

              <button
                type="submit"
                disabled={verifying || otp.length !== 6}
                className="mt-4 w-full rounded-full bg-[#c86018] px-6 py-3.5 text-sm font-bold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
              >
                {verifying ? "Verifying…" : "Verify email"}
              </button>

              <p className="mt-4 text-center text-xs text-[#6b6560]">
                Didn&rsquo;t get it?{" "}
                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resending}
                  className="font-semibold text-ink underline decoration-[#d9c9b6] underline-offset-4 hover:decoration-ink disabled:opacity-50"
                >
                  {resending ? "Sending…" : "Resend code"}
                </button>
              </p>
            </form>
          </>
        ) : (
          <>
            <h1 className="mt-10 text-[40px] leading-[1.1] font-medium tracking-tight">
              {mode === "login" ? (
                <>
                  Welcome <span className="text-[#e08a6f] italic">back.</span>
                </>
              ) : (
                <>
                  Get <span className="text-[#e08a6f] italic">started.</span>
                </>
              )}
            </h1>
            <p className="mt-3 text-[15px] text-[#6b6560]">
              {mode === "signup" ? "14-day free trial, no card required." : "Three ways in."}
            </p>

        <form onSubmit={handleSubmit} className="mt-10">
          {mode === "signup" ? (
            <div className="mb-5 grid grid-cols-2 gap-3">
              <div>
                <label htmlFor="firstName" className="text-[11px] font-semibold tracking-widest uppercase">
                  First name
                </label>
                <input
                  id="firstName"
                  type="text"
                  autoComplete="given-name"
                  required
                  placeholder="Jane"
                  value={firstName}
                  onChange={(e) => setFirstName(e.target.value)}
                  className="mt-2 w-full rounded-lg border border-[#e2d6c8] bg-[#f6f2ea] px-4 py-3 text-sm text-ink placeholder-[#a39b8d] outline-none focus-visible:border-[#c86018]"
                />
              </div>
              <div>
                <label htmlFor="lastName" className="text-[11px] font-semibold tracking-widest uppercase">
                  Last name
                </label>
                <input
                  id="lastName"
                  type="text"
                  autoComplete="family-name"
                  required
                  placeholder="Doe"
                  value={lastName}
                  onChange={(e) => setLastName(e.target.value)}
                  className="mt-2 w-full rounded-lg border border-[#e2d6c8] bg-[#f6f2ea] px-4 py-3 text-sm text-ink placeholder-[#a39b8d] outline-none focus-visible:border-[#c86018]"
                />
              </div>
            </div>
          ) : null}

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
            className="mt-2 w-full rounded-lg border border-[#e2d6c8] bg-[#f6f2ea] px-4 py-3 text-sm text-ink placeholder-[#a39b8d] outline-none focus-visible:border-[#c86018]"
          />

          <label htmlFor="password" className="mt-5 block text-[11px] font-semibold tracking-widest uppercase">
            Password
          </label>
          <div className="relative mt-2">
            <input
              id="password"
              type={showPassword ? "text" : "password"}
              autoComplete={mode === "login" ? "current-password" : "new-password"}
              required
              minLength={6}
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full rounded-lg border border-[#e2d6c8] bg-[#f6f2ea] px-4 py-3 pr-11 text-sm text-ink placeholder-[#a39b8d] outline-none focus-visible:border-[#c86018]"
            />
            <button
              type="button"
              onClick={() => setShowPassword((v) => !v)}
              aria-label={showPassword ? "Hide password" : "Show password"}
              className="absolute inset-y-0 right-0 flex w-11 items-center justify-center text-[#a39b8d] hover:text-ink"
            >
              {showPassword ? (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                  <path d="M9.5 4.5 3 21M14.5 3 8 19.5" />
                </svg>
              ) : (
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                  <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" />
                  <circle cx="12" cy="12" r="3" />
                </svg>
              )}
            </button>
          </div>

          {error ? (
            <p className="mt-3 text-xs text-[#a8321a]" role="alert">
              {error}
            </p>
          ) : null}

          <button
            type="submit"
            disabled={loading}
            className="mt-4 w-full rounded-full bg-[#c86018] px-6 py-3.5 text-sm font-bold text-white transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {loading ? "Please wait…" : mode === "login" ? "Log in" : "Create account"}
          </button>

          <p className="mt-4 text-center text-xs text-[#6b6560]">
            {mode === "login" ? "New to Pagebirdy?" : "Already have an account?"}{" "}
            <button
              type="button"
              onClick={() => {
                setError(null);
                setMode(mode === "login" ? "signup" : "login");
              }}
              className="font-semibold text-ink underline decoration-[#d9c9b6] underline-offset-4 hover:decoration-ink"
            >
              {mode === "login" ? "Sign up" : "Log in"}
            </button>
          </p>

          <div className="mt-7 flex items-center gap-3">
            <span className="h-px flex-1 bg-[#e2d6c8]" />
            <span className="text-[10px] font-semibold tracking-widest text-[#a39b8d] uppercase">
              Or, faster
            </span>
            <span className="h-px flex-1 bg-[#e2d6c8]" />
          </div>

          <div className="mt-5 flex flex-col gap-3">
            <button
              type="button"
              onClick={handleApple}
              className="flex items-center justify-center gap-2.5 rounded-full border border-[#e2d6c8] bg-white px-6 py-3.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
            >
              <svg viewBox="0 0 384 512" className="h-4 w-4" fill="currentColor">
                <path d="M318.7 268.7c-.2-36.7 16.4-64.4 50-84.8-18.8-26.9-47.2-41.7-84.7-44.6-35.5-2.8-74.3 20.7-88.5 20.7-15 0-49.4-19.7-76.4-19.7C63.3 141.2 4 184.8 4 273.5q0 39.3 14.4 81.2c12.8 36.7 59 126.7 107.2 125.2 25.2-.6 43-17.9 75.8-17.9 31.8 0 48.3 17.9 76.4 17.9 48.6-.7 90.4-82.5 102.6-119.3-65.2-30.7-61.7-90-61.7-91.9zm-56.6-164.2c27.3-32.4 24.8-61.9 24-72.5-24.1 1.4-52 16.4-67.9 34.9-17.5 19.8-27.8 44.3-25.6 71.9 26.1 2 49.9-11.4 69.5-34.3z" />
              </svg>
              Continue with Apple
            </button>
            <button
              type="button"
              onClick={handleGoogle}
              className="flex items-center justify-center gap-2.5 rounded-full border border-[#e2d6c8] bg-white px-6 py-3.5 text-sm font-semibold text-ink transition-opacity hover:opacity-90"
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
          </>
        )}
      </section>
      </div>

      <aside className="hidden flex-1 flex-col justify-between rounded-[14px] p-10 lg:flex" style={{ background: "linear-gradient(180deg,#cac9c8 0,#ac9f73 9%,#bb5706 19%,#8b3335 46%,#544b75 82%,#45699a 100%)" }}>
        <p className="text-[11px] font-bold tracking-[0.15em] text-black/55 uppercase">Layout-preserving translation</p>
        <div>
          <h2 className="max-w-[420px] text-[38px] leading-[1.08] font-medium tracking-tight text-white">
            Translate the document. Keep the design.
          </h2>
          <ul className="mt-6 space-y-2 text-[14px] text-white/80">
            <li>InDesign, PDF, Word, PowerPoint, Excel and images</li>
            <li>40+ languages, right-to-left included</li>
            <li>Fonts, columns, tables and page breaks stay put</li>
          </ul>
        </div>
      </aside>
      </div>
    </div>
  );
}
