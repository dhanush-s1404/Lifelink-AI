import Link from "next/link";
import {
  ArrowRight,
  BookLock,
  CheckCircle2,
  FileText,
  HeartHandshake,
  KeyRound,
  LockKeyhole,
  ShieldCheck,
  ShieldAlert,
  Siren,
  Sparkles,
  Users,
  Zap,
} from "lucide-react";

import { Logo } from "@/components/ui/Logo";

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

const howItWorks = [
  {
    step: "01",
    title: "Build your vault",
    description:
      "Organize your family's most important records — documents, accounts, medical details, and legal files — all in one place.",
  },
  {
    step: "02",
    title: "Invite the people you trust",
    description:
      "Add trusted contacts. Access is granted by mutual consent, so both sides must agree before anything is shared.",
  },
  {
    step: "03",
    title: "Rest easy",
    description:
      "If you ever stop responding, your contacts can reach what they need — automatically, securely, and only when it matters.",
  },
];

const metrics = [
  { value: "End-to-end", label: "encryption" },
  { value: "Mutual", label: "consent model" },
  { value: "Grace", label: "period control" },
  { value: "Read-only", label: "emergency access" },
];

export default function Home() {
  return (
    <div className="min-h-screen bg-white dark:bg-night-950">
      <header className="sticky top-0 z-40 border-b border-slate-200/80 bg-white/80 backdrop-blur-xl dark:border-slate-800/80 dark:bg-night-950/80">
        <nav
          className="mx-auto flex h-16 max-w-6xl items-center justify-between px-4 sm:px-6"
          aria-label="Main"
        >
          <Logo href="/" />
          <div className="flex items-center gap-2">
            <Link
              href="/auth/login"
              className="rounded-xl px-4 py-2 text-sm font-medium text-slate-700 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-800"
            >
              Sign in
            </Link>
            <Link
              href="/auth/register"
              className="rounded-xl bg-brand-gradient px-4 py-2 text-sm font-semibold text-white shadow-card transition-all hover:shadow-glow hover:brightness-110 active:scale-[0.98]"
            >
              Create account
            </Link>
          </div>
        </nav>
      </header>

      <main>
        {/* Hero */}
        <section className="relative overflow-hidden">
          <div className="pointer-events-none absolute inset-x-0 top-0 h-[36rem] bg-brand-gradient-soft dark:bg-night-gradient" />
          <div className="pointer-events-none absolute -top-32 left-1/2 h-[30rem] w-[52rem] -translate-x-1/2 rounded-full bg-brand-400/20 blur-3xl dark:bg-brand-600/10" />
          <div className="pointer-events-none absolute right-0 top-24 h-64 w-64 rounded-full bg-cyan-400/20 blur-3xl dark:bg-cyan-500/10" />

          <div className="relative mx-auto max-w-6xl px-4 pb-16 pt-16 sm:px-6 sm:pt-24">
            <div className="mx-auto max-w-3xl text-center">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-brand-200 bg-white/80 px-3 py-1 text-xs font-medium text-brand-800 shadow-sm backdrop-blur dark:border-brand-800 dark:bg-night-900/80 dark:text-brand-300">
                <LockKeyhole className="h-3.5 w-3.5" aria-hidden="true" />
                End-to-end encrypted
              </span>
              <h1 className="mt-6 animate-fade-up text-4xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-6xl">
                The emergency vault your family can{" "}
                <span className="bg-brand-gradient bg-clip-text text-transparent">count on</span>.
              </h1>
              <p className="mx-auto mt-6 max-w-2xl animate-fade-up text-lg leading-relaxed text-slate-600 dark:text-slate-300" style={{ animationDelay: "60ms" }}>
                LifeLink AI keeps your most important information secure, organized, and
                reachable by the people you trust — only when it matters most.
              </p>
              <div className="mt-9 flex animate-fade-up flex-col items-center justify-center gap-3 sm:flex-row" style={{ animationDelay: "120ms" }}>
                <Link
                  href="/auth/register"
                  className="group inline-flex w-full items-center justify-center gap-2 rounded-xl bg-brand-gradient px-7 py-3.5 text-sm font-semibold text-white shadow-glow transition-all hover:shadow-glow-lg hover:brightness-110 active:scale-[0.98] sm:w-auto"
                >
                  Get started free
                  <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
                </Link>
                <Link
                  href="/auth/login"
                  className="inline-flex w-full items-center justify-center rounded-xl border border-slate-300 bg-white px-7 py-3.5 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-600 dark:bg-night-900 dark:text-slate-200 dark:hover:bg-night-800 sm:w-auto"
                >
                  Sign in to your vault
                </Link>
              </div>
            </div>

            {/* Product preview */}
            <div className="relative mx-auto mt-16 max-w-4xl animate-fade-up" style={{ animationDelay: "200ms" }}>
              <div className="pointer-events-none absolute -inset-x-8 -top-8 bottom-0 rounded-[2.5rem] bg-brand-gradient opacity-[0.07] blur-2xl" />
              <div className="relative overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-lifted dark:border-slate-700 dark:bg-night-900">
                <div className="flex items-center justify-between border-b border-slate-100 px-5 py-3.5 dark:border-slate-800">
                  <div className="flex items-center gap-1.5">
                    <span className="h-2.5 w-2.5 rounded-full bg-red-400" />
                    <span className="h-2.5 w-2.5 rounded-full bg-amber-400" />
                    <span className="h-2.5 w-2.5 rounded-full bg-emerald-400" />
                  </div>
                  <span className="text-xs font-medium text-slate-400 dark:text-slate-500">
                    app.lifelink.ai/dashboard
                  </span>
                </div>
                <div className="grid grid-cols-1 gap-4 p-5 sm:grid-cols-3 sm:p-6">
                  {[
                    { icon: BookLock, label: "Vaults", value: "4", tint: "text-brand-600 dark:text-brand-400" },
                    { icon: FileText, label: "Documents", value: "32", tint: "text-cyan-600 dark:text-cyan-400" },
                    { icon: Users, label: "Contacts", value: "3", tint: "text-emerald-600 dark:text-emerald-400" },
                  ].map((card) => (
                    <div key={card.label} className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-700 dark:bg-night-800">
                      <div className="flex items-center justify-between">
                        <span className={`${card.tint}`}>
                          <card.icon className="h-5 w-5" aria-hidden="true" />
                        </span>
                        <span className="text-2xl font-bold text-slate-900 dark:text-white">{card.value}</span>
                      </div>
                      <p className="mt-2 text-xs font-medium text-slate-500 dark:text-slate-400">{card.label}</p>
                    </div>
                  ))}
                  <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 sm:col-span-2 dark:border-emerald-900 dark:bg-emerald-950/40">
                    <div className="flex items-center gap-2 text-sm font-medium text-emerald-800 dark:text-emerald-300">
                      <ShieldAlert className="h-4 w-4" aria-hidden="true" />
                      Emergency active — grace period 48h
                    </div>
                    <div className="mt-3 flex items-center gap-2">
                      <div className="h-1.5 flex-1 overflow-hidden rounded-full bg-emerald-200 dark:bg-emerald-900">
                        <div className="h-full w-2/3 rounded-full bg-emerald-500" />
                      </div>
                      <span className="text-xs font-medium text-emerald-700 dark:text-emerald-300">16h left</span>
                    </div>
                  </div>
                  <div className="flex flex-col items-start justify-center rounded-xl border border-brand-200 bg-brand-50 p-4 dark:border-brand-800 dark:bg-brand-900/30">
                    <div className="flex items-center gap-2 text-sm font-medium text-brand-800 dark:text-brand-300">
                      <Sparkles className="h-4 w-4" aria-hidden="true" />
                      AI assistant
                    </div>
                    <p className="mt-1 text-xs text-brand-700 dark:text-brand-300/80">
                      “Where is the life insurance policy?”
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* Feature grid */}
        <section className="border-y border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-night-900/60">
          <div className="mx-auto max-w-6xl px-4 py-20 sm:px-6">
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {features.map((feature) => (
                <div
                  key={feature.title}
                  className="group rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-lifted dark:border-slate-700 dark:bg-night-900"
                >
                  <span className="flex h-11 w-11 items-center justify-center rounded-xl bg-brand-gradient shadow-card transition-transform duration-300 group-hover:scale-110">
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

        {/* How it works */}
        <section className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
          <div className="mx-auto max-w-3xl text-center">
            <span className="text-xs font-semibold uppercase tracking-widest text-brand-600 dark:text-brand-400">
              How it works
            </span>
            <h2 className="mt-3 text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
              Three steps to peace of mind
            </h2>
            <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">
              LifeLink AI is designed so your family has what they need in a crisis — without
              exposing your data to anyone, anytime.
            </p>
          </div>
          <div className="mx-auto mt-12 grid max-w-5xl gap-6 md:grid-cols-3">
            {howItWorks.map((item, index) => (
              <div
                key={item.step}
                className="relative rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition-all duration-300 hover:-translate-y-1 hover:shadow-lifted dark:border-slate-700 dark:bg-night-900"
              >
                <span className="bg-brand-gradient bg-clip-text text-4xl font-bold text-transparent">
                  {item.step}
                </span>
                <h3 className="mt-4 text-base font-semibold text-slate-900 dark:text-white">
                  {item.title}
                </h3>
                <p className="mt-2 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                  {item.description}
                </p>
                {index < 2 && (
                  <ArrowRight
                    className="absolute -right-4 top-1/2 hidden h-5 w-5 -translate-y-1/2 text-slate-300 md:block dark:text-slate-600"
                    aria-hidden="true"
                  />
                )}
              </div>
            ))}
          </div>
        </section>

        {/* Consent + control */}
        <section className="border-y border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-night-900/60">
          <div className="mx-auto max-w-6xl px-4 py-24 sm:px-6">
            <div className="mx-auto max-w-3xl text-center">
              <h2 className="text-3xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-4xl">
                Built around consent and control
              </h2>
              <p className="mt-4 text-lg text-slate-600 dark:text-slate-300">
                Every access decision is explicit, reversible, and audited.
              </p>
            </div>
            <div className="mx-auto mt-12 max-w-3xl space-y-4">
              {[
                {
                  icon: Users,
                  title: "You decide who gets access",
                  description:
                    "Every trusted contact is approved by both sides before they can request access.",
                },
                {
                  icon: ShieldCheck,
                  title: "Emergency access with a grace period",
                  description:
                    "Contacts gain read-only access only after you don't respond within your set grace period.",
                },
                {
                  icon: LockKeyhole,
                  title: "Security by default",
                  description:
                    "Strong password hashing, rotating sessions, one-time codes, and audit logging throughout.",
                },
              ].map((item) => (
                <div
                  key={item.title}
                  className="group flex items-start gap-4 rounded-2xl border border-slate-200 bg-white p-6 shadow-card transition-all duration-300 hover:shadow-lifted dark:border-slate-700 dark:bg-night-900"
                >
                  <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 transition-colors group-hover:bg-brand-gradient group-hover:text-white dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
                    <item.icon className="h-5 w-5" aria-hidden="true" />
                  </span>
                  <div>
                    <h3 className="text-sm font-semibold text-slate-900 dark:text-white">{item.title}</h3>
                    <p className="mt-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                      {item.description}
                    </p>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </section>

        {/* Metrics */}
        <section className="mx-auto max-w-6xl px-4 py-16 sm:px-6">
          <div className="grid grid-cols-2 gap-6 lg:grid-cols-4">
            {metrics.map((metric) => (
              <div key={metric.label} className="text-center">
                <div className="flex items-center justify-center gap-1.5 text-2xl font-bold text-slate-900 dark:text-white">
                  <CheckCircle2 className="h-5 w-5 text-brand-500 dark:text-brand-400" aria-hidden="true" />
                  {metric.value}
                </div>
                <p className="mt-1 text-sm text-slate-500 dark:text-slate-400">{metric.label}</p>
              </div>
            ))}
          </div>
        </section>

        {/* CTA */}
        <section className="relative overflow-hidden border-t border-slate-200 bg-slate-50 dark:border-slate-800 dark:bg-night-900/60">
          <div className="pointer-events-none absolute -bottom-40 left-1/2 h-80 w-[40rem] -translate-x-1/2 rounded-full bg-brand-400/20 blur-3xl" />
          <div className="relative mx-auto max-w-6xl px-4 py-20 text-center sm:px-6">
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
            <div className="mt-7 flex flex-col items-center justify-center gap-3 sm:flex-row">
              <Link
                href="/auth/register"
                className="group inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-7 py-3 text-sm font-semibold text-white shadow-glow transition-all hover:shadow-glow-lg hover:brightness-110 active:scale-[0.98]"
              >
                Create your account
                <ArrowRight className="h-4 w-4 transition-transform group-hover:translate-x-0.5" aria-hidden="true" />
              </Link>
              <Link
                href="/auth/login"
                className="inline-flex items-center gap-2 rounded-xl border border-slate-300 bg-white px-7 py-3 text-sm font-semibold text-slate-700 shadow-sm transition hover:bg-slate-50 dark:border-slate-600 dark:bg-night-900 dark:text-slate-200 dark:hover:bg-night-800"
              >
                <Zap className="h-4 w-4 text-brand-500" aria-hidden="true" />
                I already have an account
              </Link>
            </div>
          </div>
        </section>
      </main>

      <footer className="border-t border-slate-200 bg-white dark:border-slate-800 dark:bg-night-950">
        <div className="mx-auto flex max-w-6xl flex-col items-center justify-between gap-4 px-4 py-8 sm:flex-row sm:px-6">
          <div className="flex items-center gap-2.5">
            <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-brand-gradient">
              <ShieldCheck className="h-3.5 w-3.5 text-white" aria-hidden="true" />
            </span>
            <p className="text-sm font-semibold text-slate-700 dark:text-slate-200">LifeLink AI</p>
          </div>
          <p className="text-xs text-slate-400 dark:text-slate-500">
            Secure digital emergency vault for the people you love.
          </p>
        </div>
      </footer>
    </div>
  );
}