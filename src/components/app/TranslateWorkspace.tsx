"use client";

import { useEffect, useState } from "react";
import { UploadPane } from "./UploadPane";
import { OutputPane } from "./OutputPane";
import { SyncedDocumentPair } from "./PdfPreview";
import {
  getSegments,
  listLanguages,
  translateDocument,
  type Language,
  type Segment,
  type TranslateResult,
} from "@/lib/translate";

type Status = "idle" | "translating" | "error" | "done";

export function TranslateWorkspace() {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("es");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<TranslateResult | null>(null);
  const [segments, setSegments] = useState<Segment[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [languages, setLanguages] = useState<Language[]>([]);

  useEffect(() => {
    listLanguages()
      .then((res) => setLanguages(res.languages))
      .catch(() => setLanguages([]));
  }, []);

  function handleFileChange(next: File | null) {
    setFile(next);
    setStatus("idle");
    setResult(null);
    setSegments([]);
    setError(null);
  }

  async function handleTranslate() {
    if (!file) return;
    setStatus("translating");
    setError(null);
    try {
      const res = await translateDocument({ file, targetLanguage: language });
      setResult(res);
      if (res.previewUrl) {
        const jobSegments = await getSegments(res.jobId).catch(() => []);
        setSegments(jobSegments);
      }
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
  }

  if (
    (status === "done" || status === "translating") &&
    result?.previewUrl &&
    file?.type === "application/pdf"
  ) {
    return (
      <div className="flex min-h-0 min-w-0 flex-1 border-t border-rule bg-paper-dim">
        <SyncedDocumentPair
          source={{ kind: "file", file }}
          target={{ kind: "url", url: result.previewUrl }}
          segments={segments}
          downloadUrl={result.downloadUrl}
          fileName={result.translatedFileName}
          language={language}
          languages={languages}
          onLanguageChange={setLanguage}
          onTranslate={handleTranslate}
          translating={status === "translating"}
          jobId={result.jobId}
        />
      </div>
    );
  }

  return (
    <div className="flex min-w-0 flex-1 divide-x divide-rule overflow-auto">
      <UploadPane
        file={file}
        onFileChange={handleFileChange}
        language={language}
        onLanguageChange={setLanguage}
        onTranslate={handleTranslate}
        status={status === "translating" ? "translating" : "idle"}
      />
      <OutputPane
        status={status}
        result={result}
        error={error}
        file={file}
        segments={segments}
      />
    </div>
  );
}
