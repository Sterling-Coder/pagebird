import type { Metadata } from "next";
import ContactForm from "@/components/ContactForm";

export const metadata: Metadata = {
  title: "Contact — Pagebirdy",
  description: "Send us the document you dread translating.",
};

export default function ContactPage() {
  return (
    <>
      <section className="mx-auto max-w-7xl px-6 pt-20 lg:px-10">
        <span className="font-pb-mono mb-4 inline-flex items-center gap-2 text-[11px] font-bold tracking-widest text-pb-accent uppercase">
          <span className="inline-block h-2 w-2 rounded-sm bg-pb-accent" />
          Get in touch
        </span>
        <h1 className="font-pb-display max-w-2xl text-5xl text-pb-text md:text-7xl">
          Send us the document you dread{" "}
          <span className="text-pb-accent italic">translating.</span>
        </h1>
      </section>

      <section className="mx-auto mt-14 grid max-w-7xl grid-cols-1 gap-12 border-t border-pb-border px-6 pt-14 pb-20 md:grid-cols-2 md:gap-0 lg:px-10">
        <div className="flex flex-col gap-7 md:border-r md:border-pb-border md:pr-14 md:pb-16">
          <ContactForm />
        </div>

        <div className="flex flex-col gap-10 md:pl-14">
          <div className="flex flex-col gap-2.5">
            <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-accent uppercase">General</span>
            <h3 className="text-[19px] font-bold text-pb-text">founder@thepagebirdy.com</h3>
            <p className="text-sm leading-relaxed text-pb-text-muted">
              Questions about the product, pricing, or a document you&rsquo;d like to
              test.
            </p>
          </div>
          <div className="flex flex-col gap-2.5 border-t border-pb-border pt-6">
            <span className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">Office</span>
            <p className="text-sm leading-relaxed text-pb-text-muted">
              Bangalore, India
            </p>
          </div>
        </div>
      </section>
    </>
  );
}
