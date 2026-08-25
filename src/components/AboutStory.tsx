export function AboutStory() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="grid gap-10 sm:grid-cols-2 sm:gap-16">
          <div>
            <h2 className="text-2xl font-black uppercase tracking-tight">
              The problem
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-soft">
              Every team that translates documents ends up with the same
              three-person relay: a translator, a designer to rebuild the
              layout, and someone doing QA to catch what broke in between.
              The handoff is where quality and time both get lost.
            </p>
          </div>
          <div>
            <h2 className="text-2xl font-black uppercase tracking-tight">
              What we&apos;re building
            </h2>
            <p className="mt-4 text-sm leading-relaxed text-ink-soft">
              Docly reads a document&apos;s layout before it translates a
              single word, so text lands back in the frame it came from.
              One tool, one pass, no handoff. We&apos;re starting with
              document formats and expanding from there — a browser
              extension is next.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
