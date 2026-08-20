"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { KeyRound, MailCheck } from "lucide-react";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { AuthLayout } from "@/components/auth/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { apiPost } from "@/lib/api";

const forgotSchema = z.object({
  email: z.string().email("Enter a valid email address"),
});

type ForgotForm = z.infer<typeof forgotSchema>;

export default function ForgotPasswordPage() {
  const [sent, setSent] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ForgotForm>({ resolver: zodResolver(forgotSchema) });

  const onSubmit = async (values: ForgotForm) => {
    setSubmitting(true);
    try {
      // The API always returns 202 (anti-enumeration); we show a neutral message.
      await apiPost("/auth/password-reset/request", { email: values.email });
      setSent(true);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <AuthLayout>
      {sent ? (
        <div className="animate-fade-up">
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-emerald-50 text-emerald-600 ring-1 ring-emerald-100 dark:bg-emerald-900/40 dark:text-emerald-300 dark:ring-emerald-800/60">
              <MailCheck className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-[1.75rem]">
                Check your inbox
              </h1>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
                Password reset requested
              </p>
            </div>
          </div>
          <p className="mt-6 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
            If an account exists for that email, you will receive a password reset message
            shortly. Follow the link in the email to choose a new password.
          </p>
          <div className="mt-8 rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 text-sm text-emerald-800 dark:border-emerald-900 dark:bg-emerald-950/40 dark:text-emerald-300">
            Don&apos;t see it? Check your spam folder — the message usually arrives within a few
            minutes.
          </div>
          <Link href="/auth/login">
            <Button variant="secondary" size="lg" className="mt-8 w-full">
              Back to sign in
            </Button>
          </Link>
        </div>
      ) : (
        <div>
          <div className="flex items-center gap-2.5">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
              <KeyRound className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-[1.75rem]">
                Reset your password
              </h1>
              <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
                We&apos;ll email you a secure reset link.
              </p>
            </div>
          </div>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-6 flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              error={errors.email?.message}
              {...register("email")}
            />
            <Button type="submit" size="lg" loading={submitting} className="mt-1">
              Send reset link
            </Button>
          </form>
          <Link href="/auth/login">
            <Button variant="ghost" size="md" className="mt-6 w-full">
              Back to sign in
            </Button>
          </Link>
        </div>
      )}
    </AuthLayout>
  );
}