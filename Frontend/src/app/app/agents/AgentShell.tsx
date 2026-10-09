"use client";

import type { ReactNode } from "react";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, PageHeader } from "@/components/app/ui";

/** Frame shared by every agent workspace: header, then the form
 * on the left and the result on the right. */
export function AgentShell({ name, desc, form, result }: {
  name: string; desc: string; form: ReactNode; result: ReactNode;
}) {
  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.agents} title={name} desc={desc} />
      <div className="grid min-h-0 flex-1 grid-cols-1 gap-4 overflow-auto px-6 pb-8 lg:grid-cols-[360px_minmax(0,1fr)]">
        <div className="h-fit rounded-2xl border border-[color:var(--app-border)] bg-[var(--app-surface-2)] p-5">{form}</div>
        <div className="min-h-[320px] rounded-2xl border border-[color:var(--app-border)] bg-[var(--app-surface)] p-5">{result}</div>
      </div>
    </div>
  );
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="mb-4 block">
      <span className="mb-1.5 block text-[12px] text-muted">{label}</span>
      {children}
    </label>
  );
}

export function FilePicker({ accept, file, onFile, hint }: {
  accept: string; file: File | null; onFile: (f: File | null) => void; hint: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-[color:var(--app-border-hover)] bg-[var(--app-surface)] px-4 py-5 text-center">
      <input type="file" accept={accept} onChange={(e) => onFile(e.target.files?.[0] ?? null)}
        className="block w-full text-[12.5px] text-ink-soft file:mr-3 file:rounded-full file:border-0 file:bg-[var(--app-surface-3)] file:px-3 file:py-1.5 file:text-[12px] file:text-ink" />
      <p className="mt-2 text-[11.5px] text-muted">{file ? `${file.name} · ${(file.size / 1024 / 1024).toFixed(1)} MB` : hint}</p>
    </div>
  );
}
