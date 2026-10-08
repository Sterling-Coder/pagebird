// Service worker: owns the session and every call to the Pagebirdy API, so
// the token never reaches a web page and page CORS never applies.
import { CONFIG } from "./config.js";
import { DEFAULT_SETTINGS } from "./languages.js";

const SESSION_KEY = "session";
const SETTINGS_KEY = "settings";

async function getSession() {
  return (await chrome.storage.local.get(SESSION_KEY))[SESSION_KEY] || null;
}

async function getSettings() {
  return { ...DEFAULT_SETTINGS, ...((await chrome.storage.local.get(SETTINGS_KEY))[SETTINGS_KEY] || {}) };
}

async function saveSession(body, email) {
  const session = {
    access_token: body.access_token,
    refresh_token: body.refresh_token,
    expires_at: Date.now() + Math.max(30, (body.expires_in || 3600) - 30) * 1000,
    email: email || body.user?.email || "",
  };
  await chrome.storage.local.set({ [SESSION_KEY]: session });
  return session;
}

async function supabaseToken(grant, payload) {
  const res = await fetch(`${CONFIG.SUPABASE_URL}/auth/v1/token?grant_type=${grant}`, {
    method: "POST",
    headers: { apikey: CONFIG.SUPABASE_ANON_KEY, "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  const body = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(body.error_description || body.msg || "Sign-in failed");
  return body;
}

async function signIn(email, password) {
  const body = await supabaseToken("password", { email, password });
  return saveSession(body, email);
}

async function signOut() {
  await chrome.storage.local.remove(SESSION_KEY);
}

async function accessToken() {
  let session = await getSession();
  if (!session) throw Object.assign(new Error("Sign in to Pagebirdy first."), { code: "signed_out" });
  if (Date.now() >= session.expires_at) {
    try {
      session = await saveSession(await supabaseToken("refresh_token",
        { refresh_token: session.refresh_token }), session.email);
    } catch {
      await signOut();
      throw Object.assign(new Error("Your session expired. Sign in again."), { code: "signed_out" });
    }
  }
  return session.access_token;
}

async function translate(texts, context) {
  const { lang } = await getSettings();
  const res = await fetch(`${CONFIG.API_BASE_URL}/api/translate/text`, {
    method: "POST",
    headers: { Authorization: `Bearer ${await accessToken()}`, "Content-Type": "application/json" },
    body: JSON.stringify({ texts, target_lang: lang, context: context || "" }),
  });
  const body = await res.json().catch(() => ({}));
  if (res.status === 401) {
    await signOut();
    throw Object.assign(new Error("Your session expired. Sign in again."), { code: "signed_out" });
  }
  if (!res.ok) {
    throw Object.assign(new Error(typeof body.detail === "string" ? body.detail : "Translation failed."),
      { code: res.status === 402 ? "trial_ended" : res.status === 429 ? "rate_limited" : "failed" });
  }
  return { translations: body.translations, direction: body.direction, lang: body.target_lang };
}

async function languages() {
  const res = await fetch(`${CONFIG.API_BASE_URL}/api/languages`);
  if (!res.ok) throw new Error("languages unavailable");
  const body = await res.json();
  return body.languages.map((l) => ({ code: l.code, name: l.name }));
}

const HANDLERS = {
  translate: (m) => translate(m.texts, m.context),
  signIn: (m) => signIn(m.email, m.password).then((s) => ({ email: s.email })),
  signOut: () => signOut().then(() => ({})),
  session: () => getSession().then((s) => ({ email: s ? s.email : null })),
  languages: () => languages().then((list) => ({ languages: list })),
};

chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
  const handler = HANDLERS[message && message.type];
  if (!handler) return false;
  handler(message)
    .then((data) => sendResponse({ ok: true, ...data }))
    .catch((e) => sendResponse({ ok: false, error: e.message, code: e.code || "failed" }));
  return true; // answered asynchronously
});

chrome.runtime.onInstalled.addListener(() => {
  chrome.contextMenus.create({ id: "pb-selection", title: "Translate selection with Pagebirdy", contexts: ["selection"] });
  chrome.contextMenus.create({ id: "pb-page", title: "Translate this page with Pagebirdy", contexts: ["page"] });
});

chrome.contextMenus.onClicked.addListener((info, tab) => {
  if (!tab || tab.id === undefined) return;
  chrome.tabs.sendMessage(tab.id, { type: info.menuItemId === "pb-page" ? "page-translate" : "selection-translate" })
    .catch(() => {});
});
