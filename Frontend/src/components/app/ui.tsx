"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { listLanguages, type Language } from "@/lib/translate";

export const ICON = {
  home: "M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z",
  inbox: "M22 12h-6l-2 3h-4l-2-3H2M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z",
  jobs: "M3 3h18v18H3zM9 3v18M15 3v18",
  projects: "M22 19a2 2 0 0 1-2 2H4a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h5l2 3h9a2 2 0 0 1 2 2z",
  agents: "M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2M12 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
  glossary: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6M8 13h8M8 17h5",
  flow: "M6 3v12M18 9a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM6 21a3 3 0 1 0 0-6 3 3 0 0 0 0 6zM18 9a9 9 0 0 1-9 9",
  puzzle: "M12 2a2 2 0 0 1 2 2v1h4a2 2 0 0 1 2 2v4h-1a2 2 0 1 0 0 4h1v4a2 2 0 0 1-2 2h-4v-1a2 2 0 1 0-4 0v1H6a2 2 0 0 1-2-2v-4h1a2 2 0 1 0 0-4H4V7a2 2 0 0 1 2-2h4V4a2 2 0 0 1 2-2z",
  team: "M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2M9 11a4 4 0 1 0 0-8 4 4 0 0 0 0 8zM23 21v-2a4 4 0 0 0-3-3.87M16 3.13a4 4 0 0 1 0 7.75",
  settings: "M12 15a3 3 0 1 0 0-6 3 3 0 0 0 0 6z",
  arrow: "M7 17L17 7M8 7h9v9",
  user: "M20 21v-1a5 5 0 0 0-5-5H9a5 5 0 0 0-5 5v1M12 12a4 4 0 1 0 0-8 4 4 0 0 0 0 8z",
};

export function Icon({ d, className = "h-[15px] w-[15px]" }: { d: string; className?: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" strokeLinecap="round"
      strokeLinejoin="round" className={`shrink-0 ${className}`}>
      <path d={d} />
    </svg>
  );
}

/** Title row of an app page: icon, title, count, one line of description, actions. */
export function PageHeader({ icon, title, count, desc, right }: {
  icon: string; title: string; count?: number; desc?: string; right?: ReactNode;
}) {
  return (
    <div className="flex flex-wrap items-center gap-2.5 pb-4 pl-6 pr-14 pt-5">
      <span className="text-ink-soft"><Icon d={icon} /></span>
      <h1 className="text-[15px] font-semibold text-ink">{title}</h1>
      {count !== undefined ? <span className="text-[12.5px] text-muted">{count}</span> : null}
      {desc ? <span className="hidden text-[12.5px] text-muted md:inline">{desc}</span> : null}
      <div className="ml-auto flex items-center gap-2">{right}</div>
    </div>
  );
}

export function Pill({ children, active = false, onClick }: { children: ReactNode; active?: boolean; onClick?: () => void }) {
  return (
    <button type="button" onClick={onClick}
      className={`rounded-full border px-3 py-1 text-[12.5px] transition-colors ${
        active
          ? "border-[color:var(--app-ink)] bg-[var(--app-ink)] text-[color:var(--app-surface)]"
          : "border-[color:var(--app-border-strong)] bg-[var(--app-surface)] text-ink-soft hover:border-[color:var(--app-border-hover)]"
      }`}>
      {children}
    </button>
  );
}

export function PrimaryButton({ children, disabled, type = "button", onClick }: {
  children: ReactNode; disabled?: boolean; type?: "button" | "submit"; onClick?: () => void;
}) {
  return (
    <button type={type} disabled={disabled} onClick={onClick}
      className="rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90 disabled:opacity-40">
      {children}
    </button>
  );
}

// Text/background use theme tokens (globals.css .app-theme) so badges read in
// both light and dark; dots are mid-tone and work on either.
export const STATUS_STYLE: Record<string, { label: string; dot: string; text: string; bg: string }> = {
  processing: { label: "Translating", dot: "#e08a2c", text: "var(--app-warn)", bg: "var(--app-warn-bg)" },
  complete: { label: "Delivered", dot: "#4caf50", text: "var(--app-success)", bg: "var(--app-success-bg)" },
  failed: { label: "Failed", dot: "#d9534f", text: "var(--app-danger)", bg: "var(--app-danger-bg)" },
};

export function StatusBadge({ status }: { status: string }) {
  const s = STATUS_STYLE[status] ?? { label: status, dot: "#a39b8d", text: "var(--app-ink-soft)", bg: "var(--app-neutral-bg)" };
  return (
    <span className="inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-[11.5px]" style={{ color: s.text, background: s.bg }}>
      <span className="h-1.5 w-1.5 rounded-full" style={{ background: s.dot }} />
      {s.label}
    </span>
  );
}

/** Target-language picker fed by GET /api/languages. */
export function LanguageSelect({ value, onChange }: { value: string; onChange: (code: string) => void }) {
  const [langs, setLangs] = useState<Language[]>([]);
  useEffect(() => {
    listLanguages()
      .then((r) => {
        setLangs(r.languages);
        if (!value) onChange(r.default);
      })
      .catch(() => setLangs([]));
    // Load once; `onChange` only seeds the default.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
  return (
    <select value={value} onChange={(e) => onChange(e.target.value)} aria-label="Target language"
      className="rounded-xl border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-2 text-[13px] text-ink outline-none focus:border-[color:var(--app-accent)]">
      {langs.length === 0 ? <option value={value}>{value || "Loading…"}</option> : null}
      {langs.map((l) => <option key={l.code} value={l.code}>{l.name}</option>)}
    </select>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="rounded-xl bg-[var(--app-surface-2)] px-4 py-6 text-center text-[13px] text-muted">{children}</p>;
}

export function timeAgo(epochSec: number): string {
  const s = Math.max(0, Date.now() / 1000 - epochSec);
  if (s < 60) return "just now";
  if (s < 3600) return `${Math.floor(s / 60)} min ago`;
  if (s < 86400) return `${Math.floor(s / 3600)} h ago`;
  return new Date(epochSec * 1000).toLocaleDateString();
}
