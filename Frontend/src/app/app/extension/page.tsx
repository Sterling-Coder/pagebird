import Link from "next/link";
import type { ReactNode } from "react";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, Icon, PageHeader } from "@/components/app/ui";

// Facts on this page come from Frontend/extension (manifest.json, README.md,
// background.js, content.js). Keep them in step when the extension changes.

const FEATURES: { title: string; body: ReactNode; icon: string }[] = [
  {
    title: "Translate a selection",
    body: (
      <>
        Select any word or sentence and click the <b className="font-semibold text-ink">文</b> button, or right-click
        and choose “Translate selection with Pagebirdy”. The translation appears beside it.
      </>
    ),
    icon: "M4 7V4h16v3M9 20h6M12 4v16",
  },
  {
    title: "Translate the whole page",
    body: (
      <>
        Use “Translate this page” in the toolbar popup or the right-click menu. Text is rewritten in place, and
        content that loads later is translated too. “Show original” puts it back.
      </>
    ),
    icon: "M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8zM14 2v6h6",
  },
  {
    title: "Your language, your account",
    body: <>Pick the target language in the popup, and turn the selection button off if you don’t want it.</>,
    icon: "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM2 12h20M12 2a15.3 15.3 0 0 1 0 20M12 2a15.3 15.3 0 0 0 0 20",
  },
];

const STEPS: { title: string; body: ReactNode }[] = [
  {
    title: "Get the extension",
    body: (
      <>
        It isn’t on the Chrome Web Store yet. <Link href="/contact" className="text-[color:var(--app-accent)] hover:underline">Ask us for the build</Link>,
        or use the <code className="rounded bg-[var(--app-surface)] px-1 font-mono text-[11.5px]">Frontend/extension</code> folder from the repository.
      </>
    ),
  },
  {
    title: "Load it in Chrome",
    body: (
      <>
        Open <code className="rounded bg-[var(--app-surface)] px-1 font-mono text-[11.5px]">chrome://extensions</code>, turn on
        Developer mode, click “Load unpacked” and pick the folder.
      </>
    ),
  },
  {
    title: "Sign in",
    body: <>Click the Pagebirdy icon in the toolbar and sign in with this account. Pick the language you want.</>,
  },
  {
    title: "Translate",
    body: <>Select text and click 文, or choose “Translate this page”. “Show original” restores it.</>,
  },
];

const PERMISSIONS: [string, string][] = [
  ["Read and change sites you visit", "Needed to show the 文 button and to rewrite page text when you ask it to."],
  ["Storage", "Keeps your sign-in and settings on this device, in the extension only. Pages never see your token."],
  ["Right-click menu", "Adds “Translate selection” and “Translate this page”."],
];

const FAQ: [string, ReactNode][] = [
  [
    "Is the text I translate stored?",
    <>No. Text is sent to Pagebirdy to translate and nothing is kept. Numbers, URLs, emails and <code className="font-mono">{"{placeholders}"}</code> come back unchanged.</>,
  ],
  [
    "Does it count against my plan?",
    <>It uses your Pagebirdy login and plan. Requests are rate limited per account, about 120 every 10 minutes by default.</>,
  ],
  [
    "Which parts of a page are skipped?",
    <>Code blocks, form fields, editable areas and anything marked “don’t translate” are left alone. Text inside cross-origin frames or closed shadow roots can’t be reached.</>,
  ],
  [
    "Can I try the translation first?",
    <>Yes. <Link href="/app/agents/text" className="text-[color:var(--app-accent)] hover:underline">Quick Translate</Link> uses the same engine in the browser, no install needed.</>,
  ],
];

function SectionTitle({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <div className="mb-3 px-1">
      <h2 className="text-[14px] font-semibold text-ink">{children}</h2>
      {hint ? <p className="text-[12.5px] text-muted">{hint}</p> : null}
    </div>
  );
}

/** Pure-CSS picture of the extension at work: a selected sentence, the 文
 * button and the translation card. Decorative. */
function PopupMock() {
  return (
    <div aria-hidden="true" className="overflow-hidden rounded-2xl border border-[color:var(--app-border)] bg-[var(--app-surface)] shadow-[0_8px_28px_var(--app-shadow)]">
      <div className="flex items-center gap-1.5 border-b border-[color:var(--app-border)] bg-[var(--app-surface-2)] px-3 py-2">
        <span className="h-2 w-2 rounded-full bg-[var(--app-border-strong)]" />
        <span className="h-2 w-2 rounded-full bg-[var(--app-border-strong)]" />
        <span className="h-2 w-2 rounded-full bg-[var(--app-border-strong)]" />
        <span className="ml-2 min-w-0 flex-1 truncate rounded-full bg-[var(--app-surface)] px-3 py-0.5 text-[10.5px] text-muted">
          shop.example.com/help/refunds
        </span>
      </div>
      <div className="relative p-4 sm:p-5">
        <div className="mb-3 h-2 w-1/3 rounded bg-[var(--app-surface-3)]" />
        <p className="text-[13px] leading-relaxed text-ink-soft">
          Our team reviews every order within one business day, and{" "}
          <mark className="rounded bg-[var(--app-highlight)] px-0.5 text-ink">refunds are issued to the original payment method.</mark>
          <span className="ml-1 inline-flex h-5 w-5 translate-y-0.5 items-center justify-center rounded-md bg-[var(--app-ink)] text-[11px] font-semibold text-[color:var(--app-surface)]">
            文
          </span>
        </p>
        <div className="mt-3 max-w-[340px] rounded-xl border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] p-3.5 shadow-[0_8px_28px_var(--app-shadow)]">
          <div className="mb-1 flex items-center justify-between text-[10.5px] uppercase tracking-[0.08em] text-muted">
            <span>Pagebirdy → Spanish</span>
            <span className="normal-case tracking-normal">Copy</span>
          </div>
          <p className="text-[13px] text-ink">Los reembolsos se emiten al método de pago original.</p>
        </div>
        <div className="mt-4 space-y-2">
          <div className="h-2 w-full rounded bg-[var(--app-surface-3)]" />
          <div className="h-2 w-4/5 rounded bg-[var(--app-surface-3)]" />
        </div>
      </div>
    </div>
  );
}

