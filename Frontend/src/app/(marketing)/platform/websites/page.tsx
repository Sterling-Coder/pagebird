import Link from "next/link";
import ClosingBand from "@/components/ClosingBand";
import type { Metadata } from "next";
import type { ReactNode } from "react";
import DemoKeyframes from "@/components/websites/DemoKeyframes";
import LinkDemo from "@/components/websites/LinkDemo";
import ExtensionDemo from "@/components/websites/ExtensionDemo";

export const metadata: Metadata = {
  title: "Website Translator — Pagebirdy",
  description:
    "Two ways to translate the web: paste a public page link and get a translated, read-only copy, or use the Pagebirdy Chrome extension to translate any word, sentence or page while you browse.",
};

/* ── Palette ───────────────────────────────────────────────────────────── */
const C = {
  bg: "#0a0908",
  card: "#1d1c1a",
  panel: "#292826",
  line: "1px solid rgba(255,255,255,0.08)",
  text: "#f0ece3",
  secondary: "#a8a49a",
  muted: "#8a8478",
  coral: "#e08a6f",
  button: "#c86018",
  green: "#8fd14f",
  violet: "#a98bf0",
};

const CONTAINER = "mx-auto max-w-[1100px] px-5 sm:px-8 lg:px-14";

/* ── Content ───────────────────────────────────────────────────────────── */
const LINK_STEPS = [
  { title: "Paste one page", desc: "Open the Website agent in the app and paste the URL of a public English web page." },
  { title: "Pick a language", desc: "Choose the target language. The page is fetched, cleaned of scripts and translated in the background." },
  { title: "Review the copy", desc: "Open the translated, read-only copy. Edit any segment in the review view and rebuild it." },
];

const EXT_STEPS = [
  { title: "Select any text", desc: "Highlight a word or sentence on any site. The translation appears right beside it, or use the right-click menu." },
  { title: "Or translate the page", desc: "Click Translate this page. The visible text is rewritten in place and the layout stays as it is." },
  { title: "Flip back any time", desc: "Show original restores the page. Text that loads later is translated as it appears." },
];

const SAFETY = [
  "Only public internet addresses on ports 80 and 443 can be fetched. Localhost and private networks are refused.",
  "Every redirect is checked again before it is followed.",
  "All scripts are removed from the page before it is translated.",
  "The copy is served sandboxed: no scripts run and it has an opaque origin.",
  "Jobs are rate-limited per user and capped at a few at once.",
];

const KEPT = ["Brand names", "Prices", "Numbers", "URLs", "Emails"];

const LIMITS = [
  { title: "One page per job", desc: "It doesn't crawl a whole site or produce /fr/ or /de/ subfolders." },
  { title: "No login pages", desc: "Pages that need you to sign in can't be fetched." },
  { title: "No script-rendered text", desc: "If a page builds its text with JavaScript, there's nothing to translate. The job tells you why." },
];

const EXT_FEATURES = [
  { title: "Beside the selection", desc: "Select a word or sentence and the translation pops up next to it. Right-click works too." },
  { title: "Whole page, in place", desc: "Rewrites the visible text, keeps the layout, and follows content that loads later." },
  { title: "Right-to-left aware", desc: "Arabic, Hebrew and other RTL languages flip the page direction." },
  { title: "Small popup", desc: "Set your target language and turn the selection button on or off." },
  { title: "Works behind logins", desc: "It runs in your browser, so it reads the page you already have open." },
  { title: "Your Pagebirdy login", desc: "Signs in with your account. Numbers, links and emails come back unchanged." },
];

const COMPARE: { row: string; link: string; ext: string }[] = [
  { row: "Best for", link: "Sharing a translated copy of a public page", ext: "Reading anything while you browse" },
  { row: "You give it", link: "The URL of one public English page", ext: "Whatever is on your screen" },
  { row: "You get", link: "A translated, read-only copy you can review and edit", ext: "Translation beside your selection, or the page rewritten in place" },
  { row: "Runs on", link: "Pagebirdy, in the app", ext: "Your browser" },
  { row: "Pages behind a login", link: "No", ext: "Yes" },
  { row: "Text rendered by JavaScript", link: "No, and the job explains why", ext: "Yes, including content that loads later" },
  { row: "Availability", link: "Available now", ext: "Early access" },
];

