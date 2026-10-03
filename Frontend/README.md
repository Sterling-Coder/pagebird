# Pagebirdy frontend

Next.js (App Router) app — the marketing site and the actual translation product.

## Run

```bash
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000). Needs the backend running (default `http://localhost:8000`, see `NEXT_PUBLIC_API_BASE_URL`) and Supabase env vars for auth to work.

## Layout

```
src/app/
  (marketing)/     public site — home, /product, /integrations, /contact
  login/           email + Google/Apple sign-in (Google/Apple show "coming soon")
  auth/callback/   Supabase OAuth callback
  app/             the actual product, behind auth
    jobs/[projectId]/
      files/             project Files list — upload, job status, Run QA, failure reasons
      files/[fileId]/    Finder-style file/links preview, translation editor, QA detail
      linguistic-assets/ statistics/ settings/   per-project pages
    settings/  team/     account settings, team members
  api/contact/     contact form → email via Resend (rate-limited)

src/components/
  app/             product UI — upload pane, output pane, PDF preview/editor, links Finder view,
                   QA detail, logs panel, trial banner + talk-to-us panel
  (root)           marketing UI — header, footer, login form, contact form, demo video modal
                   (auto-opens once after scrolling the home page)

src/lib/
  translate.ts     job/translate API calls (upload, download, links batch, job status, QA/eval)
  jobTypes.ts      job type catalogue (only Document / PDF enabled)
  team.ts          team members API
  projects.ts      projects/folders CRUD
  supabase/        Supabase client + authenticated fetch helper
  pdfjs.ts         pdf.js loader for in-browser PDF rendering
  logs.ts          polls the backend's client-scoped activity log panel
```

## Key flows

- **Document upload** (`.pdf`, `.idml`; `.indd` is rejected — export IDML first) → `translate.ts`'s `translateDocument` → backend returns a job id right away and translates in the background → Files page polls job status and shows the error if it failed → `SyncedDocumentPair` (source/target side-by-side, segment editing, undo) in `PdfPreview.tsx`.
- **Links batch upload** (`.ai`/`.eps`/`.pdf`/`.psd` folder) → `translateLinks` → `LinksPreview.tsx`, a Finder-style split view (file list left, full preview right) backed by per-file list/fetch endpoints rather than a whole-zip download.
- **QA** — Run QA button on the Files list calls `/api/jobs/{id}/eval`; reports are stored server-side and listed per project; `QaDetail.tsx` shows one, and the server's QA error is shown as-is when it fails.
- **Auth** — Supabase, cookie-based session via `@supabase/ssr`; `authFetch.ts` attaches the auth header to every backend call.

## Environment

Not committed. Needed: `NEXT_PUBLIC_API_BASE_URL` (backend URL), `NEXT_PUBLIC_SUPABASE_URL` + `NEXT_PUBLIC_SUPABASE_ANON_KEY` for auth. Contact form: `RESEND_API_KEY`, `CONTACT_TO_EMAIL`, `CONTACT_FROM_EMAIL`.

## Notes

- Format list / integrations page reflect what's actually built vs. roadmap — `.idml` is the proven, tested path; the integrations grid (Slack, Zapier, GitHub, S3, REST API) is marked "coming soon" since none of it is wired up yet.
- The wordmark is split as `page` + `<span>birdy</span>` in JSX in a few components (Header, Footer, LoginForm, AppNavRail, product page) — a plain-text search for "pagebirdy" won't find it there.
