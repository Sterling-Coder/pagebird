"use client";

import { useState } from "react";

type Mode = "login" | "signup";

export function LoginForm() {
  const [mode, setMode] = useState<Mode>("login");

  return (
    <section className="mx-auto flex min-h-[70vh] max-w-md flex-col justify-center px-6 py-16 sm:px-8">
      <span className="font-mono text-[11px] uppercase tracking-widest text-red">
        {mode === "login" ? "Welcome back" : "Create account"}
      </span>
      <h1 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
        {mode === "login" ? "Log in to Docly" : "Sign up for Docly"}
      </h1>

      <div className="relative mt-8">
        <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
        <form
          onSubmit={(event) => event.preventDefault()}
          className="relative z-10 space-y-5 border-2 border-ink bg-paper p-6"
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
  );
}
