"use client";

import { useEffect, useState } from "react";

/** The "how it works" video player: a modal opened by the `pb-open-demo-video`
 * window event (see WatchDemoButton). Nothing shows until someone asks for it. */
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

  useEffect(() => {
    function onOpen() {
      setOpen(true);
    }
    window.addEventListener("pb-open-demo-video", onOpen);
    return () => window.removeEventListener("pb-open-demo-video", onOpen);
  }, []);

  return (
    <>
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
