import { NextResponse } from "next/server";
import { Resend } from "resend";

const CONTACT_TO_EMAIL = process.env.CONTACT_TO_EMAIL ?? "founder@thepagebirdy.com";
const CONTACT_FROM_EMAIL = process.env.CONTACT_FROM_EMAIL ?? "onboarding@resend.dev";

export async function POST(request: Request) {
  const resendApiKey = process.env.RESEND_API_KEY;
  if (!resendApiKey) {
    console.error("RESEND_API_KEY is not configured");
    return NextResponse.json({ error: "Contact form is not configured." }, { status: 500 });
  }

  let body: { name?: string; email?: string; company?: string; message?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: "Invalid request body." }, { status: 400 });
  }

  const name = body.name?.trim();
  const email = body.email?.trim();
  const company = body.company?.trim() ?? "";
  const message = body.message?.trim() ?? "";

  if (!name || !email) {
    return NextResponse.json({ error: "Name and email are required." }, { status: 400 });
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
