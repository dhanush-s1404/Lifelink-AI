"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
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
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Reset your password</CardTitle>
        </CardHeader>
        <CardBody>
          {sent ? (
            <div className="flex flex-col gap-3">
              <p className="text-sm text-slate-700">
                If an account exists for that email, you will receive a password reset message
                shortly. Check your inbox.
              </p>
              <Link href="/auth/login" className="text-sm font-medium text-brand-600 hover:underline">
                Back to sign in
              </Link>
            </div>
          ) : (
            <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
              <Input
                label="Email"
                type="email"
                autoComplete="email"
                placeholder="you@example.com"
                error={errors.email?.message}
                {...register("email")}
              />
              <Button type="submit" size="lg" loading={submitting}>
                Send reset link
              </Button>
              <Link href="/auth/login" className="text-center text-sm font-medium text-brand-600 hover:underline">
                Back to sign in
              </Link>
            </form>
          )}
        </CardBody>
      </Card>
    </main>
  );
}
