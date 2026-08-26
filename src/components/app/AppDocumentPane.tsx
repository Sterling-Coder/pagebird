type Section = { heading: string; body: string };

type PaneContent = {
  title: string;
  language: string;
  sections: Section[];
};

export function AppDocumentPane({ content }: { content: PaneContent }) {
  return (
    <div className="min-w-[320px] flex-1 border-r border-rule last:border-r-0">
      <div className="bg-red px-5 py-3">
        <p className="text-sm font-black uppercase tracking-tight text-paper">
          {content.title}
        </p>
      </div>

      <div className="grid grid-cols-3 divide-x divide-rule border-b border-rule bg-paper-dim">
        <div className="px-4 py-2">
          <p className="font-mono text-[9px] uppercase tracking-widest text-muted">Format</p>
          <p className="mt-0.5 text-xs text-ink-soft">PDF</p>
        </div>
        <div className="px-4 py-2">
          <p className="font-mono text-[9px] uppercase tracking-widest text-muted">Language</p>
          <p className="mt-0.5 text-xs text-ink-soft">{content.language}</p>
        </div>
        <div className="px-4 py-2">
          <p className="font-mono text-[9px] uppercase tracking-widest text-muted">Status</p>
          <p className="mt-0.5 text-xs text-red">Translated</p>
        </div>
      </div>

      <div className="space-y-6 px-5 py-5">
        {content.sections.map((section) => (
          <div key={section.heading}>
            <p className="text-xs font-black uppercase tracking-tight text-ink">
              {section.heading}
            </p>
            <p className="mt-2 text-[12px] leading-relaxed text-ink-soft">
              {section.body}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
}
