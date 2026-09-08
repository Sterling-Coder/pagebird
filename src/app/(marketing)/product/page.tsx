import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Product — Pagebird",
  description: "The layout engine behind every Pagebird translation.",
};

const DEEP_DIVES = [
  {
    n: "01",
    title: "Layout tree parsing",
    body: "A full layout graph — nested tables, merged cells, floating images, footnote anchors — built before a single word is translated.",
  },
  {
    n: "02",
    title: "Adaptive typography",
    body: "Tighter tracking, reduced leading, then a measured size step down — in that order, always inside bounds you'd accept by hand.",
  },
  {
    n: "03",
    title: "Bidirectional layout",
    body: "Arabic, Hebrew and Urdu mirror margins, gutters, bullets and image alignment — the whole page, not just the sentence.",
  },
];

const FORMATS = [".docx", ".pdf", ".pptx", ".xlsx", ".idml", ".srt", ".html", ".xliff"];

export default function ProductPage() {
  return (
    <>
      <section className="border-b-[3px] border-pb-ink px-6 py-18 pb-14 md:px-14">
        <span className="font-pb-mono-brand text-[12.5px] font-bold tracking-widest text-pb-accent uppercase">
          — the layout engine
        </span>
        <h1 className="font-pb-display mt-4.5 max-w-4xl text-5xl md:text-7xl">
          We don&rsquo;t extract text. We map{" "}
          <span className="text-pb-accent italic">structure.</span>
        </h1>
        <p className="mt-6 max-w-2xl text-[17px] leading-relaxed text-pb-muted">
          Pagebird reads your document as a full layout graph — frames, styles, tables,
          anchors — translates the text inside it, then rewrites the same graph back
          into the original file format.
        </p>
      </section>

      {/* WORKSPACE SCREENSHOT — mirrors the real /app workspace layout */}
      <section className="border-b-[3px] border-pb-ink px-6 py-14 md:px-14">
        <div className="border-[3px] border-pb-ink shadow-[14px_14px_0_var(--color-pb-accent)]">
          <div className="flex items-center gap-2.5 border-b-[3px] border-pb-ink bg-white px-5 py-3.5">
            <span className="font-pb-mono-brand text-[11.5px] text-pb-faint">
              app.pagebird.com/jobs/q3-investor-deck
            </span>
          </div>
          <div className="flex h-auto flex-col bg-white md:h-[460px] md:flex-row">
            {/* nav rail */}
            <div className="hidden w-44 shrink-0 flex-col gap-1 border-r-[3px] border-pb-ink bg-[#f6f4ea] p-4 md:flex">
              <span className="font-pb-display px-1 pb-4 text-lg italic">
                page<span className="text-pb-accent">bird</span>
              </span>
              <span className="flex items-center gap-2.5 border-l-[3px] border-pb-accent bg-white px-2.5 py-2 text-[13px] font-semibold">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                  <path d="M6 2h9l5 5v15H6z" />
                  <path d="M15 2v5h5" />
                </svg>
                Jobs
              </span>
              <span className="flex items-center gap-2.5 px-2.5 py-2 text-[13px] text-pb-faint">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                  <circle cx="9" cy="8" r="3" />
                  <path d="M2 21c0-3.9 3.1-7 7-7s7 3.1 7 7" />
                </svg>
                Team
              </span>
              <span className="flex items-center gap-2.5 px-2.5 py-2 text-[13px] text-pb-faint">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                  <circle cx="12" cy="12" r="3" />
                  <path d="M19.4 15a1.7 1.7 0 0 0 1.9 2l.1.1a2 2 0 1 1-2.8 2.8" />
                </svg>
                Settings
              </span>
            </div>

            <div className="flex flex-1 flex-col">
              {/* top bar */}
              <div className="flex items-center justify-between border-b-[3px] border-pb-ink px-5 py-3">
                <span className="font-pb-mono-brand text-[11px] tracking-widest text-pb-faint uppercase">
                  Q3 Investor Deck · 日本語
                </span>
                <span className="font-pb-mono-brand rounded-none bg-pb-accent px-2 py-1 text-[10px] font-bold tracking-widest text-white uppercase">
                  Translating
                </span>
              </div>

              <div className="flex flex-1 flex-col md:flex-row">
                {/* source pane */}
                <div className="flex flex-1 flex-col gap-3 border-b-[3px] border-pb-ink p-6 md:border-r-[3px] md:border-b-0">
                  <span className="font-pb-mono-brand text-[11px] font-bold text-pb-faint uppercase">
                    Source document
                  </span>
                  <div className="flex flex-1 flex-col gap-3 overflow-hidden border-2 border-pb-line p-4.5 text-[11.5px] leading-relaxed text-pb-ink">
                    <p className="font-bold">Q3 Investor Update</p>
                    <p>
                      Revenue grew 34% quarter over quarter, driven by expansion in the
                      EMEA region and renewed enterprise contracts.
                    </p>
                    <p>
                      Northwind Logistics renewed its enterprise agreement for three
                      years, anchoring roughly 18% of Q3 recurring revenue.
                    </p>
                    <p className="text-pb-faint">
                      Headcount grew from 142 to 168, with new hires concentrated in
                      engineering and customer success.
                    </p>
                  </div>
                </div>

                {/* output pane */}
                <div className="flex flex-1 flex-col gap-3 p-6">
                  <span className="font-pb-mono-brand text-[11px] font-bold text-pb-accent uppercase">
                    Output — 日本語
                  </span>
                  <div className="flex flex-1 flex-col gap-3 overflow-hidden border-2 border-pb-accent p-4.5 text-[11.5px] leading-relaxed text-pb-ink">
                    <p className="font-bold">第3四半期 投資家アップデート</p>
                    <p>
                      収益は前四半期比34%増加し、EMEA地域の拡大と大企業契約の更新が牽引しました。
                    </p>
                    <p>
                      Northwindロジスティクスは3年間のエンタープライズ契約を更新し、
                      第3四半期の経常収益の約18%を占めています。
                    </p>
                    <p className="animate-pulse bg-[#f3c4b8]/50 text-pb-muted">
                      従業員数は142名から168名に増加し、新規採用はエンジニアリングと
                      カスタマーサクセスに集中しました。
                    </p>
                  </div>
                  <div className="flex items-start gap-2 border-2 border-pb-ink bg-[#fff3e0] px-3.5 py-3">
                    <span className="font-pb-mono-brand text-[11.5px] leading-relaxed">
                      ⚠ &ldquo;Northwind&rdquo; matched glossary — left untranslated
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* DEEP DIVES */}
      <section className="border-b-[3px] border-pb-ink">
        <div className="grid grid-cols-1 md:grid-cols-3">
          {DEEP_DIVES.map((d, i) => (
            <div
              key={d.n}
              className={`flex flex-col gap-3.5 p-11 ${i < 2 ? "border-b-[3px] border-pb-ink md:border-r-[3px] md:border-b-0" : ""}`}
            >
              <span className="font-pb-display text-4xl text-pb-accent">{d.n}</span>
              <h3 className="text-[19px] font-bold">{d.title}</h3>
              <p className="text-sm leading-relaxed text-pb-muted">{d.body}</p>
            </div>
          ))}
        </div>
      </section>

      {/* FORMATS */}
      <section className="flex items-center gap-0 border-b-[3px] border-pb-ink px-6 py-6.5 md:px-14">
        <span className="font-pb-mono-brand pr-10 text-xs font-bold tracking-wide">FORMATS</span>
        <div className="flex flex-1 flex-wrap items-center gap-7 text-sm font-semibold">
          {FORMATS.map((f) => (
            <span key={f}>{f}</span>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="flex flex-col items-start justify-between gap-6 bg-pb-ink px-6 py-14 text-pb-paper md:flex-row md:items-center md:px-14">
        <h2 className="font-pb-display max-w-lg text-3xl">
          See it hold up on your own document.
        </h2>
        <Link
          href="/contact"
          className="flex h-13.5 flex-shrink-0 items-center bg-pb-accent px-7 text-[15px] font-bold text-pb-paper"
        >
          Translate a document free →
        </Link>
      </section>
    </>
  );
}
