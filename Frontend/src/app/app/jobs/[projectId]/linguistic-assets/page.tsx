"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { getProject, type Project } from "@/lib/projects";
import { languageName } from "@/lib/languageNames";
import { T } from "@/components/app/UploadPane";

export default function LinguisticAssetsPage() {
  const params = useParams<{ projectId: string }>();
  const [project, setProject] = useState<Project | null>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    getProject(params.projectId)
      .then(setProject)
      .catch(() => setProject(null))
      .finally(() => setLoaded(true));
  }, [params.projectId]);

  const hasMemory = Boolean(project?.target_lang) && (project?.file_count ?? 0) > 0;

  return (
    <div className="overflow-auto px-6 py-5 text-[13px] text-ink-soft">
      <section className={`max-w-2xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Translation memory</h2>
        <p className="mt-0.5 text-[12px] text-muted">
          Built and reused automatically for each source → target language pair. There&apos;s nothing to set up: every file you
          translate makes the next one more consistent.
        </p>
        {!loaded ? (
          <p className="mt-4 text-muted">Loading…</p>
        ) : hasMemory && project ? (
          <table className="mt-4 w-full border-collapse">
            <thead>
              <tr className={`border-b ${T.border} text-left text-[11.5px] text-muted`}>
                <th className="py-2 font-medium">Name</th>
                <th className="py-2 font-medium">Source language</th>
                <th className="py-2 font-medium">Target language</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td className="py-2 text-ink">{project.name}</td>
                <td className="py-2">{languageName(project.source_lang) ?? "English"}</td>
                <td className="py-2">{languageName(project.target_lang)}</td>
              </tr>
            </tbody>
          </table>
        ) : (
          <p className={`mt-4 rounded-xl ${T.surface2} px-4 py-5 text-center text-muted`}>
            No translation memory yet —{" "}
            <Link href={`/app/jobs/${params.projectId}/files?upload=1`} className={`${T.accentText} hover:underline`}>
              upload and translate a file
            </Link>{" "}
            to start one.
          </p>
        )}
      </section>

      <section className={`mt-4 max-w-2xl ${T.card} p-5`}>
        <h2 className="text-[14px] font-semibold text-ink">Glossary</h2>
        <p className="mt-0.5 text-[12px] text-muted">
          Terms that must always be translated the same way — product names, legal phrases — live in your workspace glossary and
          apply to every project.
        </p>
        <Link href="/app/glossary" className={`mt-3 inline-flex ${T.secondaryBtn}`}>
          Open the glossary
        </Link>
      </section>
    </div>
  );
}
