"use client";

import type { ReactNode } from "react";
import { useDemoClock } from "./useDemoClock";

const GREEN = "#8fd14f";
const URL_TEXT = "https://northwind.coffee/beans";

/* Timeline, in 100 ms ticks. */
const TYPE_START = 6;
const TYPE_END = TYPE_START + URL_TEXT.length; // 36
const PRESS = 42;
const STAGE_START = 46;
const STAGE_LEN = 7;
const STAGES = [
  { label: "Checking the address", note: "public host, port 443" },
  { label: "Fetching the page", note: "each redirect re-checked" },
  { label: "Removing scripts", note: "12 <script> tags dropped" },
  { label: "Translating", note: "38 segments to Spanish" },
  { label: "Rebuilding the copy", note: "same markup and styles" },
];
const RESULT = STAGE_START + STAGES.length * STAGE_LEN; // 81
const CYCLE = 135;
const REST = 110;

/** Preserved token: brand names, prices and the like come back unchanged. */
function Kept({ children }: { children: ReactNode }) {
  return (
    <span style={{ color: GREEN, textDecoration: "underline dotted", textUnderlineOffset: 3 }}>{children}</span>
  );
}

function MockSite({ translated }: { translated: boolean }) {
  const t = (en: ReactNode, es: ReactNode) => (translated ? es : en);
  return (
    <div className="rounded-[14px] p-4 sm:p-5" style={{ background: "#f4efe6", color: "#2a2520" }}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-[13px] font-bold tracking-tight">
          {translated ? <Kept>Northwind Coffee</Kept> : "Northwind Coffee"}
        </span>
        <span className="flex gap-3 text-[11px]" style={{ color: "#6b6258" }}>
          <span>{t("Shop", "Tienda")}</span>
          <span>{t("Origins", "Orígenes")}</span>
          <span className="hidden sm:inline">{t("Wholesale", "Mayoristas")}</span>
        </span>
      </div>
      <p className="mt-5 text-[19px] leading-[1.15] font-semibold sm:text-[22px]" style={{ fontFamily: "var(--font-fraunces), serif" }}>
        {t("Single-origin beans, roasted to order.", "Granos de origen único, tostados por encargo.")}
      </p>
      <p className="mt-2 text-[12px] leading-relaxed" style={{ color: "#5b534a" }}>
        {translated ? (
          <>
            Desde <Kept>$14.50</Kept> la bolsa. Envío gratis a partir de <Kept>$40</Kept>. Escríbenos a{" "}
            <Kept>hello@northwind.coffee</Kept>.
          </>
        ) : (
          "From $14.50 a bag. Free shipping over $40. Write to us at hello@northwind.coffee."
        )}
      </p>
      <div className="mt-4 flex items-center gap-3">
        <span className="rounded-full px-3.5 py-1.5 text-[11px] font-semibold text-white" style={{ background: "#2a2520" }}>
          {t("Shop the beans", "Ver los granos")}
        </span>
        <span className="text-[11px]" style={{ color: "#6b6258" }}>
          {t("Our farmers →", "Nuestros productores →")}
        </span>
      </div>
    </div>
  );
}

