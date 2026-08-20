"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { useToast } from "@/lib/toast";

import { AuthLayout } from "@/components/auth/AuthLayout";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError, apiPost } from "@/lib/api";

function OtpVerifyContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { push } = useToast();
  const purpose = searchParams.get("purpose") ?? "login";
  const next = searchParams.get("next") ?? "/dashboard";

  const [otpCode, setOtpCode] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [resending, setResending] = useState(false);
  const [resendDisabled, setResendDisabled] = useState(true);
  const [resendTime, setResendTime] = useState(30);

  useEffect(() => {
    const input = document.querySelector<HTMLInputElement>("#otp-input");
    input?.focus();
  }, []);

  useEffect(() => {
    if (!resendDisabled) return;
    const interval = setInterval(() => {
      setResendTime((current) => {
        if (current <= 1) {
          clearInterval(interval);
          setResendDisabled(false);
          return 30;
        }
        return current - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [resendDisabled]);

  const handleResend = async () => {
    setResending(true);
    try {
      await apiPost("/auth/otp/resend", { purpose });
      push("success", "A new code has been sent.");
      setResendDisabled(true);
      setResendTime(30);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to resend the code.";
      push("error", message);
    } finally {
      setResending(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (otpCode.length !== 6) {
      push("error", "Enter the full 6-digit code");
      return;
    }
    setSubmitting(true);
    try {
      await apiPost("/auth/otp/verify", { otp_code: otpCode, purpose });
      router.push(next);
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to verify the code.";
      push("error", message);
      setOtpCode("");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <div className="flex items-center gap-2.5">
        <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
          <ShieldCheck className="h-5 w-5" aria-hidden="true" />
        </span>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 dark:text-white sm:text-[1.75rem]">
            Verify your code
          </h1>
          <p className="mt-0.5 text-sm text-slate-600 dark:text-slate-400">
            Two-step verification
          </p>
        </div>
      </div>

      <p className="mt-6 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
        A 6-digit verification code was sent to your email. Enter it below to continue.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 flex flex-col gap-4">
        <Input
          id="otp-input"
          label="Verification code"
          type="text"
          inputMode="numeric"
          autoComplete="one-time-code"
          placeholder="123456"
          maxLength={6}
          value={otpCode}
          onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, "").slice(0, 6))}
          required
          className="text-center text-lg font-semibold tracking-[0.5em]"
        />
        <Button type="submit" size="lg" loading={submitting} disabled={otpCode.length !== 6}>
          Verify
        </Button>
      </form>

      <div className="mt-6 flex items-center justify-between rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-sm dark:border-slate-700 dark:bg-night-900">
        <span className="text-slate-500 dark:text-slate-400">
          {resendDisabled ? `Resend available in ${resendTime}s` : "Didn't get a code?"}
        </span>
        <button
          type="button"
          onClick={handleResend}
          disabled={resendDisabled || resending}
          className="font-medium text-brand-600 transition hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300 disabled:cursor-not-allowed disabled:text-slate-400"
        >
          {resending ? "Sending…" : "Resend code"}
        </button>
      </div>
    </>
  );
}

export default function OtpVerifyPage() {
  return (
    <AuthLayout>
      <Suspense fallback={<p className="text-sm text-slate-500 dark:text-slate-400">Loading…</p>}>
        <OtpVerifyContent />
      </Suspense>
    </AuthLayout>
  );
}