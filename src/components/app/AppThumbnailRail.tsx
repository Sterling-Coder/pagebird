const PAGES = Array.from({ length: 6 }, (_, i) => i + 1);

export function AppThumbnailRail() {
  return (
    <div className="hidden w-24 shrink-0 overflow-y-auto border-r border-rule bg-paper-dim py-4 sm:block">
      {PAGES.map((page) => (
        <button
          key={page}
          type="button"
          className={`group mx-auto mb-3 flex h-24 w-16 flex-col gap-1 border bg-paper p-2 transition-colors ${
            page === 1 ? "border-red" : "border-rule hover:border-ink"
          }`}
        >
          <div className="h-1 w-3/4 bg-ink/70" />
          <div className="h-1 w-1/2 bg-ink/70" />
          <div className="mt-1 h-1 w-full bg-rule" />
          <div className="h-1 w-full bg-rule" />
          <div className="h-1 w-2/3 bg-rule" />
          <span
            className={`mt-auto text-center font-mono text-[9px] ${
              page === 1 ? "text-red" : "text-muted"
            }`}
          >
            {page}
          </span>
        </button>
      ))}
    </div>
  );
}
