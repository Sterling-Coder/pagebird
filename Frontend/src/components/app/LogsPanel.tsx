"use client";

import { useEffect, useRef, useState } from "react";
import { getLogs, type LogLine } from "@/lib/logs";

const POLL_MS = 2000;
const MAX_LINES = 300;

export function LogsPanel() {
  const [open, setOpen] = useState(false);
  const [lines, setLines] = useState<LogLine[]>([]);
  const lastIdRef = useRef(0);
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    let cancelled = false;

    async function poll() {
      try {
        const next = await getLogs(lastIdRef.current);
        if (cancelled || next.length === 0) return;
        lastIdRef.current = next[next.length - 1].id;
        setLines((prev) => [...prev, ...next].slice(-MAX_LINES));
      } catch {
        // best-effort — try again next tick
      }
    }

    poll();
    const interval = setInterval(poll, POLL_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, [open]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [lines]);

  return (
    <div className="relative">
      <button
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-pressed={open}
        className={`flex items-center gap-2 font-mono text-[11px] uppercase tracking-widest transition-colors ${
          open ? "text-red" : "text-ink-soft hover:text-ink"
        }`}
      >
        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-3.5 w-3.5">
          <path d="M4 4h16v12H8l-4 4z" />
          <path d="M8 9h8M8 12h5" />
        </svg>
        Logs
      </button>

      {open ? (
        <div className="absolute right-0 top-full z-50 mt-2 w-[520px] max-w-[80vw] border border-ink bg-ink text-paper shadow-lg">
          <div className="flex items-center justify-between border-b border-paper/20 px-3 py-1.5">
            <span className="font-mono text-[10px] uppercase tracking-widest text-paper/60">
              Server activity
            </span>
            <button
              type="button"
              onClick={() => setLines([])}
              className="font-mono text-[10px] uppercase tracking-widest text-paper/60 hover:text-paper"
            >
              Clear
            </button>
          </div>
          <div
            ref={scrollRef}
            className="h-72 overflow-auto p-3 font-mono text-[11px] leading-relaxed"
          >
            {lines.length === 0 ? (
              <p className="text-paper/40">Waiting for activity…</p>
            ) : (
              lines.map((l) => (
                <p
                  key={l.id}
                  className={l.level === "ERROR" ? "text-red" : "text-paper/80"}
                >
                  {l.line}
                </p>
              ))
            )}
          </div>
        </div>
      ) : null}
    </div>
  );
}
