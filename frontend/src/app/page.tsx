import Link from "next/link";
import {
  BookLock,
  HeartHandshake,
  ShieldCheck,
  Sparkles,
  Siren,
  KeyRound,
  LockKeyhole,
  ArrowRight,
  CheckCircle2,
} from "lucide-react";

const features = [
  {
    icon: BookLock,
    title: "Digital vault",
    description:
      "Store the documents and details your family needs most — wills, insurance, accounts, medical records — encrypted and organized.",
  },
  {
    icon: HeartHandshake,
    title: "Trusted contacts",
    description:
      "Choose the people you trust. Vault access requires mutual consent, so only you and your contacts decide who sees what.",
  },
  {
    icon: Siren,
    title: "Emergency access",
    description:
      "If you can't confirm you're okay within a grace period, your trusted contacts are granted read-only access to the vault.",
  },
  {
    icon: Sparkles,
    title: "AI assistant",
    description:
      "Ask LifeLink AI to surface the right information at the right moment, always scoped to what you have access to.",
  },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4" aria-label="Main">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-600">
              <ShieldCheck className="h-5 w-5 text-white" aria-hidden="true" />
            </span>
            <span className="text-lg font-semibold tracking-tight text-slate-900">LifeLink AI</span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100"
            >
              Sign in
            </Link>
            <Link
              href="/auth/register"
              className="rounded-lg bg-brand-600 px-4 py-2 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
            >
              Create account
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="mx-auto max-w-6xl px-6 pb-20 pt-20 sm:pt-28">
          <div className="mx-auto max-w-3xl text-center">
            <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-brand-50 px-3 py-1 text-xs font-medium text-brand-800">
              <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
              End-to-end encrypted
            </span>
            <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 sm:text-5xl">
              The emergency vault your family can count on.
            </h1>
            <p className="mt-5 text-lg leading-relaxed text-slate-600">
              LifeLink AI keeps your most important information secure, organized, and
              reachable by the people you trust — only when it matters most.
            </p>
            <div className="mt-8 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/auth/register"
                className="inline-flex w-full items-center justify-center gap-2 rounded-lg bg-brand-600 px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700 sm:w-auto"
              >
                Get started
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
              <Link
                href="/auth/login"
                className="inline-flex w-full items-center justify-center rounded-lg border border-slate-300 bg-white px-6 py-3 text-sm font-medium text-slate-700 transition hover:bg-slate-50 sm:w-auto"
              >
                Sign in to your vault
              </Link>
            </div>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-50">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
                >
                  <span className="flex h-10 w-10 items-center justify-center rounded-lg bg-brand-50">
                    <feature.icon className="h-5 w-5 text-brand-700" aria-hidden="true" />
                  </span>
                  <h2 className="mt-4 text-base font-semibold text-slate-900">{feature.title}</h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600">{feature.description}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-20">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900">
              Built around consent and control
            </h2>
            <p className="mt-4 text-lg text-slate-600">
              LifeLink AI is designed so your family has what they need in a crisis — without
              exposing your data to anyone, anytime.
            </p>
          </div>
          <div className="mx-auto mt-12 max-w-3xl space-y-4">
            {[
              {
                title: "You decide who gets access",
                description:
                  "Every trusted contact is approved by both sides before they can request access.",
              },
              {
                title: "Emergency access with a grace period",
                description:
                  "Contacts gain read-only access only after you don't respond within your set grace period.",
              },
              {
                title: "Security by default",
                description:
                  "Strong password hashing, rotating sessions, one-time codes, and audit logging throughout.",
              },
            ].map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-4 rounded-xl border border-slate-200 bg-white p-6 shadow-sm"
              >
                <CheckCircle2 className="mt-0.5 h-5 w-5 shrink-0 text-brand-600" aria-hidden="true" />
                <div>
                  <h3 className="text-sm font-semibold text-slate-900">{item.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600">{item.description}</p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="border-t border-slate-200 bg-slate-50">
          <div className="mx-auto max-w-6xl px-6 py-16 text-center">
            <KeyRound className="mx-auto h-8 w-8 text-brand-600" aria-hidden="true" />
            <h2 className="mt-4 text-2xl font-bold tracking-tight text-slate-900">
              Ready when it matters
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-slate-600">
              Create your free account, add your vault, and choose the people who can reach it
              in an emergency.
            </p>
            <div className="mt-6">
              <Link
                href="/auth/register"
                className="inline-flex items-center gap-2 rounded-lg bg-brand-600 px-6 py-3 text-sm font-medium text-white shadow-sm transition hover:bg-brand-700"
              >
                Create your account
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <p className="text-sm text-slate-500">LifeLink AI</p>
          <p className="text-xs text-slate-400">
            Secure digital emergency vault for the people you love.
          </p>
        </div>
      </footer>
    </div>
  );
}