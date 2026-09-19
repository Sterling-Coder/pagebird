const displayNames = new Intl.DisplayNames(["en"], { type: "language" });

export function languageName(code: string | null | undefined): string | null {
  if (!code) return null;
  let resolved: string | undefined;
  try {
    resolved = displayNames.of(code);
  } catch {
    resolved = undefined;
  }
  // Intl.DisplayNames echoes back tags it can't resolve (e.g. "english")
  // instead of throwing, so an unchanged result means resolution failed.
  return resolved && resolved.toLowerCase() !== code.toLowerCase() ? resolved : capitalize(code);
}

function capitalize(s: string): string {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