export default function ExtensionPage() {
  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.puzzle} title="Chrome extension" desc="Translate what you read on any website." />
      <div className="min-h-0 flex-1 overflow-auto px-4 pb-12 sm:px-6">
        <div className="mx-auto flex max-w-[920px] flex-col gap-10">
          {/* Hero */}
          <section className="grid items-center gap-6 rounded-2xl border border-[color:var(--app-border)] bg-[var(--app-surface-2)] p-5 sm:p-7 md:grid-cols-[minmax(0,1fr)_minmax(0,1.1fr)]">
            <div className="flex min-w-0 flex-col gap-4">
              <div className="flex flex-wrap items-center gap-2 text-[11.5px]">
                <span className="rounded-full bg-[var(--app-surface)] px-2.5 py-0.5 font-medium text-ink-soft">Pagebirdy Translate · v0.1.0</span>
                <span className="rounded-full bg-[var(--app-warn-bg)] px-2.5 py-0.5 font-medium text-[color:var(--app-warn)]">Early access</span>
              </div>
              <h2 className="text-[22px] font-semibold leading-tight text-ink [text-wrap:balance]">
                Read any website in your language, without leaving the page.
              </h2>
              <p className="text-[13px] leading-relaxed text-ink-soft">
                Select a sentence to translate it, or translate the whole page in place. It signs in with your Pagebirdy
                account, so there’s nothing new to set up.
              </p>
              <div className="flex flex-wrap items-center gap-3">
                <Link href="/contact"
                  className="rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90">
                  Request the extension
                </Link>
                <a href="#install" className="text-[12.5px] text-ink-soft underline-offset-4 hover:text-ink hover:underline">
                  How to install
                </a>
              </div>
              <p className="text-[11.5px] text-muted">Not on the Chrome Web Store yet. Works in Chrome and other Chromium browsers that load unpacked extensions.</p>
            </div>
            <PopupMock />
          </section>

          {/* What it does */}
          <section>
            <SectionTitle>What it does</SectionTitle>
            <div className="grid gap-3 sm:grid-cols-3">
              {FEATURES.map((f) => (
                <div key={f.title} className="flex flex-col gap-2 rounded-2xl border border-[color:var(--app-border)] p-4">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--app-surface-2)] text-ink-soft">
                    <Icon d={f.icon} />
                  </span>
                  <h3 className="text-[13.5px] font-semibold text-ink">{f.title}</h3>
                  <p className="text-[12.5px] leading-relaxed text-ink-soft">{f.body}</p>
                </div>
              ))}
            </div>
          </section>

          {/* Install */}
          <section id="install" className="scroll-mt-4">
            <SectionTitle hint="About two minutes.">Install it</SectionTitle>
            <ol className="grid gap-3 sm:grid-cols-2">
              {STEPS.map((s, i) => (
                <li key={s.title} className="flex gap-3 rounded-2xl bg-[var(--app-surface-2)] p-4">
                  <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-[var(--app-surface)] text-[12px] font-semibold text-ink tabular-nums">
                    {i + 1}
                  </span>
                  <div className="min-w-0">
                    <div className="text-[13.5px] font-semibold text-ink">{s.title}</div>
                    <p className="mt-1 text-[12.5px] leading-relaxed text-ink-soft">{s.body}</p>
                  </div>
                </li>
              ))}
            </ol>
          </section>

          {/* Permissions + FAQ */}
          <div className="grid gap-10 md:grid-cols-2 md:gap-6">
            <section>
              <SectionTitle hint="What Chrome will ask for, and why.">Permissions and privacy</SectionTitle>
              <ul className="divide-y divide-[color:var(--app-border)] rounded-2xl border border-[color:var(--app-border)]">
                {PERMISSIONS.map(([t, d]) => (
                  <li key={t} className="px-4 py-3">
                    <p className="text-[13px] text-ink">{t}</p>
                    <p className="text-[12px] leading-relaxed text-muted">{d}</p>
                  </li>
                ))}
              </ul>
            </section>

            <section>
              <SectionTitle>Questions</SectionTitle>
              <div className="divide-y divide-[color:var(--app-border)] rounded-2xl border border-[color:var(--app-border)]">
                {FAQ.map(([q, a]) => (
                  <details key={q} className="group px-4 py-3">
                    <summary className="flex cursor-pointer list-none items-center justify-between gap-3 text-[13px] text-ink [&::-webkit-details-marker]:hidden">
                      {q}
                      <span aria-hidden="true" className="text-muted transition-transform group-open:rotate-45">+</span>
                    </summary>
                    <p className="mt-2 text-[12.5px] leading-relaxed text-ink-soft">{a}</p>
                  </details>
                ))}
              </div>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
