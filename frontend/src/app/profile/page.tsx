"use client";

import { CalendarDays, Mail, ShieldCheck, User as UserIcon } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/lib/auth";

function formatDate(value: string | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function DetailRow({
  icon,
  label,
  value,
}: {
  icon: React.ReactNode;
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div className="flex items-start gap-3 rounded-xl border border-slate-100 px-4 py-3 dark:border-slate-800">
      <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-slate-400 dark:bg-night-800 dark:text-slate-500">
        {icon}
      </span>
      <div className="min-w-0">
        <dt className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
          {label}
        </dt>
        <dd className="mt-0.5 text-sm font-medium text-slate-900 dark:text-white">{value}</dd>
      </div>
    </div>
  );
}

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-5">
            <span className="flex h-16 w-16 shrink-0 items-center justify-center rounded-2xl bg-brand-gradient text-2xl font-bold text-white shadow-card">
              {(user?.full_name?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
            </span>
            <div className="min-w-0">
              <h1 className="page-heading">{user?.full_name ?? "Your account"}</h1>
              <p className="page-subheading">{user?.email}</p>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Account details</CardTitle>
              </CardHeader>
              <CardBody>
                <dl className="space-y-3">
                  <DetailRow
                    icon={<Mail className="h-4 w-4" aria-hidden="true" />}
                    label="Email"
                    value={user?.email}
                  />
                  <DetailRow
                    icon={<UserIcon className="h-4 w-4" aria-hidden="true" />}
                    label="Full name"
                    value={user?.full_name ?? "Not set"}
                  />
                  <DetailRow
                    icon={<CalendarDays className="h-4 w-4" aria-hidden="true" />}
                    label="Joined"
                    value={formatDate(user?.created_at)}
                  />
                  <div className="flex items-start gap-3 rounded-xl border border-slate-100 px-4 py-3 dark:border-slate-800">
                    <span className="mt-0.5 flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-slate-50 text-slate-400 dark:bg-night-800 dark:text-slate-500">
                      <ShieldCheck className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div className="min-w-0">
                      <dt className="text-xs font-medium uppercase tracking-wide text-slate-400 dark:text-slate-500">
                        Status
                      </dt>
                      <dd className="mt-1 flex items-center gap-2">
                        {user?.is_active ? <Badge tone="success">Active</Badge> : <Badge tone="neutral">Inactive</Badge>}
                        {user?.is_verified ? <Badge tone="brand">Email verified</Badge> : <Badge tone="warning">Email not verified</Badge>}
                      </dd>
                    </div>
                  </div>
                </dl>
              </CardBody>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Manage your account</CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Update your name and password, and review the devices signed in to your
                    account.
                  </p>
                  <div className="mt-5 flex flex-col gap-3">
                    <Link href="/settings">
                      <Button variant="secondary" className="w-full">
                        Edit profile &amp; password
                      </Button>
                    </Link>
                    <Link href="/security">
                      <Button variant="secondary" className="w-full">
                        Review active sessions
                      </Button>
                    </Link>
                  </div>
                </CardBody>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Quick links</CardTitle>
                </CardHeader>
                <CardBody>
                  <div className="grid grid-cols-2 gap-3">
                    <Link
                      href="/vault"
                      className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-brand-200 hover:bg-brand-50/50 dark:border-slate-700 dark:text-slate-200 dark:hover:border-brand-800 dark:hover:bg-brand-900/20"
                    >
                      Vault
                    </Link>
                    <Link
                      href="/trusted-contacts"
                      className="rounded-xl border border-slate-200 px-4 py-3 text-sm font-medium text-slate-700 transition hover:border-brand-200 hover:bg-brand-50/50 dark:border-slate-700 dark:text-slate-200 dark:hover:border-brand-800 dark:hover:bg-brand-900/20"
                    >
                      Contacts
                    </Link>
                  </div>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}