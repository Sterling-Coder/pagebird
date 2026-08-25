export function Footer() {
  return (
    <footer className="border-t border-rule">
      <div className="mx-auto flex max-w-6xl flex-col gap-4 px-6 py-8 sm:flex-row sm:items-center sm:justify-between sm:px-8">
        <span className="font-black uppercase text-lg">Docly</span>
        <div className="flex flex-wrap gap-6 font-mono text-[11px] uppercase tracking-widest text-muted">
          <a href="#how-it-works" className="hover:text-ink transition-colors">
            Product
          </a>
          <a href="#languages" className="hover:text-ink transition-colors">
            Languages
          </a>
          <a href="#formats" className="hover:text-ink transition-colors">
            Formats
          </a>
          <span>© 2026 Docly</span>
        </div>
      </div>
    </footer>
  );
}
