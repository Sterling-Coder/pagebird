"use client";

import { useEffect, useState } from "react";

export function DemoVideoButton() {
  const [open, setOpen] = useState(false);

  useEffect(() => {
    if (!open) return;
    function onKey(e: KeyboardEvent) {
      if (e.key === "Escape") setOpen(false);
    }
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open]);

  return (
    <>
      <button
        type="button"
        onClick={() => setOpen(true)}
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
