const NAV_ITEMS = [
  {
    label: "Documents",
    active: true,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <path d="M6 2h9l5 5v15H6z" />
        <path d="M15 2v5h5" />
      </svg>
    ),
  },
  {
    label: "History",
    active: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <circle cx="12" cy="12" r="9" />
        <path d="M12 7v5l3 3" />
      </svg>
    ),
  },
  {
    label: "Team",
    active: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <circle cx="9" cy="8" r="3" />
        <path d="M2 21c0-3.9 3.1-7 7-7s7 3.1 7 7" />
        <path d="M16 4.2a3 3 0 0 1 0 5.8" />
        <path d="M22 21c0-3.3-2.3-6-5.5-6.8" />
      </svg>
    ),
  },
  {
    label: "Settings",
    active: false,
    icon: (
      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-5 w-5">
        <circle cx="12" cy="12" r="3" />
        <path d="M19.4 15a1.7 1.7 0 0 0 .3 1.9l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.9-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.6 1.7 1.7 0 0 0-1.9.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.9 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.6-1.1 1.7 1.7 0 0 0-.3-1.9l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.9.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.9-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.9V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z" />
      </svg>
    ),
  },
];

export function AppNavRail() {
  return (
    <div className="flex w-14 shrink-0 flex-col items-center border-r border-ink bg-paper-dim py-4">
      <div className="mb-6 flex h-8 w-8 items-center justify-center bg-ink text-sm font-black uppercase text-paper">
        D
      </div>

      <nav className="flex flex-1 flex-col items-center gap-1">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.label}
            type="button"
            aria-label={item.label}
            className={`relative flex h-10 w-10 items-center justify-center transition-colors ${
              item.active ? "text-red" : "text-ink-soft hover:text-ink"
            }`}
          >
            {item.active ? (
              <span className="absolute left-0 top-1/2 h-5 w-[3px] -translate-y-1/2 bg-red" />
            ) : null}
            {item.icon}
          </button>
        ))}
      </nav>
    </div>
  );
}
