function ViewfinderBracket({ className }: { className: string }) {
  return (
    <div className={`pointer-events-none absolute h-8 w-8 ${className}`} aria-hidden="true">
      <svg viewBox="0 0 32 32" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-full w-full text-paper/40">
        <path d="M2 12V2h10" />
      </svg>
    </div>
  );
}

export function TerminalPanel() {
  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: "repeating-linear-gradient(90deg, var(--paper) 0 1px, transparent 1px 48px)",
        }}
      />
      <div
        className="absolute inset-0 opacity-[0.04]"
        style={{
          backgroundImage: "repeating-linear-gradient(0deg, var(--paper) 0 1px, transparent 1px 3px)",
        }}
      />

      <ViewfinderBracket className="left-8 top-8" />
      <ViewfinderBracket className="right-8 top-8 rotate-90" />
      <ViewfinderBracket className="bottom-8 right-8 rotate-180" />
      <ViewfinderBracket className="bottom-8 left-8 -rotate-90" />

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

      <div className="absolute bottom-16 left-16 h-6 w-[3px] bg-red" />
    </aside>
  );
}
