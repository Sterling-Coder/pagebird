import { NextResponse } from "next/server";
import { Resend } from "resend";

const CONTACT_TO_EMAIL = process.env.CONTACT_TO_EMAIL ?? "founder@thepagebirdy.com";
const CONTACT_FROM_EMAIL = process.env.CONTACT_FROM_EMAIL ?? "onboarding@resend.dev";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const NAME_MAX = 200;
const COMPANY_MAX = 200;
const MESSAGE_MAX = 5000;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 3;

// Best-effort only: resets per serverless instance, but still blocks casual
// abuse of this route as a free email relay to arbitrary addresses.
const submissionsByIp = new Map<string, number[]>();

function isRateLimited(ip: string): boolean {
  const now = Date.now();
  const timestamps = (submissionsByIp.get(ip) ?? []).filter(
    (t) => now - t < RATE_LIMIT_WINDOW_MS
  );
  if (timestamps.length >= RATE_LIMIT_MAX) {
    submissionsByIp.set(ip, timestamps);
    return true;
  }
  timestamps.push(now);
  submissionsByIp.set(ip, timestamps);
  return false;
}

export async function POST(request: Request) {
  const resendApiKey = process.env.RESEND_API_KEY;
  if (!resendApiKey) {
    console.error("RESEND_API_KEY is not configured");
    return NextResponse.json({ error: "Contact form is not configured." }, { status: 500 });
  }

  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  if (isRateLimited(ip)) {
    return NextResponse.json({ error: "Too many requests. Please try again later." }, { status: 429 });
  }

  let body: { name?: string; email?: string; company?: string; message?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const name = body.name?.trim().slice(0, NAME_MAX);
  const email = body.email?.trim();
  const company = body.company?.trim().slice(0, COMPANY_MAX) ?? "";
  const message = body.message?.trim().slice(0, MESSAGE_MAX) ?? "";

  if (!name || !email || !EMAIL_RE.test(email)) {
    return NextResponse.json({ error: "A valid name and email are required." }, { status: 400 });
  }

  const resend = new Resend(resendApiKey);

  try {
    const { error } = await resend.emails.send({
      from: `Pagebirdy Contact Form <${CONTACT_FROM_EMAIL}>`,
      to: CONTACT_TO_EMAIL,
      replyTo: email,
      subject: `New contact form submission from ${name}`,
      text: [
        `Name: ${name}`,
        `Email: ${email}`,
        `Company: ${company || "-"}`,
        "",
        "What are you translating?",
        message || "-",
      ].join("\n"),
    });

    if (error) {
      console.error("Resend error:", error);
      return NextResponse.json({ error: "Failed to send message." }, { status: 502 });
    }

    const { error: confirmationError } = await resend.emails.send({
      from: `Pagebirdy <${CONTACT_FROM_EMAIL}>`,
      to: email,
      subject: "We got your message",
      text: [
        `Hi ${name},`,
        "",
        "Thanks for reaching out to Pagebirdy. We received your message and will get back to you within [X] business hours.",
        "",
        "— Pagebirdy",
      ].join("\n"),
    });

    if (confirmationError) {
      console.error("Resend confirmation error:", confirmationError);
    }

    return NextResponse.json({ ok: true });
  } catch (err) {
    console.error("Contact form send failed:", err);
    return NextResponse.json({ error: "Failed to send message." }, { status: 500 });
  }
}
