export function HandoffSection() {
  return (
    <section className="border-b-4 border-ink">
      <div className="mx-auto max-w-6xl px-6 pb-16 pt-16 sm:px-8">
        <div className="flex justify-end">
          <span className="-rotate-2 border border-ink px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest text-ink-soft">
            Fig. 1 — the handoff, removed
          </span>
        </div>

        <div className="mt-8 grid gap-10 divide-y divide-rule sm:grid-cols-3 sm:divide-x sm:divide-y-0">
          <p className="text-[15px] leading-relaxed text-ink-soft sm:pr-8">
            <span className="float-left mr-2 text-6xl font-black leading-[0.8] text-red">
              M
            </span>
            ost teams route a document through three tools: one to translate
            the text, one to rebuild the layout, and one to check nothing
            broke. Every handoff loses something, and what gets lost is
            usually a caption, a table, or an image nobody re-translated.
          </p>
          <p className="text-[15px] leading-relaxed text-ink-soft sm:px-8">
            Docly works the other way. The layout is read before a single
            word is translated, so text lands back in the frame it came
            from. There&apos;s no second pass to rebuild what the first pass
            didn&apos;t touch.
          </p>
          <div className="space-y-4 text-[15px] leading-relaxed text-ink-soft sm:pl-8">
            <p>
              For a small team that means one file in, one file out — no
              export step, no formatting cleanup after. For a bigger team it
              means every document in the pipeline gets the same treatment,
              page one or page four hundred.
            </p>
            <p>
              Currently supporting DOC, PDF, INDD and IDML, with new formats
              added by request.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
