"use client";

import { useEffect, useState } from "react";
import { usePathname } from "next/navigation";

const AUTO_SHOWN_KEY = "pb-demo-auto-shown";
const AUTO_OPEN_SCROLL_PX = 600;

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
    // storage blocked
  }
}

export function DemoVideoButton() {
  const [open, setOpen] = useState(false);
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
      if (demoAlreadyShown()) return;
      show(true);
    }
    window.addEventListener("scroll", onScroll, { passive: true });
    onScroll();
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
        className="font-pb-mono fixed right-6 bottom-6 z-40 flex items-center gap-2.5 rounded-full border border-pb-border bg-pb-bg-card px-4 py-3 text-[11px] font-bold tracking-widest text-pb-text uppercase shadow-lg transition-all duration-300 hover:-translate-y-0.5 hover:border-pb-accent/30 md:right-10 md:bottom-10"
      >
        <span className="flex h-7 w-7 items-center justify-center rounded-full bg-pb-accent text-pb-bg">
          <svg viewBox="0 0 24 24" fill="currentColor" className="h-3 w-3 translate-x-[1px]">
            <path d="M8 5v14l11-7z" />
          </svg>
        </span>
        How it works
      </button>

      {open ? (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 p-6 backdrop-blur-sm"
          onClick={() => setOpen(false)}
        >
          <div
            className="relative max-h-[85vh] max-w-3xl overflow-hidden rounded-xl border border-pb-border bg-black shadow-2xl"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              type="button"
              onClick={() => setOpen(false)}
              aria-label="Close video"
              className="font-pb-mono absolute -top-10 right-0 flex h-8 w-8 items-center justify-center rounded-full border border-white/20 text-white/80 transition-colors hover:bg-white/10"
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
