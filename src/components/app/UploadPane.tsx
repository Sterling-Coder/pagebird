"use client";

import { useEffect, useRef, useState } from "react";
import { listLanguages, type Language } from "@/lib/translate";
import { PdfPreview } from "./PdfPreview";

function formatBytes(bytes: number) {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export function UploadPane({
  file,
  onFileChange,
  language,
  onLanguageChange,
  onTranslate,
  status,
}: {
  file: File | null;
  onFileChange: (file: File | null) => void;
  language: string;
  onLanguageChange: (lang: string) => void;
  onTranslate: () => void;
  status: "idle" | "translating" | "error";
}) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragOver, setDragOver] = useState(false);
  const [languages, setLanguages] = useState<Language[]>([]);

  useEffect(() => {
    listLanguages()
      .then((res) => setLanguages(res.languages))
      .catch(() => setLanguages([]));
  }, []);

  function handleFiles(files: FileList | null) {
    if (files && files[0]) onFileChange(files[0]);
  }

  return (
    <div className="flex min-w-[320px] flex-1 flex-col border-r border-rule p-6">
      <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
        Source document
      </p>
      <label className="mt-4 block">
        <span className="mb-2 block font-mono text-[10px] uppercase tracking-widest text-muted">
          Translate to
        </span>
        <select
          value={language}
          onChange={(event) => onLanguageChange(event.target.value)}
          className="w-full border border-rule bg-paper px-3 py-2 font-mono text-[11px] uppercase tracking-widest text-ink"
        >
          {languages.map((lang) => (
            <option key={lang.code} value={lang.code}>
              {lang.name}
            </option>
          ))}
        </select>
      </label>

      <input
        ref={inputRef}
        type="file"
        accept=".pdf,.indd,.idml"
        className="hidden"
        onChange={(e) => handleFiles(e.target.files)}
      />

      {file ? (
        <div className="mt-4 flex min-h-0 flex-1 flex-col border border-rule">
          <div className="flex items-center justify-between border-b border-rule px-3 py-2">
            <div>
              <p className="font-mono text-[12px] text-ink">{file.name}</p>
              <p className="text-xs text-muted">{formatBytes(file.size)}</p>
            </div>
            <button
              type="button"
              onClick={() => onFileChange(null)}
              className="font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 hover:decoration-ink"
            >
              Remove
            </button>
          </div>
          {file.type === "application/pdf" ? (
            <PdfPreview source={{ kind: "file", file }} />
          ) : (
            <div className="flex flex-1 items-center justify-center p-8 text-center">
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
                No inline preview for this file type
              </p>
            </div>
          )}
        </div>
      ) : (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            handleFiles(e.dataTransfer.files);
          }}
          onClick={() => inputRef.current?.click()}
          className={`mt-4 flex flex-1 cursor-pointer flex-col items-center justify-center border-2 border-dashed p-8 text-center transition-colors ${
            dragOver ? "border-red bg-red-dim/40" : "border-rule hover:border-ink"
          }`}
        >
          <p className="font-mono text-[12px] uppercase tracking-widest text-ink-soft">
            Drop a file, or click to browse
          </p>
          <p className="mt-2 text-xs text-muted">PDF · INDD · IDML</p>
        </div>
      )}
      <button
        type="button"
        onClick={onTranslate}
        disabled={!file || status === "translating"}
        className="mt-6 w-full bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-40"
      >
        {status === "translating" ? "Translating…" : "Translate document"}
      </button>
    </div>
  );
}
