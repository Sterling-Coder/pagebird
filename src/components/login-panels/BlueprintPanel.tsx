function TickRow() {
  const ticks = Array.from({ length: 24 });
  return (
    <div className="absolute left-0 right-0 top-0 flex h-6 items-end">
      {ticks.map((_, i) => (
        <div
          key={i}
          className="flex-1 border-l border-paper/15"
          style={{ height: i % 4 === 0 ? "16px" : "8px" }}
        />
      ))}
    </div>
  );
}

function TickCol() {
  const ticks = Array.from({ length: 20 });
  return (
    <div className="absolute bottom-0 left-0 top-0 flex w-6 flex-col justify-end">
      {ticks.map((_, i) => (
        <div
          key={i}
          className="flex-1 border-t border-paper/15"
          style={{ width: i % 4 === 0 ? "16px" : "8px" }}
        />
      ))}
    </div>
  );
}

export function BlueprintPanel() {
  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage:
            "linear-gradient(var(--paper) 1px, transparent 1px), linear-gradient(90deg, var(--paper) 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      <TickRow />
      <TickCol />

      <div
        className="absolute left-10 top-14 h-px w-2/3 bg-paper/20"
        style={{ backgroundImage: "repeating-linear-gradient(90deg, var(--paper) 0 6px, transparent 6px 12px)" }}
      />
      <div
        className="absolute left-14 top-10 h-2/3 w-px bg-paper/20"
        style={{ backgroundImage: "repeating-linear-gradient(180deg, var(--paper) 0 6px, transparent 6px 12px)" }}
      />

      <p
        className="pointer-events-none absolute -bottom-[6vw] -right-[4vw] select-none text-[32vw] font-black uppercase leading-none tracking-tighter text-transparent"
        style={{ WebkitTextStroke: "1px rgba(253,252,247,0.16)" }}
      >
        D
      </p>

      <div
        className="pointer-events-none absolute -left-16 -top-16 h-56 w-56"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, var(--red) 0 14px, transparent 14px 28px)",
          opacity: 0.6,
        }}
      />

      <div className="absolute bottom-10 left-10 h-16 w-px bg-red" />
      <div className="absolute bottom-10 left-10 h-px w-16 bg-red" />
    </aside>
  );
}
