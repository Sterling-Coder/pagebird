export type JobTypeId = "document" | "srt" | "image" | "website" | "youtube";

export type JobTypeConfig = {
  id: JobTypeId;
  label: string;
  description: string;
  enabled: boolean;
};

export const JOB_TYPES: JobTypeConfig[] = [
  {
    id: "document",
    label: "Document / PDF",
    description: "PDF, INDD, IDML — layout-preserving translation.",
    enabled: true,
  },
  {
    id: "srt",
    label: "SRT / VTT Subtitles",
    description: "Translate subtitle files, timing preserved.",
    enabled: false,
  },
  {
    id: "image",
    label: "Image Translator",
    description: "Translate text embedded in images.",
    enabled: false,
  },
  {
    id: "website",
    label: "Website Translator",
    description: "Translate a live site's pages.",
    enabled: false,
  },
  {
    id: "youtube",
    label: "YouTube Subtitle Translator",
    description: "Pull and translate a video's captions.",
    enabled: false,
  },
];

export function getJobType(id: string): JobTypeConfig | undefined {
  return JOB_TYPES.find((t) => t.id === id);
}
