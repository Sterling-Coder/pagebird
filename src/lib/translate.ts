export type TranslateRequest = {
  file: File;
  targetLanguage: string;
};

export type TranslateResult = {
  translatedFileName: string;
  pages: number;
  downloadUrl: string;
};

/**
 * Backend integration point. Swap this implementation for a real API call
 * (e.g. `fetch("/api/translate", { method: "POST", body: formData })`).
 * Currently unwired — throws so the UI can show an honest "not connected"
 * state instead of fabricating a result.
 */
export async function translateDocument(
  _request: TranslateRequest
): Promise<TranslateResult> {
  throw new Error("translateDocument() is not wired to a backend yet.");
}
