"use client";

import { useState } from "react";
import { KeyRound, User } from "lucide-react";
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
        <div className="flex items-center gap-2">
          <User className="h-4 w-4 text-brand-600" aria-hidden="true" />
          <CardTitle>Profile</CardTitle>
        </div>
      </CardHeader>
      <CardBody>
        <form onSubmit={submit} className="flex flex-col gap-4">
          <Input
            label="Full name"
            placeholder="Jane Doe"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
          />
          <div>
            <span className="text-sm font-medium text-slate-700">Email</span>
            <p className="mt-1 text-sm text-slate-500">{user?.email}</p>
          </div>
          <div>
            <Button type="submit" loading={submitting} disabled={fullName.trim() === (user?.full_name ?? "")}>
              Save changes
            </Button>
          </div>
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
        <div className="flex items-center gap-2">
          <KeyRound className="h-4 w-4 text-brand-600" aria-hidden="true" />
          <CardTitle>Change password</CardTitle>
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
          <div>
            <Button type="submit" loading={submitting} disabled={!current || !next || !confirm}>
              Update password
            </Button>
          </div>
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
          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <ProfileForm onSaved={() => setVersion((v) => v + 1)} />
            <PasswordForm />
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}