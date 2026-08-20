"use client";

import { useState } from "react";
import { KeyRound, ShieldCheck, User } from "lucide-react";
import { useRouter } from "next/navigation";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { ApiError, apiPatch, apiPost } from "@/lib/api";
import { useAuth } from "@/lib/auth";
import { useToast } from "@/lib/toast";

function ProfileForm({ onSaved }: { onSaved: () => void }) {
  const { user, refreshUser } = useAuth();
  const { push } = useToast();
  const [fullName, setFullName] = useState(user?.full_name ?? "");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    try {
      await apiPatch("/users/me", { full_name: fullName.trim() || null });
      await refreshUser();
      push("success", "Profile updated");
      onSaved();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not update your profile.";
      push("error", message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
            <User className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <CardTitle>Profile</CardTitle>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              How your name appears across LifeLink
            </p>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <form onSubmit={submit} className="flex flex-col gap-5">
          <Input
            label="Full name"
            placeholder="Jane Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <div>
            <span className="field-label">Email</span>
            <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-3.5 py-2.5 text-sm text-slate-600 dark:border-slate-700 dark:bg-night-800 dark:text-slate-300">
              <ShieldCheck className="h-4 w-4 text-emerald-500" aria-hidden="true" />
              {user?.email}
            </div>
          </div>
          <Button
            type="submit"
            loading={submitting}
            disabled={fullName.trim() === (user?.full_name ?? "")}
            className="w-full sm:w-auto"
          >
            Save changes
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

function PasswordForm() {
  const { push } = useToast();
  const router = useRouter();
  const [current, setCurrent] = useState("");
  const [next, setNext] = useState("");
  const [confirm, setConfirm] = useState("");
  const [submitting, setSubmitting] = useState(false);

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (next.length < 8) {
      push("error", "New password must be at least 8 characters");
      return;
    }
    if (next !== confirm) {
      push("error", "New passwords do not match");
      return;
    }
    setSubmitting(true);
    try {
      await apiPost("/users/me/password", {
        current_password: current,
        new_password: next,
      });
      push("success", "Password changed");
      setCurrent("");
      setNext("");
      setConfirm("");
      router.refresh();
    } catch (err) {
      const message = err instanceof ApiError ? err.message : "Could not change your password.";
      push("error", message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2.5">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
            <KeyRound className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <CardTitle>Change password</CardTitle>
            <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
              Use at least 8 characters with a mix of letters, numbers, and symbols
            </p>
          </div>
        </div>
      </CardHeader>
      <CardBody>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Input
            label="Current password"
            type="password"
            autoComplete="current-password"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            required
          />
          <Input
            label="New password"
            type="password"
            autoComplete="new-password"
            value={next}
            onChange={(e) => setNext(e.target.value)}
            required
          />
          <Input
            label="Confirm new password"
            type="password"
            autoComplete="new-password"
            value={confirm}
            onChange={(e) => setConfirm(e.target.value)}
            required
          />
          <Button
            type="submit"
            loading={submitting}
            disabled={!current || !next || !confirm}
            className="w-full sm:w-auto"
          >
            Update password
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

export default function SettingsPage() {
  const [version, setVersion] = useState(0);
  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <h1 className="page-heading">Settings</h1>
          <p className="page-subheading">Manage your profile and account security.</p>
          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <ProfileForm onSaved={() => setVersion((v) => v + 1)} />
            <PasswordForm />
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}