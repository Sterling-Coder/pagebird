"use client";

/** Opens the "how it works" video (the player lives in DemoVideoButton, mounted
 * once by the marketing layout). Sits next to the primary call to action. */
export function WatchDemoButton() {
  return (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event("pb-open-demo-video"))}
      className="group inline-flex items-center gap-3 rounded-full py-1 pr-4 pl-1 text-[14px] font-semibold text-[#f0ece3] outline-none transition-colors hover:text-white focus-visible:ring-2 focus-visible:ring-[#e08a6f]"
    >
      <span className="flex h-10 w-10 items-center justify-center rounded-full bg-[#f0ece3] text-[#1a1814] transition-transform duration-200 group-hover:scale-105">
        <svg viewBox="0 0 24 24" fill="currentColor" className="h-4 w-4 translate-x-[1px]" aria-hidden>
          <path d="M8 5v14l11-7z" />
        </svg>
      </span>
      <span className="flex flex-col items-start leading-tight">
        Watch the demo
        <span className="text-[12px] font-normal text-[#f0ece3]/70 tabular-nums">1:30</span>
      </span>
    </button>
  );
}
