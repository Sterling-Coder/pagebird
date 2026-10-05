import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "About — Pagebirdy",
  description: "We build layout-preserving document translation tools for designers, publishers and global teams.",
};

export default function AboutPage() {
  return (
    <div style={{ background: "#0c0b09", minHeight: "100vh" }}>

      {/* Hero */}
      <section style={{
        background: "linear-gradient(180deg, #1a1410 0%, #0f0d0a 50%, #0c0b09 100%)",
        borderBottom: "1px solid rgba(255,255,255,0.06)",
        paddingTop: "120px",
        paddingBottom: "80px",
      }}>
        <div className="mx-auto max-w-[1100px] px-8 lg:px-14">
          <div className="flex items-center gap-3 mb-6">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">About</span>
          </div>
          <h1 className="pb-stencil" style={{ fontSize: "clamp(2.8rem, 5vw, 5rem)", lineHeight: 1.0, maxWidth: "700px" }}>
            Built for<br />designers who<br />ship globally.
          </h1>
          <p className="mt-6 max-w-xl text-[16px] leading-relaxed text-pb-text-muted">
            Pagebirdy started from a single frustration: translated documents that looked nothing like the originals. We built the tool we wanted to use.
          </p>
        </div>
      </section>

      {/* Mission */}
      <section style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="grid grid-cols-1 gap-16 lg:grid-cols-2 lg:gap-24">
            <div>
              <h2 className="pb-stencil mb-6" style={{ fontSize: "clamp(1.6rem, 2.8vw, 2.4rem)", lineHeight: 1.05 }}>
                The problem we solve.
              </h2>
              <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.55)", lineHeight: 1.7 }}>
                Professional documents — InDesign layouts, PDFs, subtitle files — lose their formatting when passed through standard translation tools. Columns collapse. Fonts break. Page counts change. Designers spend days manually re-applying styles.
              </p>
              <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.55)", lineHeight: 1.7, marginTop: "16px" }}>
                Pagebirdy translates the text and rebuilds the document in the same breath. The file that comes back is ready to open, not ready to rebuild.
              </p>
            </div>
            <div>
              <h2 className="pb-stencil mb-6" style={{ fontSize: "clamp(1.6rem, 2.8vw, 2.4rem)", lineHeight: 1.05 }}>
                How we work.
              </h2>
              <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.55)", lineHeight: 1.7 }}>
                We run two AI translation engines in parallel — OpenAI and DeepL — and use a consensus model to catch errors before they reach your client. When the engines agree, the translation ships. When they disagree, the segment is flagged.
              </p>
              <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.55)", lineHeight: 1.7, marginTop: "16px" }}>
                Every format gets a dedicated parser: IDML layouts, SRT timecodes, image OCR regions. Nothing is generic.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Values */}
      <section style={{ borderBottom: "1px solid rgba(255,255,255,0.05)" }}>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <div className="flex items-center gap-3 mb-14">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Principles</span>
          </div>
          <div className="grid grid-cols-1 gap-px md:grid-cols-3" style={{ border: "1px solid rgba(255,255,255,0.06)", borderRadius: "12px", overflow: "hidden" }}>
            {[
              {
                n: "01",
                title: "Layout first.",
                body: "We treat document structure as sacred. Translation is a guest in someone else's design — it should leave no trace.",
              },
              {
                n: "02",
                title: "No surprises.",
                body: "What you upload is what you get back. Same extension, same page count, same font handling. Every time.",
              },
              {
                n: "03",
                title: "Honest quality.",
                body: "We show you a QA score. We surface disagreements. We don't hide uncertainty behind a confident output.",
              },
            ].map((v) => (
              <div key={v.n} style={{ background: "#0f0e0c", padding: "32px 28px" }}>
                <div className="font-pb-mono mb-4 text-[10px] text-pb-text-muted">{v.n}</div>
                <h3 style={{ fontSize: "17px", fontWeight: 700, color: "#f0ece3", marginBottom: "10px" }}>{v.title}</h3>
                <p style={{ fontSize: "13px", lineHeight: 1.7, color: "rgba(240,236,227,0.45)" }}>{v.body}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section>
        <div className="mx-auto max-w-[1100px] px-8 py-20 lg:px-14 lg:py-28">
          <h2 className="pb-stencil mb-6" style={{ fontSize: "clamp(1.8rem, 3vw, 2.8rem)", lineHeight: 1.1 }}>
            Try it on a real file.
          </h2>
          <p style={{ fontSize: "15px", color: "rgba(240,236,227,0.5)", marginBottom: "28px" }}>
            5 free pages. No card. No time limit.
          </p>
          <div className="flex items-center gap-6">
            <Link
              href="/login"
              className="font-pb-mono rounded-full bg-pb-accent px-7 py-3 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
            >
              Translate free
            </Link>
            <Link href="/contact" className="font-pb-mono text-[13px] text-pb-text-muted hover:text-white transition-colors">
              Talk to us →
            </Link>
          </div>
        </div>
      </section>

    </div>
  );
}
