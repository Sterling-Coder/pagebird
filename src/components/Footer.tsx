"use client";

const PRODUCT_LINKS = [
  { label: "Document Translator", href: "/translator" },
  { label: "Browser Extension", href: "/extension" },
  { label: "Pricing", href: "/pricing" },
];

const COMPANY_LINKS = [
  { label: "About", href: "/about" },
  { label: "Contact", href: "mailto:hello@docly.example" },
];

export function Footer() {
  return (
    <footer className="border-t border-ink">
      <div className="bg-ink text-paper">
        <div className="mx-auto max-w-6xl px-6 py-16 sm:px-8">
          <div className="grid gap-8 sm:grid-cols-[1.2fr_1fr] sm:items-end">
            <div>
              <span className="font-mono text-[11px] uppercase tracking-widest text-red">
                Still doing this by hand?
              </span>
              <h2 className="mt-3 text-3xl font-black uppercase leading-[1.05] tracking-tight sm:text-4xl">
                Get the next format
                <br />
                update before your
                <br />
                team asks for it.
              </h2>
            </div>

            <form
              onSubmit={(event) => event.preventDefault()}
              className="flex flex-col gap-3 sm:flex-row"
            >
              <input
                type="email"
                placeholder="you@company.com"
                aria-label="Email address"
                className="w-full border border-paper/30 bg-transparent px-4 py-3 text-sm text-paper placeholder:text-paper/50 outline-none focus-visible:border-paper sm:flex-1"
              />
              <button
                type="submit"
                className="whitespace-nowrap bg-red px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-90"
              >
                Notify me →
              </button>
            </form>
          </div>
        </div>
      </div>

      <div className="mx-auto max-w-6xl px-6 py-10 sm:px-8">
        <div className="grid gap-8 sm:grid-cols-[1.3fr_1fr_1fr_1fr]">
          <div>
            <span className="text-lg font-black uppercase tracking-tight">
              Docly
            </span>
            <p className="mt-3 max-w-xs text-sm leading-relaxed text-ink-soft">
              Translation that reads the layout first, so nothing breaks
              between the languages.
            </p>
          </div>

          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
              Product
            </p>
            <ul className="mt-4 space-y-2">
              {PRODUCT_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-ink-soft transition-colors hover:text-ink"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
              Company
            </p>
            <ul className="mt-4 space-y-2">
              {COMPANY_LINKS.map((link) => (
                <li key={link.href}>
                  <a
                    href={link.href}
                    className="text-sm text-ink-soft transition-colors hover:text-ink"
                  >
                    {link.label}
                  </a>
                </li>
              ))}
            </ul>
          </div>

          <div>
            <p className="font-mono text-[11px] uppercase tracking-widest text-muted">
              Social
            </p>
            <ul className="mt-4 space-y-2">
              <li>
                <a
                  href="https://x.com"
                  className="text-sm text-ink-soft transition-colors hover:text-ink"
                >
                  X / Twitter
                </a>
              </li>
              <li>
                <a
                  href="https://linkedin.com"
                  className="text-sm text-ink-soft transition-colors hover:text-ink"
                >
                  LinkedIn
                </a>
              </li>
              <li>
                <a
                  href="https://github.com"
                  className="text-sm text-ink-soft transition-colors hover:text-ink"
                >
                  GitHub
                </a>
              </li>
            </ul>
          </div>
        </div>

        <div className="mt-10 border-t border-rule pt-6">
          <span className="font-mono text-[11px] uppercase tracking-widest text-muted">
            © 2026 Docly
          </span>
        </div>
      </div>

      <div className="overflow-hidden border-t border-rule py-2 sm:py-0" aria-hidden="true">
        <p
          className="select-none whitespace-nowrap text-center text-[22vw] font-black uppercase leading-none tracking-tighter text-transparent sm:-mb-[3vw] sm:mt-[-1.5vw]"
          style={{ WebkitTextStroke: "1.5px var(--ink)" }}
        >
          Docly
        </p>
      </div>
    </footer>
  );
}
