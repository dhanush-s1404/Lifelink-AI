"use client";

import { useRouter, useSearchParams } from "next/navigation";
import { Suspense, useEffect, useState } from "react";
import { ShieldCheck } from "lucide-react";
import { useToast } from "@/lib/toast";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
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
    <Card className="w-full max-w-md">
      <CardHeader>
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-5 w-5 text-brand-600" aria-hidden="true" />
          <CardTitle>Verify your code</CardTitle>
        </div>
      </CardHeader>
      <CardBody>
        <p className="mb-4 text-sm text-slate-600">
          A 6-digit verification code was sent to your email. Enter it below to continue.
        </p>

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
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
          />
          <Button type="submit" size="lg" loading={submitting} disabled={otpCode.length !== 6}>
            Verify
          </Button>
        </form>

        <div className="mt-6 flex items-center justify-between text-sm">
          <span className="text-slate-500">
            {resendDisabled ? `Resend available in ${resendTime}s` : "Didn't get a code?"}
          </span>
          <button
            type="button"
            onClick={handleResend}
            disabled={resendDisabled || resending}
            className="font-medium text-brand-600 hover:underline disabled:cursor-not-allowed disabled:text-slate-400"
          >
            {resending ? "Sending…" : "Resend code"}
          </button>
        </div>
      </CardBody>
    </Card>
  );
}

export default function OtpVerifyPage() {
  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Suspense
        fallback={
          <Card className="w-full max-w-md">
            <CardHeader>
              <CardTitle>Verify your code</CardTitle>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-slate-500">Loading…</p>
            </CardBody>
          </Card>
        }
      >
        <OtpVerifyContent />
      </Suspense>
    </main>
  );
}