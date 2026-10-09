"use client";

import NotificationBell from "./NotificationBell";

/** Notifications bell pinned to the top-right corner of the main panel. It
 * floats over the page so it takes no vertical space. */
export function AppTopBar() {
  return (
    <div data-tour="notifications" className="absolute right-4 top-4 z-20 flex items-center">
      <NotificationBell />
    </div>
  );
}

export function SidebarIcon() {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
      <rect x="3" y="4" width="18" height="16" rx="1" />
      <path d="M9 4v16" />
    </svg>
  );
}
