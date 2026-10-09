"use client";

import Link from "next/link";
import { useId, useRef, useState, type KeyboardEvent } from "react";

export interface FAQItem {
  category: string;
  q: string;
  a: string;
}

const ALL = "All";

const HAIRLINE = "rgba(255,255,255,0.08)";

export default function PricingFAQ({
  items,
  categories,
}: {
  items: FAQItem[];
  categories: string[];
}) {
  const baseId = useId();
  const [filter, setFilter] = useState<string>(ALL);
  const [openKey, setOpenKey] = useState<string | null>(items[0]?.q ?? null);
  const triggers = useRef<Array<HTMLButtonElement | null>>([]);

  const visible = filter === ALL ? items : items.filter((i) => i.category === filter);
  const counts = new Map<string, number>();
  for (const i of items) counts.set(i.category, (counts.get(i.category) ?? 0) + 1);

  function choose(cat: string) {
    setFilter(cat);
    const next = cat === ALL ? items : items.filter((i) => i.category === cat);
    setOpenKey(next[0]?.q ?? null);
  }

  function onTriggerKey(e: KeyboardEvent<HTMLButtonElement>, idx: number) {
    const last = visible.length - 1;
    let target: number | null = null;
    if (e.key === "ArrowDown") target = idx === last ? 0 : idx + 1;
    else if (e.key === "ArrowUp") target = idx === 0 ? last : idx - 1;
    else if (e.key === "Home") target = 0;
    else if (e.key === "End") target = last;
    if (target === null) return;
    e.preventDefault();
    triggers.current[target]?.focus();
  }

  return (
    <section style={{ background: "#0a0908" }} aria-labelledby={`${baseId}-title`}>
      <div className="mx-auto grid max-w-[1100px] grid-cols-1 gap-12 px-4 py-20 sm:px-8 lg:grid-cols-[minmax(0,5fr)_minmax(0,7fr)] lg:gap-16 lg:px-14 lg:py-28">
        {/* Left: heading, intro, contact */}
        <div className="lg:sticky lg:top-28 lg:self-start">
          <div className="mb-6 flex items-center gap-3">
            <span className="inline-block h-2 w-2 bg-pb-accent" />
            <span className="font-pb-mono text-[11px] font-bold uppercase tracking-widest text-pb-accent">
              FAQ
            </span>
          </div>
          <h2
            id={`${baseId}-title`}
            className="pb-stencil"
            style={{ fontSize: "clamp(2rem, 3.4vw, 3rem)", lineHeight: 1.05, margin: 0 }}
          >
            Questions,
            <br />
            answered.
          </h2>
          <p className="mt-5 max-w-sm text-[15px] leading-relaxed" style={{ color: "#a8a49a" }}>
            Plans, file types, languages, the Chrome extension and what happens to your files. If
            something isn&apos;t covered here, ask us directly.
          </p>

          <div
            className="mt-8 max-w-sm p-6"
            style={{ background: "#1d1c1a", border: `1px solid ${HAIRLINE}`, borderRadius: 24 }}
          >
            <p className="text-[14px] font-semibold" style={{ color: "#f0ece3" }}>
              Still have a question?
            </p>
            <p className="mt-1.5 text-[13px] leading-relaxed" style={{ color: "#8a8478" }}>
              Send us a sample file or a tricky layout and we&apos;ll tell you how it will come out.
            </p>
            <Link
              href="/contact"
              className="mt-5 inline-flex items-center gap-2 rounded-full px-5 py-2.5 text-[13px] font-semibold transition-colors hover:brightness-110 focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08a6f]"
              style={{ background: "#c86018", color: "#fff" }}
            >
              Contact us
              <span aria-hidden="true">→</span>
            </Link>
          </div>
        </div>

        {/* Right: filters + accordion */}
        <div className="min-w-0">
          <div
            role="group"
            aria-label="Filter questions by topic"
            className="mb-6 flex flex-wrap gap-2"
          >
            {[ALL, ...categories].map((cat) => {
              const active = filter === cat;
              const n = cat === ALL ? items.length : counts.get(cat) ?? 0;
              return (
                <button
                  key={cat}
                  type="button"
                  aria-pressed={active}
                  onClick={() => choose(cat)}
                  className="inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-[13px] transition-colors duration-200 motion-reduce:transition-none focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-[#e08a6f]"
                  style={{
                    background: active ? "#f0ece3" : "#1d1c1a",
                    color: active ? "#15130f" : "#a8a49a",
                    border: `1px solid ${active ? "#f0ece3" : HAIRLINE}`,
                  }}
                >
                  {cat}
                  <span
                    className="font-pb-mono text-[11px]"
                    style={{ color: active ? "rgba(21,19,15,0.55)" : "#8a8478" }}
                  >
                    {n}
                  </span>
                </button>
              );
            })}
          </div>

          <div
            className="p-2 sm:p-3"
            style={{ background: "#1d1c1a", border: `1px solid ${HAIRLINE}`, borderRadius: 24 }}
          >
            <ul className="m-0 list-none p-0">
              {visible.map((item, idx) => {
                const open = openKey === item.q;
                const slug = `${baseId}-${items.indexOf(item)}`;
                const btnId = `${slug}-btn`;
                const panelId = `${slug}-panel`;
                return (
                  <li
                    key={item.q}
                    style={{
                      borderTop: idx === 0 ? undefined : `1px solid ${open ? "transparent" : HAIRLINE}`,
                    }}
                  >
                    <div
                      className="transition-colors duration-300 motion-reduce:transition-none"
                      style={{
                        background: open ? "#292826" : "transparent",
                        borderRadius: 16,
                      }}
                    >
                      <h3 className="m-0">
                        <button
                          ref={(el) => {
                            triggers.current[idx] = el;
                          }}
                          id={btnId}
                          type="button"
                          aria-expanded={open}
                          aria-controls={panelId}
                          onClick={() => setOpenKey(open ? null : item.q)}
                          onKeyDown={(e) => onTriggerKey(e, idx)}
                          className="group flex w-full items-center gap-4 rounded-2xl px-4 py-4 text-left sm:px-5 focus-visible:outline-2 focus-visible:-outline-offset-2 focus-visible:outline-[#e08a6f]"
                        >
                          <span className="min-w-0 flex-1">
                            {filter === ALL && (
                              <span
                                className="mb-1 block font-pb-mono text-[10px] uppercase tracking-[0.14em]"
                                style={{ color: "#8a8478" }}
                              >
                                {item.category}
                              </span>
                            )}
                            <span
                              className="block text-[15px] font-medium leading-snug transition-colors group-hover:text-[#f0ece3]"
                              style={{ color: open ? "#f0ece3" : "#d6d1c6" }}
                            >
                              {item.q}
                            </span>
                          </span>
                          <PlusMinus open={open} />
                        </button>
                      </h3>
                      <div
                        id={panelId}
                        role="region"
                        aria-labelledby={btnId}
                        inert={!open}
                        className="grid transition-[grid-template-rows,opacity] duration-300 ease-[cubic-bezier(0.22,1,0.36,1)] motion-reduce:transition-none"
                        style={{
                          gridTemplateRows: open ? "1fr" : "0fr",
                          opacity: open ? 1 : 0,
                        }}
                      >
                        <div className="overflow-hidden">
                          <p
                            className="m-0 max-w-[60ch] px-4 pb-5 text-[14px] leading-relaxed sm:px-5"
                            style={{ color: "#a8a49a" }}
                          >
                            {item.a}
                          </p>
                        </div>
                      </div>
                    </div>
                  </li>
                );
              })}
            </ul>
          </div>
        </div>
      </div>
    </section>
  );
}

function PlusMinus({ open }: { open: boolean }) {
  return (
    <span
      aria-hidden="true"
      className="relative inline-flex h-8 w-8 shrink-0 items-center justify-center rounded-full transition-[transform,background-color] duration-300 motion-reduce:transition-none"
      style={{
        background: open ? "#e08a6f" : "rgba(255,255,255,0.04)",
        border: `1px solid ${open ? "#e08a6f" : HAIRLINE}`,
        transform: open ? "rotate(180deg)" : "rotate(0deg)",
      }}
    >
      <span
        className="absolute h-[1.5px] w-3 rounded-full"
        style={{ background: open ? "#15130f" : "#f0ece3" }}
      />
      <span
        className="absolute h-3 w-[1.5px] rounded-full transition-transform duration-300 motion-reduce:transition-none"
        style={{
          background: open ? "#15130f" : "#f0ece3",
          transform: open ? "scaleY(0)" : "scaleY(1)",
        }}
      />
    </span>
  );
}
