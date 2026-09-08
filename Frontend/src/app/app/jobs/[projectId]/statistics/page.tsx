"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import { getProject, type Project } from "@/lib/projects";

export default function ProjectStatisticsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);

  useEffect(() => {
    getProject(params.projectId).then(setProject).catch(() => setProject(null));
  }, [params.projectId]);

  const counts = project?.status_counts ?? {};

  return (
    <div className="p-6 text-sm text-ink-soft">
      <p className="mb-3 font-mono text-[11px] uppercase tracking-widest text-muted">
        Segment status
      </p>
      {Object.keys(counts).length === 0 ? (
        <p className="text-muted">No segments yet.</p>
      ) : (
        <ul className="space-y-1">
          {Object.entries(counts).map(([status, count]) => (
            <li key={status}>
              {status}: {count}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
