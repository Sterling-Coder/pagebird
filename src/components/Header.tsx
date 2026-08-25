"use client";

import { useEffect, useRef, useState } from "react";
import Link from "next/link";

export function Header() {
  const [productOpen, setProductOpen] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const productRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!productOpen) return;

    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") setProductOpen(false);
    }

    function handleClickOutside(event: MouseEvent) {
      if (!productRef.current?.contains(event.target as Node)) {
        setProductOpen(false);
      }
    }

    document.addEventListener("keydown", handleKeyDown);
    document.addEventListener("mousedown", handleClickOutside);
    return () => {
      document.removeEventListener("keydown", handleKeyDown);
      document.removeEventListener("mousedown", handleClickOutside);
    };
  }, [productOpen]);

  return (
    <>
      <div className="h-[3px] bg-ink" />
      <header className="relative border-b border-ink">
        <div className="mx-auto grid max-w-6xl grid-cols-3 items-center px-6 py-5 sm:px-8">
          <span />
          <Link
            href="/"
            className="justify-self-center text-center text-lg font-black uppercase tracking-tight sm:text-xl"
          >
            The Docly Dispatch
          </Link>

          <nav className="hidden justify-self-end items-center gap-6 font-mono text-[11px] uppercase tracking-widest sm:flex">
            <div ref={productRef} className="relative">
              <button
                type="button"
                onClick={() => setProductOpen((open) => !open)}
                aria-haspopup="true"
                aria-expanded={productOpen}
                className="text-ink-soft transition-colors hover:text-ink"
              >
                Product ▾
              </button>
              {productOpen ? (
                <div className="absolute right-0 top-full w-56 border border-ink bg-paper py-2 shadow-[4px_4px_0_rgba(0,0,0,1)]">
                  <Link
                    href="/translator"
                    className="block px-4 py-2 text-ink-soft hover:bg-paper-dim hover:text-ink"
                  >
                    Document Translator
                  </Link>
                  <Link
                    href="/extension"
                    className="block px-4 py-2 text-ink-soft hover:bg-paper-dim hover:text-ink"
                  >
                    Browser Extension
                  </Link>
                </div>
              ) : null}
            </div>
            <Link href="/pricing" className="text-ink-soft transition-colors hover:text-ink">
              Pricing
            </Link>
            <Link href="/about" className="text-ink-soft transition-colors hover:text-ink">
              About
            </Link>
          </nav>

          <button
            type="button"
            onClick={() => setMobileOpen((open) => !open)}
            className="justify-self-end font-mono text-[11px] uppercase tracking-widest text-ink-soft sm:hidden"
            aria-expanded={mobileOpen}
            aria-label="Toggle menu"
          >
            {mobileOpen ? "Close" : "Menu"}
          </button>
        </div>

        {mobileOpen ? (
          <nav className="flex flex-col gap-1 border-t border-rule px-6 py-4 font-mono text-[11px] uppercase tracking-widest sm:hidden">
            <Link href="/translator" className="py-2 text-ink-soft hover:text-ink">
              Document Translator
            </Link>
            <Link href="/extension" className="py-2 text-ink-soft hover:text-ink">
              Browser Extension
            </Link>
            <Link href="/pricing" className="py-2 text-ink-soft hover:text-ink">
              Pricing
            </Link>
            <Link href="/about" className="py-2 text-ink-soft hover:text-ink">
              About
            </Link>
          </nav>
        ) : null}
      </header>
    </>
  );
}
