export function RadarPanel() {
  const rings = [80, 160, 240, 320, 400];

  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div className="absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2">
        {rings.map((r) => (
          <div
            key={r}
            className="absolute rounded-full border border-paper/10"
            style={{
              width: r * 2,
              height: r * 2,
              left: -r,
              top: -r,
            }}
          />
        ))}

        <div
          className="absolute h-[420px] w-[420px] origin-bottom-left"
          style={{
            left: 0,
            top: -420,
            background:
              "conic-gradient(from 0deg, var(--red) 0deg, transparent 28deg)",
            opacity: 0.35,
          }}
        />

        <div className="absolute left-0 top-0 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-red" />
        <div className="absolute left-1/2 top-0 h-px w-[800px] -translate-x-1/2 bg-paper/10" />
        <div className="absolute left-0 top-1/2 h-[800px] w-px -translate-y-1/2 bg-paper/10" />
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
