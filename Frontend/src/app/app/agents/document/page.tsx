"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { AgentShell, Field, FilePicker } from "../AgentShell";
import { JobProgress, useJob, useJobParam } from "../JobStatus";
import { LanguageSelect, PrimaryButton, Empty } from "@/components/app/ui";
import { listFormats, startDocumentJob } from "@/lib/agents";
import { listProjects, type Project } from "@/lib/projects";
import { API_BASE_URL } from "@/lib/translate";
import { downloadAuthed } from "@/lib/supabase/authFetch";

export default function DocumentAgentPage() {
  const [file, setFile] = useState<File | null>(null);
  const [lang, setLang] = useState("");
  const [projectId, setProjectId] = useState("");
  const [projects, setProjects] = useState<Project[]>([]);
  const [accept, setAccept] = useState(".pdf,.idml,.docx,.pptx,.xlsx,.txt");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [jobId, setJobId] = useJobParam();
  const job = useJob(jobId);

  useEffect(() => {
    listProjects().then(setProjects).catch(() => setProjects([]));
    listFormats()
      .then((f) => setAccept(f.documents.map((d) => d.ext).join(",")))
      .catch(() => {});
  }, []);

  async function start(e: React.FormEvent) {
    e.preventDefault();
    if (!file || !lang) return;
    setBusy(true);
    setError(null);
    try {
      setJobId(await startDocumentJob(file, lang, projectId || undefined));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setBusy(false);
    }
  }

  const done = job?.status === "complete";
  const name = job?.original_filename ?? "translation";

  return (
    <AgentShell
      name="Document & Office Agent"
      desc="InDesign, PDF, Word, PowerPoint, Excel and text — the same file type comes back."
      form={
        <form onSubmit={start}>
          <Field label="File">
            <FilePicker accept={accept} file={file} onFile={setFile} hint={accept.replaceAll(",", " ")} />
          </Field>
          <Field label="Translate into"><LanguageSelect value={lang} onChange={setLang} /></Field>
          <Field label="Project (optional)">
            <select value={projectId} onChange={(e) => setProjectId(e.target.value)}
              className="w-full rounded-xl border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-2 text-[13px] text-ink">
              <option value="">No project</option>
              {projects.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
          {error ? <p className="mb-3 text-[12.5px] text-[color:var(--app-danger)]">{error}</p> : null}
          <PrimaryButton type="submit" disabled={!file || !lang || busy}>{busy ? "Uploading…" : "Translate"}</PrimaryButton>
          <p className="mt-3 text-[11.5px] text-muted">.indd isn&apos;t supported — export IDML from InDesign. Old .doc/.ppt/.xls need re-saving.</p>
        </form>
      }
      result={
        !job ? (
          <Empty>Your translated file appears here. It keeps running if you leave the page — find it under Jobs.</Empty>
        ) : (
          <div className="space-y-4">
            <JobProgress job={job} />
            {done ? (
              <div className="flex flex-wrap gap-2">
                <button type="button" onClick={() => downloadAuthed(`${API_BASE_URL}/api/jobs/${job.id}/download`, name)}
                  className="rounded-full bg-[var(--app-accent)] px-4 py-2 text-[12.5px] font-semibold text-white">Download translation</button>
                {job.project_id ? (
                  <Link href={`/app/jobs/${job.project_id}/files/${job.id}`}
                    className="rounded-full border border-[color:var(--app-border-strong)] px-4 py-2 text-[12.5px] text-ink">Review segments</Link>
                ) : null}
                <button type="button" onClick={() => { setJobId(null); setFile(null); }}
                  className="rounded-full border border-[color:var(--app-border-strong)] px-4 py-2 text-[12.5px] text-ink">Translate another</button>
              </div>
            ) : null}
          </div>
        )
      }
    />
  );
}
