"use client";

import { useEffect, useState } from "react";
import { AgentShell, Field } from "../AgentShell";
import { JobProgress, useJob, useJobParam } from "../JobStatus";
import { LanguageSelect, PrimaryButton, Empty, Pill } from "@/components/app/ui";
import { getWebsiteHtml, startWebsiteJob } from "@/lib/agents";

export default function WebsiteAgentPage() {
  const [url, setUrl] = useState("");
  const [lang, setLang] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useJobParam();
  const job = useJob(jobId);
  const [view, setView] = useState<"result" | "source">("result");
  const [html, setHtml] = useState<string | null>(null);

  useEffect(() => {
    if (job?.status !== "complete") return;
    let stop = false;
    getWebsiteHtml(job.id, view).then((h) => { if (!stop) setHtml(h); }).catch(() => { if (!stop) setHtml(null); });
    return () => { stop = true; };
  }, [job?.status, job?.id, view]);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (!url.trim() || !lang) return;
    setBusy(true);
    setError(null);
    setHtml(null);
    try {
      setJobId(await startWebsiteJob(url.trim(), lang));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not start the translation.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AgentShell
      name="Web Agent"
      desc="Paste a public English page. You get a translated, read-only copy with scripts removed."
      form={
        <form onSubmit={start}>
          <Field label="Page URL">
            <input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/pricing"
              className="w-full rounded-xl border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-2 text-[13px] text-ink outline-none focus:border-[color:var(--app-accent)]" />
          </Field>
          <Field label="Translate into"><LanguageSelect value={lang} onChange={setLang} /></Field>
          {error ? <p className="mb-3 text-[12.5px] text-[color:var(--app-danger)]">{error}</p> : null}
          <PrimaryButton type="submit" disabled={!url.trim() || !lang || busy}>{busy ? "Starting…" : "Translate page"}</PrimaryButton>
          <p className="mt-3 text-[11.5px] text-muted">Only public pages on standard ports. Pages that need a login or JavaScript to show their text can&apos;t be translated.</p>
        </form>
      }
      result={
        !job ? (
          <Empty>The translated page appears here.</Empty>
        ) : (
          <div className="flex h-full flex-col gap-3">
            <JobProgress job={job} />
            {job.status === "complete" ? (
              <>
                <div className="flex gap-2">
                  <Pill active={view === "result"} onClick={() => setView("result")}>Translated</Pill>
                  <Pill active={view === "source"} onClick={() => setView("source")}>Original</Pill>
                </div>
                {html !== null ? (
                  // No allow-scripts, no allow-same-origin: the copy can't run code or reach the app.
                  <iframe title="Translated page" sandbox="" srcDoc={html}
                    className="min-h-[520px] w-full flex-1 rounded-xl border border-[color:var(--app-border)] bg-[var(--app-surface)]" />
                ) : <p className="text-[12.5px] text-muted">Loading the page…</p>}
              </>
            ) : null}
          </div>
        )
      }
    />
  );
}
