const RECENT = [
  { client: "Ledgerline Group", lang: "French", pages: 24, time: "2 min ago" },
  { client: "Northstar Health", lang: "German", pages: 8, time: "19 min ago" },
  { client: "Fielda Ops", lang: "Japanese", pages: 41, time: "1 hr ago" },
];

export function LoginShowcase() {
  return (
    <aside
      className="relative hidden overflow-hidden lg:block"
      style={{
        backgroundImage:
          "linear-gradient(90deg, var(--red) 0%, var(--red) 12%, #a83a26 24%, #7c2c1c 38%, #4c1a11 55%, #241009 75%, var(--ink) 100%)",
      }}
      aria-hidden="true"
    >
      <div className="relative z-10 px-10 pt-14">
        <p className="max-w-md text-3xl font-black uppercase leading-[1.1] tracking-tight text-paper sm:text-4xl">
          Every file.
          <br />
          Every language.
          <br />
          One dashboard.
        </p>
      </div>

      <div className="absolute inset-x-8 bottom-8 border border-paper/15 bg-paper shadow-[0_24px_60px_rgba(0,0,0,0.45)]">
        <div className="flex items-center gap-2 border-b border-rule bg-paper-dim px-4 py-2.5">
          <span className="h-2.5 w-2.5 rounded-full bg-red" />
          <span className="h-2.5 w-2.5 rounded-full bg-muted/40" />
          <span className="h-2.5 w-2.5 rounded-full bg-muted/40" />
          <span className="ml-2 font-mono text-[10px] uppercase tracking-widest text-muted">
            Docly · Dashboard
          </span>
        </div>

        <div className="px-5 py-4">
          <div className="flex items-baseline justify-between">
            <p className="font-black uppercase tracking-tight text-ink">
              Recent translations
            </p>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
              73 total
            </span>
          </div>

          <div className="mt-4 divide-y divide-rule border-t border-rule">
            {RECENT.map((row) => (
              <div
                key={row.client}
                className="flex items-center justify-between py-2.5 text-sm"
              >
                <div>
                  <p className="text-ink">{row.client}</p>
                  <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
                    {row.lang} · {row.pages} pages
                  </p>
                </div>
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
                  {row.time}
                </span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </aside>
  );
}
