"use client";

import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import { useToast } from "@/lib/toast";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";

export default function OtpVerifyPage() {
  const router = useRouter();
  const { push } = useToast();
  const [otpCode, setOtpCode] = useState<string>("");
  const [resendDisabled, setResendDisabled] = useState(false);
  const [resendTime, setResendTime] = useState(30);

  useEffect(() => {
    // Set timeout for auto-focus (simulated - input order matters in JSX)
    const input = document.querySelector('[data-index="0"]') as HTMLInputElement | null;
    if (input) {
      input.focus();
    }
  }, []);

  const handleResend = async () => {
    try {
      await fetch(`/auth/otp/resend`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ purpose: "login" }),
        credentials: "include",
      });
      setResendDisabled(true);
    } catch (err: any) {
      if (err instanceof Error) {
        push("error", err.message || "Failed to resend OTP");
      } else {
        push("error", "Unable to resend OTP. Please try again.");
      }
    }
  };

  // Countdown timer
  useEffect(() => {
    let minutes = resendTime;
    const interval = setInterval(() => {
      setResendTime((minutes) => {
        if (minutes <= 0) {
          clearInterval(interval);
          setResendDisabled(false);
          return 30;
        }
        return minutes - 1;
      });
    }, 1000);
    return () => clearInterval(interval);
  }, [resendTime]);

  const handleSubmit = async () => {
    if (otpCode.length !== 6) {
      push("error", "Please enter a 6-digit code");
      return;
    }
    try {
      await fetch(`/auth/otp/verify`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ otp_code: otpCode }),
        credentials: "include",
      });
      router.push("/dashboard");
    } catch (err: any) {
      if (err instanceof Error) {
        push("error", err.message || "Failed to verify code");
      } else {
        push("error", "Unable to verify code. Please try again.");
      }
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Verify Your Code</CardTitle>
        </CardHeader>
        <CardBody>
          <p className="mb-4">
            A 6-digit verification code has been sent to your email.
          </p>

          <form onSubmit={e => { e.preventDefault(); handleSubmit(); }} className="flex flex-col gap-4">
            <Input
              data-index="0"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[0] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />
            <Input
              data-index="1"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[1] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />
            <Input
              data-index="2"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[2] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />
            <Input
              data-index="3"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[3] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />
            <Input
              data-index="4"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[4] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />
            <Input
              data-index="5"
              type="number"
              inputMode="numeric"
              placeholder=""
              maxLength={1}
              value={otpCode[5] || ""}
              onChange={(e) => {
                const value = e.target.value.replace(/\D/g, "").substring(0, 1);
                setOtpCode((c) => c.replace(/\D/g, "").substring(0, 6) + value);
              }}
            />

            <div className="mt-4">
              <p className="text-sm text-slate-500">
                Or paste the full code below
              </p>
              <Input
                type="text"
                inputMode="numeric"
                placeholder="123456"
                maxLength={6}
                onChange={(e) => {
                  const value = e.target.value.replace(/\D/g, "").substring(0, 6);
                  if (value.length === 6) {
                    setOtpCode(value);
                  }
                }}
              />
            </div>

            {resendDisabled && (
              <p className="mt-4 text-sm text-slate-500">
                Resend in {resendTime}s
              </p>
            )}

            {!resendDisabled && (
              <button
                type="button"
                onClick={handleResend}
                className="rounded-lg border border-slate-300 px-4 py-2 text-sm text-slate-700 transition hover:bg-slate-100"
              >
                Resend OTP
              </button>
            )}

            <Button type="submit" size="lg" disabled={resendDisabled}>
              Verify
            </Button>
          </form>

          <p className="mt-6 text-center text-sm text-slate-600">
            No account yet?{" "}
            <a href="/auth/register" className="font-medium text-brand-600 hover:underline">
              Create one
            </a>
          </p>
        </CardBody>
      </Card>
    </main>
  );
}