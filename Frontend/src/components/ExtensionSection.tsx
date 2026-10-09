import Link from "next/link";

const POINTS = [
  { title: "Select, then read", desc: "Highlight a word or a sentence on any site and the translation appears right beside it." },
  { title: "Or translate the whole page", desc: "One click rewrites the visible text in place, keeps the layout, and switches back just as fast." },
  { title: "Your language, remembered", desc: "Pick it once in the small settings panel. Right-to-left languages flip the page direction for you." },
];

export default function ExtensionSection() {
  return (
    <section style={{ background: "#0a0908", position: "relative", zIndex: 20, isolation: "isolate" }}>
      <div className="mx-auto grid max-w-[1100px] items-center gap-12 px-8 pb-24 lg:grid-cols-2 lg:px-14">
        <div>
          <p className="font-pb-mono mb-4 text-[11px] uppercase tracking-[0.14em] text-[#e08a6f]">Chrome extension</p>
          <h2
            className="pb-stencil mb-6 max-w-[520px]"
            style={{ fontSize: "clamp(2rem,3.5vw,3.2rem)", lineHeight: 1.05 }}
          >
            Translate anything<br />you read online.
          </h2>
          <ul className="space-y-5">
            {POINTS.map((p) => (
              <li key={p.title}>
                <h3 className="text-[15px] font-semibold text-[#f0ece3]">{p.title}</h3>
                <p className="mt-1 max-w-[460px] text-[13.5px] leading-relaxed text-white/60">{p.desc}</p>
              </li>
            ))}
          </ul>
          <div className="mt-8 flex flex-wrap items-center gap-4">
            <Link
              href="/contact"
              className="font-pb-mono rounded px-6 py-3.5 text-[11px] font-bold uppercase tracking-[0.12em] text-white"
              style={{ background: "#c86018" }}
            >
              Get early access →
            </Link>
            <span className="text-[12px] text-white/45">Chrome Web Store listing coming soon. Uses your Pagebirdy account.</span>
          </div>
        </div>

        {/* Mock: a selected sentence with its translation card */}
        <div aria-hidden className="relative rounded-[20px] bg-[#141311] p-6 text-[#f0ece3] ring-1 ring-white/[0.07]">
          <div className="mb-4 flex gap-1.5">
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
            <span className="h-2.5 w-2.5 rounded-full bg-white/15" />
          </div>
          <p className="text-[14px] leading-relaxed text-white/70">
            Our team reviews every order within one business day, and{" "}
            <mark className="rounded bg-[#c86018]/40 px-0.5 text-white">refunds are issued to the original payment method.</mark>{" "}
            Contact support if anything looks wrong.
          </p>
          <div className="mt-4 w-[88%] rounded-[10px] border border-[#e2d6c8] bg-[#fffaf4] p-3.5 text-[#15130f] shadow-[0_8px_28px_rgba(0,0,0,0.35)]">
            <div className="font-pb-mono mb-1.5 text-[10px] uppercase tracking-[0.08em] text-[#8a6a4a]">Pagebirdy → ES</div>
            <p className="text-[13px] leading-snug">Los reembolsos se emiten al método de pago original.</p>
          </div>
        </div>
      </div>
    </section>
  );
}
