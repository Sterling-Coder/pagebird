import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";
import { AppTopBar } from "@/components/app/AppTopBar";
import { PageHeader } from "@/components/app/ui";
import { ReplayTourButton } from "@/components/app/Tour";

export const metadata: Metadata = {
  title: "Getting started",
};

const HELP_ICON = "M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20zM9.1 9a3 3 0 0 1 5.8 1c0 2-3 3-3 3M12 17h.01";

type Section = { id: string; title: string; href?: string; linkLabel?: string; body: ReactNode };

function A({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link href={href} className="text-[var(--app-accent,#c86018)] underline-offset-2 hover:underline">
      {children}
    </Link>
  );
}

const SECTIONS: Section[] = [
  {
    id: "basics",
    title: "How the app is laid out",
    href: "/app",
    linkLabel: "Go to Home",
    body: (
      <>
        <p>
          The sidebar on the left takes you everywhere. <A href="/app">Home</A> greets you, lets you name a project to
          create it, suggests next steps, and lists recent projects and anything that needs attention.
        </p>
        <p>
          Every translation is a <strong>job</strong>. Jobs run in the background, so you can start one, close the tab and
          come back later. Finished and failed jobs show up in <A href="/app/inbox">Inbox</A>, on the{" "}
          <A href="/app/jobs">Jobs</A> board and in their project.
        </p>
      </>
    ),
  },
  {
    id: "upload",
    title: "Translate a document",
    href: "/app/agents/document",
    linkLabel: "Open the Document & Office agent",
    body: (
      <>
        <ol className="list-decimal space-y-1 pl-5">
          <li>Open <A href="/app/agents">Agents</A> and pick the Document &amp; Office agent.</li>
          <li>Choose a file: PDF, IDML, Word (.docx), PowerPoint (.pptx), Excel (.xlsx) or plain text.</li>
          <li>Pick the language to translate into and, if you like, a project to file it under.</li>
          <li>Press <strong>Translate</strong>. Progress shows on the right, and you get the same file type back.</li>
        </ol>
        <p>
          InDesign <code>.indd</code> files aren&apos;t supported: in InDesign use File, Export, InDesign Markup (IDML) and
          upload that. Old <code>.doc</code>, <code>.ppt</code> and <code>.xls</code> files need re-saving in the newer
          format first. Right-to-left languages such as Arabic and Hebrew are mirrored for you.
        </p>
      </>
    ),
  },
  {
    id: "review",
    title: "Review and download",
    href: "/app/jobs",
    linkLabel: "Open the Jobs board",
    body: (
      <>
        <p>
          When a job finishes, press <strong>Download translation</strong> on the agent page, or find it later on the{" "}
          <A href="/app/jobs">Jobs</A> board, which sorts every translation into Translating, Needs attention and
          Delivered. Filter by type to narrow it down.
        </p>
        <p>
          Jobs filed under a project can be opened from <A href="/app/projects">Projects</A>. Each project has four tabs:
          Files (open a file to review its segments and download it), Settings, Linguistic assets and Statistics.
        </p>
      </>
    ),
  },
  {
    id: "images",
    title: "Translate an image",
    href: "/app/agents/image",
    linkLabel: "Open the OCR agent",
    body: (
      <p>
        The OCR agent reads the words in a PNG, JPEG, WEBP, PSD or AI file and paints the translation back into the image.
        Upload the file, pick a language and press Translate, the same way as a document.
      </p>
    ),
  },
  {
    id: "website",
    title: "Translate a web page",
    href: "/app/agents/website",
    linkLabel: "Open the Web agent",
    body: (
      <p>
        Paste the link to one public English page into the Web agent and pick a language. You get a translated,
        read-only copy of that page with scripts removed. Pages that need a login, or JavaScript to show their text,
        can&apos;t be translated. For a quick sentence or paragraph, use{" "}
        <A href="/app/agents/text">Quick Translate</A> instead.
      </p>
    ),
  },
  {
    id: "extension",
    title: "Use the Chrome extension",
    href: "/app/extension",
    linkLabel: "Extension setup",
    body: (
      <p>
        The extension translates what you read on any website, using this account. Load it in Chrome, sign in from its
        toolbar icon, then select text and click the translate button, or translate the whole page from the popup. The
        Extension page has step-by-step install instructions.
      </p>
    ),
  },
  {
    id: "glossary",
    title: "Glossary and workflows",
    href: "/app/glossary",
    linkLabel: "Open the Glossary",
    body: (
      <p>
        The <A href="/app/glossary">Glossary</A> lists locked terms for each language: wherever the source term appears,
        every translation uses the agreed wording. It&apos;s read-only for now. <A href="/app/workflows">Workflows</A>{" "}
        (Beta) shows the steps each agent runs, in order, every time you start a translation.
      </p>
    ),
  },
  {
    id: "team",
    title: "Work with your team",
    href: "/app/team",
    linkLabel: "Open Team",
    body: (
      <p>
        Invite teammates by email from <A href="/app/team">Team</A>. When someone invites you, the invitation appears in
        your <A href="/app/inbox">Inbox</A> and on the Team page, where you can accept or decline it.
      </p>
    ),
  },
  {
    id: "notifications",
    title: "Notifications and Inbox",
    href: "/app/inbox",
    linkLabel: "Open Inbox",
    body: (
      <p>
        The bell in the top-right corner shows job updates as they happen. <A href="/app/inbox">Inbox</A> keeps the last week of
        finished and failed translations, plus team invitations, so nothing slips past while you&apos;re away. Choose
        which events notify you under Preferences on your <A href="/app/profile">Profile</A>.
      </p>
    ),
  },
  {
    id: "theme",
    title: "Theme, sidebar and account",
    href: "/app/settings",
    linkLabel: "Open Settings",
    body: (
      <p>
        Use the theme toggle next to your name at the bottom of the sidebar to switch between light and dark, and the
        button beside the logo to hide the sidebar. Click your name at the bottom of the sidebar to open your <A href="/app/profile">Profile</A>:
        your plan, usage, and which notifications you want. <A href="/app/settings">Settings</A> holds your account
        details and sign-out.
      </p>
    ),
  },
];

