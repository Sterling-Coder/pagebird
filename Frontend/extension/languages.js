// Fallback list, used until GET /api/languages answers (or when it cannot).
export const FALLBACK_LANGUAGES = [
  { code: "es", name: "Spanish" }, { code: "fr", name: "French" }, { code: "de", name: "German" },
  { code: "pt", name: "Portuguese" }, { code: "it", name: "Italian" }, { code: "zh", name: "Chinese" },
  { code: "ja", name: "Japanese" }, { code: "ko", name: "Korean" }, { code: "hi", name: "Hindi" },
  { code: "ar", name: "Arabic" }, { code: "he", name: "Hebrew" }, { code: "fa", name: "Persian" },
  { code: "ur", name: "Urdu" },
];
export const DEFAULT_SETTINGS = { lang: "es", selectionButton: true };
