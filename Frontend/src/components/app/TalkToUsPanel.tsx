"use client";

import { useEffect, useRef, useState } from "react";
import { getMe } from "@/lib/team";

export function TalkToUsPanel({ onClose }: { onClose: () => void }) {
  const [message, setMessage] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleKeyDown(e: KeyboardEvent) {
      if (e.key === "Escape") onClose();
    }
    function handleClickOutside(e: MouseEvent) {
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) onClose();
    }
    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [onClose]);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);

    try {
      const me = await getMe().catch(() => null);

      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: me?.full_name || me?.email || "Pagebirdy user",
          email: me?.email,
          message,
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
  }

  return (
    <div
      ref={panelRef}
      className="fixed right-6 bottom-6 z-50 w-full max-w-sm border border-ink bg-paper shadow-lg"
    >
      <div className="flex items-center justify-between border-b border-rule px-5 py-4">
        <span className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
          Talk to us
        </span>
        <button
          type="button"
          onClick={onClose}
          aria-label="Close"
          className="text-ink-soft hover:text-ink"
        >
          ✕
        </button>
      </div>

      {submitted ? (
        <div className="flex flex-col items-center gap-2 p-8 text-center">
          <span className="text-lg font-semibold text-ink">Message sent.</span>
          <p className="text-sm text-ink-soft">
            We&rsquo;ll get back to you within 48 business hours.
          </p>
          <button
            type="button"
            onClick={onClose}
            className="mt-3 border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
          >
            Close
          </button>
        </div>
      ) : (
        <form onSubmit={handleSubmit} className="flex flex-col gap-3 p-5">
          <label
            htmlFor="talk-to-us-message"
            className="font-mono text-[11px] uppercase tracking-widest text-ink-soft"
          >
            What&rsquo;s going on?
          </label>
          <textarea
            id="talk-to-us-message"
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            required
            rows={4}
            placeholder="Tell us what you need..."
            className="w-full resize-none border border-rule bg-transparent p-3 text-sm text-ink outline-none placeholder:text-ink-soft focus:border-ink"
          />
          {error && <p className="text-sm font-semibold text-red">{error}</p>}
          <button
            type="submit"
            disabled={submitting}
            className="mt-1 flex h-11 items-center justify-center bg-red font-mono text-[11px] uppercase tracking-widest text-paper disabled:opacity-60"
          >
            {submitting ? "Sending…" : "Send message"}
          </button>
        </form>
      )}
    </div>
  );
}
