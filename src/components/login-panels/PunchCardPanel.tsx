const COLS = 22;
const ROWS = 26;

function seededOpacity(x: number, y: number) {
  const n = Math.sin(x * 12.9898 + y * 78.233) * 43758.5453;
  const frac = n - Math.floor(n);
  return 0.04 + frac * 0.14;
}

export function PunchCardPanel() {
  const cells = [];
  for (let y = 0; y < ROWS; y++) {
    for (let x = 0; x < COLS; x++) {
      cells.push({ x, y, opacity: seededOpacity(x, y) });
    }
  }

  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div
        className="absolute inset-6 grid gap-[3px]"
        style={{ gridTemplateColumns: `repeat(${COLS}, 1fr)` }}
      >
        {cells.map(({ x, y, opacity }) => (
          <div
            key={`${x}-${y}`}
            className="aspect-square bg-paper"
            style={{ opacity }}
          />
        ))}
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
