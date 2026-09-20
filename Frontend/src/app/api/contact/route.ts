import { NextResponse } from "next/server";
import { Resend } from "resend";

const CONTACT_TO_EMAIL = process.env.CONTACT_TO_EMAIL ?? "founder@thepagebirdy.com";
const CONTACT_FROM_EMAIL = process.env.CONTACT_FROM_EMAIL ?? "onboarding@resend.dev";

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
}

function confirmationEmailHtml(name: string): string {
  const safeName = escapeHtml(name);
  return `<!doctype html>
<html>
  <body style="margin:0;padding:0;background:#f6f3ea;font-family:Georgia,'Times New Roman',serif;">
    <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background:#f6f3ea;padding:32px 16px;">
      <tr>
        <td align="center">
          <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px;width:100%;background:#fdfcf7;border:3px solid #15130f;">
            <tr>
              <td style="background:#153a2e;padding:22px 28px;">
                <span style="font-family:Georgia,'Times New Roman',serif;font-style:italic;font-size:24px;color:#f2ede0;">
                  page<span style="color:#e08a6f;">birdy</span>
                </span>
              </td>
            </tr>
            <tr>
              <td style="padding:32px 28px;">
                <p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#15130f;">
                  Hi ${safeName},
                </p>
                <p style="margin:0 0 16px;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#15130f;">
                  Thanks for reaching out to Pagebirdy. We received your message and will get back to you within <strong>48 business hours</strong>.
                </p>
                <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:15px;line-height:1.6;color:#6e6a61;">
                  — Pagebirdy
                </p>
              </td>
            </tr>
            <tr>
              <td style="padding:16px 28px;border-top:3px solid #dad4c7;">
                <p style="margin:0;font-family:Arial,Helvetica,sans-serif;font-size:12px;color:#8fa090;">
                  Pagebirdy · K-8 curriculum translation
                </p>
              </td>
            </tr>
          </table>
        </td>
      </tr>
    </table>
  </body>
</html>`;
}

const NAME_MAX = 200;
const COMPANY_MAX = 200;
const MESSAGE_MAX = 5000;
const MAX_BODY_BYTES = 20_000;
const RATE_LIMIT_WINDOW_MS = 60_000;
const RATE_LIMIT_MAX = 3;
const RATE_LIMIT_MAX_TRACKED_KEYS = 5000;

// Best-effort only: resets per serverless instance, but still blocks casual
// abuse of this route (as an email relay or to spam one recipient across
// rotating IPs). Keyed by both IP and target email so bypassing one axis
// alone doesn't defeat the limit, and pruned on every write so the map
// can't grow unbounded.
const submissionsByKey = new Map<string, number[]>();

function isRateLimited(key: string): boolean {
  const now = Date.now();
  const timestamps = (submissionsByKey.get(key) ?? []).filter(
    (t) => now - t < RATE_LIMIT_WINDOW_MS
  );

  if (timestamps.length >= RATE_LIMIT_MAX) {
    submissionsByKey.set(key, timestamps);
    return true;
  }

  timestamps.push(now);
  submissionsByKey.set(key, timestamps);

  if (submissionsByKey.size > RATE_LIMIT_MAX_TRACKED_KEYS) {
    const oldestKey = submissionsByKey.keys().next().value;
    if (oldestKey !== undefined) submissionsByKey.delete(oldestKey);
  }

  return false;
}

export async function POST(request: Request) {
  const resendApiKey = process.env.RESEND_API_KEY;
  if (!resendApiKey) {
    console.error("RESEND_API_KEY is not configured");
    return NextResponse.json({ error: "Contact form is not configured." }, { status: 500 });
  }

  const ip = request.headers.get("x-forwarded-for")?.split(",")[0]?.trim() ?? "unknown";
  if (isRateLimited(`ip:${ip}`)) {
    return NextResponse.json({ error: "Too many requests. Please try again later." }, { status: 429 });
  }

  const contentLength = Number(request.headers.get("content-length") ?? "0");
  if (contentLength > MAX_BODY_BYTES) {
    return NextResponse.json({ error: "Request body too large." }, { status: 413 });
  }

  let body: { name?: string; email?: string; company?: string; message?: string };
  try {
    const raw = await request.text();
    if (raw.length > MAX_BODY_BYTES) {
      return NextResponse.json({ error: "Request body too large." }, { status: 413 });
    }
    body = JSON.parse(raw);
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

  if (isRateLimited(`email:${email.toLowerCase()}`)) {
    return NextResponse.json({ error: "Too many requests. Please try again later." }, { status: 429 });
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
        "Thanks for reaching out to Pagebirdy. We received your message and will get back to you within 48 business hours.",
        "",
        "— Pagebirdy",
      ].join("\n"),
      html: confirmationEmailHtml(name),
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
