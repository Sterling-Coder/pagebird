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

      <aside
        className="relative hidden overflow-hidden bg-ink lg:block"
        aria-hidden="true"
      >
        <div
          className="absolute inset-0 opacity-[0.07]"
          style={{
            backgroundImage:
              "linear-gradient(var(--paper) 1px, transparent 1px), linear-gradient(90deg, var(--paper) 1px, transparent 1px)",
            backgroundSize: "56px 56px",
          }}
        />

        <div
          className="pointer-events-none absolute left-1/2 top-1/2 h-[60%] w-[60%] -translate-x-1/2 -translate-y-1/2 rounded-full opacity-40"
          style={{
            background:
              "radial-gradient(circle, var(--red) 0%, transparent 70%)",
            filter: "blur(80px)",
          }}
        />

        <p
          className="pointer-events-none absolute -bottom-[6vw] -right-[4vw] select-none text-[32vw] font-black uppercase leading-none tracking-tighter text-transparent"
          style={{ WebkitTextStroke: "1.5px rgba(253,252,247,0.18)" }}
        >
          D
        </p>

        <div
          className="pointer-events-none absolute -left-16 -top-16 h-56 w-56"
          style={{
            backgroundImage:
              "repeating-linear-gradient(45deg, var(--red) 0 14px, transparent 14px 28px)",
            opacity: 0.6,
          }}
        />

        <div className="absolute bottom-10 left-10 h-16 w-px bg-red" />
        <div className="absolute bottom-10 left-10 h-px w-16 bg-red" />

        <div
          className="pointer-events-none absolute left-[14%] top-[18%] h-24 w-32 -rotate-6 border border-paper/15 bg-paper/[0.03]"
          style={{ backdropFilter: "blur(2px)" }}
        >
          <div className="m-3 h-1.5 w-3/4 bg-paper/15" />
          <div className="mx-3 mt-2 h-1 w-1/2 bg-paper/10" />
        </div>

        <div
          className="pointer-events-none absolute left-[38%] top-[38%] h-28 w-36 rotate-3 border border-paper/15 bg-paper/[0.03]"
          style={{ backdropFilter: "blur(2px)" }}
        >
          <div className="m-3 h-1.5 w-2/3 bg-red/40" />
          <div className="mx-3 mt-2 h-1 w-1/2 bg-paper/10" />
          <div className="mx-3 mt-1.5 h-1 w-1/3 bg-paper/10" />
        </div>

        <div
          className="pointer-events-none absolute left-[22%] top-[58%] h-20 w-28 rotate-12 border border-paper/15 bg-paper/[0.03]"
          style={{ backdropFilter: "blur(2px)" }}
        >
          <div className="m-3 h-1.5 w-2/3 bg-paper/15" />
        </div>

        <div className="pointer-events-none absolute inset-y-0 left-0 w-1/3 overflow-hidden">
          <div
            className="animate-scan-sweep absolute inset-y-0 w-px"
            style={{
              background: "var(--red)",
              boxShadow: "0 0 16px 2px rgba(214,71,44,0.6)",
            }}
          />
        </div>
      </aside>
    </div>
  );
}
