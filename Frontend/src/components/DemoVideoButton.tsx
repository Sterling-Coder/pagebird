"use client";

import { useEffect, useRef, useState } from "react";
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
  const [dismissed, setDismissed] = useState(false);
  const previewRef = useRef<HTMLVideoElement>(null);
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
      {dismissed ? null : (
        <div
          className="group fixed right-6 bottom-6 z-40 hidden w-[300px] overflow-hidden rounded-2xl border border-white/15 bg-[#1a1814] shadow-[0_24px_60px_rgba(0,0,0,0.5)] transition-transform duration-300 hover:-translate-y-0.5 sm:block md:right-10 md:bottom-10"
          onMouseEnter={() => {
            if (window.matchMedia("(prefers-reduced-motion: reduce)").matches) return;
            previewRef.current?.play().catch(() => {});
          }}
          onMouseLeave={() => {
            const v = previewRef.current;
            if (v) {
              v.pause();
              v.currentTime = 0;
            }
          }}
        >
          <button
            type="button"
            onClick={() => show(false)}
            aria-label="Watch how it works"
            className="relative block aspect-video w-full cursor-pointer text-left focus-visible:outline-2 focus-visible:outline-offset-[-2px] focus-visible:outline-[#e08a6f]"
          >
            <video
              ref={previewRef}
              className="absolute inset-0 h-full w-full object-cover"
              src="/how-it-works.mp4"
              poster="/how-it-works-poster.jpg"
              preload="none"
              muted
              loop
              playsInline
            />
            <span className="absolute inset-0 bg-gradient-to-t from-black/85 via-black/10 to-black/20" />
            <span className="absolute inset-0 flex items-center justify-center">
              <span className="flex h-12 w-12 items-center justify-center rounded-full bg-[#e08a6f] text-[#1a1814] shadow-lg transition-all duration-200 group-hover:scale-110 group-hover:opacity-0">
                <svg viewBox="0 0 24 24" fill="currentColor" className="h-5 w-5 translate-x-[1px]">
                  <path d="M8 5v14l11-7z" />
                </svg>
              </span>
            </span>
            <span className="absolute right-3 bottom-3 left-3 flex items-end justify-between">
              <span className="text-[15px] leading-tight font-semibold text-[#f0ece3]">Watch how it works</span>
              <span className="rounded-md bg-black/60 px-1.5 py-0.5 text-[11px] font-medium text-[#f0ece3] tabular-nums">1:30</span>
            </span>
          </button>
          <button
            type="button"
            onClick={() => setDismissed(true)}
            aria-label="Dismiss video"
            className="absolute top-2 right-2 flex h-7 w-7 items-center justify-center rounded-full bg-black/55 text-[#f0ece3]/80 transition-colors hover:bg-black/80 hover:text-white focus-visible:outline-2 focus-visible:outline-[#e08a6f]"
          >
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" className="h-3.5 w-3.5">
              <path d="M6 6l12 12M18 6L6 18" />
            </svg>
          </button>
        </div>
      )}

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
