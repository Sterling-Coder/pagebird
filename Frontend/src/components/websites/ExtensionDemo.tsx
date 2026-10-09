"use client";

import type { ReactNode } from "react";
import { useDemoClock } from "./useDemoClock";

const VIOLET = "#a98bf0";
const SEL = "Direct trade takes longer, but the beans taste better.";
const SEL_FR = "Le commerce direct prend plus de temps, mais les grains ont meilleur goût.";

/* Timeline, in 100 ms ticks. */
const SEL_START = 8;
const SEL_END = 26;
const BTN_SHOW = 27;
const BUBBLE = 31;
const BUBBLE_END = 58;
const ICON = 62;
const POPUP = 65;
const POPUP_PRESS = 76;
const PAGE_START = 80;
const STAGGER = 4;
const RESTORE_PRESS = 112;
const RESTORE = 115;
const CYCLE = 132;
const REST = 45;

function Kept({ children }: { children: ReactNode }) {
  return <span style={{ textDecoration: `underline dotted ${VIOLET}`, textUnderlineOffset: 3 }}>{children}</span>;
}

/** Swaps to the translated version once `on`, with a short fade. */
function Swap({ on, en, fr }: { on: boolean; en: ReactNode; fr: ReactNode }) {
  return (
    <span key={on ? "fr" : "en"} className="wsd-fade">
      {on ? fr : en}
    </span>
  );
}

