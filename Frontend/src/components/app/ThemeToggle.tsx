"use client";

import { useTheme, type ThemeMode } from "./AppShell";
import { Icon } from "./ui";

const OPTIONS: { mode: ThemeMode; label: string; icon: string }[] = [
  {
    mode: "light",
    label: "Light",
    icon: "M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10zM12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42",
  },
  { mode: "dark", label: "Dark", icon: "M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z" },
  { mode: "system", label: "System", icon: "M2 4h20v12H2zM8 20h8M12 16v4" },
];

/** Compact Light / Dark / System switch for the app theme. */
export function ThemeToggle({ className = "", showLabels = false }: { className?: string; showLabels?: boolean }) {
  const { mode, setTheme } = useTheme();
  return (
    <div
      role="radiogroup"
      aria-label="Theme"
      data-tour="theme-toggle"
      className={`inline-flex items-center gap-0.5 rounded-full border border-[color:var(--app-border)] bg-[var(--app-surface-2)] p-0.5 ${className}`}
    >
      {OPTIONS.map((o) => {
        const active = mode === o.mode;
        return (
          <button
            key={o.mode}
            type="button"
            role="radio"
            aria-checked={active}
            aria-label={o.label}
            title={o.label}
            onClick={() => setTheme(o.mode)}
            className={`flex items-center gap-1.5 rounded-full px-1.5 py-1 text-[11.5px] transition-colors ${
              active
                ? "bg-[var(--app-surface)] text-[color:var(--app-ink)] shadow-[0_1px_2px_var(--app-shadow)]"
                : "text-[color:var(--app-muted)] hover:text-[color:var(--app-ink)]"
            }`}
          >
            <Icon d={o.icon} className="h-3.5 w-3.5" />
            {showLabels ? <span>{o.label}</span> : null}
          </button>
        );
      })}
    </div>
  );
}

export default ThemeToggle;
