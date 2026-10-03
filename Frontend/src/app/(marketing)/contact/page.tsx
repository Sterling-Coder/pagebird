import type { Metadata } from "next";
import ContactForm from "@/components/ContactForm";

export const metadata: Metadata = {
  title: "Contact — Pagebirdy",
  description: "Send us the document you dread translating.",
};

export default function ContactPage() {
  return (
    <>
      {/* Hero */}
      <section className="relative overflow-hidden" style={{
        background: "linear-gradient(180deg, #c8a820 0%, #c86018 8%, #b03010 18%, #8a1c10 32%, #5a1018 50%, #2e0a20 68%, #180818 82%, #0c0810 100%)",
        minHeight: "38vh",
      }}>
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(90deg, rgba(0,0,0,0.18) 0px, rgba(0,0,0,0.18) 1px, transparent 1px, transparent 80px)",
        }} />
        <div className="pointer-events-none absolute inset-0" style={{
          backgroundImage: "repeating-linear-gradient(180deg, transparent 0px, transparent 2px, rgba(0,0,0,0.06) 2px, rgba(0,0,0,0.06) 3px)",
        }} />
        <div className="relative mx-auto max-w-[1100px] px-8 pt-28 pb-12 lg:px-14 lg:pt-36">
          <div className="pb-enter-label flex items-center gap-3 mb-8">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold tracking-widest text-pb-accent uppercase">Get in touch</span>
          </div>
          <h1 className="pb-enter pb-stencil" style={{ fontSize: "clamp(2.8rem, 4.5vw, 4.5rem)" }}>
            Send us the<br />document you dread.
          </h1>
        </div>
      </section>

      {/* Form section */}
      <section className="pb-glass-section">
        <div className="mx-auto max-w-[1100px] px-8 py-16 lg:px-14 lg:py-20">
          <div className="grid grid-cols-1 gap-12 md:grid-cols-2 md:gap-0">
            <div className="flex flex-col gap-7 md:pr-14" style={{ borderRight: "1px solid rgba(255,255,255,0.06)" }}>
              <ContactForm />
            </div>
            <div className="flex flex-col gap-10 md:pl-14">
              <div className="flex flex-col gap-2.5">
                <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-accent uppercase">General</span>
                <h3 className="text-[19px] font-bold text-pb-text">founder@thepagebirdy.com</h3>
                <p className="text-sm leading-relaxed text-pb-text-muted">
                  Questions about the product, pricing, or a document you&rsquo;d like to test.
                </p>
              </div>
              <div className="flex flex-col gap-2.5 pt-6" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Office</span>
                <p className="text-sm leading-relaxed text-pb-text-muted">Bangalore, India</p>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}
