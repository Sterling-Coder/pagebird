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
    jobs/          projects → folders → files, Finder-style file/links preview, translation editor

src/components/
  app/             product UI — upload pane, output pane, PDF preview/editor, links Finder view, logs panel
  (root)           marketing UI — header, footer, login form, contact form, demo video modal

src/lib/
  translate.ts     job/translate API calls (upload, download, links batch, job status)
  projects.ts      projects/folders CRUD
  supabase/        Supabase client + authenticated fetch helper
  pdfjs.ts         pdf.js loader for in-browser PDF rendering
  logs.ts          polls the backend's client-scoped activity log panel
```

## Key flows

- **Document upload** → `translate.ts`'s `translateDocument` → backend job → poll status → `SyncedDocumentPair` (source/target side-by-side, segment editing, undo) in `PdfPreview.tsx`.
- **Links batch upload** (`.ai`/`.eps`/`.pdf`/`.psd` folder) → `translateLinks` → `LinksPreview.tsx`, a Finder-style split view (file list left, full preview right) backed by per-file list/fetch endpoints rather than a whole-zip download.
- **Auth** — Supabase, cookie-based session via `@supabase/ssr`; `authFetch.ts` attaches the auth header to every backend call.

## Environment

Not committed. Needed: `NEXT_PUBLIC_API_BASE_URL` (backend URL), Supabase project URL + anon key for the client, service-role key server-side where used.

## Notes

- Format list / integrations page reflect what's actually built vs. roadmap — `.idml` is the proven, tested path; the integrations grid (Slack, Zapier, GitHub, S3, REST API) is marked "coming soon" since none of it is wired up yet.
- The wordmark is split as `page` + `<span>birdy</span>` in JSX in a few components (Header, Footer, LoginForm, AppNavRail, product page) — a plain-text search for "pagebirdy" won't find it there.
