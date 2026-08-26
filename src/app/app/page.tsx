"use client";

import { useState } from "react";
import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";
import { TranslateWorkspace } from "@/components/app/TranslateWorkspace";
import { AppSidebar } from "@/components/app/AppSidebar";

export default function AppWorkspacePage() {
  const [navOpen, setNavOpen] = useState(true);

  return (
    <div className="flex h-screen bg-paper">
      {navOpen ? <AppNavRail /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar navOpen={navOpen} onToggleNav={() => setNavOpen((v) => !v)} />
        <div className="flex min-h-0 flex-1">
          <TranslateWorkspace />
          <AppSidebar />
        </div>
      </div>
    </div>
  );
}
