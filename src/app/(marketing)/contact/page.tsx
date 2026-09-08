import type { Metadata } from "next";
import ContactForm from "@/components/ContactForm";

export const metadata: Metadata = {
  title: "Contact — Pagebird",
  description: "Send us the document you dread translating.",
};

export default function ContactPage() {
  return (
    <>
      <section className="px-6 pt-18 md:px-14">
        <span className="font-pb-mono-brand text-[12.5px] font-bold tracking-widest text-pb-accent uppercase">
          — get in touch
        </span>
        <h1 className="font-pb-display mt-4.5 max-w-2xl text-5xl md:text-7xl">
          Send us the document you dread{" "}
          <span className="text-pb-accent italic">translating.</span>
        </h1>
      </section>

      <section className="mt-12 grid grid-cols-1 gap-12 border-b-[3px] border-pb-ink px-6 pt-14 pb-16 md:grid-cols-2 md:gap-0 md:px-14 md:pt-0">
        <div className="flex flex-col gap-7 md:border-r-[3px] md:border-pb-ink md:pr-14 md:pb-16">
          <ContactForm />
        </div>

        <div className="flex flex-col gap-10 md:pl-14">
          <div className="flex flex-col gap-2.5">
            <span className="font-pb-mono-brand text-[11px] font-bold text-pb-accent">GENERAL</span>
            <h3 className="text-[19px] font-bold">hello@pagebird.com</h3>
            <p className="text-sm leading-relaxed text-pb-muted">
              Questions about the product, pricing, or a document you&rsquo;d like to
              test.
            </p>
          </div>
          <div className="flex flex-col gap-2.5">
            <span className="font-pb-mono-brand text-[11px] font-bold text-pb-accent">SALES</span>
            <h3 className="text-[19px] font-bold">sales@pagebird.com</h3>
            <p className="text-sm leading-relaxed text-pb-muted">
              Enterprise volume, data residency, SSO and procurement.
            </p>
          </div>
          <div className="flex flex-col gap-2.5">
            <span className="font-pb-mono-brand text-[11px] font-bold text-pb-accent">SUPPORT</span>
            <h3 className="text-[19px] font-bold">support@pagebird.com</h3>
            <p className="text-sm leading-relaxed text-pb-muted">
              Existing customers — [X]h response time on paid plans.
            </p>
          </div>
          <div className="flex flex-col gap-2.5 border-t-2 border-pb-line pt-6">
            <span className="font-pb-mono-brand text-[11px] font-bold text-pb-faint">OFFICE</span>
            <p className="text-sm leading-relaxed text-pb-muted">
              [Street address]
              <br />
              [City, postal code]
              <br />
              [Country]
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