export default function HelpPage() {
  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface,#ffffff)]">
      <AppTopBar />
      <PageHeader icon={HELP_ICON} title="Getting started" desc="Short how-tos for every part of Pagebirdy." />
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-12">
        <div className="grid max-w-[1040px] gap-8 lg:grid-cols-[200px_minmax(0,1fr)]">
          <nav aria-label="On this page" className="hidden lg:block">
            <ul className="sticky top-0 space-y-1 text-[12.5px]">
              {SECTIONS.map((s) => (
                <li key={s.id}>
                  <a href={`#${s.id}`} className="block rounded-md px-2 py-1 text-[var(--app-ink-soft,#57524b)] hover:bg-[var(--app-surface-2,#f6f2ea)] hover:text-[var(--app-ink,#1d1b18)]">
                    {s.title}
                  </a>
                </li>
              ))}
            </ul>
          </nav>

          <div className="space-y-4">
            <div className="flex flex-wrap items-center justify-between gap-3 rounded-2xl bg-[var(--app-surface-2,#f6f2ea)] p-4">
              <p className="text-[13px] text-[var(--app-ink-soft,#57524b)]">
                Prefer a guided look? The tour walks through the sidebar and notifications in under a minute.
              </p>
              <ReplayTourButton />
            </div>

            {SECTIONS.map((s, i) => (
              <section
                key={s.id}
                id={s.id}
                aria-labelledby={`${s.id}-title`}
                className="scroll-mt-4 rounded-2xl border border-[var(--app-border,#ebe5da)] p-5"
              >
                <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
                  <span className="font-mono text-[11px] text-[var(--app-muted,#8f8778)]">{String(i + 1).padStart(2, "0")}</span>
                  <h2 id={`${s.id}-title`} className="text-[14.5px] font-semibold text-[var(--app-ink,#1d1b18)]">{s.title}</h2>
                  {s.href ? (
                    <Link href={s.href} className="ml-auto text-[12.5px] text-[var(--app-accent,#c86018)] hover:underline">
                      {s.linkLabel} →
                    </Link>
                  ) : null}
                </div>
                <div className="mt-2.5 space-y-2 text-[13px] leading-relaxed text-[var(--app-ink-soft,#57524b)]">{s.body}</div>
              </section>
            ))}

            <section aria-labelledby="support-title" className="rounded-2xl border border-[var(--app-border,#ebe5da)] p-5">
              <h2 id="support-title" className="text-[14.5px] font-semibold text-[var(--app-ink,#1d1b18)]">Still stuck?</h2>
              <p className="mt-2 text-[13px] leading-relaxed text-[var(--app-ink-soft,#57524b)]">
                If a job fails, its reason is shown on the job. For anything else, <A href="/contact">contact support</A> and
                we&apos;ll get back to you.
              </p>
            </section>
          </div>
        </div>
      </div>
    </div>
  );
}
