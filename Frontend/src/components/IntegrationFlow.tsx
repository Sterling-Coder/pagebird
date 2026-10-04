"use client";

import { useEffect, useRef } from "react";

const SOURCES = [
  { label: "InDesign",    color: "#e08a6f" },
  { label: "Illustrator", color: "#d4785a" },
  { label: "Photoshop",   color: "#e08a6f" },
  { label: "YouTube",     color: "#c94040" },
  { label: "Premiere",    color: "#c94040" },
  { label: "WordPress",   color: "#5a9e5a" },
];

const OUTPUTS = [
  { label: "中文",      color: "#e08a6f" },
  { label: "العربية",  color: "#8b6fbf" },
  { label: "Français", color: "#4a9e8a" },
  { label: "Deutsch",  color: "#5a9e5a" },
  { label: "Español",  color: "#c94040" },
  { label: "+35 more", color: "rgba(255,255,255,0.35)" },
];

interface HubNode {
  ox: number; oy: number;
  x: number;  y: number;
  vx: number; vy: number;
  r: number;
  phase: number;
  label: string;
  color: string;
  kind: "source" | "engine" | "output";
}

function bezierPt(x0: number, y0: number, cpx: number, cpy: number, x1: number, y1: number, t: number) {
  const m = 1 - t;
  return { x: m * m * x0 + 2 * m * t * cpx + t * t * x1, y: m * m * y0 + 2 * m * t * cpy + t * t * y1 };
}

