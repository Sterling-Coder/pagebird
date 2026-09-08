"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject, type Project } from "@/lib/projects";

export default function LinguisticAssetsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
  }, [params.projectId]);

  return (
    <div className="p-6 text-sm text-ink-soft">
      <h2 className="mb-1 text-lg font-bold text-ink">Linguistic assets</h2>
      <p className="mb-6 max-w-lg text-xs text-muted">
        Translation memory is created and reused automatically for every source
        → target language pair — there's nothing to configure yet.
      </p>

      <p className="mb-2 font-mono text-[11px] uppercase tracking-widest text-muted">
        Translation memory
      </p>

      {project?.target_lang ? (
        <table className="w-full max-w-2xl border-collapse text-sm">
          <thead>
            <tr className="border-b border-rule text-left font-mono text-[11px] uppercase tracking-widest text-muted">
              <th className="py-2">Name</th>
              <th className="py-2">Source language</th>
              <th className="py-2">Target language</th>
            </tr>
          </thead>
          <tbody>
            <tr className="border-b border-rule">
              <td className="py-2 text-ink">{project.name}</td>
              <td className="py-2">{project.source_lang ?? "—"}</td>
              <td className="py-2">{project.target_lang}</td>
            </tr>
          </tbody>
        </table>
      ) : (
        <p className="text-muted">
          No translation memory yet — upload and translate a file to create one.
        </p>
      )}
    </div>
  );
}
