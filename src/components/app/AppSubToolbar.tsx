"use client";

import { useState } from "react";

type View = "bilingual" | "original";

export function AppSubToolbar() {
  const [view, setView] = useState<View>("bilingual");
  const [page, setPage] = useState(1);
  const totalPages = 18;

  return (
    <div className="flex h-11 shrink-0 items-center justify-between border-b border-rule bg-paper-dim px-4 font-mono text-[11px] uppercase tracking-widest text-muted">
      <div className="flex items-center gap-4">
        <button
          type="button"
          onClick={() => setPage((p) => Math.max(1, p - 1))}
          className="transition-colors hover:text-ink"
          aria-label="Previous page"
        >
          ←
        </button>
        <span>
          Page {page} / {totalPages}
        </span>
        <button
          type="button"
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          className="transition-colors hover:text-ink"
          aria-label="Next page"
        >
          →
        </button>
      </div>

      <button
        type="button"
        onClick={() => setView(view === "bilingual" ? "original" : "bilingual")}
        className="text-red transition-opacity hover:opacity-80"
      >
        {view === "bilingual" ? "Close translation" : "Show translation"}
      </button>

      <button
        type="button"
        className="border border-ink px-3 py-1 text-ink transition-colors hover:bg-ink hover:text-paper"
      >
        Export ↓
      </button>
    </div>
  );
}
