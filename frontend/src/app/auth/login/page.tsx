"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Eye, EyeOff, ShieldCheck } from "lucide-react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { ApiError } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/lib/toast";

const loginSchema = z.object({
  email: z.string().email("Enter a valid email address"),
  password: z.string().min(1, "Password is required"),
  rememberMe: z.boolean().optional(),
});

type LoginForm = z.infer<typeof loginSchema>;

export default function LoginPage() {
  const { login } = useAuth();
  const router = useRouter();
  const { push } = useToast();
  const [submitting, setSubmitting] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<LoginForm>({ resolver: zodResolver(loginSchema) });

  const onSubmit = async (values: LoginForm) => {
    setSubmitting(true);
    try {
      await login(values.email, values.password, values.rememberMe ?? false);
      router.push("/dashboard");
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Unable to sign in. Please try again.";
      push("error", message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="flex min-h-screen bg-slate-50 dark:bg-night-950">
      <div className="flex w-full flex-col items-center justify-center p-6 lg:w-1/2">
        <div className="w-full max-w-md">
          <div className="mb-8 flex items-center gap-2">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-gradient shadow-glow">
              <ShieldCheck className="h-5 w-5 text-white" aria-hidden="true" />
            </span>
            <span className="text-xl font-bold tracking-tight text-slate-900 dark:text-white">
              LifeLink AI
            </span>
          </div>

          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Welcome back</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Sign in to access your emergency vault.
          </p>

          <form onSubmit={handleSubmit(onSubmit)} className="mt-8 flex flex-col gap-4">
            <Input
              label="Email"
              type="email"
              autoComplete="email"
              placeholder="you@example.com"
              error={errors.email?.message}
              {...register("email")}
            />
            <div className="relative">
              <Input
                label="Password"
                type={showPassword ? "text" : "password"}
                autoComplete="current-password"
                placeholder="••••••••"
                error={errors.password?.message}
                {...register("password")}
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-3 top-[2.4rem] -translate-y-1/2 text-slate-500 hover:text-slate-900 dark:text-slate-400 dark:hover:text-white"
                aria-label={showPassword ? "Hide password" : "Show password"}
              >
                {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
              </button>
            </div>
            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-600 dark:text-slate-300">
                <input
                  type="checkbox"
                  className="h-4 w-4 rounded border-slate-300 text-brand-600 focus:ring-brand-600 dark:border-slate-600 dark:bg-night-800"
                  {...register("rememberMe")}
                />
                Remember me
              </label>
              <Link
                href="/auth/forgot-password"
                className="text-sm font-medium text-brand-600 hover:underline dark:text-brand-400"
              >
                Forgot password?
              </Link>
            </div>
            <Button type="submit" size="lg" loading={submitting}>
              Sign in
            </Button>
          </form>
          <p className="mt-6 text-center text-sm text-slate-600 dark:text-slate-400">
            No account yet?{" "}
            <Link href="/auth/register" className="font-medium text-brand-600 hover:underline dark:text-brand-400">
              Create one
            </Link>
          </p>
        </div>
      </div>

      <div className="relative hidden overflow-hidden bg-night-950 lg:block lg:w-1/2">
        <div className="pointer-events-none absolute -top-24 right-0 h-96 w-96 rounded-full bg-brand-600/30 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-0 h-96 w-96 rounded-full bg-cyan-500/20 blur-3xl" />
        <div className="relative flex h-full flex-col justify-between p-12">
          <div className="space-y-6">
            {[
              { title: "Encrypted at rest", text: "Your records stay protected with strong cryptography." },
              { title: "Controlled access", text: "Trusted contacts get read-only access, only in emergencies." },
              { title: "You stay in charge", text: "Grace periods, confirmations, and full audit history." },
            ].map((item) => (
              <div key={item.title} className="rounded-2xl border border-slate-700/60 bg-night-900/70 p-5 backdrop-blur">
                <h3 className="text-sm font-semibold text-white">{item.title}</h3>
                <p className="mt-1 text-sm text-slate-400">{item.text}</p>
              </div>
            ))}
          </div>
          <p className="text-sm text-slate-500">
            The emergency vault your family can count on.
          </p>
        </div>
      </div>
    </main>
  );
}