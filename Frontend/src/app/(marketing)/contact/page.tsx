import type { Metadata } from "next";
import ClosingBand from "@/components/ClosingBand";
import ContactForm from "@/components/ContactForm";

export const metadata: Metadata = {
  title: "Contact — Pagebirdy",
  description:
    "Talk to Pagebirdy about pricing, enterprise formats and glossaries, support, or early access to the Chrome extension.",
};

// Plain dark: one solid ground, hairline rules instead of boxes, colour only as solid fills.
const BG = "#0e0d0c";
const CARD_BORDER = "1px solid #2a2826";

const STEPS = [
  ["Tell us about your files", "Formats, languages and rough volume."],
  ["We reply within a day", "A real person, with answers or a time to talk."],
  ["Start translating", "Use the 14-day free trial while we talk."],
];

export default function ContactPage() {
  return (
    <>
      <section className="relative min-h-screen" style={{ background: BG }}>
        <div className="relative mx-auto max-w-[1080px] px-5 pt-28 pb-24 sm:px-8 lg:pt-36 lg:pb-32">
          <header className="flex max-w-[720px] flex-col gap-5">
            <span className="pb-enter-label text-[12px] font-semibold tracking-[0.15em] uppercase" style={{ color: "#e08a6f" }}>
              Contact
            </span>
            <h1
              className="pb-enter font-semibold leading-[1.05] tracking-[-0.02em] [text-wrap:balance]"
              style={{ fontSize: "clamp(2.25rem, 5vw, 3.75rem)", color: "#f0ece3" }}
            >
              Talk to a human about your documents.
            </h1>
            <p className="pb-enter pb-enter-delay-1 max-w-[560px] text-[17px] leading-relaxed" style={{ color: "#a8a49a" }}>
              InDesign, PDF, Office files, images or a whole website: tell us what you&rsquo;re translating
              and we&rsquo;ll help you get it back with the layout intact.
            </p>
          </header>

          <div className="mt-16 grid grid-cols-1 gap-16 pt-12 lg:mt-20 lg:grid-cols-[minmax(0,1fr)_280px] lg:gap-24"
            style={{ borderTop: CARD_BORDER }}>
            <div className="pb-enter pb-enter-delay-2 min-w-0">
              <h2 className="text-[22px] font-semibold tracking-tight" style={{ color: "#f0ece3" }}>
                Send us a message
              </h2>
              <p className="mt-1.5 mb-9 text-[14px] leading-relaxed" style={{ color: "#8a8478" }}>
                Pick a topic so it reaches the right person.
              </p>
              <ContactForm />
            </div>

            <aside className="pb-enter pb-enter-delay-3 flex flex-col gap-10 lg:pt-1">
              <dl className="flex flex-col gap-6">
                <div className="flex flex-col gap-1">
                  <dt className="text-[13px]" style={{ color: "#8a8478" }}>Email us directly</dt>
                  <dd>
                    <a
                      href="mailto:hello@pagebirdy.com"
                      className="rounded text-[17px] font-semibold underline-offset-4 outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[#e08a6f]"
                      style={{ color: "#f0ece3" }}
                    >
                      hello@pagebirdy.com
                    </a>
                  </dd>
                </div>
                <div className="flex flex-col gap-1">
                  <dt className="text-[13px]" style={{ color: "#8a8478" }}>Response time</dt>
                  <dd className="text-[17px] font-semibold" style={{ color: "#f0ece3" }}>Within one business day</dd>
                </div>
              </dl>

              <div>
                <h2 className="mb-2 text-[13px]" style={{ color: "#8a8478" }}>What happens next</h2>
                <ol>
                  {STEPS.map(([title, body], i) => (
                    <li key={title} className="flex gap-4 py-4" style={{ borderTop: CARD_BORDER }}>
                      <span className="text-[15px] font-semibold tabular-nums" style={{ color: "#e08a6f" }}>{i + 1}</span>
                      <div className="flex flex-col gap-0.5">
                        <span className="text-[15px] font-semibold" style={{ color: "#f0ece3" }}>{title}</span>
                        <span className="text-[13.5px] leading-relaxed" style={{ color: "#8a8478" }}>{body}</span>
                      </div>
                    </li>
                  ))}
                </ol>
              </div>
            </aside>
          </div>
        </div>
      </section>
      <ClosingBand
        color="#2f5fb3"
        title={<>Rather see it work?<br />Try it on a real file.</>}
        sub="Every account starts with a 14-day trial. No card needed."
        cta="Translate free"
        href="/login"
      />
    </>
  );
}
