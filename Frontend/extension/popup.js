import { CONFIG } from "./config.js";
import { DEFAULT_SETTINGS, FALLBACK_LANGUAGES } from "./languages.js";

const $ = (id) => document.getElementById(id);
const send = (message) => chrome.runtime.sendMessage(message);

function say(text, isError = false) {
  $("msg").textContent = text || "";
  $("msg").className = isError ? "err" : "";
}

async function loadSettings() {
  const { settings } = await chrome.storage.local.get("settings");
  return { ...DEFAULT_SETTINGS, ...(settings || {}) };
}

async function saveSettings(patch) {
  await chrome.storage.local.set({ settings: { ...(await loadSettings()), ...patch } });
}

async function activeTab() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  return tab;
}

async function pageState() {
  const tab = await activeTab();
  try {
    const res = await chrome.tabs.sendMessage(tab.id, { type: "page-status" });
    return !!(res && res.active);
  } catch {
    return false;   // no content script here (chrome:// pages, the web store, ...)
  }
}

async function fillLanguages(current) {
  let list = FALLBACK_LANGUAGES;
  const res = await send({ type: "languages" }).catch(() => null);
  if (res && res.ok && res.languages.length) list = res.languages;
  $("lang").replaceChildren(...list.map((l) => {
    const o = document.createElement("option");
    o.value = l.code; o.textContent = l.name;
    return o;
  }));
  $("lang").value = list.some((l) => l.code === current) ? current : list[0].code;
}

async function showSignedIn(email) {
  $("signedOut").hidden = true;
  $("signedIn").hidden = false;
  $("who").textContent = email;
  const settings = await loadSettings();
  await fillLanguages(settings.lang);
  await saveSettings({ lang: $("lang").value });
  $("selectionButton").checked = settings.selectionButton;
  $("showOriginal").hidden = !(await pageState());
}

function showSignedOut() {
  $("signedIn").hidden = true;
  $("signedOut").hidden = false;
  $("who").textContent = "";
}

$("loginForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  say("Signing in…");
  const res = await send({ type: "signIn", email: $("email").value.trim(), password: $("password").value });
  if (!res.ok) return say(res.error, true);
  $("password").value = "";
  say("");
  showSignedIn(res.email);
});

$("signOut").addEventListener("click", async () => { await send({ type: "signOut" }); say(""); showSignedOut(); });
$("lang").addEventListener("change", () => saveSettings({ lang: $("lang").value }));
$("selectionButton").addEventListener("change", () => saveSettings({ selectionButton: $("selectionButton").checked }));

$("translatePage").addEventListener("click", async () => {
  const tab = await activeTab();
  try {
    await chrome.tabs.sendMessage(tab.id, { type: "page-translate" });
    window.close();
  } catch {
    say("This page can't be translated (browser pages are off limits). Try a normal website.", true);
  }
});

$("showOriginal").addEventListener("click", async () => {
  const tab = await activeTab();
  await chrome.tabs.sendMessage(tab.id, { type: "page-revert" }).catch(() => {});
  window.close();
});

$("signupLink").href = `${CONFIG.APP_URL}/login`;

(async () => {
  const res = await send({ type: "session" });
  if (res && res.ok && res.email) showSignedIn(res.email); else showSignedOut();
})();
