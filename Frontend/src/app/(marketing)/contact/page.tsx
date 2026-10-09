import type { Metadata } from "next";
import ClosingBand from "@/components/ClosingBand";
import ContactForm from "@/components/ContactForm";

export const metadata: Metadata = {
  title: "Contact — Pagebirdy",
  description:
    "Talk to Pagebirdy about pricing, enterprise formats and glossaries, support, or early access to the Chrome extension.",
};

const CARD_BORDER = "1px solid rgba(255,255,255,0.08)";

const REASONS = [
  {
    title: "Sales & pricing",
    tint: "#e08a6f",
    body: "Plans, volume pricing, or what fits after your 14-day free trial.",
    icon: (
      <path d="M4 7h12M4 7l2-3h8l2 3M4 7v8a1 1 0 001 1h10a1 1 0 001-1V7M8 11h4" />
    ),
  },
  {
    title: "Enterprise",
    tint: "#8b6fbf",
    body: "Custom formats, shared glossaries, and high-volume IDML workflows.",
    icon: <path d="M4 16V5l6-2 6 2v11M8 16v-4h4v4M7.5 8h1M11.5 8h1" />,
  },
  {
    title: "Support",
    tint: "#4fc4a8",
    body: "A file that didn't come back the way you expected? Send it our way.",
    icon: (
      <path d="M10 17a7 7 0 100-14 7 7 0 000 14zM8 8a2 2 0 113 1.7c-.6.4-1 .8-1 1.5M10 13.5h.01" />
    ),
  },
  {
    title: "Chrome extension",
    tint: "#6f9cff",
    body: "Early access to translating pages and selections right in the browser.",
    icon: <path d="M10 17a7 7 0 100-14 7 7 0 000 14zM10 13a3 3 0 100-6 3 3 0 000 6zM10 7h6.5M7.4 11.5L4 5.6M12.6 11.5L9.3 17" />,
  },
];

