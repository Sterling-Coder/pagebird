"use client";

import { useState } from "react";
import { JOB_TYPES } from "@/lib/jobTypes";
import { createProject, type Project } from "@/lib/projects";

export function CreateJobModal({
  open,
  onClose,
  onCreated,
}: {
  open: boolean;
  onClose: () => void;
  onCreated: (project: Project) => void;
}) {
  const [name, setName] = useState("");
  const [jobType, setJobType] = useState(JOB_TYPES[0].id);
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  if (!open) return null;

  async function handleCreate() {
    if (!name.trim()) return;
    setCreating(true);
    setError(null);
    try {
      const project = await createProject({
        name: name.trim(),
        jobType,
        sourceLanguage: "English",
      });
      onCreated(project);
      setName("");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to create job");
    } finally {
      setCreating(false);
    }
  }

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-ink/40">
      <div className="w-full max-w-md border border-ink bg-paper p-6">
        <p className="font-mono text-[11px] uppercase tracking-widest text-ink-soft">
          New job
        </p>

        <label className="mt-4 block">
          <span className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-muted">
            Name
          </span>
          <input
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full border border-rule bg-paper px-3 py-2 text-sm text-ink"
            placeholder="Project name"
          />
        </label>

        <div className="mt-4 grid gap-2">
          {JOB_TYPES.map((type) => (
            <button
              key={type.id}
              type="button"
              disabled={!type.enabled}
              onClick={() => setJobType(type.id)}
              className={`flex items-center justify-between border px-3 py-2 text-left transition-colors ${
                jobType === type.id ? "border-red" : "border-rule"
              } ${type.enabled ? "hover:border-ink" : "cursor-not-allowed opacity-40"}`}
            >
              <span>
                <span className="block text-sm text-ink">{type.label}</span>
                <span className="block text-xs text-muted">{type.description}</span>
              </span>
              {!type.enabled ? (
                <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
                  Coming soon
                </span>
              ) : null}
            </button>
          ))}
        </div>

        {error ? <p className="mt-3 text-sm text-red">{error}</p> : null}

        <div className="mt-6 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            className="border border-rule px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-ink-soft hover:text-ink"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleCreate}
            disabled={!name.trim() || creating}
            className="bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper disabled:opacity-40"
          >
            {creating ? "Creating…" : "Create project"}
          </button>
        </div>
      </div>
    </div>
  );
}
