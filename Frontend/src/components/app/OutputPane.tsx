import type { Segment, TranslateResult } from "@/lib/translate";
import { SyncedDocumentPair } from "./PdfPreview";
import { downloadAuthed } from "@/lib/supabase/authFetch";

type Status = "idle" | "translating" | "error" | "done";

export function OutputPane({
  status,
  result,
  error,
  file,
  segments,
}: {
  status: Status;
  result: TranslateResult | null;
  error: string | null;
  file: File | null;
  segments: Segment[];
}) {
  return (
    <div className="flex min-w-[320px] flex-1 flex-col p-6">
      <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
        Output
      </p>

      <div
        className={`mt-4 flex min-h-0 flex-1 flex-col border border-rule bg-paper-dim ${
          status === "done" && result?.previewUrl
            ? ""
            : "items-center justify-center p-8 text-center"
        }`}
      >
        {status === "idle" ? (
          <p className="font-mono text-[12px] uppercase tracking-widest text-muted">
            {file
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
              Translation failed
            </p>
            <p className="mt-2 text-xs leading-relaxed text-ink-soft">
              {error}
            </p>
          </div>
        ) : null}

        {status === "done" && result ? (
          result.previewUrl && file?.type === "application/pdf" ? (
            <SyncedDocumentPair
              source={{ kind: "file", file }}
              target={{ kind: "url", url: result.previewUrl }}
              segments={segments}
              downloadUrl={result.downloadUrl}
              fileName={result.translatedFileName}
            />
          ) : (
            <div>
              <p className="font-mono text-[12px] text-ink">
                {result.translatedFileName}
              </p>
              {result.pages !== null ? (
                <p className="mt-1 text-xs text-muted">{result.pages} pages</p>
              ) : null}
              <p className="mt-2 max-w-sm text-xs leading-relaxed text-ink-soft">
                No inline preview for this file type.
              </p>
              <button
                type="button"
                onClick={() => downloadAuthed(result.downloadUrl, result.translatedFileName)}
                className="mt-4 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
              >
                Download →
              </button>
            </div>
          )
        ) : null}
      </div>
    </div>
  );
}
