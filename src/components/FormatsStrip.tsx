const FORMATS = [
  { ext: "DOC", label: "Word documents" },
  { ext: "PDF", label: "Any PDF, scanned or native" },
  { ext: "INDD", label: "InDesign, layers intact" },
  { ext: "IDML", label: "InDesign markup" },
];

export function FormatsStrip() {
  return (
    <section id="formats" className="border-y border-rule">
      <div className="mx-auto grid max-w-6xl grid-cols-2 divide-x divide-y divide-rule sm:grid-cols-4 sm:divide-y-0">
        {FORMATS.map((format) => (
          <div
            key={format.ext}
            className="flex items-center gap-4 px-6 py-8 sm:px-8"
          >
            <span className="font-black uppercase text-2xl">{format.ext}</span>
            <span className="text-xs leading-snug text-muted">
              {format.label}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
