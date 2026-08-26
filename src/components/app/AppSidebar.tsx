"use client";

import { useState } from "react";

const TABS = ["Chat", "History"] as const;

const RECENT = [
  { client: "Ledgerline Group", lang: "French", pages: 24, time: "2 min ago" },
  { client: "Northstar Health", lang: "German", pages: 8, time: "19 min ago" },
  { client: "Fielda Ops", lang: "Japanese", pages: 41, time: "1 hr ago" },
];

export function AppSidebar() {
  const [tab, setTab] = useState<(typeof TABS)[number]>("Chat");

  return (
    <div className="flex w-full shrink-0 flex-col border-l border-ink bg-paper sm:w-80">
      <div className="flex border-b border-rule">
        {TABS.map((t) => (
          <button
            key={t}
            type="button"
            onClick={() => setTab(t)}
            className={`flex-1 border-b-2 px-4 py-3 font-mono text-[11px] uppercase tracking-widest transition-colors ${
              tab === t
                ? "border-red text-ink"
                : "border-transparent text-muted hover:text-ink-soft"
            }`}
          >
            {t}
          </button>
        ))}
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {tab === "Chat" ? (
          <div className="flex h-full items-center justify-center text-center">
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
              Ask anything about this document
            </p>
          </div>
        ) : (
          <div>
            <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-muted">
              Recent translations
            </p>
            <div className="divide-y divide-rule border-t border-rule">
              {RECENT.map((row) => (
                <div key={row.client} className="flex items-center justify-between py-2.5">
                  <div>
                    <p className="text-sm text-ink">{row.client}</p>
                    <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
                      {row.lang} · {row.pages} pages
                    </p>
                  </div>
                  <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
                    {row.time}
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>

      <div className="border-t border-rule p-3">
        <form onSubmit={(event) => event.preventDefault()} className="flex gap-2">
          <input
            type="text"
            placeholder="Ask anything, / prompts"
            className="flex-1 border border-rule bg-paper px-3 py-2 text-sm text-ink outline-none focus-visible:border-ink"
          />
          <button
            type="submit"
            aria-label="Send"
            className="flex h-9 w-9 shrink-0 items-center justify-center bg-red text-paper transition-opacity hover:opacity-90"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-4 w-4">
              <path d="M5 12h14" />
              <path d="M13 6l6 6-6 6" />
            </svg>
          </button>
        </form>
      </div>
    </div>
  );
}
