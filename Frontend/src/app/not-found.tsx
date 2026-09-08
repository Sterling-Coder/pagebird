import Link from "next/link";

export default function NotFound() {
  return (
    <div className="mx-auto max-w-6xl px-6 py-32 text-center sm:px-8">
      <span className="font-mono text-[11px] uppercase tracking-widest text-red">
        404
      </span>
      <h1 className="mt-3 text-4xl font-black uppercase tracking-tight sm:text-5xl">
        This page didn&apos;t make it through translation.
      </h1>
      <p className="mx-auto mt-4 max-w-md text-ink-soft">
        The page you&apos;re looking for doesn&apos;t exist. It might have moved.
      </p>
      <Link
        href="/"
        className="mt-8 inline-block bg-ink px-6 py-3 font-mono text-[11px] uppercase tracking-widest text-paper transition-opacity hover:opacity-80"
      >
        Back to home →
      </Link>
    </div>
  );
}
