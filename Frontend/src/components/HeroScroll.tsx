"use client";

import { useEffect } from "react";

/** Publishes how far the visitor has scrolled past the hero, as `--pb-scroll`
 * (0 at the top, 1 after most of a screen), so the glass wall can flatten into
 * hairline rules on the way to the next section. */
export default function HeroScroll() {
  useEffect(() => {
    const root = document.documentElement;
    let frame = 0;
    const update = () => {
      frame = 0;
      const p = Math.min(1, Math.max(0, window.scrollY / (window.innerHeight * 0.8)));
      root.style.setProperty("--pb-scroll", p.toFixed(3));
    };
    const onScroll = () => {
      if (!frame) frame = requestAnimationFrame(update);
    };
    update();
    window.addEventListener("scroll", onScroll, { passive: true });
    window.addEventListener("resize", onScroll);
    return () => {
      window.removeEventListener("scroll", onScroll);
      window.removeEventListener("resize", onScroll);
      if (frame) cancelAnimationFrame(frame);
      root.style.removeProperty("--pb-scroll");
    };
  }, []);
  return null;
}
