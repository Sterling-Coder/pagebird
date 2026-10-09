import Link from "next/link";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, Icon, PageHeader } from "@/components/app/ui";

type Kind = "Trigger" | "Agent" | "Tool" | "Deliver";
type Step = { kind: Kind; text: string };
type Flow = { name: string; href: string; icon: string; formats: string; steps: Step[] };

// Step kinds use the app's semantic tokens so they read in light and dark.
const KIND_STYLE: Record<Kind, { color: string; bg: string }> = {
  Trigger: { color: "var(--app-success)", bg: "var(--app-success-bg)" },
  Agent: { color: "var(--app-accent)", bg: "var(--app-warn-bg)" },
  Tool: { color: "var(--app-ink-soft)", bg: "var(--app-neutral-bg)" },
  Deliver: { color: "var(--app-ink)", bg: "var(--app-surface-3)" },
};

// The built-in workflows: each is exactly what the matching agent runs today.
const FLOWS: Flow[] = [
  {
    name: "Document & Office", href: "/app/agents/document", icon: ICON.glossary,
    formats: ".idml .pdf .docx .pptx .xlsx",
    steps: [
      { kind: "Trigger", text: "You upload a file" },
      { kind: "Agent", text: "Protect maths, numbers and links" },
      { kind: "Agent", text: "Translate with your glossary" },
      { kind: "Tool", text: "Rebuild the same file, right-to-left if needed" },
      { kind: "Deliver", text: "Download and review segments" },
    ],
  },
  {
    name: "Image", href: "/app/agents/image", icon: ICON.projects,
    formats: ".png .jpg .webp .psd .ai",
    steps: [
      { kind: "Trigger", text: "You upload an image" },
      { kind: "Tool", text: "Read the text with OCR" },
      { kind: "Agent", text: "Translate what should change" },
      { kind: "Tool", text: "Repaint in the same box and colour" },
      { kind: "Deliver", text: "Image in the same format" },
    ],
  },
  {
    name: "Website", href: "/app/agents/website", icon: ICON.puzzle,
    formats: "Any public URL",
    steps: [
      { kind: "Trigger", text: "You paste a public URL" },
      { kind: "Tool", text: "Fetch safely, scripts removed" },
      { kind: "Agent", text: "Translate as website copy" },
      { kind: "Deliver", text: "Read-only translated page" },
    ],
  },
];

const SHARED = [
  { label: "Glossary", desc: "Terms every workflow keeps the same.", href: "/app/glossary", icon: ICON.glossary },
  { label: "Team", desc: "Teammates see and download the results.", href: "/app/team", icon: ICON.team },
  { label: "Notifications", desc: "Get told when a job finishes or fails.", href: "/app/profile#preferences", icon: ICON.inbox },
];

const COMING = [
  { name: "Second-pass review", desc: "Send each translation to a teammate to approve before it's marked delivered." },
  { name: "Deliver to Drive or Slack", desc: "Drop the finished file into a shared folder or post it to a channel." },
  { name: "One file, many languages", desc: "Start one upload and get every target language you choose." },
];

function KindChip({ kind }: { kind: Kind }) {
  const s = KIND_STYLE[kind];
  return (
    <span className="inline-block rounded-full px-2 py-0.5 text-[10.5px] font-medium uppercase tracking-[0.06em]"
      style={{ color: s.color, background: s.bg }}>
      {kind}
    </span>
  );
}

