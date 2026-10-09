"use client";

export function WatchDemoButton() {
  return (
    <button
      type="button"
      onClick={() => window.dispatchEvent(new Event("pb-open-demo-video"))}
      className="font-pb-mono text-[12px] tracking-widest text-pb-text-secondary uppercase transition-colors hover:text-pb-text"
    >
      Watch demo →
    </button>
  );
}
