"use client";

import { useEffect, useRef, useState, useSyncExternalStore } from "react";

const REDUCED_QUERY = "(prefers-reduced-motion: reduce)";

function subscribeReduced(onChange: () => void) {
  const mq = window.matchMedia(REDUCED_QUERY);
  mq.addEventListener("change", onChange);
  return () => mq.removeEventListener("change", onChange);
}

/** True when the visitor asked the OS for less motion. False on the server. */
export function useReducedMotion(): boolean {
  return useSyncExternalStore(
    subscribeReduced,
    () => window.matchMedia(REDUCED_QUERY).matches,
    () => false,
  );
}

/**
 * A looping demo clock. Ticks every `stepMs` while the element is on screen and
 * the visitor allows motion; otherwise it holds `restFrame` (a finished,
 * readable frame) so the demo still makes sense as a still image.
 */
export function useDemoClock<T extends Element>(cycle: number, restFrame: number, stepMs = 100) {
  const ref = useRef<T>(null);
  const [inView, setInView] = useState(false);
  const [tick, setTick] = useState(0);
  const reduced = useReducedMotion();

  useEffect(() => {
    const el = ref.current;
    if (!el) return;
    const io = new IntersectionObserver(([entry]) => setInView(entry.isIntersecting), { threshold: 0.25 });
    io.observe(el);
    return () => io.disconnect();
  }, []);

  const running = inView && !reduced;

  useEffect(() => {
    if (!running) return;
    const id = window.setInterval(() => setTick((t) => (t + 1) % cycle), stepMs);
    return () => window.clearInterval(id);
  }, [running, cycle, stepMs]);

  return { ref, t: reduced ? restFrame : tick, running };
}
