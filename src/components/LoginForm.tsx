"use client";

import { useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { GridPanel } from "./login-panels/GridPanel";
import { BlueprintPanel } from "./login-panels/BlueprintPanel";
import { PrintRegistrationPanel } from "./login-panels/PrintRegistrationPanel";
import { TerminalPanel } from "./login-panels/TerminalPanel";
import { CartographicPanel } from "./login-panels/CartographicPanel";
import { RadarPanel } from "./login-panels/RadarPanel";
import { PunchCardPanel } from "./login-panels/PunchCardPanel";

type Mode = "login" | "signup";

const PANELS = {
  grid: GridPanel,
  blueprint: BlueprintPanel,
  print: PrintRegistrationPanel,
  terminal: TerminalPanel,
  map: CartographicPanel,
  radar: RadarPanel,
  punch: PunchCardPanel,
} as const;

export function LoginForm() {
  const [mode, setMode] = useState<Mode>("login");
  const searchParams = useSearchParams();
  const panelParam = searchParams.get("panel");
  const Panel =
    panelParam && panelParam in PANELS
      ? PANELS[panelParam as keyof typeof PANELS]
      : PANELS.grid;

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

      <Panel />
    </div>
  );
}
