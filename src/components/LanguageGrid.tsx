const LANGUAGES = [
  "English", "French", "German", "Spanish", "Portuguese", "Italian",
  "Dutch", "Swedish", "Polish", "Japanese", "Korean", "Mandarin",
  "Cantonese", "Arabic", "Hebrew", "Hindi", "Bengali", "Vietnamese",
  "Thai", "Indonesian", "Turkish", "Russian", "Ukrainian", "Greek",
  "Finnish", "Norwegian", "Danish", "Czech", "Romanian", "Malay",
  "Filipino", "Swahili",
];

export function LanguageGrid() {
  return (
    <section id="languages" className="border-t border-rule bg-paper-dim">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="mb-10 max-w-xl">
          <span className="font-mono text-[11px] uppercase tracking-widest text-red">
            Coverage
          </span>
          <h2 className="mt-3 font-black uppercase text-3xl tracking-tight sm:text-4xl">
            32 languages, same accuracy in each.
          </h2>
        </div>
        <ul className="flex flex-wrap gap-x-6 gap-y-3">
          {LANGUAGES.map((lang) => (
            <li
              key={lang}
              className="font-mono text-[12px] uppercase tracking-widest text-ink-soft"
            >
              {lang}
            </li>
          ))}
        </ul>
      </div>
    </section>
  );
}