const FAQ = [
  {
    q: "Can it translate my whole website?",
    a: "No. A website link job translates one public page. It doesn't crawl your site, create /fr/ or /de/ subfolders, or install as a CMS or WordPress plugin. For several pages, run one job per page.",
  },
  {
    q: "Why did my page fail to translate?",
    a: "The usual reasons are a page that needs a login, or a page that renders its text with JavaScript. Pagebirdy removes scripts and only works with the HTML the server sends, so in those cases there's no text to translate. The job explains which one it hit. The Chrome extension handles both, because it works on the page in your browser.",
  },
  {
    q: "Is it safe to paste any link?",
    a: "Pagebirdy only fetches public internet addresses on ports 80 and 443, never localhost or private networks, and re-checks every redirect. All scripts are removed, and the translated copy is served sandboxed with no scripts and an opaque origin. Jobs are rate-limited per user and capped at a few at once.",
  },
  {
    q: "What stays untranslated?",
    a: "Brand names, prices, numbers, URLs and email addresses are kept as they are. If anything else needs a fix, edit the segment in the review view and rebuild the copy.",
  },
  {
    q: "How do I get the Chrome extension?",
    a: "It's in early access and not on the Chrome Web Store yet. Ask for access through the contact page. Once installed, it signs in with your Pagebirdy account.",
  },
  {
    q: "Does the extension change the website itself?",
    a: "No. It only changes the text in your own browser tab, and Show original puts it back. The text it sends to Pagebirdy for translation isn't stored.",
  },
];

/* ── Small pieces ──────────────────────────────────────────────────────── */
function Label({ children, color = C.coral }: { children: ReactNode; color?: string }) {
  return (
    <div className="flex items-center gap-3">
      <span className="inline-block h-2 w-2" style={{ background: color }} />
      <span className="font-pb-mono text-[11px] font-bold tracking-widest uppercase" style={{ color }}>
        {children}
      </span>
    </div>
  );
}

function Pill({ children, color }: { children: ReactNode; color: string }) {
  return (
    <span
      className="font-pb-mono inline-flex items-center rounded-full px-2.5 py-0.5 text-[10px] font-bold tracking-widest uppercase"
      style={{ color, background: `${color}1a`, border: `1px solid ${color}40` }}
    >
      {children}
    </span>
  );
}

function PrimaryButton({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="font-pb-mono inline-flex items-center justify-center rounded-full px-6 py-3 text-[12px] font-bold tracking-widest text-white uppercase transition-[filter] hover:brightness-110"
      style={{ background: C.button }}
    >
      {children}
    </Link>
  );
}

function SecondaryButton({ href, children }: { href: string; children: ReactNode }) {
  return (
    <Link
      href={href}
      className="font-pb-mono inline-flex items-center justify-center rounded-full px-6 py-3 text-[12px] font-bold tracking-widest uppercase transition-colors hover:bg-white/5"
      style={{ color: C.text, border: "1px solid rgba(255,255,255,0.16)" }}
    >
      {children}
    </Link>
  );
}

function Steps({ steps, color }: { steps: { title: string; desc: string }[]; color: string }) {
  return (
    <ol className="grid grid-cols-1 gap-3 md:grid-cols-3">
      {steps.map((s, i) => (
        <li key={s.title} className="rounded-[24px] p-6" style={{ background: C.card, border: C.line }}>
          <span className="font-pb-mono text-[11px] font-bold tracking-widest" style={{ color }}>
            {String(i + 1).padStart(2, "0")}
          </span>
          <h3 className="mt-3 text-[16px] font-semibold" style={{ color: C.text }}>{s.title}</h3>
          <p className="mt-2 text-[14px] leading-relaxed" style={{ color: C.secondary }}>{s.desc}</p>
        </li>
      ))}
    </ol>
  );
}

