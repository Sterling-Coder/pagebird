# Pagebirdy Translate (Chrome extension)

Manifest V3, plain JavaScript, no build step.

- **Select text** on any page, click the 文 button (or right-click, "Translate selection"), and the translation appears beside it.
- **Translate this page** rewrites the visible text in place (toolbar popup or right-click). "Show original" restores it. New content that loads later is translated too.
- **Settings** (toolbar popup): target language, and whether the selection button shows.

## Load it

1. Edit `config.js`: `API_BASE_URL`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `APP_URL`. These are the same public values the web app uses (`NEXT_PUBLIC_*`). Add your deployed API origin to `host_permissions` in `manifest.json` if it is not `localhost:8000`, `*.up.railway.app` or `*.supabase.co`.
2. Chrome, `chrome://extensions`, turn on Developer mode, **Load unpacked**, pick this folder.
3. Click the toolbar icon and sign in with your Pagebirdy account.

## How it works

- `background.js` (service worker) holds the Supabase session in `chrome.storage.local`, refreshes it, and makes every API call. Pages never see the token.
- Text goes to `POST /api/translate/text` (backend `pagebirdy/text_api.py`): authenticated, trial-checked, rate limited per user (`PAGEBIRDY_TEXT_RATE_LIMIT`, default 120 requests per 10 minutes), at most 100 texts per request. Nothing is stored. Numbers, URLs, emails and `{placeholders}` come back unchanged.
- `content.js` draws its UI in a closed shadow root, skips `script`, `style`, `code`, `pre`, form fields, `contenteditable` and anything marked `translate="no"` / `.notranslate`, and translates on-screen text first.

## Not done yet

- Not published to the Chrome Web Store.
- Not tested in a real browser session in this repo's CI; load it unpacked and try a few sites first.
- Pages that render text inside closed shadow roots or cross-origin iframes are not reached.
