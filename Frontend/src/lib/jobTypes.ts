export type JobTypeId = "document" | "image" | "website" | "srt" | "youtube";

export type JobTypeConfig = {
  id: JobTypeId;
  label: string;
  description: string;
  /** What the person hands over, as shown on the type card. */
  formats: string;
  /** How work enters a project of this type: files, a page URL, or nothing yet. */
  input: "files" | "url" | null;
  enabled: boolean;
  /** Dot colour on the type pill. */
  color: string;
};

export const JOB_TYPES: JobTypeConfig[] = [
  {
    id: "document",
    label: "Document & Office",
    description: "Layout-preserving translation. The same file type comes back, ready to print or edit.",
    formats: "PDF · InDesign IDML · Word · PowerPoint · Excel · Text",
    input: "files",
    enabled: true,
    color: "#e8ac2e",
  },
  {
    id: "image",
    label: "Image",
    description: "Reads the text in an image and redraws the translation in the same place, colour and size.",
    formats: "PNG · JPEG · WEBP · Photoshop · Illustrator",
    input: "files",
    enabled: true,
    color: "#5aa58a",
  },
  {
    id: "website",
    label: "Website",
    description: "Paste a public page URL and get a translated, read-only copy you can review and download.",
    formats: "Any public web page URL",
    input: "url",
    enabled: true,
    color: "#5b8bd9",
  },
  {
    id: "srt",
    label: "Subtitles",
    description: "SRT / VTT subtitle files with their timing kept.",
    formats: "SRT · VTT",
    input: null,
    enabled: false,
    color: "#a39b8d",
  },
  {
    id: "youtube",
    label: "YouTube captions",
    description: "Pull a video's captions and translate them.",
    formats: "YouTube link",
    input: null,
    enabled: false,
    color: "#a39b8d",
  },
];

export const ENABLED_JOB_TYPES = JOB_TYPES.filter((t) => t.enabled);

export function getJobType(id: string | null | undefined): JobTypeConfig | undefined {
  return JOB_TYPES.find((t) => t.id === id);
}

/** Used until GET /api/formats answers (and if it never does). */
export const FALLBACK_DOCUMENT_EXTS = [".pdf", ".idml", ".docx", ".pptx", ".xlsx", ".txt"];
/** Used until GET /api/image-translation/config answers. */
export const FALLBACK_IMAGE_EXTS = [".png", ".jpg", ".jpeg", ".webp", ".psd", ".psb", ".ai"];

/** Why a picked file can't be uploaded, or null when it can. Mirrors the
 * backend's own messages so the person learns it before waiting on an upload. */
export function rejectReason(name: string, accepted: string[]): string | null {
  const dot = name.lastIndexOf(".");
  const ext = dot >= 0 ? name.slice(dot).toLowerCase() : "";
  if (ext === ".indd") {
    return "InDesign .indd files can't be translated directly. In InDesign use File → Export → InDesign Markup (IDML) and upload the .idml.";
  }
  const legacy: Record<string, string> = { ".doc": ".docx", ".ppt": ".pptx", ".xls": ".xlsx" };
  if (legacy[ext]) {
    return `Old ${ext} files aren't supported. Open it in Office, save it as ${legacy[ext]} and upload that.`;
  }
  if (!accepted.includes(ext)) {
    return `${ext || "Files without an extension"} can't be translated here. Accepted: ${accepted.join(" ")}`;
  }
  return null;
}

/** What a job in a project is, read from its row. */
export type FileKind = "pdf" | "idml" | "office" | "image" | "website" | "links";

export function fileKind(job: {
  job_type?: string;
  original_filename?: string | null;
  meta?: { format?: string } | null;
}): FileKind {
  if (job.job_type === "links") return "links";
  const f = job.meta?.format ?? "";
  if (f === "image") return "image";
  if (f === "website") return "website";
  if (["docx", "pptx", "xlsx", "txt"].includes(f)) return "office";
  if (f === "idml") return "idml";
  if (f === "pdf") return "pdf";
  // A job that is still running may not have its format recorded yet.
  const ext = (job.original_filename ?? "").toLowerCase().split(".").pop() ?? "";
  if (ext === "idml") return "idml";
  if (["docx", "pptx", "xlsx", "txt"].includes(ext)) return "office";
  if (["png", "jpg", "jpeg", "webp", "psd", "psb", "ai"].includes(ext)) return "image";
  return "pdf";
}

/** Segment edits followed by POST /api/jobs/{id}/rebuild. Image and IDML jobs
 * have no rebuild on the backend. */
export function supportsRebuild(kind: FileKind): boolean {
  return kind === "pdf" || kind === "office" || kind === "website";
}

const KIND_LABEL: Record<string, string> = {
  pdf: "PDF", idml: "IDML", docx: "Word", pptx: "PowerPoint", xlsx: "Excel", txt: "Text",
  image: "Image", website: "Web page", links: "Linked graphics",
};

export function fileKindLabel(job: {
  job_type?: string;
  original_filename?: string | null;
  meta?: { format?: string } | null;
}): string {
  const kind = fileKind(job);
  if (kind === "office") {
    const f = job.meta?.format ?? (job.original_filename ?? "").toLowerCase().split(".").pop() ?? "";
    return KIND_LABEL[f] ?? "Office";
  }
  return KIND_LABEL[kind];
}

/** A backend stage key ("extracting_text") as words ("Extracting text"). */
export function stageLabel(stage: string | null | undefined): string | null {
  if (!stage) return null;
  const words = stage.replace(/[_-]+/g, " ").trim();
  return words ? words.charAt(0).toUpperCase() + words.slice(1) : null;
}