/* ── Page ──────────────────────────────────────────────────────────────── */
export default function WebsitesPage() {
  return (
    <div style={{ background: C.bg, color: C.text }} className="overflow-x-clip">
      <DemoKeyframes />

      {/* ─── HERO ─── */}
      <section className={`${CONTAINER} pt-32 pb-16 lg:pt-44 lg:pb-24`}>
        <div className="pb-enter-label">
          <Label>Website translator</Label>
        </div>
        <h1 className="pb-enter pb-enter-delay-1 pb-stencil mt-8 max-w-[14ch]" style={{ fontSize: "clamp(2.5rem, 6vw, 4.75rem)" }}>
          Translate the web, two ways.
        </h1>
        <p className="pb-enter pb-enter-delay-2 mt-8 max-w-[600px] text-[16px] leading-relaxed lg:text-[18px]" style={{ color: C.secondary }}>
          Paste a link to get a translated copy of a public page you can review and share. Or read any site in your
          language as you browse, with the Pagebirdy Chrome extension.
        </p>

        <div className="pb-enter pb-enter-delay-3 mt-12 grid grid-cols-1 gap-3 md:grid-cols-2">
          {[
            {
              href: "#link",
              color: C.green,
              tag: "Available now",
              title: "Website link",
              desc: "One public page in, a translated read-only copy out. Runs in the Pagebirdy app.",
            },
            {
              href: "#extension",
              color: C.violet,
              tag: "Early access",
              title: "Chrome extension",
              desc: "Translate a selection or the whole page you're reading, in place, in your browser.",
            },
          ].map((p) => (
            <a
              key={p.href}
              href={p.href}
              className="group flex flex-col rounded-[24px] p-6 transition-colors hover:bg-[#232220]"
              style={{ background: C.card, border: C.line }}
            >
              <div className="flex items-center justify-between gap-3">
                <span className="inline-block h-2.5 w-2.5 rounded-sm" style={{ background: p.color }} />
                <Pill color={p.color}>{p.tag}</Pill>
              </div>
              <h2 className="mt-6 text-[20px] font-semibold" style={{ color: C.text }}>{p.title}</h2>
              <p className="mt-2 text-[14px] leading-relaxed" style={{ color: C.secondary }}>{p.desc}</p>
              <span className="font-pb-mono mt-6 text-[11px] font-bold tracking-widest uppercase" style={{ color: p.color }}>
                See how it works <span className="inline-block transition-transform group-hover:translate-y-0.5">↓</span>
              </span>
            </a>
          ))}
        </div>
      </section>

      {/* ─── WEBSITE LINK ─── */}
      <section id="link" className="scroll-mt-24" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <div className={`${CONTAINER} py-20 lg:py-28`}>
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-[5fr_6fr] lg:gap-14">
            <div className="min-w-0">
              <div className="flex flex-wrap items-center gap-3">
                <Label color={C.green}>Website link</Label>
                <Pill color={C.green}>In the app</Pill>
              </div>
              <h2 className="mt-6 text-[32px] leading-[1.1] font-semibold tracking-tight md:text-[40px]" style={{ color: C.text }}>
                Paste a link. Get a translated copy of the page.
              </h2>
              <p className="mt-5 text-[15px] leading-relaxed" style={{ color: C.secondary }}>
                Give the Website agent the URL of one public English web page and pick a language. Pagebirdy fetches it,
                strips every script, translates the text and hands back a read-only copy with the same markup and styles.
              </p>
              <div className="mt-6 flex flex-wrap gap-2">
                <span className="font-pb-mono text-[11px] tracking-widest uppercase self-center mr-1" style={{ color: C.muted }}>
                  Kept as is
                </span>
                {KEPT.map((k) => (
                  <span
                    key={k}
                    className="rounded-full px-3 py-1 text-[12px]"
                    style={{ background: C.panel, color: C.text, border: C.line }}
                  >
                    {k}
                  </span>
                ))}
              </div>
              <div className="mt-8 flex flex-wrap gap-3">
                <PrimaryButton href="/login">Translate a page</PrimaryButton>
              </div>
            </div>
            <div className="min-w-0">
              <LinkDemo />
            </div>
          </div>

          <div className="mt-16">
            <Steps steps={LINK_STEPS} color={C.green} />
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 lg:grid-cols-[3fr_2fr]">
            <div className="rounded-[24px] p-6 sm:p-8" style={{ background: C.card, border: C.line }}>
              <h3 className="text-[18px] font-semibold" style={{ color: C.text }}>Fetched safely, served sandboxed</h3>
              <p className="mt-2 text-[14px]" style={{ color: C.secondary }}>
                Pasting a link means Pagebirdy visits it for you, so the fetcher is locked down.
              </p>
              <ul className="mt-6 flex flex-col gap-3">
                {SAFETY.map((s) => (
                  <li key={s} className="flex gap-3 rounded-[14px] p-3.5 text-[14px] leading-relaxed" style={{ background: C.panel, color: C.text }}>
                    <span className="font-pb-mono shrink-0 text-[12px]" style={{ color: C.green }}>✓</span>
                    <span>{s}</span>
                  </li>
                ))}
              </ul>
            </div>
            <div className="rounded-[24px] p-6 sm:p-8" style={{ background: C.card, border: C.line }}>
              <h3 className="text-[18px] font-semibold" style={{ color: C.text }}>What it won&rsquo;t do</h3>
              <p className="mt-2 text-[14px]" style={{ color: C.secondary }}>
                It translates one page you can link to. Not a site, and not a plugin.
              </p>
              <ul className="mt-6 flex flex-col gap-3">
                {LIMITS.map((l) => (
                  <li key={l.title} className="rounded-[14px] p-3.5" style={{ background: C.panel }}>
                    <span className="block text-[14px] font-semibold" style={{ color: C.text }}>{l.title}</span>
                    <span className="mt-1 block text-[13px] leading-relaxed" style={{ color: C.secondary }}>{l.desc}</span>
                  </li>
                ))}
              </ul>
              <p className="mt-5 text-[13px] leading-relaxed" style={{ color: C.muted }}>
                Need a logged-in or script-heavy page? The Chrome extension reads it in your browser.
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* ─── CHROME EXTENSION ─── */}
      <section id="extension" className="scroll-mt-24" style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <div className={`${CONTAINER} py-20 lg:py-28`}>
          <div className="grid grid-cols-1 items-center gap-10 lg:grid-cols-[6fr_5fr] lg:gap-14">
            <div className="order-2 min-w-0 lg:order-1">
              <ExtensionDemo />
            </div>
            <div className="order-1 min-w-0 lg:order-2">
              <div className="flex flex-wrap items-center gap-3">
                <Label color={C.violet}>Chrome extension</Label>
                <Pill color={C.violet}>Early access</Pill>
              </div>
              <h2 className="mt-6 text-[32px] leading-[1.1] font-semibold tracking-tight md:text-[40px]" style={{ color: C.text }}>
                Read any site in your language, as you browse.
              </h2>
              <p className="mt-5 text-[15px] leading-relaxed" style={{ color: C.secondary }}>
                Select a word or a sentence and the translation appears beside it. Or translate the whole page in place
                and switch back with one click. It works on pages behind a login too, because it runs in your browser.
              </p>
              <p className="mt-4 text-[13px] leading-relaxed" style={{ color: C.muted }}>
                Not on the Chrome Web Store yet. Early-access users install it directly and sign in with their Pagebirdy
                account.
              </p>
              <div className="mt-8 flex flex-wrap gap-3">
                <PrimaryButton href="/contact">Get early access</PrimaryButton>
              </div>
            </div>
          </div>

          <div className="mt-16">
            <Steps steps={EXT_STEPS} color={C.violet} />
          </div>

          <div className="mt-3 grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {EXT_FEATURES.map((f) => (
              <div key={f.title} className="rounded-[24px] p-6" style={{ background: C.card, border: C.line }}>
                <span className="inline-block h-1.5 w-1.5" style={{ background: C.violet }} />
                <h3 className="mt-4 text-[15px] font-semibold" style={{ color: C.text }}>{f.title}</h3>
                <p className="mt-2 text-[14px] leading-relaxed" style={{ color: C.secondary }}>{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── COMPARISON ─── */}
      <section style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <div className={`${CONTAINER} py-20 lg:py-28`}>
          <Label>Which one?</Label>
          <h2 className="mt-6 max-w-[640px] text-[32px] leading-[1.1] font-semibold tracking-tight md:text-[40px]" style={{ color: C.text }}>
            Share a translated page, or read anything while browsing.
          </h2>

          {/* Desktop: table */}
          <div className="mt-12 hidden overflow-hidden rounded-[24px] md:block" style={{ background: C.card, border: C.line }}>
            <table className="w-full table-fixed text-left">
              <thead>
                <tr>
                  <th className="w-[26%] p-6" />
                  <th className="p-6 align-bottom">
                    <span className="flex items-center gap-2 text-[16px] font-semibold" style={{ color: C.text }}>
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: C.green }} /> Website link
                    </span>
                  </th>
                  <th className="p-6 align-bottom">
                    <span className="flex items-center gap-2 text-[16px] font-semibold" style={{ color: C.text }}>
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: C.violet }} /> Chrome extension
                    </span>
                  </th>
                </tr>
              </thead>
              <tbody>
                {COMPARE.map((r) => (
                  <tr key={r.row} style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
                    <th scope="row" className="font-pb-mono p-6 py-4 text-[11px] font-bold tracking-widest uppercase" style={{ color: C.muted }}>
                      {r.row}
                    </th>
                    <td className="p-6 py-4 text-[14px] leading-relaxed" style={{ color: C.text }}>{r.link}</td>
                    <td className="p-6 py-4 text-[14px] leading-relaxed" style={{ color: C.text }}>{r.ext}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Mobile: two cards */}
          <div className="mt-10 grid grid-cols-1 gap-3 md:hidden">
            {[
              { name: "Website link", color: C.green, key: "link" as const },
              { name: "Chrome extension", color: C.violet, key: "ext" as const },
            ].map((col) => (
              <div key={col.key} className="rounded-[24px] p-6" style={{ background: C.card, border: C.line }}>
                <span className="flex items-center gap-2 text-[17px] font-semibold" style={{ color: C.text }}>
                  <span className="h-2.5 w-2.5 rounded-sm" style={{ background: col.color }} /> {col.name}
                </span>
                <dl className="mt-4 flex flex-col gap-3">
                  {COMPARE.map((r) => (
                    <div key={r.row} className="rounded-[14px] p-3.5" style={{ background: C.panel }}>
                      <dt className="font-pb-mono text-[10px] font-bold tracking-widest uppercase" style={{ color: C.muted }}>{r.row}</dt>
                      <dd className="mt-1 text-[14px] leading-relaxed" style={{ color: C.text }}>{r[col.key]}</dd>
                    </div>
                  ))}
                </dl>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ─── FAQ ─── */}
      <section style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <div className={`${CONTAINER} grid grid-cols-1 gap-10 py-20 lg:grid-cols-[1fr_2fr] lg:py-28`}>
          <div>
            <Label>FAQ</Label>
            <h2 className="mt-6 text-[32px] leading-[1.1] font-semibold tracking-tight md:text-[40px]" style={{ color: C.text }}>
              Questions, answered.
            </h2>
          </div>
          <div className="flex flex-col gap-3">
            {FAQ.map((f) => (
              <details key={f.q} className="group rounded-[24px] p-5 sm:p-6" style={{ background: C.card, border: C.line }}>
                <summary className="flex cursor-pointer list-none items-start justify-between gap-4 text-[16px] font-semibold [&::-webkit-details-marker]:hidden" style={{ color: C.text }}>
                  <span>{f.q}</span>
                  <span
                    aria-hidden="true"
                    className="font-pb-mono mt-0.5 shrink-0 text-[16px] transition-transform group-open:rotate-45"
                    style={{ color: C.coral }}
                  >
                    +
                  </span>
                </summary>
                <p className="mt-3 text-[14px] leading-relaxed" style={{ color: C.secondary }}>{f.a}</p>
              </details>
            ))}
          </div>
        </div>
      </section>

      {/* ─── CTA ─── */}
      <section style={{ borderTop: "1px solid rgba(255,255,255,0.06)" }}>
        <div className={`${CONTAINER} py-20 lg:py-28`}>
          <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
            <div className="flex flex-col rounded-[24px] p-6 sm:p-8" style={{ background: C.card, border: C.line }}>
              <Label color={C.green}>Website link</Label>
              <h2 className="mt-6 text-[26px] leading-[1.15] font-semibold tracking-tight" style={{ color: C.text }}>
                Translate a public page now.
              </h2>
              <p className="mt-3 flex-1 text-[14px] leading-relaxed" style={{ color: C.secondary }}>
                Sign in, open the Website agent and paste a link.
              </p>
              <div className="mt-8">
                <PrimaryButton href="/login">Translate a page</PrimaryButton>
              </div>
            </div>
            <div className="flex flex-col rounded-[24px] p-6 sm:p-8" style={{ background: C.card, border: C.line }}>
              <Label color={C.violet}>Chrome extension</Label>
              <h2 className="mt-6 text-[26px] leading-[1.15] font-semibold tracking-tight" style={{ color: C.text }}>
                Read the web in your language.
              </h2>
              <p className="mt-3 flex-1 text-[14px] leading-relaxed" style={{ color: C.secondary }}>
                The extension is in early access. Tell us you&rsquo;d like to try it.
              </p>
              <div className="mt-8">
                <SecondaryButton href="/contact">Get early access</SecondaryButton>
              </div>
            </div>
          </div>
        </div>
      </section>
      <ClosingBand
        color="#4f8a3a"
        title={<>Any page, any language.<br />Paste a link to start.</>}
        sub="Website links work today in the app. The Chrome extension is in early access."
        cta="Translate a page"
        href="/login"
      />
    </div>
  );
}
