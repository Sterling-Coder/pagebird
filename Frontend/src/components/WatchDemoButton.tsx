"use client";

export function WatchDemoButton() {
  return (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event("pb-open-demo-video"))}
      className="flex h-14 items-center border-[3px] border-l-0 border-pb-ink px-6.5 text-[15px] font-bold"
    >
      Watch demo
    </button>
  );
}
