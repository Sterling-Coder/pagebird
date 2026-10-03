"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useRef } from "react";

const PLATFORM_LEFT = [
  {
    n: "01",
    title: "Documents / PDF",
    desc: "Translate InDesign IDML and PDF with full layout preservation.",
    href: "/platform/documents",
    live: true,
  },
  {
    n: "02",
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files with every cue staying in sync.",
    href: "/platform/subtitles",
    live: false,
  },
  {
    n: "03",
    title: "Image Translator",
    desc: "Detect and translate text embedded in images.",
    href: "/platform/images",
    live: false,
  },
];

const PLATFORM_RIGHT = [
  {
    n: "04",
    title: "Website Translator",
    desc: "Translate every page of a live site automatically.",
    href: "/platform/websites",
    live: false,
  },
  {
    n: "05",
    title: "YouTube Subtitles",
    desc: "Pull captions from YouTube, translate, hand back an SRT.",
    href: "/platform/youtube",
    live: false,
  },
];

export default function Header() {
  const pathname = usePathname();
  const [platformOpen, setPlatformOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);

  function openPlatform() {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    setPlatformOpen(true);
  }

  function closePlatform() {
    closeTimer.current = setTimeout(() => setPlatformOpen(false), 120);
  }

  return (
    <header
      className="fixed top-0 left-0 right-0 z-50"
      style={{
        background: "#1a1815",
        borderBottom: "1px solid rgba(255,255,255,0.07)",
      }}
    >
      <div className="mx-auto flex h-[52px] max-w-7xl items-center justify-between px-6 lg:px-10">
        {/* Logo */}
        <Link
          href="/"
          className="text-[20px] italic text-pb-text"
          style={{ fontFamily: "var(--font-fraunces), Georgia, serif" }}
        >
          page<span className="text-pb-accent">birdy</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-0 md:flex">
          {/* Platform — hover to open */}
          <div
            className="relative"
            onMouseEnter={openPlatform}
            onMouseLeave={closePlatform}
          >
            <button
              type="button"
              className={`font-pb-mono flex items-center gap-1.5 rounded-md px-4 py-1.5 text-[13px] tracking-wide transition-colors ${
                platformOpen
                  ? "bg-white/[0.1] text-white"
                  : "text-pb-text-secondary hover:text-white"
              }`}
            >
              Platform
              <svg
                width="10" height="6" viewBox="0 0 10 6" fill="none"
                stroke="currentColor" strokeWidth="1.5"
                className={`transition-transform duration-200 ${platformOpen ? "rotate-180" : ""}`}
              >
                <path d="M1 1l4 4 4-4" />
              </svg>
            </button>

            {/* Dropdown — hover area covers the gap so it doesn't close */}
            {platformOpen && (
              <div
                className="absolute top-full left-0 pt-3"
                onMouseEnter={openPlatform}
                onMouseLeave={closePlatform}
              >
                <div
                  className="w-[640px] overflow-hidden"
                  style={{
                    borderRadius: "16px",
                    background: "rgba(18, 14, 10, 0.55)",
                    backdropFilter: "blur(48px) saturate(2)",
                    WebkitBackdropFilter: "blur(48px) saturate(2)",
                    border: "1px solid rgba(255,255,255,0.1)",
                    boxShadow: "0 32px 80px rgba(0,0,0,0.5), inset 0 1px 0 rgba(255,255,255,0.07)",
                  }}
                >
                  {/* Column headers */}
                  <div className="grid grid-cols-2 px-6 pt-5 pb-4" style={{ borderBottom: "1px solid rgba(255,255,255,0.07)" }}>
                    <span className="font-pb-mono text-[10px] font-bold tracking-[0.15em] text-pb-text-muted uppercase">
                      The Pagebirdy Platform
                    </span>
                    <span className="font-pb-mono text-[10px] font-bold tracking-[0.15em] text-pb-text-muted uppercase">
                      Products
                    </span>
                  </div>

                  {/* Two-column body */}
                  <div className="grid grid-cols-2">
                    {/* Left */}
                    <div className="px-4 py-4" style={{ borderRight: "1px solid rgba(255,255,255,0.07)" }}>
                      <Link
                        href="/platform"
                        className="group mb-3 flex flex-col gap-0.5 rounded-xl px-4 py-3 transition-colors hover:bg-white/[0.05]"
                      >
                        <span className="text-[17px] font-semibold text-white">Platform overview</span>
                        <span className="text-[13px] leading-snug text-pb-text-muted">
                          All products. One translation platform.
                        </span>
                      </Link>

                      <div className="mx-4 my-2" style={{ height: "1px", background: "rgba(255,255,255,0.06)" }} />

                      {PLATFORM_LEFT.map((p) => (
                        <Link
                          key={p.href}
                          href={p.href}
                          className="group flex items-start gap-4 rounded-xl px-4 py-3 transition-colors hover:bg-white/[0.05]"
                        >
                          <span className="font-pb-mono mt-0.5 shrink-0 text-[12px] text-pb-text-muted">{p.n}</span>
                          <div>
                            <span className="text-[15px] font-semibold text-white">{p.title}</span>
                            <p className="mt-0.5 text-[12px] leading-snug text-pb-text-muted">{p.desc}</p>
                          </div>
                        </Link>
                      ))}
                    </div>

                    {/* Right */}
                    <div className="px-4 py-4">
                      <div className="px-4 py-3 mb-1">
                        <span className="font-pb-mono text-[10px] font-bold tracking-[0.12em] text-pb-accent uppercase">
                          Live now
                        </span>
                      </div>
                      {PLATFORM_RIGHT.map((p) => (
                        <Link
                          key={p.href}
                          href={p.href}
                          className="group flex items-start gap-4 rounded-xl px-4 py-3 transition-colors hover:bg-white/[0.05]"
                        >
                          <span className="font-pb-mono mt-0.5 shrink-0 text-[12px] text-pb-text-muted">{p.n}</span>
                          <div>
                            <div className="flex items-center gap-2.5">
                              <span className="text-[15px] font-semibold text-white">{p.title}</span>
                              <span className="font-pb-mono rounded-full border border-white/15 px-2 py-0.5 text-[8px] tracking-widest text-pb-text-muted uppercase">
                                Soon
                              </span>
                            </div>
                            <p className="mt-0.5 text-[12px] leading-snug text-pb-text-muted">{p.desc}</p>
                          </div>
                        </Link>
                      ))}
                    </div>
                  </div>

                  {/* Footer row */}
                  <div
                    className="flex items-center justify-between px-8 py-3.5"
                    style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}
                  >
                    <span className="text-[12px] text-pb-text-muted">
                      Start with 5 free pages — no card required.
                    </span>
                    <Link
                      href="/login"
                      className="font-pb-mono rounded-full bg-pb-accent px-5 py-1.5 text-[11px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
                    >
                      Try free →
                    </Link>
                  </div>
                </div>
              </div>
            )}
          </div>

          <Link
            href="/pricing"
            className={`font-pb-mono rounded-md px-4 py-1.5 text-[13px] tracking-wide transition-colors ${
              pathname === "/pricing" ? "bg-white/[0.08] text-white" : "text-pb-text-secondary hover:text-white"
            }`}
          >
            Pricing
          </Link>
          <Link
            href="/contact"
            className={`font-pb-mono rounded-md px-4 py-1.5 text-[13px] tracking-wide transition-colors ${
              pathname === "/contact" ? "bg-white/[0.08] text-white" : "text-pb-text-secondary hover:text-white"
            }`}
          >
            Contact
          </Link>
        </nav>

        {/* Right */}
        <div className="hidden items-center gap-5 md:flex">
          <Link
            href="/login"
            className="font-pb-mono text-[13px] tracking-wide text-pb-text-secondary transition-colors hover:text-white"
          >
            Sign in
          </Link>
          <Link
            href="/login"
            className="font-pb-mono rounded-full bg-pb-accent px-5 py-1.5 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
          >
            Try free
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          type="button"
          onClick={() => setMobileOpen(!mobileOpen)}
          className="flex h-10 w-10 items-center justify-center text-pb-text md:hidden"
          aria-label="Toggle menu"
        >
          {mobileOpen ? (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
              <path d="M18 6L6 18M6 6l12 12" />
            </svg>
          ) : (
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" className="h-5 w-5">
              <path d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          )}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div
          className="px-6 py-6 md:hidden"
          style={{ borderTop: "1px solid rgba(255,255,255,0.07)", background: "#1a1815" }}
        >
          <div className="flex flex-col gap-1">
            <Link href="/platform" className="font-pb-mono px-3 py-2.5 text-[14px] text-pb-text-secondary hover:text-white">
              Platform overview
            </Link>
            {[...PLATFORM_LEFT, ...PLATFORM_RIGHT].map((p) => (
              <Link
                key={p.href}
                href={p.href}
                className="flex items-center gap-3 px-3 py-2 pl-5 text-[13px] text-pb-text-muted hover:text-white"
              >
                <span className="font-pb-mono text-[10px]">{p.n}</span>
                {p.title}
              </Link>
            ))}
            <div className="mt-3" style={{ height: "1px", background: "rgba(255,255,255,0.07)" }} />
            <Link href="/pricing" className="font-pb-mono px-3 py-2.5 text-[14px] text-pb-text-secondary hover:text-white">
              Pricing
            </Link>
            <Link href="/contact" className="font-pb-mono px-3 py-2.5 text-[14px] text-pb-text-secondary hover:text-white">
              Contact
            </Link>
            <div className="mt-4 flex flex-col gap-3 pt-4" style={{ borderTop: "1px solid rgba(255,255,255,0.07)" }}>
              <Link href="/login" className="font-pb-mono text-center text-[13px] text-pb-text-secondary">Sign in</Link>
              <Link href="/login" className="font-pb-mono rounded-full bg-pb-accent py-2.5 text-center text-[12px] font-bold tracking-widest text-pb-bg uppercase">
                Try free
              </Link>
            </div>
          </div>
        </div>
      )}
    </header>
  );
}
