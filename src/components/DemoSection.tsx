"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const LANGUAGES = ["French", "German", "Japanese", "Arabic", "Portuguese", "Hindi"];

const SAMPLE_TRANSLATIONS: Record<string, { headline: string; body: string }> = {
  French: {
    headline: "Déploiement et restauration",
    body: "La section 4.2 décrit les procédures de déploiement pour l'environnement de préproduction, y compris les étapes de restauration.",
  },
  German: {
    headline: "Bereitstellung und Rollback",
    body: "Abschnitt 4.2 beschreibt die Bereitstellungsverfahren für die Staging-Umgebung, einschließlich der Rollback-Schritte.",
  },
  Japanese: {
    headline: "デプロイとロールバック",
    body: "セクション4.2では、ステージング環境のデプロイ手順とロールバック手順について説明します。",
  },
  Arabic: {
    headline: "النشر والتراجع",
    body: "يغطي القسم 4.2 إجراءات النشر لبيئة التجهيز، بما في ذلك خطوات التراجع عن الإصدار.",
  },
  Portuguese: {
    headline: "Implantação e reversão",
    body: "A seção 4.2 aborda os procedimentos de implantação para o ambiente de staging, incluindo as etapas de reversão.",
  },
  Hindi: {
    headline: "परिनियोजन और रोलबैक",
    body: "अनुभाग 4.2 में स्टेजिंग एनवायरनमेंट के लिए परिनियोजन प्रक्रियाएं और रोलबैक चरण शामिल हैं।",
  },
};

type Status = "idle" | "translating" | "done";

export function DemoSection() {
  const [status, setStatus] = useState<Status>("idle");
  const [language, setLanguage] = useState("French");

  function runDemo() {
    setStatus("translating");
    window.setTimeout(() => setStatus("done"), 1400);
  }

  const result = SAMPLE_TRANSLATIONS[language];

  return (
    <section id="demo" className="border-y border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Try it
          </span>
          <h2 className="mt-3 font-black uppercase text-3xl tracking-tight sm:text-4xl">
            Upload once, translate any way you like.
          </h2>
        </div>

        <div className="grid gap-8 lg:grid-cols-[0.9fr_1.1fr]">
          <div className="border border-rule bg-paper p-6">
            <div className="border border-dashed border-rule p-8 text-center">
              <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
                field-ops-manual.pdf
              </p>
              <p className="mt-1 text-sm text-ink-soft">4.2 MB · 18 pages</p>
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
              </div>
            </div>

            <button
              type="button"
              onClick={runDemo}
              disabled={status === "translating"}
              className="mt-6 w-full bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-60"
            >
              {status === "translating" ? "Translating…" : "Translate document"}
            </button>
            <p className="mt-3 text-xs text-muted">
              Demo runs on sample text. No file is uploaded.
            </p>
          </div>

          <div className="border border-rule bg-paper p-6">
            <div className="mb-4 flex items-center justify-between border-b border-rule pb-3">
              <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
                Original — English
              </span>
              <span className="font-mono text-[10px] uppercase tracking-widest text-red">
                Output — {language}
              </span>
            </div>
            <div className="grid gap-6 sm:grid-cols-2">
              <div>
                <div className="h-2.5 w-3/4 bg-ink/80 mb-2" />
                <div className="h-2.5 w-1/2 bg-ink/80 mb-4" />
                <p className="text-[12px] leading-relaxed text-ink-soft">
                  Section 4.2 covers deployment procedures for the staging
                  environment, including rollback steps for critical
                  failures.
                </p>
              </div>
              <div className="min-h-[110px]">
                <AnimatePresence mode="wait">
                  {status === "done" ? (
                    <motion.div
                      key={language}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.35 }}
                    >
                      <div className="h-2.5 w-3/4 bg-red/80 mb-2" />
                      <div className="h-2.5 w-1/2 bg-red/80 mb-4" />
                      <p className="text-[12px] leading-relaxed text-ink-soft">
                        {result.body}
                      </p>
                    </motion.div>
                  ) : (
                    <div className="flex h-full items-center">
                      <p className="font-mono text-[11px] text-muted">
                        {status === "translating"
                          ? "Preserving layout, translating text…"
                          : "Press translate to preview output."}
                      </p>
                    </div>
                  )}
                </AnimatePresence>
              </div>
            </div>
            <div className="mt-6 aspect-[16/5] w-full rounded-sm bg-gradient-to-br from-rule to-paper-dim border border-rule flex items-center justify-center">
              <span className="font-mono text-[9px] uppercase tracking-widest text-muted">
                image + caption carried through untouched
              </span>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