export default function LinkDemo() {
  const { ref, t, running } = useDemoClock<HTMLDivElement>(CYCLE, REST);

  const typed = URL_TEXT.slice(0, Math.max(0, Math.min(URL_TEXT.length, t - TYPE_START)));
  const typing = t < TYPE_END + 2;
  const pressed = t >= PRESS && t < PRESS + 3;
  const working = t >= STAGE_START && t < RESULT;
  const showResult = t >= RESULT;
  const fading = t >= CYCLE - 6;
  const stageIdx = Math.floor((t - STAGE_START) / STAGE_LEN);

  return (
    <div
      ref={ref}
      data-wsd-paused={running ? undefined : ""}
      className="overflow-hidden rounded-[24px]"
      style={{ background: "#1d1c1a", border: "1px solid rgba(255,255,255,0.08)" }}
      aria-label="Animated demo: a URL is pasted, Pagebirdy fetches and translates the page, and a Spanish copy appears."
      role="img"
    >
      {/* App bar */}
      <div className="flex items-center gap-2 px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <span className="h-2 w-2 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span className="h-2 w-2 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span className="h-2 w-2 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span className="font-pb-mono ml-2 truncate text-[11px]" style={{ color: "#8a8478" }}>
          pagebirdy · Website agent
        </span>
      </div>

      <div className="p-4 sm:p-5">
        {/* Form */}
        <div className="flex flex-col gap-2 sm:flex-row">
          <div
            className="font-pb-mono flex min-w-0 flex-1 items-center rounded-[12px] px-3 py-2.5 text-[12px]"
            style={{ background: "#292826", color: "#f0ece3", border: `1px solid ${typing && t > TYPE_START - 2 ? `${GREEN}66` : "rgba(255,255,255,0.06)"}` }}
          >
            <span className="truncate">
              {typed || <span style={{ color: "#8a8478" }}>Paste a public page URL</span>}
            </span>
            {typing && <span className="wsd-caret ml-px inline-block h-[14px] w-[2px] shrink-0" style={{ background: GREEN }} />}
          </div>
          <div className="flex gap-2">
            <div
              className="font-pb-mono flex flex-1 items-center justify-between gap-3 rounded-[12px] px-3 py-2.5 text-[12px] sm:flex-none"
              style={{ background: "#292826", color: t >= TYPE_END + 2 ? "#f0ece3" : "#8a8478" }}
            >
              <span>{t >= TYPE_END + 2 ? "Spanish" : "Language"}</span>
              <span style={{ color: "#8a8478" }}>▾</span>
            </div>
            <div
              className="font-pb-mono rounded-[12px] px-4 py-2.5 text-[12px] font-bold transition-transform duration-150"
              style={{
                background: GREEN,
                color: "#10140a",
                transform: pressed ? "scale(0.94)" : "scale(1)",
                opacity: t >= TYPE_END + 2 ? 1 : 0.45,
              }}
            >
              Translate
            </div>
          </div>
        </div>

        {/* Stage area */}
        <div
          className="relative mt-4 min-h-[300px] rounded-[16px] p-3 transition-opacity duration-500 sm:min-h-[280px] sm:p-4"
          style={{ background: "#292826", opacity: fading ? 0 : 1 }}
        >
          {!working && !showResult && (
            <div className="flex h-full min-h-[270px] flex-col items-center justify-center gap-2 text-center">
              <span className="font-pb-mono text-[11px] tracking-widest uppercase" style={{ color: "#8a8478" }}>
                One page per job
              </span>
              <span className="max-w-[260px] text-[13px]" style={{ color: "#a8a49a" }}>
                The translated copy will appear here, read-only and sandboxed.
              </span>
            </div>
          )}

          {working && (
            <ol className="wsd-fade flex flex-col gap-2.5 py-2">
              {STAGES.map((s, i) => {
                const done = i < stageIdx;
                const active = i === stageIdx;
                return (
                  <li
                    key={s.label}
                    className="flex items-center gap-3 rounded-[12px] px-3 py-2.5 transition-colors duration-300"
                    style={{
                      background: active ? "rgba(143,209,79,0.08)" : "transparent",
                      opacity: done || active ? 1 : 0.35,
                    }}
                  >
                    <span
                      className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-full text-[10px] ${active ? "wsd-pulse" : ""}`}
                      style={{
                        background: done ? GREEN : "transparent",
                        border: `1px solid ${done || active ? GREEN : "rgba(255,255,255,0.2)"}`,
                        color: "#10140a",
                      }}
                    >
                      {done ? "✓" : ""}
                    </span>
                    <span className="min-w-0 flex-1">
                      <span className="block text-[13px]" style={{ color: "#f0ece3" }}>{s.label}</span>
                      <span className="font-pb-mono block truncate text-[10px]" style={{ color: "#8a8478" }}>{s.note}</span>
                    </span>
                  </li>
                );
              })}
            </ol>
          )}

          {showResult && (
            <div className="wsd-fade">
              <div className="mb-3 flex flex-wrap items-center gap-2">
                <span
                  className="font-pb-mono rounded-md px-2 py-0.5 text-[10px] tracking-wider uppercase"
                  style={{ color: GREEN, background: `${GREEN}1f`, border: `1px solid ${GREEN}44` }}
                >
                  Spanish copy
                </span>
                <span className="font-pb-mono text-[10px] tracking-wider uppercase" style={{ color: "#8a8478" }}>
                  Sandboxed · no scripts · read-only
                </span>
                <span
                  className="font-pb-mono ml-auto rounded-md px-2 py-0.5 text-[10px]"
                  style={{ color: "#f0ece3", background: "#1d1c1a", border: "1px solid rgba(255,255,255,0.08)" }}
                >
                  Review &amp; edit
                </span>
              </div>
              <MockSite translated />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
