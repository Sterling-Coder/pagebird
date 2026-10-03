"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState, useEffect, useRef } from "react";

const PRODUCTS = [
  {
    title: "Document / PDF",
    desc: "PDF, IDML — layout-preserving translation.",
    href: "/platform/documents",
    live: true,
  },
  {
    title: "SRT / VTT Subtitles",
    desc: "Translate subtitle files, timing preserved.",
    href: "/platform/subtitles",
    live: false,
  },
  {
    title: "Image Translator",
    desc: "Translate text embedded in images.",
    href: "/platform/images",
    live: false,
  },
  {
    title: "Website Translator",
    desc: "Translate a live site's pages.",
    href: "/platform/websites",
    live: false,
  },
  {
    title: "YouTube Subtitles",
    desc: "Pull and translate a video's captions.",
    href: "/platform/youtube",
    live: false,
  },
];

export default function Header() {
  const pathname = usePathname();
  const [platformOpen, setPlatformOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setPlatformOpen(false);
      }
    }
    if (platformOpen) document.addEventListener("mousedown", handleClick);
    return () => document.removeEventListener("mousedown", handleClick);
  }, [platformOpen]);

  useEffect(() => {
    setPlatformOpen(false);
    setMobileOpen(false);
  }, [pathname]);

  return (
    <header className="sticky top-0 z-50 border-b border-pb-border bg-pb-bg/90 backdrop-blur-lg">
      <div className="mx-auto flex h-16 max-w-7xl items-center justify-between px-6 lg:px-10">
        {/* Logo */}
        <Link
          href="/"
          className="text-[22px] italic text-pb-text"
          style={{ fontFamily: "var(--font-fraunces), Georgia, serif" }}
        >
          page<span className="text-pb-accent">birdy</span>
        </Link>

        {/* Desktop nav */}
        <nav className="hidden items-center gap-1 md:flex">
          {/* Platform dropdown */}
          <div ref={dropdownRef} className="relative">
            <button
              type="button"
              onClick={() => setPlatformOpen(!platformOpen)}
              className={`font-pb-mono flex items-center gap-1.5 rounded-lg px-4 py-2 text-[13px] tracking-wide transition-colors ${
                platformOpen ? "bg-pb-bg-raised text-pb-text" : "text-pb-text-secondary hover:text-pb-text"
              }`}
            >
              Platform
              <svg
                width="10"
                height="10"
                viewBox="0 0 10 10"
                fill="none"
                stroke="currentColor"
                strokeWidth="1.5"
                className={`transition-transform ${platformOpen ? "rotate-180" : ""}`}
              >
                <path d="M2 4l3 3 3-3" />
              </svg>
            </button>

            {platformOpen ? (
              <div className="pb-glass absolute top-full left-1/2 mt-2 w-[520px] -translate-x-1/2 rounded-xl p-1.5 shadow-2xl">
                <div className="grid grid-cols-1 gap-0.5">
                  <Link
                    href="/platform"
                    className="group flex items-center gap-3 rounded-lg px-4 py-3 transition-colors hover:bg-white/[0.04]"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-pb-accent/10">
                      <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" className="h-4.5 w-4.5 text-pb-accent">
                        <rect x="3" y="3" width="18" height="18" rx="2" />
                        <path d="M3 9h18M9 21V9" />
                      </svg>
                    </div>
                    <div>
                      <span className="font-pb-mono text-[13px] font-bold text-pb-text">Platform overview</span>
                      <p className="mt-0.5 text-[12px] text-pb-text-muted">All products in one view.</p>
                    </div>
                  </Link>

                  <div className="mx-3 my-1 h-px bg-pb-border" />
                  <span className="font-pb-mono px-4 pt-2 pb-1 text-[10px] font-bold tracking-widest text-pb-text-muted uppercase">
                    Products
                  </span>

                  {PRODUCTS.map((p) => (
                    <Link
                      key={p.href}
                      href={p.href}
                      className="group flex items-center justify-between rounded-lg px-4 py-2.5 transition-colors hover:bg-white/[0.04]"
                    >
                      <div>
                        <span className={`text-[13px] font-semibold ${p.live ? "text-pb-text" : "text-pb-text-secondary"}`}>
                          {p.title}
                        </span>
                        <p className="mt-0.5 text-[12px] text-pb-text-muted">{p.desc}</p>
                      </div>
                      {!p.live ? (
                        <span className="font-pb-mono ml-4 shrink-0 rounded-full bg-pb-accent-dim px-2.5 py-0.5 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
                          Soon
                        </span>
                      ) : null}
                    </Link>
                  ))}
                </div>
              </div>
            ) : null}
          </div>

          <Link
            href="/pricing"
            className={`font-pb-mono rounded-lg px-4 py-2 text-[13px] tracking-wide transition-colors ${
              pathname === "/pricing" ? "bg-pb-bg-raised text-pb-text" : "text-pb-text-secondary hover:text-pb-text"
            }`}
          >
            Pricing
          </Link>
          <Link
            href="/contact"
            className={`font-pb-mono rounded-lg px-4 py-2 text-[13px] tracking-wide transition-colors ${
              pathname === "/contact" ? "bg-pb-bg-raised text-pb-text" : "text-pb-text-secondary hover:text-pb-text"
            }`}
          >
            Contact
          </Link>
        </nav>

        {/* Right side */}
        <div className="hidden items-center gap-4 md:flex">
          <Link
            href="/login"
            className="font-pb-mono text-[13px] tracking-wide text-pb-text-secondary transition-colors hover:text-pb-text"
          >
            Sign in
          </Link>
          <Link
            href="/login"
            className="font-pb-mono rounded-full bg-pb-accent px-5 py-2 text-[12px] font-bold tracking-widest text-pb-bg uppercase transition-all hover:brightness-110"
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
      {mobileOpen ? (
        <div className="border-t border-pb-border bg-pb-bg px-6 py-6 md:hidden">
          <div className="flex flex-col gap-1">
            <Link href="/platform" className="font-pb-mono rounded-lg px-3 py-2.5 text-[14px] text-pb-text hover:bg-pb-bg-raised">
              Platform
            </Link>
            {PRODUCTS.map((p) => (
              <Link
                key={p.href}
                href={p.href}
                className="flex items-center justify-between rounded-lg px-3 py-2 pl-6 text-[13px] text-pb-text-secondary hover:bg-pb-bg-raised hover:text-pb-text"
              >
                {p.title}
                {!p.live ? (
                  <span className="font-pb-mono rounded-full bg-pb-accent-dim px-2 py-0.5 text-[9px] font-bold tracking-widest text-pb-accent uppercase">
                    Soon
                  </span>
                ) : null}
              </Link>
            ))}
            <Link href="/pricing" className="font-pb-mono rounded-lg px-3 py-2.5 text-[14px] text-pb-text hover:bg-pb-bg-raised">
              Pricing
            </Link>
            <Link href="/contact" className="font-pb-mono rounded-lg px-3 py-2.5 text-[14px] text-pb-text hover:bg-pb-bg-raised">
              Contact
            </Link>
            <div className="mt-4 flex flex-col gap-3 border-t border-pb-border pt-4">
              <Link href="/login" className="font-pb-mono text-center text-[13px] text-pb-text-secondary">
                Sign in
              </Link>
              <Link href="/login" className="font-pb-mono rounded-full bg-pb-accent py-2.5 text-center text-[12px] font-bold tracking-widest text-pb-bg uppercase">
                Try free
              </Link>
            </div>
          </div>
        </div>
      ) : null}
    </header>
  );
}
