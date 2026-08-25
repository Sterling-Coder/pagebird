type Product = {
  eyebrow: string;
  title: string;
  body: string;
  cta: string;
  href: string;
};

const PRODUCTS: Product[] = [
  {
    eyebrow: "Document Translator",
    title: "Upload a file. Get it back translated.",
    body: "DOC, PDF, INDD and IDML — 30+ languages, 95% accuracy, layout untouched.",
    cta: "See the translator",
    href: "/translator",
  },
  {
    eyebrow: "Browser Extension",
    title: "Highlight text. Translate it in place.",
    body: "Any webpage, any selection — replaced where it stood, no copy-paste.",
    cta: "See the extension",
    href: "/extension",
  },
];

function ProductCard({ product }: { product: Product }) {
  return (
    <div className="relative">
      <div className="absolute inset-0 translate-x-2 translate-y-2 bg-ink" aria-hidden="true" />
      <a
        href={product.href}
        className="relative z-10 block border-2 border-ink bg-paper p-6 transition-opacity hover:opacity-90"
      >
        <p className="font-mono text-[11px] uppercase tracking-widest text-red">
          {product.eyebrow}
        </p>
        <h3 className="mt-3 text-2xl font-black uppercase tracking-tight">
          {product.title}
        </h3>
        <p className="mt-3 text-sm leading-relaxed text-ink-soft">
          {product.body}
        </p>
        <p className="mt-6 font-mono text-[11px] uppercase tracking-widest">
          {product.cta} →
        </p>
      </a>
    </div>
  );
}

export function ProductTeaserGrid() {
  return (
    <section className="border-t border-rule">
      <div className="mx-auto max-w-6xl px-6 py-20 sm:px-8">
        <div className="grid gap-10 pt-2 sm:grid-cols-2 sm:gap-8">
          {PRODUCTS.map((product) => (
            <ProductCard key={product.href} product={product} />
          ))}
        </div>
      </div>
    </section>
  );
}
