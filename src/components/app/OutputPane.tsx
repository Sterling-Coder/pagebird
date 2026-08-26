import type { TranslateResult } from "@/lib/translate";

type Status = "idle" | "translating" | "error" | "done";

export function OutputPane({
  status,
  result,
  error,
  hasFile,
}: {
  status: Status;
  result: TranslateResult | null;
  error: string | null;
  hasFile: boolean;
}) {
  return (
    <div className="flex min-w-[320px] flex-1 flex-col p-6">
      <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
        Output
      </p>

      <div className="mt-4 flex flex-1 flex-col items-center justify-center border border-rule bg-paper-dim p-8 text-center">
        {status === "idle" ? (
          <p className="font-mono text-[12px] uppercase tracking-widest text-muted">
            {hasFile
              ? "Ready — press translate"
              : "Upload a document to see the translation here"}
          </p>
        ) : null}

        {status === "translating" ? (
          <p className="font-mono text-[12px] uppercase tracking-widest text-muted">
            Sending to backend…
          </p>
        ) : null}

        {status === "error" ? (
          <div className="max-w-sm">
            <p className="font-mono text-[11px] uppercase tracking-widest text-red">
              Backend not connected
            </p>
            <p className="mt-2 text-xs leading-relaxed text-ink-soft">
              {error}
            </p>
            <p className="mt-4 font-mono text-[10px] uppercase tracking-widest text-muted">
              Wire translateDocument() in src/lib/translate.ts
            </p>
          </div>
        ) : null}

        {status === "done" && result ? (
          <div>
            <p className="font-mono text-[12px] text-ink">
              {result.translatedFileName}
            </p>
            <p className="mt-1 text-xs text-muted">{result.pages} pages</p>
            <a
              href={result.downloadUrl}
              className="mt-4 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
            >
              Download →
            </a>
          </div>
        ) : null}
      </div>
    </div>
  );
}
