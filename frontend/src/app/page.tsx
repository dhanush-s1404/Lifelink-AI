import Link from "next/link";

export default function Home() {
  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-8 p-8 text-center">
      <div>
        <h1 className="text-4xl font-bold tracking-tight text-slate-900">LifeLink AI</h1>
        <p className="mt-4 max-w-xl text-lg text-slate-600">
          The secure digital emergency vault and digital legacy platform. Store the
          information your family needs during an emergency — and control exactly who can
          see it, and when.
        </p>
      </div>
      <div className="flex gap-4">
        <Link
          href="/auth/login"
          className="rounded-lg bg-brand-600 px-5 py-2.5 text-sm font-medium text-white transition hover:bg-brand-700"
        >
          Sign in
        </Link>
        <Link
          href="/auth/register"
          className="rounded-lg border border-slate-300 px-5 py-2.5 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
        >
          Create account
        </Link>
      </div>
      <p className="text-xs text-slate-400">
        Foundation milestone — the full platform is under active development.
      </p>
    </main>
  );
}
