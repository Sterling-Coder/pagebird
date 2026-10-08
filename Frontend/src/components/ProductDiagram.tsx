"use client";

import { useState, useRef, useEffect } from "react";

interface Node {
  ox: number; oy: number;
  x: number;  y: number;
  vx: number; vy: number;
  r: number;
  phase: number;
  isKey: boolean;
  label: string;
}

const PRODUCTS = [
  { id: "documents", n: "01", label: "Documents / PDF",     color: "#e08a6f", agent: "Layout Agent",
    steps: [".idml/.pdf", "Parse frames",    "Extract text",    "AI Translate", "Rebuild layout",  "Output"] },
  { id: "subtitles", n: "02", label: "SRT / VTT Subtitles",  color: "#8b6fbf", agent: "Timecode Agent",
    steps: [".srt/.vtt",  "Parse cues",      "Extract text",    "AI Translate", "Sync timecodes",  "Output"] },
  { id: "images",    n: "03", label: "Image Translator",     color: "#4a9e8a", agent: "OCR Agent",
    steps: ["Image/PSD",  "Detect regions",  "OCR",             "AI Translate", "Render in place", "Output"] },
  { id: "websites",  n: "04", label: "Website Translator",   color: "#5a9e5a", agent: "Web Crawler",
    steps: ["URL",        "Crawl pages",     "Extract strings", "AI Translate", "Rebuild HTML",    "/fr/ /de/"] },
  { id: "youtube",   n: "05", label: "YouTube Subtitles",    color: "#c94040", agent: "Caption Agent",
    steps: ["YouTube URL","Fetch captions",  "Parse cues",      "AI Translate", "Export SRT",      "Upload-ready"] },
];

// Key node positions as fractions of canvas
const KEY_FX = [0.07, 0.25, 0.43, 0.57, 0.75, 0.93];
const KEY_FY = [0.44, 0.28, 0.62, 0.28, 0.62, 0.44];

// Ambient particle rest positions
const AMB_F: [number, number][] = [
  [0.14, 0.14], [0.32, 0.82], [0.50, 0.10], [0.68, 0.86], [0.85, 0.18],
  [0.19, 0.62], [0.37, 0.40], [0.55, 0.68], [0.72, 0.36], [0.89, 0.76],
  [0.09, 0.86], [0.28, 0.18], [0.51, 0.92], [0.68, 0.08], [0.88, 0.56],
  [0.41, 0.18], [0.63, 0.80], [0.79, 0.22],
];

function bezierPt(x0: number, y0: number, cpx: number, cpy: number, x1: number, y1: number, t: number) {
  const m = 1 - t;
  return { x: m * m * x0 + 2 * m * t * cpx + t * t * x1, y: m * m * y0 + 2 * m * t * cpy + t * t * y1 };
}

