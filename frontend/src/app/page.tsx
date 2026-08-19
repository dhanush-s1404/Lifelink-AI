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
    <div className="min-h-screen bg-white dark:bg-night-950">
      <header className="sticky top-0 z-40 border-b border-slate-200 bg-white/80 backdrop-blur dark:border-slate-800 dark:bg-night-950/80">
        <nav className="mx-auto flex max-w-6xl items-center justify-between px-6 py-4" aria-label="Main">
          <div className="flex items-center gap-2">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
              <ShieldCheck className="h-5 w-5 text-white" aria-hidden="true" />
            </span>
            <span className="text-lg font-semibold tracking-tight text-slate-900 dark:text-white">
              LifeLink AI
            </span>
          </div>
          <div className="flex items-center gap-3">
            <Link
              href="/auth/login"
              className="rounded-lg px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-800"
            >
              Sign in
            </Link>
            <Link
              href="/auth/register"
              className="rounded-lg bg-brand-gradient px-4 py-2 text-sm font-medium text-white shadow-card transition hover:brightness-110"
            >
              Create account
            </Link>
          </div>
        </nav>
      </header>

      <main>
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-96 bg-brand-gradient-soft dark:bg-night-gradient" />
          <div className="pointer-events-none absolute -top-32 left-1/2 h-96 w-[48rem] -translate-x-1/2 rounded-full bg-brand-400/20 blur-3xl dark:bg-brand-600/10" />
          <div className="relative mx-auto max-w-6xl px-6 pb-24 pt-20 sm:pt-28">
            <div className="mx-auto max-w-3xl text-center">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-white/80 px-3 py-1 text-xs font-medium text-brand-800 backdrop-blur dark:border-brand-800 dark:bg-night-900/80 dark:text-brand-300">
                <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
                End-to-end encrypted
              </span>
              <h1 className="mt-6 text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
                The emergency vault your family can{" "}
                <span className="bg-brand-gradient bg-clip-text text-transparent">count on</span>.
              </h1>
              <p className="mx-auto mt-6 max-w-2xl text-lg leading-relaxed text-slate-600 dark:text-slate-300">
                LifeLink AI keeps your most important information secure, organized, and
                reachable by the people you trust — only when it matters most.
              </p>
              <div className="mt-9 flex flex-col items-center justify-center gap-3 sm:flex-row">
                <Link
                  href="/auth/register"
                  className="inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient px-7 py-3.5 text-sm font-semibold text-white shadow-glow transition hover:brightness-110 sm:w-auto"
                >
                  Get started
                  <ArrowRight className="h-4 w-4" aria-hidden="true" />
                </Link>
                <Link
                  href="/auth/login"
                  className="inline-flex w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-7 py-3.5 text-sm font-semibold text-slate-700 transition hover:bg-slate-50 dark:border-slate-600 dark:bg-night-900 dark:text-slate-200 dark:hover:bg-night-800 sm:w-auto"
                >
                  Sign in to your vault
                </Link>
              </div>
            </div>
          </div>
        </section>

        <section className="border-y border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-night-900/60">
          <div className="mx-auto max-w-6xl px-6 py-20">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:-translate-y-0.5 hover:shadow-pop dark:border-slate-700 dark:bg-night-900"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient shadow-card">
                    <feature.icon className="h-5 w-5 text-white" aria-hidden="true" />
                  </span>
                  <h2 className="mt-5 text-base font-semibold text-slate-900 dark:text-white">
                    {feature.title}
                  </h2>
                  <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                    {feature.description}
                  </p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="mx-auto max-w-6xl px-6 py-24">
          <div className="mx-auto max-w-3xl text-center">
            <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Built around consent and control
            </h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">
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
                className="flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition hover:shadow-pop dark:border-slate-700 dark:bg-night-900"
              >
                <CheckCircle2
                  className="mt-0.5 h-5 w-5 shrink-0 text-brand-500 dark:text-brand-400"
                  aria-hidden="true"
                />
                <div>
                  <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{item.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                    {item.description}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </section>

        <section className="relative overflow-hidden border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-night-900/60">
          <div className="pointer-events-none absolute -bottom-40 left-1/2 h-80 w-[40rem] -translate-x-1/2 rounded-full bg-brand-400/20 blur-3xl" />
          <div className="relative mx-auto max-w-6xl px-6 py-20 text-center">
            <KeyRound
              className="mx-auto h-9 w-9 text-brand-500 dark:text-brand-400"
              aria-hidden="true"
            />
            <h2 className="mt-4 text-3xl font-bold tracking-tight text-slate-900 dark:text-white">
              Ready when it matters
            </h2>
            <p className="mx-auto mt-3 max-w-xl text-slate-600 dark:text-slate-300">
              Create your free account, add your vault, and choose the people who can reach it
              in an emergency.
            </p>
            <div className="mt-7">
              <Link
                href="/auth/register"
                className="inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-7 py-3 text-sm font-semibold text-white shadow-glow transition hover:brightness-110"
              >
                Create your account
                <ArrowRight className="h-4 w-4" aria-hidden="true" />
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-night-950">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-6 py-8 sm:flex-row">
          <p className="text-sm text-slate-500 dark:text-slate-400">LifeLink AI</p>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Secure digital emergency vault for the people you love.
          </p>
        </div>
      </footer>
    </div>
  );
}