"use client";

import { useState } from "react";

export default function ContactForm() {
  const [submitted, setSubmitted] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (submitted) {
    return (
      <div className="flex h-full min-h-64 flex-col items-center justify-center gap-3 border-[3px] border-pb-ink p-10 text-center">
        <span className="font-pb-display text-2xl">Message sent.</span>
        <p className="text-sm text-pb-muted">
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
      <div className="flex flex-col gap-2.5 border-b-2 border-pb-ink pb-4.5">
        <label className="font-pb-mono-brand text-[11px] font-bold text-pb-faint" htmlFor="name">
          NAME
        </label>
        <input
          id="name"
          name="name"
          type="text"
          required
          placeholder="Jane Doe"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-ink outline-none placeholder:text-pb-faint"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b-2 border-pb-ink pb-4.5">
        <label className="font-pb-mono-brand text-[11px] font-bold text-pb-faint" htmlFor="email">
          WORK EMAIL
        </label>
        <input
          id="email"
          name="email"
          type="email"
          required
          placeholder="jane@company.com"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-ink outline-none placeholder:text-pb-faint"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b-2 border-pb-ink pb-4.5">
        <label className="font-pb-mono-brand text-[11px] font-bold text-pb-faint" htmlFor="company">
          COMPANY
        </label>
        <input
          id="company"
          name="company"
          type="text"
          placeholder="Northwind Holdings"
          className="w-full bg-transparent py-1.5 text-[17px] text-pb-ink outline-none placeholder:text-pb-faint"
        />
      </div>
      <div className="flex flex-col gap-2.5 border-b-2 border-pb-ink pb-4.5">
        <label className="font-pb-mono-brand text-[11px] font-bold text-pb-faint" htmlFor="message">
          WHAT ARE YOU TRANSLATING?
        </label>
        <textarea
          id="message"
          name="message"
          rows={3}
          placeholder="Quarterly reports, product manuals, legal contracts..."
          className="w-full resize-none bg-transparent py-1.5 text-[17px] leading-relaxed text-pb-ink outline-none placeholder:text-pb-faint"
        />
      </div>
      {error && <p className="text-sm font-bold text-pb-accent">{error}</p>}
      <button
        type="submit"
        disabled={submitting}
        className="mt-2 flex h-14 items-center justify-center bg-pb-ink text-[15px] font-bold text-pb-paper disabled:opacity-60"
      >
        {submitting ? "Sending…" : "Send message →"}
      </button>
    </form>
  );
}
