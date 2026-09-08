export function ComingSoonWorkspace({ label }: { label: string }) {
  return (
    <div className="flex min-h-0 flex-1 flex-col items-center justify-center gap-2 p-8 text-center">
      <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
        {label}
      </p>
      <p className="text-sm text-muted">Coming soon.</p>
    </div>
  );
}
