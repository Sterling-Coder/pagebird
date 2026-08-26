export function GridPanel() {
  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div
        className="absolute inset-0 opacity-[0.07]"
        style={{
          backgroundImage:
            "linear-gradient(var(--paper) 1px, transparent 1px), linear-gradient(90deg, var(--paper) 1px, transparent 1px)",
          backgroundSize: "56px 56px",
        }}
      />

      <p
        className="pointer-events-none absolute -bottom-[6vw] -right-[4vw] select-none text-[32vw] font-black uppercase leading-none tracking-tighter text-transparent"
        style={{ WebkitTextStroke: "1.5px rgba(253,252,247,0.18)" }}
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
