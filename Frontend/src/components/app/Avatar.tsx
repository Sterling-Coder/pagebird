"use client";

import { useState } from "react";

const GRADIENTS = ["#6b9cf4,#8b6fbf", "#e6a15a,#d0644a", "#5fb38f,#3d8a8a", "#d77fa1,#9b5fb5", "#7fb3d7,#4a7fb0"];

function gradientFor(seed: string) {
  let hash = 0;
  for (const ch of seed) hash = (hash * 31 + ch.charCodeAt(0)) >>> 0;
  return `linear-gradient(135deg,${GRADIENTS[hash % GRADIENTS.length]})`;
}

/** Round avatar: the uploaded photo when there is one, otherwise an initial on
 * a gradient picked from `seed` (an email or id) so a person keeps one colour.
 * `pending` draws a dashed outline for someone who hasn't joined yet. */
export function Avatar({ url, name, seed, size = 28, pending = false }: {
  url?: string | null;
  name: string;
  seed?: string;
  size?: number;
  pending?: boolean;
}) {
  const [broken, setBroken] = useState<string | null>(null);
  const initial = name.trim().charAt(0).toUpperCase() || "?";
  const box = { width: size, height: size, fontSize: Math.round(size * 0.4) };

  if (url && broken !== url && !pending) {
    return (
      // A user upload on Supabase Storage; next/image would need the host allow-listed for no gain at this size.
      // eslint-disable-next-line @next/next/no-img-element
      <img src={url} alt="" onError={() => setBroken(url)} style={box}
        className="shrink-0 rounded-full object-cover" />
    );
  }
  if (pending) {
    return (
      <span aria-hidden="true" style={box}
        className="flex shrink-0 items-center justify-center rounded-full border border-dashed border-[var(--app-border-strong)] font-semibold text-[var(--app-muted)]">
        {initial}
      </span>
    );
  }
  return (
    <span aria-hidden="true" style={{ ...box, background: gradientFor(seed ?? name) }}
      className="flex shrink-0 items-center justify-center rounded-full font-bold text-white">
      {initial}
    </span>
  );
}
