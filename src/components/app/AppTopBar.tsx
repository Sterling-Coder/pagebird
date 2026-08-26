import Link from "next/link";

export function AppTopBar() {
  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-ink bg-paper px-4">
      <div className="flex items-center gap-3">
        <button
          type="button"
          aria-label="Toggle sidebar"
          className="text-ink-soft transition-colors hover:text-ink"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
            <rect x="3" y="4" width="18" height="16" rx="1" />
            <path d="M9 4v16" />
          </svg>
        </button>
        <span className="font-mono text-[11px] text-ink-soft">
          field-ops-manual.pdf
        </span>
      </div>

      <div className="flex items-center gap-5 font-mono text-[11px] uppercase tracking-widest text-ink-soft">
        <Link href="#" className="transition-colors hover:text-ink">
          Share
        </Link>
        <Link href="#" className="transition-colors hover:text-ink">
          Help
        </Link>
        <Link
          href="/"
          className="border border-ink px-3 py-1.5 text-ink transition-colors hover:bg-ink hover:text-paper"
        >
          Exit
        </Link>
      </div>
    </div>
  );
}
