"use client";

import { useId, useRef, useState } from "react";

const TOPICS = [
  { value: "sales", label: "Sales & pricing", hint: "Plans, volume pricing, or what fits after your 14-day free trial." },
  { value: "enterprise", label: "Enterprise", hint: "Custom formats, shared glossaries and high-volume IDML workflows." },
  { value: "support", label: "Support", hint: "A file that didn't come back the way you expected? Tell us which one." },
  { value: "extension", label: "Chrome extension", hint: "Early access to translating pages and selections in the browser." },
] as const;

type TopicValue = (typeof TOPICS)[number]["value"];
type FieldName = "name" | "email" | "message";
type Errors = Partial<Record<FieldName, string>>;

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const MESSAGE_MAX = 4800; // API caps at 5000; leave room for the topic prefix.

const C = {
  cardBorder: "#2a2826",
  inputBorder: "#34312d",
  error: "#f08a7a",
  coral: "#e08a6f",
  text: "#f0ece3",
  secondary: "#a8a49a",
  muted: "#8a8478",
  primary: "#c86018",
};

function validate(values: { name: string; email: string; message: string }): Errors {
  const errors: Errors = {};
  if (!values.name.trim()) errors.name = "Tell us your name.";
  if (!values.email.trim()) errors.email = "We need an email to reply to.";
  else if (!EMAIL_RE.test(values.email.trim())) errors.email = "That email doesn't look right.";
  if (values.message.trim().length < 10) errors.message = "Add a sentence or two so we can help.";
  return errors;
}

const inputClass =
  "w-full rounded-none border-0 border-b bg-transparent px-0 py-2.5 text-[16px] leading-snug outline-none transition-colors placeholder:text-[#5f5a52] focus-visible:border-[#e08a6f] aria-[invalid=true]:border-[#f08a7a]";

const labelClass = "text-[13px] font-semibold";