export default function IntegrationFlow() {
  const secRef = useRef<HTMLDivElement>(null);
  const cvRef  = useRef<HTMLCanvasElement>(null);
  const rafRef = useRef(0);
  const nsRef  = useRef<HubNode[]>([]);
  const mRef   = useRef({ x: -9999, y: -9999 });
  const inViewRef = useRef(false);

  useEffect(() => {
    const secMaybe = secRef.current;
    const cvMaybe  = cvRef.current;
    if (!secMaybe || !cvMaybe) return;
    const sec = secMaybe as HTMLDivElement;
    const cv  = cvMaybe as HTMLCanvasElement;
    const ctx = cv.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;
    let W = 0, H = 0;

    // dot t-values: 6 source→engine dots + 6 engine→output dots
    const srcDots = SOURCES.map((_, i) => ({ t: i / SOURCES.length }));
    const outDots = OUTPUTS.map((_, i) => ({ t: i / OUTPUTS.length }));

    function build(w: number, h: number) {
      const ns: HubNode[] = [];
      const ey = h * 0.5;
      const ex = w * 0.5;
      const pad = h * 0.10;
      const rowH = (h - pad * 2) / (SOURCES.length - 1);

      SOURCES.forEach((s, i) => ns.push({
        ox: w * 0.13, oy: pad + i * rowH,
        x:  w * 0.13, y:  pad + i * rowH,
        vx: 0, vy: 0, r: 6, phase: i * 0.9, label: s.label, color: s.color, kind: "source",
      }));

      ns.push({
        ox: ex, oy: ey, x: ex, y: ey,
        vx: 0, vy: 0, r: 42, phase: 0, label: "PAGEBIRDY", color: "#e08a6f", kind: "engine",
      });

      OUTPUTS.forEach((o, i) => ns.push({
        ox: w * 0.87, oy: pad + i * rowH,
        x:  w * 0.87, y:  pad + i * rowH,
        vx: 0, vy: 0, r: 6, phase: i * 0.9, label: o.label, color: o.color, kind: "output",
      }));

      nsRef.current = ns;
    }

    function resize() {
      const { width, height } = sec.getBoundingClientRect();
      W = Math.max(width, 300); H = Math.max(height, 360);
      cv.width  = W * dpr; cv.height = H * dpr;
      cv.style.width  = W + "px"; cv.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build(W, H);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(sec);

    const obs = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) inViewRef.current = true; },
      { threshold: 0.15 }
    );
    obs.observe(sec);

    let alive = true;

    function tick() {
      if (!alive) return;
      const { x: mx, y: my } = mRef.current;
      const t = performance.now() * 0.001;
      const ns = nsRef.current;
      const inView = inViewRef.current;

      ctx.clearRect(0, 0, W, H);

      const sources = ns.filter(n => n.kind === "source");
      const engine  = ns.find(n => n.kind === "engine")!;
      const outputs = ns.filter(n => n.kind === "output");

      // ── Physics ───────────────────────────────────────────────
      for (const n of ns) {
        const sp = n.kind === "engine" ? 0.045 : 0.030;
        n.vx += Math.sin(t * 0.5 + n.phase) * 0.04;
        n.vy += Math.cos(t * 0.38 + n.phase * 1.2) * 0.04;
        n.vx += (n.ox - n.x) * sp;
        n.vy += (n.oy - n.y) * sp;
        const dx = n.x - mx, dy = n.y - my, d = Math.sqrt(dx * dx + dy * dy);
        const repR = n.kind === "engine" ? 160 : 100;
        if (d < repR && d > 0.1) {
          const f = ((repR - d) / repR) ** 1.5 * (n.kind === "engine" ? 4.5 : 2.8);
          n.vx += (dx / d) * f; n.vy += (dy / d) * f;
        }
        n.vx *= 0.84; n.vy *= 0.84;
        n.x += n.vx;  n.y += n.vy;
      }

      if (!engine) { rafRef.current = requestAnimationFrame(tick); return; }

      // ── Source → engine lines + dots ─────────────────────────
      sources.forEach((src, si) => {
        const cpx = (src.x + engine.x) * 0.5;
        const cpy = src.y;

        ctx.save();
        ctx.beginPath(); ctx.moveTo(src.x, src.y); ctx.quadraticCurveTo(cpx, cpy, engine.x, engine.y);
        ctx.strokeStyle = src.color; ctx.globalAlpha = inView ? 0.22 : 0;
        ctx.lineWidth = 0.8; ctx.setLineDash([3, 6]); ctx.stroke();
        ctx.setLineDash([]); ctx.restore();

        if (inView) {
          srcDots[si].t = (srcDots[si].t + 0.003) % 1;
          const pt = bezierPt(src.x, src.y, cpx, cpy, engine.x, engine.y, srcDots[si].t);
          const fade = srcDots[si].t < 0.07 ? srcDots[si].t / 0.07 : srcDots[si].t > 0.93 ? (1 - srcDots[si].t) / 0.07 : 1;
          ctx.save();
          ctx.shadowColor = src.color; ctx.shadowBlur = 8;
          ctx.beginPath(); ctx.arc(pt.x, pt.y, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = src.color; ctx.globalAlpha = fade * 0.9; ctx.fill();
          ctx.restore();
        }
      });

      // ── Engine → output lines + dots ─────────────────────────
      outputs.forEach((out, oi) => {
        const cpx = (engine.x + out.x) * 0.5;
        const cpy = out.y;

        ctx.save();
        ctx.beginPath(); ctx.moveTo(engine.x, engine.y); ctx.quadraticCurveTo(cpx, cpy, out.x, out.y);
        ctx.strokeStyle = out.color; ctx.globalAlpha = inView ? 0.22 : 0;
        ctx.lineWidth = 0.8; ctx.setLineDash([3, 6]); ctx.stroke();
        ctx.setLineDash([]); ctx.restore();

        if (inView) {
          outDots[oi].t = (outDots[oi].t + 0.003) % 1;
          const pt = bezierPt(engine.x, engine.y, cpx, cpy, out.x, out.y, outDots[oi].t);
          const fade = outDots[oi].t < 0.07 ? outDots[oi].t / 0.07 : outDots[oi].t > 0.93 ? (1 - outDots[oi].t) / 0.07 : 1;
          ctx.save();
          ctx.shadowColor = out.color; ctx.shadowBlur = 8;
          ctx.beginPath(); ctx.arc(pt.x, pt.y, 2.5, 0, Math.PI * 2);
          ctx.fillStyle = out.color; ctx.globalAlpha = fade * 0.9; ctx.fill();
          ctx.restore();
        }
      });
      ctx.globalAlpha = 1;

      // ── Source nodes ──────────────────────────────────────────
      sources.forEach(n => {
        ctx.save();
        ctx.shadowColor = n.color; ctx.shadowBlur = 10;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.color + "20"; ctx.fill();
        ctx.strokeStyle = n.color + "aa"; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.restore();
        ctx.fillStyle = n.color;
        ctx.font = `600 9px "Space Mono", monospace`;
        ctx.textAlign = "left"; ctx.textBaseline = "middle";
        ctx.fillText(n.label, n.x + n.r + 8, n.y);
      });

      // ── Output nodes ──────────────────────────────────────────
      outputs.forEach(n => {
        ctx.save();
        ctx.shadowColor = n.color; ctx.shadowBlur = 10;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = n.color + "20"; ctx.fill();
        ctx.strokeStyle = n.color + "aa"; ctx.lineWidth = 1.2; ctx.stroke();
        ctx.restore();
        ctx.fillStyle = n.color;
        ctx.font = `600 9px "Space Mono", monospace`;
        ctx.textAlign = "right"; ctx.textBaseline = "middle";
        ctx.fillText(n.label, n.x - n.r - 8, n.y);
      });

      // ── Engine node ───────────────────────────────────────────
      const pulse = 1 + Math.sin(t * 1.8) * 0.03;
      ctx.save();
      // outer glow ring
      ctx.beginPath(); ctx.arc(engine.x, engine.y, engine.r * 1.3 * pulse, 0, Math.PI * 2);
      ctx.strokeStyle = "rgba(224,138,111,0.10)"; ctx.lineWidth = 1; ctx.stroke();
      // inner ring
      ctx.shadowColor = "#e08a6f"; ctx.shadowBlur = 30;
      ctx.beginPath(); ctx.arc(engine.x, engine.y, engine.r * pulse, 0, Math.PI * 2);
      ctx.fillStyle = "rgba(224,138,111,0.10)"; ctx.fill();
      ctx.strokeStyle = "rgba(224,138,111,0.55)"; ctx.lineWidth = 1.5; ctx.stroke();
      ctx.restore();
      ctx.fillStyle = "rgba(240,236,227,0.88)";
      ctx.font = `700 9px "Space Mono", monospace`;
      ctx.textAlign = "center"; ctx.textBaseline = "middle";
      ctx.fillText("PAGEBIRDY", engine.x, engine.y - 5);
      ctx.fillStyle = "rgba(224,138,111,0.7)";
      ctx.font = `400 8px "Space Mono", monospace`;
      ctx.fillText("ENGINE", engine.x, engine.y + 7);

      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);

    const onMove  = (e: MouseEvent) => { const r = cv.getBoundingClientRect(); mRef.current = { x: e.clientX - r.left, y: e.clientY - r.top }; };
    const onLeave = () => { mRef.current = { x: -9999, y: -9999 }; };
    sec.addEventListener("mousemove", onMove);
    sec.addEventListener("mouseleave", onLeave);

    return () => {
      alive = false;
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      obs.disconnect();
      sec.removeEventListener("mousemove", onMove);
      sec.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return (
    <section
      ref={secRef}
      style={{ background: "#0a0908", borderTop: "1px solid rgba(255,255,255,0.05)", position: "relative", overflow: "hidden" }}
    >
      <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28" style={{ position: "relative" }}>

        <div className="mb-8">
          <div className="flex items-center gap-3 mb-5">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Integration flow</span>
          </div>
          <h2 className="pb-stencil" style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05 }}>
            Every tool.<br />One engine.
          </h2>
          <p className="mt-4 max-w-lg text-[15px] leading-relaxed text-pb-text-muted">
            Pagebirdy sits between your creative tools and the world&apos;s languages. Native formats in, native formats out.
          </p>
        </div>

        {/* Canvas hub diagram */}
        <div style={{ position: "relative", height: "420px" }}>
          <canvas ref={cvRef} style={{ display: "block", position: "absolute", top: 0, left: 0 }} aria-hidden="true" />
        </div>

      </div>
    </section>
  );
}
