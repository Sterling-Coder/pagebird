"use client";

import { createContext, useContext, useState } from "react";
import { AppNavRail } from "./AppNavRail";

type ShellState = { navOpen: boolean; toggleNav: () => void };

const ShellContext = createContext<ShellState>({ navOpen: true, toggleNav: () => {} });

export function useAppShell(): ShellState {
  return useContext(ShellContext);
}

/** The /app frame: a warm-grey backdrop with a white sidebar and a white main
 * panel floating on it. Pages render inside the panel and never draw their own
 * navigation. */
export function AppShell({ children }: { children: React.ReactNode }) {
  const [navOpen, setNavOpen] = useState(true);
  return (
    <ShellContext.Provider value={{ navOpen, toggleNav: () => setNavOpen((v) => !v) }}>
      <div className="flex min-h-0 flex-1 gap-2 bg-[#e2ddd6] p-2">
        {navOpen ? <AppNavRail /> : null}
        <div className="flex min-w-0 flex-1 flex-col overflow-hidden rounded-[14px] bg-white">{children}</div>
      </div>
    </ShellContext.Provider>
  );
}