export default function ContactForm() {
  const uid = useId();
  const ids = {
    name: `${uid}-name`,
    email: `${uid}-email`,
    company: `${uid}-company`,
    message: `${uid}-message`,
  };

  const [topic, setTopic] = useState<TopicValue>("sales");
  const [values, setValues] = useState({ name: "", email: "", company: "", message: "" });
  const [touched, setTouched] = useState<Partial<Record<FieldName, boolean>>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const successRef = useRef<HTMLDivElement>(null);
  const nameRef = useRef<HTMLInputElement>(null);
  const emailRef = useRef<HTMLInputElement>(null);
  const messageRef = useRef<HTMLTextAreaElement>(null);

  const errors = validate(values);
  const showError = (f: FieldName) => (touched[f] ? errors[f] : undefined);

  const update =
    (field: keyof typeof values) =>
    (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) =>
      setValues((v) => ({ ...v, [field]: e.target.value }));

  const blur = (field: FieldName) => () => setTouched((t) => ({ ...t, [field]: true }));

  async function onSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    setError(null);
    setTouched({ name: true, email: true, message: true });

    const firstInvalid = (["name", "email", "message"] as const).find((f) => errors[f]);
    if (firstInvalid) {
      const target = { name: nameRef, email: emailRef, message: messageRef }[firstInvalid];
      target.current?.focus();
      return;
    }

    setSubmitting(true);
    const topicLabel = TOPICS.find((t) => t.value === topic)?.label ?? "General";

    try {
      // The API only accepts name/email/company/message, so the topic travels
      // inside the message body.
      const res = await fetch("/api/contact", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          name: values.name.trim(),
          email: values.email.trim(),
          company: values.company.trim(),
          message: `Topic: ${topicLabel}\n\n${values.message.trim()}`,
        }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => null);
        throw new Error(body?.error ?? "Failed to send message.");
      }

      setSubmitted(true);
      requestAnimationFrame(() => successRef.current?.focus());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to send message.");
    } finally {
      setSubmitting(false);
    }
  }

  if (submitted) {
    return (
      <div
        ref={successRef}
        tabIndex={-1}
        role="status"
        className="flex min-h-[420px] flex-col items-start justify-center gap-4 outline-none motion-safe:animate-[pb-entrance-label_0.6s_cubic-bezier(0.16,1,0.3,1)_both]"
      >
        <span
          aria-hidden
          className="flex h-11 w-11 items-center justify-center rounded-full"
          style={{ background: C.primary, color: "#ffffff" }}
        >
          <svg width="20" height="20" viewBox="0 0 20 20" fill="none">
            <path d="M4.5 10.5l3.5 3.5 7.5-8" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
          </svg>
        </span>
        <h2 className="text-[26px] font-semibold tracking-tight" style={{ color: C.text }}>
          Message sent.
        </h2>
        <p className="max-w-sm text-[15px] leading-relaxed" style={{ color: C.secondary }}>
          Thanks{values.name.trim() ? `, ${values.name.trim().split(/\s+/)[0]}` : ""}. We&rsquo;ve
          sent a confirmation to <span style={{ color: C.text }}>{values.email.trim()}</span> and
          will reply, usually within one business day.
        </p>
        <button
          type="button"
          onClick={() => {
            setSubmitted(false);
            setValues({ name: "", email: "", company: "", message: "" });
            setTouched({});
          }}
          className="mt-2 rounded-full px-4 py-2 text-[13px] font-semibold outline-none transition-colors hover:bg-white/5 focus-visible:ring-2 focus-visible:ring-[#e08a6f]"
          style={{ color: C.text, border: `1px solid ${C.cardBorder}` }}
        >
          Send another message
        </button>
      </div>
    );
  }

  const fieldStyle = { borderBottomColor: C.inputBorder, color: C.text };

  return (
    <form noValidate onSubmit={onSubmit} className="flex flex-col gap-6" aria-busy={submitting}>
      <fieldset className="flex flex-col gap-3">
        <legend className={`${labelClass} mb-3`} style={{ color: C.text }}>
          What&rsquo;s this about?
        </legend>
        <div className="flex flex-wrap gap-2">
          {TOPICS.map((t) => {
            const active = topic === t.value;
            return (
              <label
                key={t.value}
                className="relative flex cursor-pointer items-center justify-center rounded-full px-4 py-2.5 text-center text-[13px] font-medium transition-colors has-[:focus-visible]:ring-2 has-[:focus-visible]:ring-[#e08a6f]"
                style={{
                  background: active ? C.primary : "transparent",
                  border: `1px solid ${active ? C.primary : C.inputBorder}`,
                  color: active ? "#ffffff" : C.secondary,
                }}
              >
                <input
                  type="radio"
                  name="topic"
                  value={t.value}
                  checked={active}
                  onChange={() => setTopic(t.value)}
                  className="sr-only"
                />
                {t.label}
              </label>
            );
          })}
        </div>
        <p className="text-[13.5px] leading-relaxed" style={{ color: C.secondary }} aria-live="polite">
          {TOPICS.find((t) => t.value === topic)?.hint}
        </p>
      </fieldset>

      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 sm:gap-4">
        <Field id={ids.name} label="Name" error={showError("name")}>
          <input
            ref={nameRef}
            id={ids.name}
            name="name"
            type="text"
            autoComplete="name"
            required
            maxLength={200}
            placeholder="Jane Doe"
            value={values.name}
            onChange={update("name")}
            onBlur={blur("name")}
            aria-invalid={!!showError("name")}
            aria-describedby={showError("name") ? `${ids.name}-err` : undefined}
            className={inputClass}
            style={fieldStyle}
          />
        </Field>
        <Field id={ids.email} label="Work email" error={showError("email")}>
          <input
            ref={emailRef}
            id={ids.email}
            name="email"
            type="email"
            autoComplete="email"
            inputMode="email"
            required
            placeholder="jane@company.com"
            value={values.email}
            onChange={update("email")}
            onBlur={blur("email")}
            aria-invalid={!!showError("email")}
            aria-describedby={showError("email") ? `${ids.email}-err` : undefined}
            className={inputClass}
            style={fieldStyle}
          />
        </Field>
      </div>

      <Field id={ids.company} label="Company" optional>
        <input
          id={ids.company}
          name="company"
          type="text"
          autoComplete="organization"
          maxLength={200}
          placeholder="Northwind Publishing"
          value={values.company}
          onChange={update("company")}
          className={inputClass}
          style={fieldStyle}
        />
      </Field>

      <Field
        id={ids.message}
        label="How can we help?"
        error={showError("message")}
        hint="Formats, languages, page counts or a link to the file all help."
      >
        <textarea
          ref={messageRef}
          id={ids.message}
          name="message"
          rows={5}
          required
          maxLength={MESSAGE_MAX}
          placeholder="We localise a 120-page IDML catalogue into Arabic and German every quarter…"
          value={values.message}
          onChange={update("message")}
          onBlur={blur("message")}
          aria-invalid={!!showError("message")}
          aria-describedby={`${ids.message}-hint${showError("message") ? ` ${ids.message}-err` : ""}`}
          className={`${inputClass} min-h-[132px] resize-y leading-relaxed`}
          style={fieldStyle}
        />
      </Field>

      <div aria-live="assertive">
        {error && (
          <p
            className="rounded-xl px-4 py-3 text-[14px] leading-relaxed"
            style={{ background: "#2a1714", border: "1px solid #5a2a24", color: C.error }}
          >
            {error} You can also email us at{" "}
            <a href="mailto:hello@pagebirdy.com" className="underline underline-offset-2">
              hello@pagebirdy.com
            </a>
            .
          </p>
        )}
      </div>

      <div className="flex flex-col-reverse gap-4 sm:flex-row sm:items-center sm:justify-between">
        <p className="text-[12px] leading-relaxed" style={{ color: C.muted }}>
          We only use your details to reply.
        </p>
        <button
          type="submit"
          disabled={submitting}
          className="inline-flex h-12 shrink-0 items-center justify-center gap-2 whitespace-nowrap rounded-full px-7 text-[15px] font-semibold text-white outline-none transition-[filter,opacity] hover:brightness-110 focus-visible:ring-2 focus-visible:ring-[#e08a6f] focus-visible:ring-offset-2 focus-visible:ring-offset-[#171614] disabled:cursor-not-allowed disabled:opacity-60"
          style={{ background: C.primary }}
        >
          {submitting && (
            <svg aria-hidden className="h-4 w-4 motion-safe:animate-spin" viewBox="0 0 24 24" fill="none">
              <circle cx="12" cy="12" r="9" stroke="currentColor" strokeOpacity="0.3" strokeWidth="3" />
              <path d="M21 12a9 9 0 0 0-9-9" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
            </svg>
          )}
          {submitting ? "Sending…" : "Send message"}
        </button>
      </div>
    </form>
  );
}

function Field({
  id,
  label,
  optional,
  hint,
  error,
  children,
}: {
  id: string;
  label: string;
  optional?: boolean;
  hint?: string;
  error?: string;
  children: React.ReactNode;
}) {
  return (
    <div className="flex flex-col gap-2">
      <label htmlFor={id} className={labelClass} style={{ color: C.text }}>
        {label}
        {optional && (
          <span className="ml-1.5 font-normal" style={{ color: C.muted }}>
            (optional)
          </span>
        )}
      </label>
      {children}
      {hint && (
        <p id={`${id}-hint`} className="text-[12px]" style={{ color: C.muted }}>
          {hint}
        </p>
      )}
      {error && (
        <p id={`${id}-err`} className="text-[13px]" style={{ color: C.error }}>
          {error}
        </p>
      )}
    </div>
  );
}
