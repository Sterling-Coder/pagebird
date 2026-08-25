type Row = { label: string; translator: string; extension: string };

const ROWS: Row[] = [
  { label: "Billing unit", translator: "Per page", extension: "Per seat / mo" },
  { label: "Formats", translator: "DOC, PDF, INDD, IDML", extension: "Any webpage, selected text" },
  { label: "Starting price", translator: "$0.08 / page", extension: "$8 / seat / mo" },
  { label: "Team plan", translator: "$149 / mo, 2,000 pages", extension: "$49 / mo, 5 seats" },
  { label: "Free tier", translator: "First document free", extension: "First 50 translations free" },
];

export function PricingComparisonTable() {
  return (
    <section className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Compare
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Translator vs. Extension
          </h2>
        </div>
        <div className="overflow-x-auto border border-rule">
          <table className="w-full min-w-[560px] border-collapse text-left text-sm">
            <thead>
              <tr className="border-b border-rule font-mono text-[11px] uppercase tracking-widest text-muted">
                <th className="px-4 py-3 font-normal">&nbsp;</th>
                <th className="px-4 py-3 font-normal">Document Translator</th>
                <th className="px-4 py-3 font-normal">Browser Extension</th>
              </tr>
            </thead>
            <tbody>
              {ROWS.map((row) => (
                <tr key={row.label} className="border-b border-rule last:border-b-0">
                  <td className="px-4 py-3 font-black uppercase text-xs">{row.label}</td>
                  <td className="px-4 py-3 text-ink-soft">{row.translator}</td>
                  <td className="px-4 py-3 text-ink-soft">{row.extension}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </section>
  );
}
