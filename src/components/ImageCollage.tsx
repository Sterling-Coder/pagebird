"use client";

import { useRef } from "react";
import { motion, useScroll, useTransform } from "framer-motion";

export function ImageCollage() {
  const containerRef = useRef<HTMLDivElement>(null);
  const { scrollYProgress } = useScroll({
    target: containerRef,
    offset: ["start end", "end start"],
  });
  const y = useTransform(scrollYProgress, [0, 1], ["-8%", "8%"]);

  return (
    <div
      ref={containerRef}
      className="relative mt-4 aspect-[7/2] w-full"
      aria-hidden="true"
    >
      <div className="absolute left-0 top-0 h-full w-[42%] bg-gradient-to-br from-ink-soft via-ink/70 to-red/60" />
      <motion.div
        className="absolute left-[37%] top-[16%] h-[78%] w-[30%] z-10 shadow-[0_8px_24px_rgba(0,0,0,0.25)]"
        style={{
          y,
          backgroundImage:
            "repeating-linear-gradient(45deg, var(--red) 0 14px, #1a1714 14px 28px)",
        }}
      />
      <div className="absolute left-[71%] top-0 h-[75%] w-[29%] bg-gradient-to-br from-red via-ink to-ink" />
    </div>
  );
}
