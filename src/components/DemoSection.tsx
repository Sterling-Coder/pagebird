"use client";

import { useState } from "react";
import { motion, AnimatePresence } from "framer-motion";

const LANGUAGES = ["French", "German", "Japanese", "Arabic", "Portuguese", "Hindi"];

const SAMPLE_TRANSLATIONS: Record<
  string,
  { title: string; heading: string; body: string }
> = {
  French: {
    title: "Rassembler toutes vos connaissances en un seul endroit",
    heading: "1. Pourquoi centraliser vos connaissances ?",
    body: "Conservez tout votre savoir au même endroit afin de ne jamais perdre une information importante. Combinez vos ressources choisies à la puissance d'analyse de l'IA.",
  },
  German: {
    title: "Sammeln Sie Ihr gesamtes Wissen an einem Ort",
    heading: "1. Warum Wissen zentral sammeln?",
    body: "Bewahren Sie Ihr gesamtes Wissen an einem Ort auf, damit wichtige Informationen nie verloren gehen. Kombinieren Sie handverlesene Quellen mit KI-gestützter Analyse.",
  },
  Japanese: {
    title: "知識をすべて一箇所に集める",
    heading: "1. なぜ知識を集約する必要があるのか？",
    body: "重要な情報を見失わないよう、すべての知識を一箇所に保管します。厳選したリソースとAIの分析力を組み合わせましょう。",
  },
  Arabic: {
    title: "اجمع كل معارفك في مكان واحد",
    heading: "١. لماذا تحتاج لتجميع المعرفة؟",
    body: "احتفظ بجميع معلوماتك في مكان واحد حتى لا تفقد أبدًا أي معلومة مهمة. اجمع بين مصادرك المختارة وقوة تحليل الذكاء الاصطناعي.",
  },
  Portuguese: {
    title: "Reúna todo o seu conhecimento em um só lugar",
    heading: "1. Por que centralizar o conhecimento?",
    body: "Mantenha todo o seu conhecimento em um só lugar para nunca perder uma informação importante. Combine suas fontes selecionadas com o poder de análise da IA.",
  },
  Hindi: {
    title: "अपना सारा ज्ञान एक ही जगह इकट्ठा करें",
    heading: "1. ज्ञान को केंद्रीकृत क्यों करें?",
    body: "अपनी सारी जानकारी एक ही स्थान पर रखें ताकि कोई महत्वपूर्ण जानकारी कभी न खोए। चुने हुए स्रोतों को AI के विश्लेषण के साथ जोड़ें।",
  },
};

const SOURCE = {
  title: "Collect all your knowledge in one place",
  heading: "1. Why centralize your knowledge?",
  body: "Keep all your information in one place so you never lose track of anything important. Combine your hand-picked resources with AI's analytical power.",
};

type Status = "idle" | "translating" | "done";

function DocPane({
  eyebrow,
  content,
  highlight,
}: {
  eyebrow: string;
  content: { title: string; heading: string; body: string };
  highlight?: boolean;
}) {
  return (
    <div className="px-5 py-6 sm:px-8 sm:py-8">
      <p
        className={`mb-4 font-mono text-[10px] uppercase tracking-widest ${
          highlight ? "text-red" : "text-muted"
        }`}
      >
        {eyebrow}
      </p>
      <p className="text-sm font-black uppercase tracking-tight">
        {content.title}
      </p>
      <p className="mt-5 text-xs font-black uppercase tracking-tight text-ink-soft">
        {content.heading}
      </p>
      <p className="mt-2 text-[12px] leading-relaxed text-ink-soft">
        {content.body}
      </p>
      <div className="mt-5 h-2 w-3/4 bg-rule" />
      <div className="mt-2 h-2 w-1/2 bg-rule" />
      <div className="mt-2 h-2 w-2/3 bg-rule" />
    </div>
  );
}

export function DemoSection() {
  const [status, setStatus] = useState<Status>("idle");
  const [language, setLanguage] = useState("French");
  const [page, setPage] = useState(1);

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
            See it side by side, before you commit.
          </h2>
          <p className="mt-3 text-sm leading-relaxed text-ink-soft">
            Upload a file, watch the original and the translation line up
            page for page — same layout, same structure, no surprises.
          </p>
        </div>

        <div className="relative border-2 border-ink bg-paper shadow-[6px_6px_0_rgba(0,0,0,1)]">
          <div className="flex items-center justify-between border-b border-ink px-4 py-3">
            <div className="flex items-center gap-3">
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 text-ink-soft"
                aria-hidden="true"
              >
                <path d="M19 12H5" />
                <path d="M11 18l-6-6 6-6" />
              </svg>
              <span className="font-mono text-[11px] text-ink-soft">
                collect-all-your-knowledge.pdf
              </span>
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="2"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-3 w-3 text-muted"
                aria-hidden="true"
              >
                <path d="M6 9l6 6 6-6" />
              </svg>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest text-muted">
              4.2 MB
            </span>
          </div>

          <div className="flex items-center justify-between border-b border-rule bg-paper-dim px-4 py-2">
            <div className="flex items-center gap-3 font-mono text-[10px] uppercase tracking-widest text-muted">
              <button
                type="button"
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                className="transition-colors hover:text-ink"
                aria-label="Previous page"
              >
                ←
              </button>
              <span>
                Page {page} / 3
              </span>
              <button
                type="button"
                onClick={() => setPage((p) => Math.min(3, p + 1))}
                className="transition-colors hover:text-ink"
                aria-label="Next page"
              >
                →
              </button>
            </div>
            <span className="font-mono text-[10px] uppercase tracking-widest text-red">
              EN → {language}
            </span>
          </div>

          <div className="relative grid divide-x divide-rule sm:grid-cols-2">
            <DocPane eyebrow="Original — English" content={SOURCE} />

            <div className="relative min-h-[220px]">
              <AnimatePresence mode="wait">
                {status === "done" ? (
                  <motion.div
                    key={language}
                    initial={{ opacity: 0, y: 6 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35 }}
                  >
                    <DocPane
                      eyebrow={`Translated — ${language}`}
                      content={result}
                      highlight
                    />
                  </motion.div>
                ) : (
                  <div className="flex h-full min-h-[220px] items-center justify-center px-8 text-center">
                    <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
                      {status === "translating"
                        ? "Preserving layout, translating…"
                        : "Press translate to preview output"}
                    </p>
                  </div>
                )}
              </AnimatePresence>
            </div>

            <div
              className="pointer-events-none absolute left-1/2 top-1/2 hidden h-9 w-9 -translate-x-1/2 -translate-y-1/2 items-center justify-center border border-ink bg-paper sm:flex"
              aria-hidden="true"
            >
              <svg
                viewBox="0 0 24 24"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.75"
                strokeLinecap="round"
                strokeLinejoin="round"
                className="h-4 w-4 text-ink-soft"
              >
                <path d="M17 2l4 4-4 4" />
                <path d="M3 11V9a4 4 0 0 1 4-4h14" />
                <path d="M7 22l-4-4 4-4" />
                <path d="M21 13v2a4 4 0 0 1-4 4H3" />
              </svg>
            </div>
          </div>
        </div>

        <div className="mt-8 grid gap-6 sm:grid-cols-[1fr_auto] sm:items-end">
          <div>
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

          <div>
            <button
              type="button"
              onClick={runDemo}
              disabled={status === "translating"}
              className="w-full bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90 disabled:opacity-60 sm:w-auto"
            >
              {status === "translating" ? "Translating…" : "Translate document"}
            </button>
            <p className="mt-2 text-xs text-muted">
              Demo runs on sample text. No file is uploaded.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
