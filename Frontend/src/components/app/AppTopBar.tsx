import { LogsPanel } from "./LogsPanel";

export function AppTopBar({
  navOpen,
  onToggleNav,
  breadcrumb,
}: {
  navOpen: boolean;
  onToggleNav: () => void;
  breadcrumb?: React.ReactNode;
}) {
  return (
    <div className="flex h-12 shrink-0 items-center justify-between border-b border-ink bg-paper px-4">
      <div className="flex items-center">
        <button
          type="button"
          onClick={onToggleNav}
          aria-label={navOpen ? "Collapse sidebar" : "Expand sidebar"}
          aria-pressed={navOpen}
          className="border border-transparent p-1 text-ink-soft transition-colors hover:border-rule hover:text-ink"
        >
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
            <rect x="3" y="4" width="18" height="16" rx="1" />
            <path d="M9 4v16" />
          </svg>
        </button>
        {breadcrumb ? (
          <div className="ml-3 font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            {breadcrumb}
          </div>
        ) : null}
      </div>
      <LogsPanel />
    </div>
  );
}
