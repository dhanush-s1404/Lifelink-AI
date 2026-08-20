import { ArrowRight, KeyRound, ShieldCheck, Siren } from "lucide-react";

import { Logo } from "@/components/ui/Logo";

const highlights = [
  {
    icon: ShieldCheck,
    title: "Encrypted at rest",
    text: "Your records stay protected with strong cryptography.",
  },
  {
    icon: KeyRound,
    title: "Controlled access",
    text: "Trusted contacts get read-only access, only in emergencies.",
  },
  {
    icon: Siren,
    title: "You stay in charge",
    text: "Grace periods, confirmations, and full audit history.",
  },
];

type AuthLayoutProps = {
  children: React.ReactNode;
};

export function AuthLayout({ children }: AuthLayoutProps) {
  return (
    <main className="flex min-h-screen bg-white dark:bg-night-950">
      {/* Form panel */}
      <div className="flex w-full flex-col items-center justify-center px-6 py-12 lg:w-1/2 lg:px-12">
        <div className="w-full max-w-md animate-fade-up">
          <Logo href="/" className="mb-10" />
          {children}
        </div>
      </div>

      {/* Brand panel */}
      <div className="relative hidden overflow-hidden bg-night-950 lg:block lg:w-1/2">
        <div className="pointer-events-none absolute -left-32 top-0 h-[28rem] w-[28rem] rounded-full bg-brand-600/30 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 right-0 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="pointer-events-none absolute left-1/2 top-1/2 h-64 w-64 -translate-x-1/2 -translate-y-1/2 rounded-full bg-brand-500/10 blur-3xl" />

        <div className="relative flex h-full flex-col justify-between p-12 xl:p-16">
          <div>
            <span className="inline-flex items-center gap-1.5 rounded-full border border-white/10 bg-white/5 px-3 py-1 text-xs font-medium text-brand-200 backdrop-blur">
              <ShieldCheck className="h-3.5 w-3.5" aria-hidden="true" />
              Your family&apos;s digital emergency vault
            </span>
            <h2 className="mt-6 max-w-md text-3xl font-bold tracking-tight text-white xl:text-4xl">
              Everything your loved ones need,{" "}
              <span className="bg-brand-gradient bg-clip-text text-transparent">
                exactly when it matters
              </span>
              .
            </h2>
          </div>

          <div className="space-y-4">
            {highlights.map((item) => (
              <div
                key={item.title}
                className="flex items-start gap-4 rounded-2xl border border-white/10 bg-white/5 p-5 backdrop-blur transition hover:bg-white/10"
              >
                <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white">
                  <item.icon className="h-5 w-5" aria-hidden="true" />
                </span>
                <div>
                  <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                  <p className="mt-1 text-sm leading-relaxed text-slate-400">{item.text}</p>
                </div>
              </div>
            ))}
            <a
              href="/"
              className="mt-2 inline-flex items-center gap-1.5 text-sm font-medium text-brand-300 transition hover:text-brand-200"
            >
              Learn how LifeLink works
              <ArrowRight className="h-4 w-4" aria-hidden="true" />
            </a>
          </div>
        </div>
      </div>
    </main>
  );
}