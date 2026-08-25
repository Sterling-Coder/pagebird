"use client";

import { useState } from "react";

const LANGUAGES = ["French", "German", "Japanese", "Spanish"];

type Status = "idle" | "translating" | "done";

export function ExtensionDemo() {
  const [status, setStatus] = useState<Status>("idle");
  const [language, setLanguage] = useState("French");

  function runDemo() {
    setStatus("translating");
    window.setTimeout(() => setStatus("done"), 900);
  }

  return (
    <section id="extension-demo" className="border-y border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Try it
          </span>
          <h2 className="mt-3 text-3xl font-black uppercase tracking-tight sm:text-4xl">
            Highlight. Right-click. Done.
          </h2>
        </div>

        <div className="border border-rule bg-paper p-6">
          <p className="font-mono text-[10px] uppercase tracking-widest text-muted">
            Sample page text
          </p>
          <p className="mt-3 text-base leading-relaxed text-ink-soft">
            {status === "done" ? (
              <span className="bg-red/10">
                {language === "French"
                  ? "Veuillez confirmer votre commande avant vendredi."
                  : language === "German"
                    ? "Bitte bestätigen Sie Ihre Bestellung bis Freitag."
                    : language === "Japanese"
                      ? "金曜日までにご注文の確認をお願いします。"
                      : "Por favor confirme su pedido antes del viernes."}
              </span>
            ) : (
              <span className="bg-red/10">
                Please confirm your order before Friday.
              </span>
            )}
          </p>

          <div className="mt-6 flex flex-wrap items-center gap-2">
            {LANGUAGES.map((lang) => (
              <button
                key={lang}
                type="button"
                onClick={() => {
                  setLanguage(lang);
                  setStatus("idle");
                }}
                className={`border px-3 py-1.5 font-mono text-[11px] uppercase tracking-widest transition-colors ${
                  language === lang
                    ? "border-ink bg-ink text-paper"
                    : "border-rule text-ink-soft hover:border-ink hover:text-ink"
                }`}
              >
                {lang}
              </button>
            ))}
            <button
              type="button"
              onClick={runDemo}
              disabled={status === "translating"}
              className="ml-auto bg-red px-6 py-2.5 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === "translating" ? "Translating…" : "Translate selection"}
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
