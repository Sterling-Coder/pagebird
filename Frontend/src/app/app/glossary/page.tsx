"use client";

import { useEffect, useState } from "react";
import { AppTopBar } from "@/components/app/AppTopBar";
import { ICON, PageHeader, Pill, Empty } from "@/components/app/ui";
import { listGlossaries, type Glossary } from "@/lib/agents";

export default function GlossaryPage() {
  const [items, setItems] = useState<Glossary[] | null>(null);
  const [code, setCode] = useState<string | null>(null);
  const [q, setQ] = useState("");

  useEffect(() => {
    listGlossaries()
      .then((g) => { setItems(g); setCode(g[0]?.code ?? null); })
      .catch(() => setItems([]));
  }, []);

  const current = items?.find((g) => g.code === code);
  const rows = (current?.terms ?? []).filter(
    (t) => !q || t.source.toLowerCase().includes(q.toLowerCase()) || t.target.toLowerCase().includes(q.toLowerCase()),
  );

  return (
    <div className="flex h-full w-full flex-col bg-[var(--app-surface)]">
      <AppTopBar />
      <PageHeader icon={ICON.glossary} title="Glossary" count={current?.terms.length}
        desc="Terms every translation is held to. Where the source term appears, this target wording is used." />
      <div className="flex flex-wrap items-center gap-2 px-6 pb-4">
        {(items ?? []).map((g) => <Pill key={g.code} active={g.code === code} onClick={() => setCode(g.code)}>{g.name}</Pill>)}
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search terms"
          className="ml-auto w-56 rounded-full border border-[color:var(--app-border-strong)] bg-[var(--app-surface)] px-3 py-1.5 text-[12.5px] text-ink outline-none focus:border-[color:var(--app-accent)]" />
      </div>
      <div className="min-h-0 flex-1 overflow-auto px-6 pb-8">
        {items === null ? <p className="text-[13px] text-muted">Loading…</p> : null}
        {items !== null && items.length === 0 ? (
          <Empty>No glossaries yet. Languages without one are still translated, just without a fixed term list.</Empty>
        ) : null}
        {current ? (
          <table className="w-full text-[13px]">
            <thead>
              <tr className="text-left text-[12px] text-muted">
                <th className="px-2 pb-2 font-normal">English</th>
                <th className="px-2 pb-2 font-normal">{current.name}</th>
                <th className="px-2 pb-2 text-right font-normal">State</th>
              </tr>
            </thead>
            <tbody>
              {rows.map((t) => (
                <tr key={t.source} className="border-t border-[color:var(--app-border)]">
                  <td className="px-2 py-2.5 text-ink">{t.source}</td>
                  <td className="px-2 py-2.5 text-ink">{t.target}</td>
                  <td className="px-2 py-2.5 text-right text-[12px] text-[color:var(--app-success)]">Locked</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : null}
        <p className="mt-6 text-[12px] text-muted">Glossaries are managed by Pagebirdy for now. Send us your term list and we&apos;ll add it.</p>
      </div>
    </div>
  );
}
