"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

// The demo opens by itself once per visitor, after they have scrolled a bit
// down the home page. "Once" is remembered in localStorage, so it holds across
// visits; a visitor who opens it themselves is never auto-prompted either.
const AUTO_SHOWN_KEY = "pb-demo-auto-shown";
const AUTO_OPEN_SCROLL_PX = 600;

// In-memory fallback for when storage is blocked, so a client-side return to
// "/" does not re-prompt within the same page session.
let shownThisSession = false;

function demoAlreadyShown(): boolean {
  if (shownThisSession) return true;
  try {
    return window.localStorage.getItem(AUTO_SHOWN_KEY) === "1";
  } catch {
    return false;
  }
}

function markDemoShown() {
  shownThisSession = true;
  try {
    window.localStorage.setItem(AUTO_SHOWN_KEY, "1");
  } catch {
    // storage blocked: worst case it can open again on a later visit
  }
}

export function DemoVideoButton() {
  const [open, setOpen] = useState(false);
  // Autoplay with sound is blocked when nothing the visitor clicked started
  // it, so the self-opened video starts muted (the controls unmute it).
  const [autoOpened, setAutoOpened] = useState(false);
  const pathname = usePathname();

  function show(auto: boolean) {
    markDemoShown();
    setAutoOpened(auto);
    setOpen(true);
  }

  useEffect(() => {
    if (pathname !== "/" || demoAlreadyShown()) return;
    function onScroll() {
      if (window.scrollY < AUTO_OPEN_SCROLL_PX) return;
      window.removeEventListener("scroll", onScroll);
      // The visitor may have opened it themselves since this effect ran.
      if (demoAlreadyShown()) return;
      show(true);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll(); // already scrolled past the point when the page loaded
    return () => window.removeEventListener("scroll", onScroll);
  }, [pathname]);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  // Lets other buttons on the page (e.g. the hero's "Watch demo") open this
  // same modal instead of duplicating the video/state elsewhere.
  useEffect(() => {
    function onOpen() {
      show(false);
    }
    window.addEventListener("pb-open-demo-video", onOpen);
    return () => window.removeEventListener("pb-open-demo-video", onOpen);
  }, []);

  return (
    <>
      <button
        type="button"
        onClick={() => show(false)}
        className="font-pb-mono-brand fixed right-6 bottom-6 z-40 flex items-center gap-2.5 border-[3px] border-pb-ink bg-pb-paper px-4 py-3 text-[12px] font-bold tracking-wide text-pb-ink uppercase shadow-[6px_6px_0_var(--color-pb-accent)] transition-all duration-300 hover:-translate-y-1 hover:shadow-[9px_9px_0_var(--color-pb-accent)] md:right-10 md:bottom-10"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-pb-accent text-pb-paper">
          <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3 translate-x-[1px]">
            <path d="M8 5v14l11-7z" />
          </svg>
        </span>
        How it works
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6"
          onClick={() => setOpen(false)}
        >
          <div
            className="relative max-h-[85vh] max-w-3xl border-[3px] border-pb-ink bg-black shadow-[10px_10px_0_var(--color-pb-accent)]"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close video"
              className="font-pb-mono-brand absolute -top-11 right-0 flex h-8 w-8 items-center justify-center border-2 border-[#f2ede0] text-[#f2ede0] hover:bg-[#f2ede0] hover:text-[#153a2e]"
            >
              ✕
            </button>
            <video
              className="block max-h-[85vh] max-w-full"
              src="/how-it-works.mp4"
              controls
              autoPlay
              muted={autoOpened}
              playsInline
            >
              Your browser doesn&rsquo;t support embedded video.
            </video>
          </div>
        </div>
      ) : null}
    </>
  );
}