function FlowCanvas({ color, steps }: { color: string; steps: string[] }) {
  const cvRef   = useRef<HTMLCanvasElement>(null);
  const rafRef  = useRef(0);
  const nsRef   = useRef<Node[]>([]);
  const mRef    = useRef({ x: -9999, y: -9999 });
  const liveRef = useRef({ color, steps, W: 0, H: 0 });

  // sync props without remounting
  useEffect(() => {
    liveRef.current.color = color;
    liveRef.current.steps = steps;
    let ki = 0;
    for (const n of nsRef.current) if (n.isKey) n.label = steps[ki++] ?? "";
  }, [color, steps]);

  useEffect(() => {
    const cvMaybe = cvRef.current;
    if (!cvMaybe) return;
    const cv  = cvMaybe as HTMLCanvasElement;
    const ctx = cv.getContext("2d")!;
    const dpr = window.devicePixelRatio || 1;

    // 2 animated dots per path segment (5 segments between 6 key nodes)
    const dotTs = Array.from({ length: 5 }, (_, si) => [si % 2 === 0 ? 0.0 : 0.5, si % 2 === 0 ? 0.5 : 0.0]);

    function build(W: number, H: number, steps: string[]) {
      const ns: Node[] = [];
      KEY_FX.forEach((fx, i) => ns.push({
        ox: fx * W, oy: KEY_FY[i] * H, x: fx * W, y: KEY_FY[i] * H,
        vx: 0, vy: 0, r: 18, phase: i * 1.1, isKey: true, label: steps[i] ?? "",
      }));
      AMB_F.forEach(([fx, fy], i) => ns.push({
        ox: fx * W, oy: fy * H, x: fx * W, y: fy * H,
        vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
        r: 2 + Math.random() * 2.2, phase: i * 0.53 + Math.random() * 2, isKey: false, label: "",
      }));
      nsRef.current = ns;
    }

    function resize() {
      const par = cv.parentElement;
      if (!par) return;
      const { width, height } = par.getBoundingClientRect();
      const W = Math.max(width, 200), H = Math.max(height, 300);
      liveRef.current.W = W; liveRef.current.H = H;
      cv.width = W * dpr; cv.height = H * dpr;
      cv.style.width = W + "px"; cv.style.height = H + "px";
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      build(W, H, liveRef.current.steps);
    }

    resize();
    const ro = new ResizeObserver(resize);
    ro.observe(cv.parentElement!);

    let alive = true;

    function tick() {
      if (!alive) return;
      const { color, W, H } = liveRef.current;
      const { x: mx, y: my } = mRef.current;
      const t = performance.now() * 0.001;
      const ns = nsRef.current;

      ctx.clearRect(0, 0, W, H);

      // ── Physics ──────────────────────────────────────────────
      for (const n of ns) {
        const sp = n.isKey ? 0.040 : 0.022;
        n.vx += Math.sin(t * 0.55 + n.phase) * 0.05;
        n.vy += Math.cos(t * 0.42 + n.phase * 1.3) * 0.05;
        n.vx += (n.ox - n.x) * sp;
        n.vy += (n.oy - n.y) * sp;
        const dx = n.x - mx, dy = n.y - my, d = Math.sqrt(dx * dx + dy * dy);
        if (d < 120 && d > 0.1) {
          const f = ((120 - d) / 120) ** 1.5 * 3.2;
          n.vx += (dx / d) * f; n.vy += (dy / d) * f;
        }
        n.vx *= 0.83; n.vy *= 0.83;
        n.x += n.vx; n.y += n.vy;
      }

      const keys = ns.filter(n => n.isKey);

      // ── Ambient proximity lines ───────────────────────────────
      const CONN = W * 0.20;
      ctx.lineWidth = 0.6;
      for (let i = 0; i < ns.length; i++) {
        for (let j = i + 1; j < ns.length; j++) {
          const a = ns[i], b = ns[j];
          if (a.isKey && b.isKey) continue;
          const ddx = b.x - a.x, ddy = b.y - a.y, dd = Math.sqrt(ddx * ddx + ddy * ddy);
          if (dd > CONN) continue;
          ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y);
          ctx.strokeStyle = color; ctx.globalAlpha = (1 - dd / CONN) * 0.10; ctx.stroke();
        }
      }
      ctx.globalAlpha = 1;

      // ── Sequential paths between key nodes ───────────────────
      for (let si = 0; si < keys.length - 1; si++) {
        const a = keys[si], b = keys[si + 1];
        const cpx = (a.x + b.x) * 0.5;
        const cpy = (a.y + b.y) * 0.5 + (a.oy < b.oy ? -22 : 22);

        // dashed base
        ctx.save();
        ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.quadraticCurveTo(cpx, cpy, b.x, b.y);
        ctx.strokeStyle = color; ctx.globalAlpha = 0.16;
        ctx.lineWidth = 1; ctx.setLineDash([3, 6]); ctx.stroke();
        ctx.setLineDash([]); ctx.restore();

        // animated dots
        dotTs[si].forEach((dt, di) => {
          dotTs[si][di] = (dt + 0.0035) % 1;
          const pt = bezierPt(a.x, a.y, cpx, cpy, b.x, b.y, dotTs[si][di]);
          const fade = dotTs[si][di] < 0.08 ? dotTs[si][di] / 0.08 : dotTs[si][di] > 0.92 ? (1 - dotTs[si][di]) / 0.08 : 1;
          ctx.save();
          ctx.shadowColor = color; ctx.shadowBlur = 10;
          ctx.beginPath(); ctx.arc(pt.x, pt.y, 3, 0, Math.PI * 2);
          ctx.fillStyle = color; ctx.globalAlpha = fade * 0.9; ctx.fill();
          ctx.restore();
        });
      }
      ctx.globalAlpha = 1;

      // ── Key nodes ─────────────────────────────────────────────
      for (const n of keys) {
        ctx.save();
        ctx.shadowColor = color; ctx.shadowBlur = 22;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = color + "1c"; ctx.fill();
        ctx.strokeStyle = color + "cc"; ctx.lineWidth = 1.5; ctx.stroke();
        ctx.restore();
        // label
        ctx.fillStyle = "rgba(240,236,227,0.65)";
        ctx.font = `600 7.5px "Space Mono", monospace`;
        ctx.textAlign = "center"; ctx.textBaseline = "top";
        n.label.split(" ").forEach((word, wi) => ctx.fillText(word, n.x, n.y + n.r + 4 + wi * 10));
      }

      // ── Ambient nodes ─────────────────────────────────────────
      for (const n of ns.filter(n => !n.isKey)) {
        ctx.save();
        ctx.shadowColor = color; ctx.shadowBlur = 5;
        ctx.beginPath(); ctx.arc(n.x, n.y, n.r, 0, Math.PI * 2);
        ctx.fillStyle = color + "40"; ctx.fill();
        ctx.restore();
      }

      rafRef.current = requestAnimationFrame(tick);
    }

    rafRef.current = requestAnimationFrame(tick);

    const par = cv.parentElement!;
    const onMove  = (e: MouseEvent) => { const r = cv.getBoundingClientRect(); mRef.current = { x: e.clientX - r.left, y: e.clientY - r.top }; };
    const onLeave = () => { mRef.current = { x: -9999, y: -9999 }; };
    par.addEventListener("mousemove", onMove);
    par.addEventListener("mouseleave", onLeave);

    return () => {
      alive = false;
      cancelAnimationFrame(rafRef.current);
      ro.disconnect();
      par.removeEventListener("mousemove", onMove);
      par.removeEventListener("mouseleave", onLeave);
    };
  }, []);

  return <canvas ref={cvRef} style={{ display: "block", position: "absolute", top: 0, left: 0 }} aria-hidden="true" />;
}