export default function ExtensionDemo() {
  const { ref, t, running } = useDemoClock<HTMLDivElement>(CYCLE, REST);

  const selecting = t >= SEL_START && t < BUBBLE_END;
  const selFrac = Math.min(1, Math.max(0, (t - SEL_START) / (SEL_END - SEL_START)));
  const selChars = selecting ? Math.round(SEL.length * selFrac) : 0;
  const showBtn = t >= BTN_SHOW && t < BUBBLE;
  const showBubble = t >= BUBBLE && t < BUBBLE_END;
  const iconHot = t >= ICON && t < PAGE_START;
  const popupOpen = t >= POPUP && t < PAGE_START;
  const popupPressed = t >= POPUP_PRESS && t < POPUP_PRESS + 3;
  const pageOn = (i: number) => t >= PAGE_START + i * STAGGER && t < RESTORE;
  const showRestore = t >= PAGE_START + 4 * STAGGER && t < RESTORE;
  const restorePressed = t >= RESTORE_PRESS && t < RESTORE;

  return (
    <div
      ref={ref}
      data-wsd-paused={running ? undefined : ""}
      role="img"
      aria-label="Animated demo: a sentence is selected and its French translation appears beside it, then the extension translates the whole article in place and restores the original."
      className="overflow-hidden rounded-[24px]"
      style={{ background: "#1d1c1a", border: "1px solid rgba(255,255,255,0.08)" }}
    >
      {/* Browser chrome */}
      <div className="flex items-center gap-2 px-4 py-3" style={{ borderBottom: "1px solid rgba(255,255,255,0.06)" }}>
        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span className="h-2 w-2 shrink-0 rounded-full" style={{ background: "rgba(255,255,255,0.14)" }} />
        <span
          className="font-pb-mono ml-2 min-w-0 flex-1 truncate rounded-full px-3 py-1 text-[11px]"
          style={{ background: "#292826", color: "#a8a49a" }}
        >
          theroastreview.com/supply-chain
        </span>
        <span
          className="flex h-6 w-6 shrink-0 items-center justify-center rounded-md transition-colors duration-200"
          style={{ background: iconHot ? `${VIOLET}33` : "transparent", border: `1px solid ${iconHot ? VIOLET : "rgba(255,255,255,0.1)"}` }}
          aria-hidden="true"
        >
          <span className="h-2 w-2" style={{ background: VIOLET }} />
        </span>
      </div>

      <div className="relative p-3 sm:p-4">
        {/* The page being read */}
        <article
          className="relative min-h-[480px] rounded-[16px] p-5 pb-14 sm:min-h-[390px] sm:p-6 sm:pb-14"
          style={{ background: "#f4efe6", color: "#2a2520" }}
        >
          <p className="font-pb-mono text-[10px] tracking-widest uppercase" style={{ color: "#8a7f72" }}>
            <Swap on={pageOn(0)} en="Industry · 6 min read" fr="Secteur · 6 min de lecture" />
          </p>
          <h4 className="mt-2 text-[19px] leading-[1.2] font-semibold sm:text-[21px]" style={{ fontFamily: "var(--font-fraunces), serif" }}>
            <Swap
              on={pageOn(0)}
              en="How small roasters are rethinking the supply chain"
              fr="Comment les petits torréfacteurs repensent la chaîne d’approvisionnement"
            />
          </h4>
          <p className="mt-3 text-[13px] leading-relaxed" style={{ color: "#4a433b" }}>
            <Swap
              on={pageOn(1)}
              en="Northwind Coffee pays farmers $4.20 per pound, almost twice the market rate."
              fr={
                <>
                  <Kept>Northwind Coffee</Kept> paie les producteurs <Kept>$4.20</Kept> la livre, presque deux fois le prix du
                  marché.
                </>
              }
            />
          </p>
          <p className="mt-2 text-[13px] leading-relaxed" style={{ color: "#4a433b" }}>
            <Swap
              on={pageOn(2)}
              en="It ships to 31 countries and answers every order from hello@northwind.coffee."
              fr={
                <>
                  L’entreprise expédie vers <Kept>31</Kept> pays et répond à chaque commande depuis{" "}
                  <Kept>hello@northwind.coffee</Kept>.
                </>
              }
            />
          </p>
          <p className="relative mt-2 text-[13px] leading-relaxed" style={{ color: "#4a433b" }}>
            {pageOn(3) ? (
              <Swap on en={SEL} fr={SEL_FR} />
            ) : (
              <>
                <span style={{ background: selChars ? `${VIOLET}55` : "transparent", borderRadius: 2 }}>
                  {SEL.slice(0, selChars)}
                </span>
                {SEL.slice(selChars)}
                {showBtn && (
                  <span
                    className="wsd-fade ml-1 inline-flex h-5 w-5 items-center justify-center rounded-md align-middle text-[11px] font-bold"
                    style={{ background: VIOLET, color: "#1a1430" }}
                  >
                    文
                  </span>
                )}
              </>
            )}
          </p>

          {/* Translation beside the selection */}
          {showBubble && (
            <div
              className="wsd-fade mt-3 rounded-[12px] p-3 text-[13px] leading-snug shadow-lg sm:absolute sm:right-4 sm:bottom-4 sm:mt-0 sm:max-w-[260px]"
              style={{ background: "#1d1c1a", color: "#f0ece3", border: `1px solid ${VIOLET}55` }}
            >
              <span className="font-pb-mono mb-1 block text-[10px] tracking-widest uppercase" style={{ color: VIOLET }}>
                English → French
              </span>
              {SEL_FR}
            </div>
          )}

          {/* In-page restore control */}
          {showRestore && (
            <div
              className="wsd-fade absolute right-3 bottom-3 left-3 flex items-center justify-between gap-3 rounded-[12px] px-3 py-2 text-[12px] sm:left-auto"
              style={{ background: "#1d1c1a", color: "#a8a49a", border: `1px solid ${VIOLET}55` }}
            >
              <span>Page translated.</span>
              <span
                className="rounded-md px-2 py-0.5 font-semibold transition-transform duration-150"
                style={{ color: VIOLET, background: `${VIOLET}1f`, transform: restorePressed ? "scale(0.92)" : "scale(1)" }}
              >
                Show original
              </span>
            </div>
          )}
        </article>

        {/* Extension popup */}
        {popupOpen && (
          <div
            className="wsd-fade absolute top-1 right-3 w-[220px] max-w-[calc(100%-24px)] rounded-[14px] p-3 shadow-2xl"
            style={{ background: "#1d1c1a", border: "1px solid rgba(255,255,255,0.12)" }}
          >
            <div className="flex items-center gap-2">
              <span className="h-2 w-2" style={{ background: VIOLET }} />
              <span className="font-pb-mono text-[10px] tracking-widest uppercase" style={{ color: "#f0ece3" }}>
                Pagebirdy
              </span>
            </div>
            <div className="mt-3 flex items-center justify-between rounded-[10px] px-2.5 py-2 text-[12px]" style={{ background: "#292826", color: "#f0ece3" }}>
              <span style={{ color: "#a8a49a" }}>Translate into</span>
              <span>French ▾</span>
            </div>
            <div className="mt-2 flex items-center justify-between px-1 text-[12px]" style={{ color: "#a8a49a" }}>
              <span>Button on selection</span>
              <span className="relative h-4 w-7 rounded-full" style={{ background: VIOLET }}>
                <span className="absolute top-0.5 right-0.5 h-3 w-3 rounded-full" style={{ background: "#1d1c1a" }} />
              </span>
            </div>
            <div
              className="mt-3 rounded-[10px] py-2 text-center text-[12px] font-semibold transition-transform duration-150"
              style={{ background: VIOLET, color: "#1a1430", transform: popupPressed ? "scale(0.95)" : "scale(1)" }}
            >
              Translate this page
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
