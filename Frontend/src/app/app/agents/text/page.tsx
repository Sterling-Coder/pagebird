"use client";

import { useState } from "react";
import { AgentShell, Field } from "../AgentShell";
import { LanguageSelect, PrimaryButton, Empty } from "@/components/app/ui";
import { translateText } from "@/lib/agents";

export default function TextAgentPage() {
  const [text, setText] = useState("");
  const [lang, setLang] = useState("");
  const [out, setOut] = useState<{ text: string; dir: string } | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function go(e: React.FormEvent) {
    e.preventDefault();
    if (!text.trim() || !lang) return;
    setBusy(true);
    setError(null);
    try {
      // One request per paragraph, so long text keeps its breaks.
      const paras = text.split(/\n{2,}/);
      const r = await translateText(paras, lang);
      setOut({ text: r.translations.join("\n\n"), dir: r.direction });
    } catch (err) {
      setError(err instanceof Error ? err.message : "Translation failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <AgentShell
      name="Quick Translate"
      desc="The same engine the browser extension uses. Numbers, links and emails come back unchanged."
      form={
        <form onSubmit={go}>
          <Field label="Text">
            <textarea value={text} onChange={(e) => setText(e.target.value)} rows={10} maxLength={20000}
              placeholder="Paste a sentence or a few paragraphs…"
              className="w-full resize-y rounded-xl border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-2 text-[13px] text-ink outline-none focus:border-[color:var(--app-accent)]" />
          </Field>
          <Field label="Translate into"><LanguageSelect value={lang} onChange={setLang} /></Field>
          {error ? <p className="mb-3 text-[12.5px] text-[color:var(--app-danger)]">{error}</p> : null}
          <PrimaryButton type="submit" disabled={!text.trim() || !lang || busy}>{busy ? "Translating…" : "Translate"}</PrimaryButton>
        </form>
      }
      result={
        out ? (
          <div>
            <p dir={out.dir === "rtl" ? "rtl" : "ltr"} className="whitespace-pre-wrap text-[14px] leading-relaxed text-ink">{out.text}</p>
            <button type="button" onClick={() => navigator.clipboard.writeText(out.text)}
              className="mt-4 rounded-full border border-[color:var(--app-border-strong)] px-4 py-1.5 text-[12.5px] text-ink">Copy</button>
          </div>
        ) : <Empty>The translation appears here.</Empty>
      }
    />
  );
}
