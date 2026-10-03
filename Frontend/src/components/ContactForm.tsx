"use client";

import { useState } from "react";

export default function ContactForm() {
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (submitted) {
    return (
      <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 rounded-xl border border-pb-border p-10 text-center">
        <span className="font-pb-display text-2xl text-pb-text">Message sent.</span>
        <p className="text-sm text-pb-text-muted">
          We&rsquo;ll get back to you within 48 business hours.
        </p>
      </div>
    );
  }

  return (
    <form
      className="flex flex-col gap-7"
      onSubmit={async (e) => {
        e.preventDefault();
        setError(null);
        setSubmitting(true);

        const form = e.currentTarget;
        const data = new FormData(form);

        try {
          const res = await fetch("/api/contact", {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({
              name: data.get("name"),
              email: data.get("email"),
              company: data.get("company"),
              message: data.get("message"),
            }),
          });

          if (!res.ok) {
            const body = await res.json().catch(() => null);
            throw new Error(body?.error ?? "Failed to send message.");
          }

          setSubmitted(true);
        } catch (err) {
          setError(err instanceof Error ? err.message : "Failed to send message.");
        } finally {
          setSubmitting(false);
        }
      }}
    >
      <div className="flex flex-col gap-2.5 border-b border-pb-border pb-4.5">
        <label className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase" htmlFor="name">
          Name
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          placeholder="Jane Doe"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-text outline-none placeholder:text-pb-text-muted"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b border-pb-border pb-4.5">
        <label className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase" htmlFor="email">
          Work email
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          placeholder="jane@company.com"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-text outline-none placeholder:text-pb-text-muted"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b border-pb-border pb-4.5">
        <label className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase" htmlFor="company">
          Company
        </label>
        <input
          id="company"
          name="company"
          type="text"
          placeholder="Northwind Holdings"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-text outline-none placeholder:text-pb-text-muted"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b border-pb-border pb-4.5">
        <label className="font-pb-mono text-[10px] font-bold tracking-widest text-pb-text-muted uppercase" htmlFor="message">
          What are you translating?
        </label>
        <textarea
          id="message"
          name="message"
          rows={3}
          placeholder="Quarterly reports, product manuals, legal contracts..."
          className="w-full resize-none bg-transparent py-1.5 text-[17px] leading-relaxed text-pb-text outline-none placeholder:text-pb-text-muted"
        />
      </div>
      {error && <p className="text-sm font-bold text-pb-accent">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="font-pb-mono mt-2 flex h-12 items-center justify-center rounded-full bg-pb-accent text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110 disabled:opacity-60"
      >
        {submitting ? "Sending…" : "Send message →"}
      </button>
    </form>
  );
}
