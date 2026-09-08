"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { AppNavRail } from "@/components/app/AppNavRail";
import { AppTopBar } from "@/components/app/AppTopBar";
import { CreateJobModal } from "@/components/app/CreateJobModal";
import { ConfirmDialog } from "@/components/app/ConfirmDialog";
import { listProjects, deleteProject, type Project } from "@/lib/projects";

export default function AppWorkspacePage() {
  const [navOpen, setNavOpen] = useState(true);
  const [projects, setProjects] = useState<Project[]>([]);
  const [modalOpen, setModalOpen] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const [confirmOpen, setConfirmOpen] = useState(false);
  const router = useRouter();

  function refresh() {
    return listProjects()
      .then(setProjects)
      .catch(() => setProjects([]));
  }

  useEffect(() => {
    refresh();
  }, []);

  function toggleSelected(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  }

  function toggleSelectAll() {
    setSelected((prev) =>
      prev.size === projects.length ? new Set() : new Set(projects.map((p) => p.id))
    );
  }

  async function handleConfirmDelete() {
    setDeleting(true);
    try {
      await Promise.all([...selected].map((id) => deleteProject(id)));
      setSelected(new Set());
      setConfirmOpen(false);
      await refresh();
    } finally {
      setDeleting(false);
    }
  }

  const selectedNames = projects.filter((p) => selected.has(p.id)).map((p) => p.name);

  return (
    <div className="flex h-screen bg-paper">
      {navOpen ? <AppNavRail /> : null}
      <div className="flex min-w-0 flex-1 flex-col">
        <AppTopBar navOpen={navOpen} onToggleNav={() => setNavOpen((v) => !v)} />
        <div className="flex min-h-0 flex-1">
          <div className="flex min-w-0 flex-1 flex-col overflow-auto p-6">
            <div className="mb-4 flex items-center justify-between">
              <h1 className="text-lg font-bold text-ink">Jobs</h1>
              <div className="flex items-center gap-3">
                {selected.size > 0 ? (
                  <button
                    type="button"
                    onClick={() => setConfirmOpen(true)}
                    disabled={deleting}
                    aria-label="Delete selected projects"
                    className="border border-rule p-2 text-ink-soft transition-colors hover:border-red hover:text-red disabled:opacity-40"
                  >
                    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.75" className="h-4 w-4">
                      <path d="M3 6h18" />
                      <path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2" />
                      <path d="M19 6l-1 14a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2L5 6" />
                    </svg>
                  </button>
                ) : null}
                <button
                  type="button"
                  onClick={() => setModalOpen(true)}
                  className="flex items-center gap-2 bg-red px-4 py-2 font-mono text-[11px] uppercase tracking-widest text-paper hover:opacity-90"
                >
                  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-3.5 w-3.5">
                    <path d="M12 5v14M5 12h14" />
                  </svg>
                  Create project
                </button>
              </div>
            </div>

            <table className="w-full border-collapse text-sm">
              <thead>
                <tr className="border-b border-rule text-left font-mono text-[11px] uppercase tracking-widest text-muted">
                  <th className="w-8 py-2">
                    <input
                      type="checkbox"
                      checked={projects.length > 0 && selected.size === projects.length}
                      onChange={toggleSelectAll}
                      aria-label="Select all projects"
                    />
                  </th>
                  <th className="py-2">Name</th>
                  <th className="py-2">Progress</th>
                  <th className="py-2">Status</th>
                  <th className="py-2">Source</th>
                  <th className="py-2">Client</th>
                  <th className="py-2">Vendor</th>
                  <th className="py-2">Deadline</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((p) => (
                  <tr
                    key={p.id}
                    onClick={() => router.push(`/app/jobs/${p.id}/files`)}
                    className="cursor-pointer border-b border-rule hover:bg-paper-dim"
                  >
                    <td className="py-2" onClick={(e) => e.stopPropagation()}>
                      <input
                        type="checkbox"
                        checked={selected.has(p.id)}
                        onChange={() => toggleSelected(p.id)}
                        aria-label={`Select ${p.name}`}
                      />
                    </td>
                    <td className="py-2 text-ink">
                      <span className="flex items-center gap-2">
                        <svg
                          viewBox="0 0 24 24"
                          fill="none"
                          stroke="currentColor"
                          strokeWidth="1.75"
                          className="h-4 w-4 shrink-0 text-red"
                        >
                          <path d="M3 7a2 2 0 0 1 2-2h4l2 2h8a2 2 0 0 1 2 2v8a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z" />
                        </svg>
                        {p.name}
                      </span>
                    </td>
                    <td className="py-2">
                      <div className="h-4 w-24 border border-rule" />
                    </td>
                    <td className="py-2 text-red">{p.status}</td>
                    <td className="py-2 text-ink-soft">
                      {p.source_lang ?? "—"} → {p.target_lang ?? "—"}
                    </td>
                    <td className="py-2 text-ink-soft">{p.client ?? "—"}</td>
                    <td className="py-2 text-ink-soft">{p.vendor ?? "—"}</td>
                    <td className="py-2 text-ink-soft">
                      {p.deadline ? new Date(p.deadline * 1000).toLocaleDateString() : "—"}
                    </td>
                  </tr>
                ))}
                {projects.length === 0 ? (
                  <tr>
                    <td colSpan={8} className="py-8 text-center text-muted">
                      No jobs yet. Create one to get started.
                    </td>
                  </tr>
                ) : null}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <CreateJobModal
        open={modalOpen}
        onClose={() => setModalOpen(false)}
        onCreated={(project) => {
          setModalOpen(false);
          router.push(`/app/jobs/${project.id}/files`);
        }}
      />

      <ConfirmDialog
        open={confirmOpen}
        title="Delete project"
        message={`Delete ${selectedNames.length} project${selectedNames.length > 1 ? "s" : ""} (${selectedNames.join(", ")})? This also deletes their files. This cannot be undone.`}
        confirmLabel="Delete"
        destructive
        busy={deleting}
        onConfirm={handleConfirmDelete}
        onCancel={() => setConfirmOpen(false)}
      />
    </div>
  );
}
