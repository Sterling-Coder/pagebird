function RegistrationMark({ className }: { className: string }) {
  return (
    <div className={`pointer-events-none absolute ${className}`} aria-hidden="true">
      <svg viewBox="0 0 32 32" className="h-6 w-6 text-paper/25" fill="none" stroke="currentColor" strokeWidth="1">
        <circle cx="16" cy="16" r="9" />
        <path d="M16 0v32M0 16h32" />
      </svg>
    </div>
  );
}

function CropMark({ className }: { className: string }) {
  return (
    <div className={`pointer-events-none absolute ${className}`} aria-hidden="true">
      <svg viewBox="0 0 20 20" className="h-4 w-4 text-paper/30" fill="none" stroke="currentColor" strokeWidth="1.5">
        <path d="M10 0v6M10 14v6M0 10h6M14 10h20" />
      </svg>
    </div>
  );
}

export function PrintRegistrationPanel() {
  return (
    <aside
      className="relative hidden overflow-hidden bg-ink lg:block"
      aria-hidden="true"
    >
      <div
        className="absolute inset-0 opacity-[0.06]"
        style={{
          backgroundImage: "radial-gradient(circle, var(--paper) 1px, transparent 1px)",
          backgroundSize: "18px 18px",
        }}
      />

      <CropMark className="left-6 top-6" />
      <CropMark className="right-6 top-6 rotate-90" />
      <CropMark className="bottom-6 left-6 -rotate-90" />
      <CropMark className="bottom-6 right-6 rotate-180" />
      <RegistrationMark className="left-1/2 top-1/3 -translate-x-1/2" />
      <RegistrationMark className="right-16 top-2/3" />

      <div
        className="pointer-events-none absolute -left-16 -top-16 h-56 w-56"
        style={{
          backgroundImage:
            "repeating-linear-gradient(45deg, var(--red) 0 14px, transparent 14px 28px)",
          opacity: 0.6,
        }}
      />
      <div className="absolute left-8 top-[13.5rem] flex h-3 w-40 overflow-hidden border border-paper/20">
        <div className="flex-1 bg-red" />
        <div className="flex-1 bg-paper" />
        <div className="flex-1 bg-ink" />
        <div className="flex-1 bg-paper/40" />
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
