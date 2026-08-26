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
    <aside className="relative hidden overflow-hidden bg-ink lg:block">
      <div
        className="absolute inset-6 grid gap-[3px]"
        style={{ gridTemplateColumns: `repeat(${COLS}, 1fr)` }}
        aria-hidden="true"
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
        aria-hidden="true"
      />

      <div className="absolute left-10 top-32 max-w-sm">
        <div className="bg-ink/90 p-2">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Docly
          </span>
          <p className="mt-3 text-2xl font-black uppercase leading-[1.1] tracking-tight text-paper">
            Translate the file.
            <br />
            Keep the pixel.
          </p>
          <ul className="mt-5 space-y-1.5 font-mono text-[11px] uppercase tracking-widest text-paper/60">
            <li>DOC · PDF · INDD · IDML</li>
            <li>30+ languages</li>
            <li>95% accuracy</li>
          </ul>
        </div>
      </div>

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
