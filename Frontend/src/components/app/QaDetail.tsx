import type { EvalReport } from "@/lib/translate";

const GATE_LABELS: Record<string, string> = {
  placeholder_integrity: "Math placeholders intact",
  coverage: "Segments translated",
  number_preservation: "Numbers preserved",
  source_leakage: "No untranslated source text",
  script_conformance: "Target script used",
  tofu: "All characters renderable",
  overflow: "Text fits its box",
  idml_overset: "No overset frames (InDesign)",
  idml_run_preservation: "IDML runs preserved",
  idml_math_runs: "IDML math runs untouched",
  idml_assets: "IDML assets untouched",
};

function fmtValue(check: { status: string; value: number | string | null }): string {
  if (check.status === "skip" || check.value === null) return "—";
  if (typeof check.value === "number") {
    const shown = check.value <= 1 ? check.value * 100 : check.value;
    return `${shown.toFixed(1)}%`;
  }
  return String(check.value);
}

/** One file's full QA detail — gates with their reasons, the layout/content
 * scores that make up the overall figure, and the plain-language glossary the
 * downloadable report also shows, so a reviewer never has to download a PDF
 * just to see WHY a check failed. Shared by the Settings page's expandable
 * row and the Files list's QA popover so the two never describe a result
 * differently. */
export function QaDetail({ report }: { report: EvalReport }) {
  if (report.not_applicable) {
    return (
      <div className="px-4 py-3 text-xs text-muted">
        QA not applicable — {report.reason ?? "nothing to score for this job"}
      </div>
    );
  }

  const gates = report.gates?.checks ?? [];
  const halves = report.overall?.halves ?? {};
  const segments = report.integrity?.segments;
  const layout = report.layout_score;

  return (
    <div className="px-4 py-4 text-xs">
      <p className="mb-3 font-mono text-[10px] uppercase tracking-widest text-muted">
        {report.format ?? "document"}
        {typeof segments === "number" ? ` · ${segments} segment${segments !== 1 ? "s" : ""}` : ""}
        {report.target_lang ? ` · target ${report.target_lang}` : ""}
      </p>

      {Object.keys(halves).length > 0 ? (
        <p className="mb-3 text-ink-soft">
          Overall accuracy is{" "}
          {Object.entries(halves)
            .map(([name, half]) => `${name} ${Math.round(half.value * 100)}% (weighted ${Math.round(half.weight * 100)}%)`)
            .join(" + ")}
          .
        </p>
      ) : null}

      {gates.length > 0 ? (
        <table className="mb-4 w-full border-collapse">
          <thead>
            <tr className="border-b border-rule text-left font-mono text-[10px] uppercase tracking-widest text-muted">
              <th className="py-1.5 pr-3">Gate</th>
              <th className="py-1.5 pr-3">Status</th>
              <th className="py-1.5 pr-3">Value</th>
              <th className="py-1.5">Why it matters</th>
            </tr>
          </thead>
          <tbody>
            {gates.map((check) => (
              <tr key={check.gate} className="border-b border-rule align-top">
                <td className="py-1.5 pr-3 text-ink">{GATE_LABELS[check.gate] ?? check.gate}</td>
                <td
                  className={`py-1.5 pr-3 font-mono text-[10px] uppercase tracking-widest ${
                    check.status === "fail" ? "text-red" : check.status === "pass" ? "text-ink" : "text-muted"
                  }`}
                >
                  {check.status === "skip" ? "N/A" : check.status}
                </td>
                <td className="py-1.5 pr-3 text-ink-soft">{fmtValue(check)}</td>
                <td className="py-1.5 text-ink-soft">
                  {check.status === "skip" ? check.reason ?? check.why : check.why}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}

      {layout && layout.score !== null ? (
        <p className="mb-3 text-ink-soft">
          Layout composite <b className="text-ink">{Math.round(layout.score * 100)}%</b>
          {layout.formula ? <span className="text-muted"> ({layout.formula})</span> : null}
          {layout.missing?.length ? (
            <span className="text-muted"> — not measured: {layout.missing.join(", ")}</span>
          ) : null}
        </p>
      ) : layout?.reason ? (
        <p className="mb-3 text-muted">{layout.reason}</p>
      ) : null}

      {report.explanations && report.explanations.length > 0 ? (
        <details className="mt-2">
          <summary className="cursor-pointer font-mono text-[10px] uppercase tracking-widest text-muted hover:text-ink">
            What each check means
          </summary>
          <dl className="mt-2 space-y-2 border-t border-rule pt-2">
            {report.explanations.map((entry) => (
              <div key={entry.term} className="border-b border-rule pb-2">
                <dt className="font-medium text-ink">{entry.term}</dt>
                <dd className="mt-0.5 text-ink-soft">{entry.text}</dd>
                {entry.formula ? (
                  <dd className="mt-0.5 font-mono text-[10px] text-muted">{entry.formula}</dd>
                ) : null}
              </div>
            ))}
          </dl>
        </details>
      ) : null}
    </div>
  );
}
