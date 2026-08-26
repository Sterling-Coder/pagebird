function Contour({ d, opacity }: { d: string; opacity: number }) {
  return <path d={d} fill="none" stroke="var(--paper)" strokeWidth="1" opacity={opacity} />;
}

export function CartographicPanel() {
  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <svg viewBox="0 0 600 720" className="absolute inset-0 h-full w-full" preserveAspectRatio="none">
        <Contour d="M -50 500 Q 150 420 300 480 T 650 460" opacity={0.12} />
        <Contour d="M -50 540 Q 150 470 300 520 T 650 510" opacity={0.1} />
        <Contour d="M -50 580 Q 150 520 300 560 T 650 560" opacity={0.08} />
        <Contour d="M -50 620 Q 150 570 300 610 T 650 610" opacity={0.06} />
        <Contour d="M -50 660 Q 150 620 300 660 T 650 660" opacity={0.05} />
      </svg>

      <div className="absolute right-10 top-10 h-16 w-16 rounded-full border border-paper/25" aria-hidden="true">
        <div className="absolute left-1/2 top-0 h-4 w-px -translate-x-1/2 bg-red" />
        <div className="absolute left-1/2 top-1/2 h-px w-full -translate-x-1/2 -translate-y-1/2 bg-paper/20" />
        <div className="absolute left-1/2 top-1/2 h-full w-px -translate-x-1/2 -translate-y-1/2 bg-paper/20" />
      </div>

      <div
        className="pointer-events-none absolute -left-16 -top-16 h-56 w-56"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, var(--red) 0 14px, transparent 14px 28px)",
          opacity: 0.6,
        }}
      />

      <p
        className="pointer-events-none absolute -bottom-[6vw] -right-[4vw] select-none text-[32vw] font-black uppercase leading-none tracking-tighter text-transparent"
        style={{ WebkitTextStroke: "1px rgba(253,252,247,0.16)" }}
      >
        D
      </p>

      <div className="absolute bottom-10 left-10 h-16 w-px bg-red" />
      <div className="absolute bottom-10 left-10 h-px w-16 bg-red" />
    </aside>
  );
}
