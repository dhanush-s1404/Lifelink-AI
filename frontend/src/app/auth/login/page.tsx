"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/lib/toast";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const { push } = useToast();
  const [submitting, setSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginForm) => {
    setSubmitting(true);
    try {
      await login(values.email, values.password);
      router.push("/dashboard");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to sign in. Please try again.";
      push("error", message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen items-center justify-center p-6">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Sign in to LifeLink AI</CardTitle>
        </CardHeader>
        <CardBody>
          <form onSubmit={handleSubmit(onSubmit)} className="flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              error={errors.email?.message}
              {...register("email")}
            />
            <Input
              label="Password"
              type="password"
              autoComplete="current-password"
              placeholder="••••••••"
              error={errors.password?.message}
              {...register("password")}
            />
            <div className="flex items-center justify-between">
              <Link
                href="/auth/forgot-password"
                className="text-sm font-medium text-brand-600 hover:underline"
              >
                Forgot password?
              </Link>
            </div>
            <Button type="submit" size="lg" loading={submitting}>
              Sign in
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600">
            No account yet?{" "}
            <Link href="/auth/register" className="font-medium text-brand-600 hover:underline">
              Create one
            </Link>
          </p>
        </CardBody>
      </Card>
    </main>
  );
}