function Pipeline({ steps }: { steps: Step[] }) {
  return (
    <ol className="flex flex-col gap-0 md:flex-row md:items-stretch">
      {steps.map((step, i) => (
        <li key={i} className="flex min-w-0 flex-col md:flex-1 md:flex-row md:items-center">
          <div className="flex min-w-0 flex-1 gap-3 rounded-xl border border-[color:var(--app-border)] bg-[var(--app-surface)] px-3 py-2.5 shadow-[0_1px_2px_var(--app-shadow)] md:h-full md:flex-col md:gap-1.5">
            <span className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full bg-[var(--app-surface-2)] text-[10.5px] font-semibold tabular-nums text-[color:var(--app-muted)]">
              {i + 1}
            </span>
            <div className="min-w-0">
              <KindChip kind={step.kind} />
              <p className="mt-1 text-[12.5px] leading-snug text-[color:var(--app-ink)]">{step.text}</p>
            </div>
          </div>
          {i < steps.length - 1 ? (
            <span aria-hidden="true"
              className="mx-auto h-3 w-px bg-[var(--app-border-hover)] md:mx-0 md:h-px md:w-3 md:shrink-0" />
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export default function WorkflowsPage() {
  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.flow} title="Workflows" desc="What runs, in order, each time you start a translation." />
      <div className="min-h-0 flex-1 overflow-auto px-4 pb-12 sm:px-6">
        <div className="mx-auto flex max-w-[920px] flex-col gap-8">
          <div className="flex flex-wrap items-center gap-3 rounded-2xl bg-[var(--app-surface-2)] px-5 py-4">
            <span className="rounded-full bg-[var(--app-warn-bg)] px-2.5 py-0.5 text-[11px] font-semibold text-[color:var(--app-warn)]">Beta</span>
            <p className="min-w-0 flex-1 text-[12.5px] text-[color:var(--app-ink-soft)]">
              A workflow is the chain of steps behind each translation. These three are built in and run automatically.
              Building your own is on the way.
            </p>
            <Link href="/app"
              className="rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white transition-opacity hover:opacity-90">
              Start a translation
            </Link>
          </div>

          <section aria-labelledby="builtin-title" className="flex flex-col gap-3">
            <div className="px-1">
              <h2 id="builtin-title" className="text-[14px] font-semibold text-[color:var(--app-ink)]">Built-in workflows</h2>
              <p className="text-[12.5px] text-[color:var(--app-muted)]">Picked for you from the kind of file you upload.</p>
            </div>
            {FLOWS.map((f) => (
              <article key={f.name} className="rounded-2xl border border-[color:var(--app-border)] p-4 sm:p-5"
                style={{ backgroundImage: "radial-gradient(var(--app-dots) 1px, transparent 1px)", backgroundSize: "16px 16px" }}>
                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-[var(--app-surface-2)] text-[color:var(--app-ink-soft)]">
                    <Icon d={f.icon} />
                  </span>
                  <div className="min-w-0 flex-1">
                    <h3 className="text-[13.5px] font-semibold text-[color:var(--app-ink)]">{f.name}</h3>
                    <p className="text-[11.5px] text-[color:var(--app-muted)]">{f.formats} · {f.steps.length} steps</p>
                  </div>
                  <Link href={f.href}
                    className="rounded-full border border-[color:var(--app-border)] bg-[var(--app-surface)] px-3.5 py-1.5 text-[12px] font-medium text-[color:var(--app-ink-soft)] transition-colors hover:border-[color:var(--app-ink-soft)] hover:text-[color:var(--app-ink)]">
                    Run it →
                  </Link>
                </div>
                <Pipeline steps={f.steps} />
              </article>
            ))}
          </section>

          <section aria-labelledby="shared-title" className="flex flex-col gap-3">
            <div className="px-1">
              <h2 id="shared-title" className="text-[14px] font-semibold text-[color:var(--app-ink)]">Used by every workflow</h2>
              <p className="text-[12.5px] text-[color:var(--app-muted)]">Set these once and each run picks them up.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {SHARED.map((s) => (
                <Link key={s.label} href={s.href}
                  className="group flex gap-3 rounded-2xl border border-[color:var(--app-border)] p-4 transition-colors hover:border-[color:var(--app-border-hover)] hover:bg-[var(--app-surface-2)]">
                  <span className="text-[color:var(--app-muted)] group-hover:text-[color:var(--app-ink)]"><Icon d={s.icon} /></span>
                  <div className="min-w-0">
                    <p className="text-[13px] font-medium text-[color:var(--app-ink)]">{s.label}</p>
                    <p className="text-[12px] text-[color:var(--app-muted)]">{s.desc}</p>
                  </div>
                </Link>
              ))}
            </div>
          </section>

          <section aria-labelledby="coming-title" className="flex flex-col gap-3">
            <div className="px-1">
              <h2 id="coming-title" className="text-[14px] font-semibold text-[color:var(--app-ink)]">Coming next</h2>
              <p className="text-[12.5px] text-[color:var(--app-muted)]">Examples of workflows you&apos;ll be able to build. Not available yet.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-3">
              {COMING.map((c) => (
                <div key={c.name} className="flex flex-col gap-2 rounded-2xl border border-dashed border-[color:var(--app-border-strong)] p-4">
                  <span className="self-start rounded-full bg-[var(--app-neutral-bg)] px-2 py-0.5 text-[10.5px] font-medium text-[color:var(--app-muted)]">
                    Coming soon
                  </span>
                  <p className="text-[13px] font-medium text-[color:var(--app-ink)]">{c.name}</p>
                  <p className="text-[12px] text-[color:var(--app-muted)]">{c.desc}</p>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
}
