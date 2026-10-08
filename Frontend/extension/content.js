// Selection translation and whole-page translation. All network calls go
// through the background service worker; this script only touches the DOM.
(() => {
  if (window.__pagebirdyLoaded) return;
  window.__pagebirdyLoaded = true;

  const MAX_SELECTION = 2000;
  const BATCH_ITEMS = 80;
  const BATCH_CHARS = 4000;
  const MAX_NODES = 4000;
  const SKIP_TAGS = new Set(["SCRIPT", "STYLE", "NOSCRIPT", "TEXTAREA", "INPUT", "SELECT", "OPTION",
    "CODE", "PRE", "KBD", "SAMP", "SVG", "MATH", "IFRAME", "CANVAS"]);

  const send = (message) => new Promise((resolve) => {
    try {
      chrome.runtime.sendMessage(message, (res) => resolve(res || { ok: false, error: "No answer from the extension.", code: "failed" }));
    } catch {
      resolve({ ok: false, error: "The extension was reloaded. Refresh this page.", code: "failed" });
    }
  });

  let settings = { lang: "es", selectionButton: true };
  chrome.storage.local.get("settings").then((r) => { settings = { ...settings, ...(r.settings || {}) }; });
  chrome.storage.onChanged.addListener((changes) => {
    if (changes.settings) settings = { ...settings, ...(changes.settings.newValue || {}) };
  });

  // ---- UI, in a shadow root so the page's CSS cannot touch it -----------------
  const host = document.createElement("div");
  host.style.cssText = "all:initial;position:absolute;top:0;left:0;z-index:2147483647;";
  const root = host.attachShadow({ mode: "closed" });
  root.innerHTML = `
    <style>
      .pb{font:13px/1.45 system-ui,-apple-system,Segoe UI,sans-serif;color:#15130f}
      .btn{position:absolute;width:30px;height:30px;border-radius:15px;border:0;cursor:pointer;
        background:#c86018;color:#fff;font:700 14px system-ui;box-shadow:0 2px 8px rgba(0,0,0,.3)}
      .card{position:absolute;width:300px;max-width:calc(100vw - 24px);background:#fffaf4;border:1px solid #e2d6c8;
        border-radius:10px;box-shadow:0 8px 28px rgba(0,0,0,.25);padding:12px 14px}
      .head{display:flex;justify-content:space-between;align-items:center;margin-bottom:6px;
        font-size:11px;letter-spacing:.06em;text-transform:uppercase;color:#8a6a4a}
      .x{border:0;background:none;cursor:pointer;font-size:16px;color:#8a6a4a;padding:0 2px}
      .txt{white-space:pre-wrap;word-break:break-word;max-height:240px;overflow:auto}
      .err{color:#a8321a}
      .row{margin-top:8px;display:flex;gap:8px}
      .row button{border:1px solid #d9c9b6;background:#fff;border-radius:6px;padding:3px 9px;cursor:pointer;font:12px system-ui}
      .toast{position:fixed;right:16px;bottom:16px;background:#15130f;color:#fff;border-radius:8px;
        padding:9px 13px;box-shadow:0 4px 18px rgba(0,0,0,.35)}
      .toast button{margin-left:10px;border:0;border-radius:5px;padding:2px 8px;cursor:pointer;font:12px system-ui}
    </style>
    <div class="pb"></div>`;
  const ui = root.querySelector(".pb");
  const mount = () => { if (!host.isConnected) document.documentElement.appendChild(host); };

  const clear = (cls) => ui.querySelectorAll(cls).forEach((n) => n.remove());
  const el = (tag, cls, text) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (text !== undefined) n.textContent = text;
    return n;
  };

  function place(node, rect, below = 8) {
    const left = Math.max(8, Math.min(window.scrollX + rect.left, window.scrollX + window.innerWidth - 316));
    node.style.left = `${left}px`;
    node.style.top = `${window.scrollY + rect.bottom + below}px`;
  }

  function selectionInfo() {
    const sel = window.getSelection();
    if (!sel || sel.isCollapsed || !sel.rangeCount) return null;
    const text = sel.toString().trim();
    if (!text || text.length > MAX_SELECTION) return null;
    const anchor = sel.anchorNode && (sel.anchorNode.nodeType === 1 ? sel.anchorNode : sel.anchorNode.parentElement);
    if (anchor && anchor.closest && anchor.closest("input,textarea,[contenteditable='true']")) return null;
    return { text, rect: sel.getRangeAt(0).getBoundingClientRect() };
  }

  function showButton(info) {
    mount(); clear(".btn"); clear(".card");
    const b = el("button", "btn", "文");
    b.title = "Translate with Pagebirdy";
    place(b, info.rect, 6);
    b.addEventListener("mousedown", (e) => e.preventDefault());
    b.addEventListener("click", () => showCard(info));
    ui.appendChild(b);
  }

  async function showCard(info) {
    mount(); clear(".btn"); clear(".card");
    const card = el("div", "card");
    const head = el("div", "head");
    head.appendChild(el("span", "", `Pagebirdy → ${settings.lang.toUpperCase()}`));
    const x = el("button", "x", "×");
    x.addEventListener("click", () => card.remove());
    head.appendChild(x);
    const body = el("div", "txt", "Translating…");
    card.append(head, body);
    place(card, info.rect);
    ui.appendChild(card);

    const res = await send({ type: "translate", texts: [info.text], context: document.title });
    if (!res.ok) {
      body.className = "txt err";
      body.textContent = res.error;
      return;
    }
    body.textContent = res.translations[0];
    body.dir = res.direction === "rtl" ? "rtl" : "ltr";
    const row = el("div", "row");
    const copy = el("button", "", "Copy");
    copy.addEventListener("click", () => navigator.clipboard.writeText(res.translations[0]).then(() => { copy.textContent = "Copied"; }));
    row.appendChild(copy);
    card.appendChild(row);
  }

  document.addEventListener("mouseup", (e) => {
    if (e.composedPath().includes(host) || !settings.selectionButton) return;
    setTimeout(() => {
      const info = selectionInfo();
      if (info) showButton(info); else { clear(".btn"); }
    }, 10);
  });
  document.addEventListener("mousedown", (e) => {
    if (!e.composedPath().includes(host)) { clear(".btn"); clear(".card"); }
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { clear(".btn"); clear(".card"); }
  });

  // ---- whole-page translation ---------------------------------------------------
  const originals = new Map();     // text node -> original value
  const written = new WeakMap();   // text node -> the value we wrote
  let pageActive = false;
  let observer = null;
  let progress = { done: 0, total: 0 };
  let priorDir = null;
  let originalTitle = null;
  let pending = new Set();
  let flushTimer = null;

  function eligible(node) {
    const parent = node.parentElement;
    if (!parent || SKIP_TAGS.has(parent.tagName)) return false;
    if (parent.closest("[translate='no'],.notranslate,[contenteditable='true'],pre,code")) return false;
    if (host.contains(node)) return false;
    if (written.get(node) === node.nodeValue) return false;
    return /\p{L}/u.test(node.nodeValue) && node.nodeValue.trim().length >= 2;
  }

  function collect(rootNode) {
    const out = [];
    const walker = document.createTreeWalker(rootNode, NodeFilter.SHOW_TEXT);
    for (let n = walker.nextNode(); n; n = walker.nextNode()) {
      if (eligible(n)) out.push(n);
      if (out.length >= MAX_NODES) break;
    }
    return out;
  }

  function inView(node) {
    const r = node.parentElement.getBoundingClientRect();
    return r.bottom > 0 && r.top < window.innerHeight * 2;
  }

  function toast(message, action) {
    mount(); clear(".toast");
    const t = el("div", "toast", message);
    if (action) {
      const b = el("button", "", action.label);
      b.addEventListener("click", action.run);
      t.appendChild(b);
    }
    ui.appendChild(t);
    return t;
  }

  async function translateNodes(nodes) {
    // What is on screen first, so the page changes where the reader is looking.
    nodes.sort((a, b) => Number(inView(b)) - Number(inView(a)));
    progress = { done: progress.done, total: progress.total + nodes.length };
    const batches = [];
    let cur = [], chars = 0;
    for (const n of nodes) {
      const len = n.nodeValue.trim().length;
      if (cur.length && (cur.length >= BATCH_ITEMS || chars + len > BATCH_CHARS)) { batches.push(cur); cur = []; chars = 0; }
      cur.push(n); chars += len;
    }
    if (cur.length) batches.push(cur);

    for (const batch of batches) {
      if (!pageActive) return;
      const sent = batch.map((n) => n.nodeValue);
      const res = await send({ type: "translate", texts: sent.map((s) => s.trim()), context: document.title });
      if (!res.ok) {
        pageActive = false;
        stopObserving();
        toast(res.error, { label: "Dismiss", run: () => clear(".toast") });
        return;
      }
      if (!pageActive) return;
      if (res.direction === "rtl" && priorDir === null) {
        priorDir = document.documentElement.getAttribute("dir") || "";
        document.documentElement.setAttribute("dir", "rtl");
      }
      batch.forEach((n, i) => {
        if (!n.isConnected || n.nodeValue !== sent[i]) return;   // the page changed it meanwhile
        const lead = sent[i].match(/^\s*/)[0];
        const trail = sent[i].match(/\s*$/)[0];
        if (!originals.has(n)) originals.set(n, sent[i]);
        const value = lead + res.translations[i].trim() + trail;
        written.set(n, value);
        n.nodeValue = value;
      });
      progress.done += batch.length;
      toast(`Translating… ${Math.round((100 * progress.done) / Math.max(1, progress.total))}%`);
    }
  }

  function startObserving() {
    observer = new MutationObserver((mutations) => {
      for (const m of mutations) {
        const targets = m.type === "characterData" ? [m.target] : [...m.addedNodes];
        for (const t of targets) {
          if (host.contains(t) || t === host) continue;
          if (t.nodeType === 3) { if (eligible(t)) pending.add(t); }
          else if (t.nodeType === 1) collect(t).forEach((n) => pending.add(n));
        }
      }
      if (pending.size && !flushTimer) {
        flushTimer = setTimeout(async () => {
          flushTimer = null;
          const nodes = [...pending].filter((n) => n.isConnected && eligible(n));
          pending = new Set();
          if (pageActive && nodes.length) await translateNodes(nodes);
        }, 800);
      }
    });
    observer.observe(document.body, { childList: true, characterData: true, subtree: true });
  }

  function stopObserving() {
    if (observer) observer.disconnect();
    observer = null; pending = new Set();
    if (flushTimer) { clearTimeout(flushTimer); flushTimer = null; }
  }

  async function translatePage() {
    if (pageActive) return;
    pageActive = true;
    progress = { done: 0, total: 0 };
    toast("Translating…");
    const nodes = collect(document.body);
    if (!nodes.length) { pageActive = false; toast("Nothing to translate on this page.", { label: "OK", run: () => clear(".toast") }); return; }
    startObserving();
    if (originalTitle === null && document.title.trim()) {
      originalTitle = document.title;
      const res = await send({ type: "translate", texts: [document.title], context: "" });
      if (res.ok) document.title = res.translations[0]; else originalTitle = null;
    }
    await translateNodes(nodes);
    if (pageActive) {
      toast("Page translated.", { label: "Show original", run: revertPage });
      setTimeout(() => { if (pageActive) clear(".toast"); }, 4000);
    }
  }

  function revertPage() {
    pageActive = false;
    stopObserving();
    for (const [node, value] of originals) if (node.isConnected) node.nodeValue = value;
    originals.clear();
    if (originalTitle !== null) { document.title = originalTitle; originalTitle = null; }
    if (priorDir !== null) {
      if (priorDir) document.documentElement.setAttribute("dir", priorDir); else document.documentElement.removeAttribute("dir");
      priorDir = null;
    }
    clear(".toast");
  }

  chrome.runtime.onMessage.addListener((message, _sender, sendResponse) => {
    switch (message && message.type) {
      case "page-translate": translatePage(); sendResponse({ ok: true }); break;
      case "page-revert": revertPage(); sendResponse({ ok: true }); break;
      case "page-status": sendResponse({ ok: true, active: pageActive || originals.size > 0, progress }); break;
      case "selection-translate": {
        const info = selectionInfo();
        if (info) showCard(info);
        sendResponse({ ok: true });
        break;
      }
      default: return false;
    }
    return false;
  });
})();