export default function ProductDiagram() {
  const [active, setActive] = useState(0);
  const product = PRODUCTS[active];

  return (
    <section style={{ background: "#0a0908" }}>
      <div className="mx-auto max-w-[1100px] px-8 py-24 lg:px-14 lg:py-36">

        <div className="mb-14">
          <div className="flex items-center gap-3 mb-5">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">How each product works</span>
          </div>
          <h2 className="pb-stencil" style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05, maxWidth: "600px" }}>
            Five products.<br />Five specialized agents.
          </h2>
        </div>

        <div className="grid grid-cols-1 gap-10 lg:grid-cols-[280px_1fr]">

          {/* LEFT: tabs */}
          <div className="flex flex-col gap-1">
            {PRODUCTS.map((p, i) => (
              <button key={p.id} type="button" onClick={() => setActive(i)}
                className="group flex items-start gap-4 rounded-xl px-4 py-4 text-left transition-all"
                style={{ background: i === active ? `${p.color}12` : "transparent", border: i === active ? `1px solid ${p.color}35` : "1px solid transparent" }}>
                <span className="font-pb-mono mt-0.5 shrink-0 text-[10px]" style={{ color: i === active ? p.color : "rgba(255,255,255,0.25)" }}>{p.n}</span>
                <div>
                  <div className="text-[14px] font-semibold" style={{ color: i === active ? "#f0ece3" : "rgba(240,236,227,0.45)" }}>{p.label}</div>
                  {i === active && <div className="mt-1 font-pb-mono text-[9px] tracking-widest uppercase" style={{ color: p.color }}>{p.agent}</div>}
                </div>
              </button>
            ))}
          </div>

          {/* RIGHT: canvas flow diagram */}
          <div style={{ position: "relative", height: "520px" }}>
            <div className="absolute top-4 right-4 z-10 font-pb-mono text-[9px] font-bold tracking-[0.14em] uppercase px-3 py-1.5 rounded-full"
              style={{ background: `${product.color}18`, border: `1px solid ${product.color}35`, color: product.color }}>
              {product.agent}
            </div>
            <FlowCanvas color={product.color} steps={product.steps} />
          </div>

        </div>
      </div>
    </section>
  );
}
