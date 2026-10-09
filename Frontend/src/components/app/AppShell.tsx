"use client";

import { createContext, useCallback, useContext, useState, useSyncExternalStore } from "react";
import { AppNavRail } from "./AppNavRail";
import { SidebarIcon } from "./AppTopBar";

type ShellState = { navOpen: boolean; toggleNav: () => void };

const ShellContext = createContext<ShellState>({ navOpen: true, toggleNav: () => {} });

export function useAppShell(): ShellState {
  return useContext(ShellContext);
}

// ---------------------------------------------------------------------------
// Theme. The choice ("light" | "dark" | "system") lives in localStorage under
// `pb-theme`; "system" follows prefers-color-scheme. The resolved theme goes on
// the shell root as data-theme, which switches the --app-* tokens in
// globals.css. An inline script sets the attribute while the HTML is parsed so
// a hard load doesn't flash light before hydration.

export type ThemeMode = "light" | "dark" | "system";
export type Theme = "light" | "dark";

const STORAGE_KEY = "pb-theme";
const DARK_QUERY = "(prefers-color-scheme: dark)";

let memoryMode: ThemeMode | null = null; // used when storage is unavailable
const modeListeners = new Set<() => void>();

function isMode(v: unknown): v is ThemeMode {
  return v === "light" || v === "dark" || v === "system";
}

function readMode(): ThemeMode {
  if (memoryMode) return memoryMode;
  try {
    const v = window.localStorage.getItem(STORAGE_KEY);
    if (isMode(v)) return v;
  } catch {
    // storage blocked (private mode, sandbox)
  }
  return "system";
}

function writeMode(mode: ThemeMode) {
  memoryMode = mode;
  try {
    window.localStorage.setItem(STORAGE_KEY, mode);
  } catch {
    // keep the in-memory choice for this session
  }
  modeListeners.forEach((l) => l());
}

function subscribeMode(cb: () => void) {
  modeListeners.add(cb);
  const onStorage = (e: StorageEvent) => {
    if (e.key === STORAGE_KEY) {
      memoryMode = null;
      cb();
    }
  };
  window.addEventListener("storage", onStorage);
  return () => {
    modeListeners.delete(cb);
    window.removeEventListener("storage", onStorage);
  };
}

function subscribeSystem(cb: () => void) {
  const mq = window.matchMedia(DARK_QUERY);
  mq.addEventListener("change", cb);
  return () => mq.removeEventListener("change", cb);
}

const systemDark = () => window.matchMedia(DARK_QUERY).matches;

type ThemeState = { theme: Theme; mode: ThemeMode; setTheme: (mode: ThemeMode) => void };

const ThemeContext = createContext<ThemeState>({ theme: "light", mode: "system", setTheme: () => {} });

/** Current app theme. `theme` is the resolved light/dark value, `mode` the
 * user's choice, `setTheme` stores a new choice. */
export function useTheme(): ThemeState {
  return useContext(ThemeContext);
}

// Runs during HTML parsing, before first paint, on hard loads only.
const THEME_SCRIPT = `(function(){try{var el=document.currentScript&&document.currentScript.parentElement;if(!el)return;var m=null;try{m=localStorage.getItem(${JSON.stringify(
  STORAGE_KEY,
)})}catch(e){}var d=m==="dark"||((m!=="light")&&window.matchMedia(${JSON.stringify(DARK_QUERY)}).matches);el.setAttribute("data-theme",d?"dark":"light")}catch(e){}})()`;

function InlineScript({ html }: { html: string }) {
  // text/plain on the client so React neither warns nor re-runs it.
  return (
    <script
      type={typeof window === "undefined" ? "text/javascript" : "text/plain"}
      suppressHydrationWarning
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

/** The /app frame: a warm-grey backdrop with a sidebar and a main panel
 * floating on it. Pages render inside the panel and never draw their own
 * navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [navOpen, setNavOpen] = useState(true);
  const mode = useSyncExternalStore<ThemeMode>(subscribeMode, readMode, () => "system");
  const prefersDark = useSyncExternalStore(subscribeSystem, systemDark, () => false);
  const theme: Theme = mode === "system" ? (prefersDark ? "dark" : "light") : mode;
  const setTheme = useCallback((m: ThemeMode) => writeMode(m), []);

  return (
    <ThemeContext.Provider value={{ theme, mode, setTheme }}>
      <ShellContext.Provider value={{ navOpen, toggleNav: () => setNavOpen((v) => !v) }}>
        <div
          data-theme={theme}
          suppressHydrationWarning
          className="app-theme flex min-h-0 flex-1 gap-2 bg-[var(--app-frame)] p-2 text-[color:var(--app-ink)]"
        >
          <InlineScript html={THEME_SCRIPT} />
          {navOpen ? (
            <AppNavRail />
          ) : (
            <button
              type="button"
              onClick={() => setNavOpen(true)}
              aria-label="Expand sidebar"
              className="hidden self-start rounded-md p-1.5 text-[color:var(--app-muted)] transition-colors hover:bg-[var(--app-nav-hover)] hover:text-[color:var(--app-ink)] md:block"
            >
              <SidebarIcon />
            </button>
          )}
          <div className="relative flex min-w-0 flex-1 flex-col overflow-hidden rounded-[14px] bg-[var(--app-surface)]">
            {children}
          </div>
        </div>
      </ShellContext.Provider>
    </ThemeContext.Provider>
  );
}
