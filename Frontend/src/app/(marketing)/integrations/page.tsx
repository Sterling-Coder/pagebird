import Link from "next/link";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Integrations — Pagebird",
  description: "Wherever the file lives, Pagebird can reach it.",
};

const INTEGRATIONS = [
  {
    title: "Google Drive",
    body: "Point at a folder. Every new doc is translated and dropped back beside the original.",
    icon: (
      <path d="M4 20V6a2 2 0 0 1 2-2h4l2 2h6a2 2 0 0 1 2 2v10a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2z" />
    ),
  },
  {
    title: "SharePoint",
    body: "Sync a document library. Version history and permissions stay intact.",
    icon: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 9h18" />
      </>
    ),
  },
  {
    title: "Slack",
    body: "Drop a file into a channel, get the translation back as a thread reply.",
    icon: (
      <>
        <rect x="3" y="3" width="18" height="18" rx="3" />
        <path d="M8 10v7" />
        <path d="M12 17v-4a2.5 2.5 0 0 1 5 0v4" />
      </>
    ),
  },
  {
    title: "REST API",
    body: "Submit a file, poll for status, download the result. Full OpenAPI spec.",
    icon: <path d="M20 6 9 17l-5-5M20 6 9 17" />,
  },
  {
    title: "Figma",
    body: "Translate text layers in place across frames without breaking auto-layout.",
    icon: (
      <>
        <rect x="4" y="4" width="16" height="16" rx="2" />
        <path d="M9 9h6v6H9z" />
      </>
    ),
  },
  {
    title: "Zapier",
    body: "Trigger translation from 6,000+ apps, no code required.",
    icon: (
      <>
        <path d="M12 2 3 7l9 5 9-5-9-5z" />
        <path d="M3 17l9 5 9-5" />
        <path d="M3 12l9 5 9-5" />
      </>
    ),
  },
  {
    title: "GitHub",
    body: "Translate docs and READMEs on push, opened as a pull request.",
    icon: <path d="m9 18 6-6-6-6" />,
  },
  {
    title: "Amazon S3",
    body: "Watch a bucket prefix; translated files land in a mirrored prefix.",
    icon: (
      <>
        <rect x="3" y="4" width="18" height="16" rx="2" />
        <path d="M3 10h18" />
      </>
    ),
  },
];

export default function IntegrationsPage() {
  return (
    <>
      <section className="border-b-[3px] border-pb-ink px-6 py-18 pb-14 md:px-14">
        <span className="font-pb-mono-brand text-[12.5px] font-bold tracking-widest text-pb-accent uppercase">
          — integrations
        </span>
        <h1 className="font-pb-display mt-4.5 max-w-3xl text-5xl md:text-6xl">
          Wherever the file lives, Pagebird can reach it.
        </h1>
        <p className="mt-5.5 max-w-xl text-[17px] leading-relaxed text-pb-muted">
          Watch a folder, connect a repo, or call the API directly. New and updated
          files come back translated without anyone opening Pagebird.
        </p>
      </section>

      <section className="grid grid-cols-1 border-b-[3px] border-pb-ink bg-pb-ink text-pb-paper sm:grid-cols-2 md:grid-cols-4">
        {INTEGRATIONS.map((item, i) => (
          <div
            key={item.title}
            className={`flex flex-col gap-3 border-pb-card-ink/15 p-8 ${
              i % 4 !== 3 ? "sm:border-r-[3px]" : ""
            } ${i < INTEGRATIONS.length - (INTEGRATIONS.length % 4 || 4) ? "border-b-[3px]" : "border-b-[3px] md:border-b-0"}`}
          >
            <svg
              width="26"
              height="26"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              strokeWidth="1.6"
              strokeLinecap="round"
              strokeLinejoin="round"
            >
              {item.icon}
            </svg>
            <h3 className="text-base font-bold">{item.title}</h3>
            <p className="text-pb-card-muted text-[13px] leading-relaxed">{item.body}</p>
          </div>
        ))}
      </section>

      <section className="flex flex-col items-start justify-between gap-6 bg-pb-ink px-6 py-14 text-pb-paper md:flex-row md:items-center md:px-14">
        <h2 className="font-pb-display max-w-lg text-2xl md:text-3xl">
          Don&rsquo;t see yours? We ship new integrations monthly.
        </h2>
        <Link
          href="/contact"
          className="flex h-13.5 flex-shrink-0 items-center bg-pb-accent px-7 text-[15px] font-bold text-pb-paper"
        >
          Request an integration →
        </Link>
      </section>
    </>
  );
}
