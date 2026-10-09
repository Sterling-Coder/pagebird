"use client";

import { useEffect, useRef, useState } from "react";
import { useRouter } from "next/navigation";
import { JOB_TYPES, type JobTypeId } from "@/lib/jobTypes";
import { createProject, type Project } from "@/lib/projects";
import { T, TargetLanguageSelect, Notice } from "./UploadPane";

/** A name for a project the person didn't name: "Untitled · 9 Oct". */
export function defaultProjectName(): string {
  return `Untitled · ${new Date().toLocaleDateString(undefined, { day: "numeric", month: "short" })}`;
}

export function CreateJobModal({
  open,
  onClose,
  onCreated,
  openOnCreate = true,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (project: Project) => void;
  /** Go straight to the new project's Files tab with the upload area open. */
  openOnCreate?: boolean;
}) {
  const router = useRouter();
  const [name, setName] = useState("");
  const [jobType, setJobType] = useState<JobTypeId>("document");
  const [lang, setLang] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);
  // Set synchronously so a double-click can't create two identical projects
  // before React re-renders the disabled button.
  const submittingRef = useRef(false);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape" && !submittingRef.current) onClose();
    };
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  async function handleCreate(e?: React.FormEvent) {
    e?.preventDefault();
    if (submittingRef.current) return;
    submittingRef.current = true;
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({
        name: name.trim() || defaultProjectName(),
        jobType,
        sourceLanguage: "en",
        targetLanguage: lang || undefined,
      });
      onCreated(project);
      setName("");
      if (openOnCreate) router.push(`/app/jobs/${project.id}/files?upload=1`);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Could not create the project.");
    } finally {
      submittingRef.current = false;
      setCreating(false);
    }
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/40 p-4"
      onMouseDown={(e) => {
        if (e.target === e.currentTarget && !submittingRef.current) onClose();
      }}
    >
      <form
        onSubmit={handleCreate}
        role="dialog"
        aria-modal="true"
        aria-labelledby="new-project-title"
        className={`max-h-[90vh] w-full max-w-lg overflow-auto ${T.card} p-6 shadow-xl`}
      >
        <h2 id="new-project-title" className="text-[16px] font-semibold text-ink">New project</h2>
        <p className="mt-1 text-[12.5px] text-muted">
          A project holds the files you translate into one language. You can add files right after.
        </p>

        <label className="mt-5 block">
          <span className="mb-1.5 block text-[12px] text-muted">Name</span>
          <input
            autoFocus
            value={name}
            onChange={(e) => setName(e.target.value)}
            className={T.input}
            placeholder={`e.g. Spring catalogue (blank: “${defaultProjectName()}”)`}
          />
        </label>

        <fieldset className="mt-5">
          <legend className="mb-1.5 block text-[12px] text-muted">What are you translating?</legend>
          <div className="grid gap-2">
            {JOB_TYPES.map((type) => {
              const selected = jobType === type.id;
              return (
                <button
                  key={type.id}
                  type="button"
                  disabled={!type.enabled}
                  aria-pressed={selected}
                  onClick={() => setJobType(type.id)}
                  className={`flex items-start gap-3 rounded-xl border px-3.5 py-3 text-left transition-colors ${
                    selected ? `${T.accentBorder} ${T.surface2}` : T.border
                  } ${type.enabled ? "hover:border-[var(--app-accent,#c86018)]" : "cursor-not-allowed opacity-50"}`}
                >
                  <span className="mt-1 h-2.5 w-2.5 shrink-0 rounded-full" style={{ background: type.color }} />
                  <span className="min-w-0 flex-1">
                    <span className="flex items-center gap-2">
                      <span className="text-[13.5px] font-medium text-ink">{type.label}</span>
                      {!type.enabled ? (
                        <span className={`rounded-full ${T.surface2} px-2 py-0.5 text-[10.5px] text-muted`}>Coming soon</span>
                      ) : null}
                    </span>
                    <span className="mt-0.5 block text-[12px] text-ink-soft">{type.description}</span>
                    <span className="mt-1 block text-[11.5px] text-muted">{type.formats}</span>
                  </span>
                </button>
              );
            })}
          </div>
        </fieldset>

        <label className="mt-5 block">
          <span className="mb-1.5 block text-[12px] text-muted">Translate from English into</span>
          <TargetLanguageSelect value={lang} onChange={setLang} />
          <span className="mt-1 block text-[11.5px] text-muted">You can still pick another language for each upload.</span>
        </label>

        {error ? <div className="mt-4"><Notice kind="error">{error}</Notice></div> : null}

        <div className="mt-6 flex justify-end gap-2">
          <button type="button" onClick={onClose} className={T.secondaryBtn}>
            Cancel
          </button>
          <button type="submit" disabled={creating} className={T.primaryBtn}>
            {creating ? "Creating…" : openOnCreate ? "Create and add files" : "Create project"}
          </button>
        </div>
      </form>
    </div>
  );
}
