"use client";

import { useRef, useState } from "react";

const LANGUAGES = ["French", "German", "Japanese", "Arabic", "Portuguese", "Hindi"];

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

  function handleFiles(files: FileList | null) {
    if (files && files[0]) onFileChange(files[0]);
  }

  return (
    <div className="flex min-w-[320px] flex-1 flex-col border-r border-rule p-6">
      <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
        Source document
      </p>

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
        <input
          ref={inputRef}
          type="file"
          accept=".pdf,.doc,.docx,.indd,.idml"
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />

        {file ? (
          <>
            <p className="font-mono text-[12px] text-ink">{file.name}</p>
            <p className="mt-1 text-xs text-muted">{formatBytes(file.size)}</p>
            <button
              type="button"
              onClick={(e) => {
                e.stopPropagation();
                onFileChange(null);
              }}
              className="mt-4 font-mono text-[11px] uppercase tracking-widest text-ink-soft underline decoration-rule underline-offset-4 hover:decoration-ink"
            >
              Remove
            </button>
          </>
        ) : (
          <>
            <p className="font-mono text-[12px] uppercase tracking-widest text-ink-soft">
              Drop a file, or click to browse
            </p>
            <p className="mt-2 text-xs text-muted">DOC · PDF · INDD · IDML</p>
          </>
        )}
      </div>

      <div className="mt-6">
        <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-muted">
          Translate to
        </p>
        <div className="flex flex-wrap gap-2">
          {LANGUAGES.map((lang) => (
            <button
              key={lang}
              type="button"
              onClick={() => onLanguageChange(lang)}
              className={`border px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest transition-colors ${
                language === lang
                  ? "border-ink bg-ink text-paper"
                  : "border-rule text-ink-soft hover:border-ink hover:text-ink"
              }`}
            >
              {lang}
            </button>
          ))}
        </div>
      </div>

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