export default function ContactPage() {
  return (
    <>
    <section
      className="relative min-h-screen overflow-hidden"
      style={{
        background:
          "radial-gradient(55% 45% at 12% 0%, rgba(224,138,111,0.13), transparent 70%), radial-gradient(45% 40% at 92% 8%, rgba(139,111,191,0.10), transparent 70%), radial-gradient(60% 40% at 60% 100%, rgba(79,196,168,0.06), transparent 70%), #0a0908",
      }}
    >
      <div className="relative mx-auto grid max-w-[1180px] grid-cols-1 gap-12 px-4 pt-28 pb-20 sm:px-8 lg:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)] lg:gap-16 lg:px-14 lg:pt-36 lg:pb-28">
        {/* Left: intro + reasons */}
        <div className="flex flex-col gap-10">
          <div className="flex flex-col gap-5">
            <span
              className="pb-enter-label text-[12px] font-semibold tracking-[0.15em] uppercase"
              style={{ color: "#e08a6f" }}
            >
              Contact
            </span>
            <h1
              className="pb-enter font-semibold leading-[1.05] tracking-[-0.02em]"
              style={{ fontSize: "clamp(2.25rem, 4.5vw, 3.5rem)", color: "#f0ece3" }}
            >
              Talk to a human
              <br />
              about your documents.
            </h1>
            <p
              className="pb-enter pb-enter-delay-1 max-w-[460px] text-[17px] leading-relaxed"
              style={{ color: "#a8a49a" }}
            >
              InDesign, PDF, Office files, images or a whole website: tell us what you&rsquo;re
              translating and we&rsquo;ll help you get it back with the layout intact.
            </p>
          </div>

          <ul className="pb-enter pb-enter-delay-2 grid grid-cols-1 gap-3 sm:grid-cols-2">
            {REASONS.map((r) => (
              <li
                key={r.title}
                className="group flex flex-col gap-3 rounded-[24px] p-5 transition-transform duration-200 hover:-translate-y-0.5"
                style={{ background: `linear-gradient(180deg, ${r.tint}10, #1d1c1a 55%)`, border: CARD_BORDER }}
              >
                <span
                  aria-hidden
                  className="flex h-9 w-9 items-center justify-center rounded-full"
                  style={{ background: `${r.tint}1f`, color: r.tint, boxShadow: `inset 0 0 0 1px ${r.tint}33` }}
                >
                  <svg
                    width="18"
                    height="18"
                    viewBox="0 0 20 20"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="1.6"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                  >
                    {r.icon}
                  </svg>
                </span>
                <div className="flex flex-col gap-1">
                  <h2 className="text-[15px] font-semibold" style={{ color: "#f0ece3" }}>
                    {r.title}
                  </h2>
                  <p className="text-[14px] leading-relaxed" style={{ color: "#a8a49a" }}>
                    {r.body}
                  </p>
                </div>
              </li>
            ))}
          </ul>

          <dl
            className="pb-enter pb-enter-delay-3 flex flex-col gap-5 pt-8 sm:flex-row sm:gap-12"
            style={{ borderTop: CARD_BORDER }}
          >
            <div className="flex flex-col gap-1">
              <dt className="text-[13px]" style={{ color: "#8a8478" }}>
                Email us directly
              </dt>
              <dd>
                <a
                  href="mailto:hello@pagebirdy.com"
                  className="rounded text-[16px] font-semibold outline-none hover:underline focus-visible:ring-2 focus-visible:ring-[#e08a6f] underline-offset-4"
                  style={{ color: "#f0ece3" }}
                >
                  hello@pagebirdy.com
                </a>
              </dd>
            </div>
            <div className="flex flex-col gap-1">
              <dt className="text-[13px]" style={{ color: "#8a8478" }}>
                Response time
              </dt>
              <dd className="text-[16px] font-semibold" style={{ color: "#f0ece3" }}>
                Usually within one business day
              </dd>
            </div>
          </dl>

          <ol className="pb-enter pb-enter-delay-3 grid grid-cols-1 gap-3 sm:grid-cols-3">
            {[
              ["01", "Tell us about your files", "Formats, languages and rough volume."],
              ["02", "We reply within a day", "A real person, with answers or a call time."],
              ["03", "Start translating", "Use the 14-day trial while we talk."],
            ].map(([n, t, d]) => (
              <li key={n} className="rounded-2xl p-4" style={{ background: "rgba(255,255,255,0.02)", border: CARD_BORDER }}>
                <span className="font-pb-mono text-[11px]" style={{ color: "#e08a6f" }}>{n}</span>
                <div className="mt-1.5 text-[14px] font-semibold" style={{ color: "#f0ece3" }}>{t}</div>
                <p className="mt-1 text-[12.5px] leading-relaxed" style={{ color: "#8a8478" }}>{d}</p>
              </li>
            ))}
          </ol>
        </div>

        {/* Right: form */}
        <div className="pb-enter pb-enter-delay-2 lg:sticky lg:top-28 lg:self-start">
          <div
            className="relative overflow-hidden rounded-[24px] p-5 sm:p-8"
            style={{
              background: "linear-gradient(180deg, #211f1d, #1a1917)",
              border: CARD_BORDER,
              boxShadow: "0 30px 80px rgba(0,0,0,0.45), inset 0 1px 0 rgba(255,255,255,0.04)",
            }}
          >
            <span aria-hidden className="absolute inset-x-0 top-0 h-px"
              style={{ background: "linear-gradient(90deg, transparent, #e08a6f, #8b6fbf, transparent)" }} />
            <div className="mb-7 flex flex-col gap-1.5">
              <h2 className="text-[22px] font-semibold tracking-tight" style={{ color: "#f0ece3" }}>
                Send us a message
              </h2>
              <p className="text-[14px] leading-relaxed" style={{ color: "#a8a49a" }}>
                Pick a topic so it reaches the right person.
              </p>
            </div>
            <ContactForm />
          </div>
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