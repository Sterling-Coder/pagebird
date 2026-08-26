"use client";

import { useState } from "react";
import { UploadPane } from "./UploadPane";
import { OutputPane } from "./OutputPane";
import { translateDocument, type TranslateResult } from "@/lib/translate";

type Status = "idle" | "translating" | "error" | "done";

export function TranslateWorkspace() {
  const [file, setFile] = useState<File | null>(null);
  const [language, setLanguage] = useState("French");
  const [status, setStatus] = useState<Status>("idle");
  const [result, setResult] = useState<TranslateResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  function handleFileChange(next: File | null) {
    setFile(next);
    setStatus("idle");
    setResult(null);
    setError(null);
  }

  async function handleTranslate() {
    if (!file) return;
    setStatus("translating");
    setError(null);
    try {
      const res = await translateDocument({ file, targetLanguage: language });
      setResult(res);
      setStatus("done");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unknown error");
      setStatus("error");
    }
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
      <OutputPane status={status} result={result} error={error} hasFile={!!file} />
    </div>
  );
}
