"use client";

import { useEffect, useId, useRef, useState } from "react";
import Link from "next/link";
import { replayTour } from "./Tour";

const itemClass =
  "flex w-full items-center rounded-lg px-3 py-2 text-left text-[13px] text-[var(--app-ink,#1d1b18)] outline-none hover:bg-[var(--app-surface-2,#f6f2ea)] focus-visible:bg-[var(--app-surface-2,#f6f2ea)]";

/**
 * "?" help menu: replay the tour, open the guide, contact support.
 * `floating` pins it bottom-right of the viewport; pass false to place it inline (e.g. in a top bar).
 */
export function HelpButton({ floating = true }: { floating?: boolean }) {
  const [open, setOpen] = useState(false);
  const rootRef = useRef<HTMLDivElement>(null);
  const buttonRef = useRef<HTMLButtonElement>(null);
  const menuRef = useRef<HTMLDivElement>(null);
  const menuId = useId();

  useEffect(() => {
    if (!open) return;
    const id = requestAnimationFrame(() => menuRef.current?.querySelector<HTMLElement>("[role=menuitem]")?.focus());
    const onDown = (e: MouseEvent) => {
      if (!rootRef.current?.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      const items = Array.from(menuRef.current?.querySelectorAll<HTMLElement>("[role=menuitem]") ?? []);
      const at = items.indexOf(document.activeElement as HTMLElement);
      if (e.key === "Escape") {
        setOpen(false);
        buttonRef.current?.focus();
      } else if (e.key === "ArrowDown" || e.key === "ArrowUp") {
        e.preventDefault();
        const d = e.key === "ArrowDown" ? 1 : -1;
        items[(at + d + items.length) % items.length]?.focus();
      } else if (e.key === "Tab") {
        setOpen(false);
      }
    };
    document.addEventListener("mousedown", onDown);
    document.addEventListener("keydown", onKey);
    return () => {
      cancelAnimationFrame(id);
      document.removeEventListener("mousedown", onDown);
      document.removeEventListener("keydown", onKey);
    };
  }, [open]);

  return (
    <div ref={rootRef} className={floating ? "fixed bottom-4 right-4 z-40" : "relative"}>
      {open ? (
        <div
          ref={menuRef}
          id={menuId}
          role="menu"
          aria-label="Help"
          className={`absolute right-0 w-56 rounded-xl border border-[var(--app-border,#e2dccf)] bg-[var(--app-surface,#ffffff)] p-1.5 shadow-[0_12px_36px_rgba(10,9,8,0.18)] ${
            floating ? "bottom-full mb-2" : "top-full mt-2"
          }`}
        >
          <button
            type="button"
            role="menuitem"
            className={itemClass}
            onClick={() => {
              setOpen(false);
              replayTour();
            }}
          >
            Replay tour
          </button>
          <Link href="/app/help" role="menuitem" className={itemClass} onClick={() => setOpen(false)}>
            Getting started guide
          </Link>
          <Link href="/contact" role="menuitem" className={itemClass} onClick={() => setOpen(false)}>
            Contact support
          </Link>
        </div>
      ) : null}
      <button
        ref={buttonRef}
        type="button"
        aria-label="Help"
        aria-haspopup="menu"
        aria-expanded={open}
        aria-controls={open ? menuId : undefined}
        onClick={() => setOpen((v) => !v)}
        className={`flex items-center justify-center rounded-full border border-[var(--app-border,#e2dccf)] bg-[var(--app-surface,#ffffff)] text-[var(--app-ink-soft,#57524b)] transition-colors hover:text-[var(--app-ink,#1d1b18)] focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[var(--app-accent,#c86018)] ${
          floating ? "h-9 w-9 shadow-[0_6px_20px_rgba(10,9,8,0.14)]" : "h-7 w-7"
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="h-4 w-4" aria-hidden="true">
          <path d="M9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01" />
        </svg>
      </button>
    </div>
  );
}
