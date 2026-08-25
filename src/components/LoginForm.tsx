"use client";

import { useState } from "react";
import Link from "next/link";

type Mode = "login" | "signup";

export function LoginForm() {
  const [mode, setMode] = useState<Mode>("login");

  return (
    <div className="relative grid w-full flex-1 lg:grid-cols-2">
      <Link
        href="/"
        aria-label="Back to Docly"
        className="fixed left-6 top-6 z-20 flex h-9 w-9 items-center justify-center border border-ink bg-paper text-ink-soft transition-colors hover:border-ink hover:text-ink sm:left-8 sm:top-8 lg:border-paper/30 lg:bg-transparent lg:text-paper/70 lg:hover:border-paper lg:hover:text-paper"
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

      <aside className="relative hidden overflow-hidden bg-ink text-paper lg:flex lg:flex-col lg:justify-between lg:p-10">
        <span className="mt-8 font-mono text-[11px] uppercase tracking-widest text-red">
          Docly · Translation × Layout × Accuracy
        </span>

        <div>
          <p className="max-w-sm text-3xl font-black uppercase leading-[1.05] tracking-tight">
            One account,
            <br />
            every language,
            <br />
            <span className="text-red">every pixel.</span>
          </p>
          <p className="mt-4 max-w-xs text-sm leading-relaxed text-paper/70">
            Manage your translations, formats and team from a single place.
            No separate logins for the extension and the translator.
          </p>
        </div>

        <div className="flex items-end justify-between border-t border-paper/20 pt-6 font-mono text-[11px] uppercase tracking-widest text-paper/50">
          <span>95% accuracy</span>
          <span>30+ languages</span>
          <span>4 formats</span>
        </div>

        <div
          className="pointer-events-none absolute -right-16 -top-16 h-48 w-48"
          style={{
            backgroundImage:
              "repeating-linear-gradient(45deg, var(--red) 0 14px, transparent 14px 28px)",
            opacity: 0.5,
          }}
          aria-hidden="true"
        />
      </aside>

      <section className="mx-auto flex w-full max-w-md flex-col items-center justify-center px-6 py-16 text-center sm:px-8">
        <span className="font-mono text-[11px] uppercase tracking-widest text-red">
          {mode === "login" ? "Welcome back" : "Create account"}
        </span>
        <h1 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
          {mode === "login" ? "Log in to Docly" : "Sign up for Docly"}
        </h1>

        <div className="relative mt-8 w-full">
          <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
          <form
            onSubmit={(event) => event.preventDefault()}
            className="relative z-10 space-y-5 border-2 border-ink bg-paper p-6 text-left"
          >
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
                className="mt-2 w-full border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
              />
            </div>

            <button
              type="submit"
              className="w-full bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90"
            >
              {mode === "login" ? "Log in" : "Create account"}
            </button>
          </form>
        </div>

        <p className="mt-6 text-center text-sm text-ink-soft">
          {mode === "login" ? "New to Docly?" : "Already have an account?"}{" "}
          <button
            type="button"
            onClick={() => setMode(mode === "login" ? "signup" : "login")}
            className="font-mono text-[11px] uppercase tracking-widest text-ink underline decoration-rule underline-offset-4 hover:decoration-ink"
          >
            {mode === "login" ? "Sign up" : "Log in"}
          </button>
        </p>
      </section>
    </div>
  );
}
