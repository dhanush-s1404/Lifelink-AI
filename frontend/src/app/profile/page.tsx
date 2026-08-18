"use client";

import { CalendarDays, Mail, User as UserIcon } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/lib/auth";

function formatDate(value: string | undefined): string {
  if (!value) return "—";
  return new Date(value).toLocaleDateString(undefined, {
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-4">
            <span className="flex h-14 w-14 items-center justify-center rounded-full bg-brand-600 text-lg font-semibold text-white">
              {(user?.full_name?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
            </span>
            <div>
              <h1 className="page-heading">{user?.full_name ?? "Your account"}</h1>
              <p className="page-subheading">{user?.email}</p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Account details</CardTitle>
              </CardHeader>
              <CardBody>
                <dl className="space-y-4 text-sm">
                  <div className="flex items-start gap-3">
                    <Mail className="mt-0.5 h-4 w-4 text-slate-400" aria-hidden="true" />
                    <div>
                      <dt className="font-medium text-slate-900">Email</dt>
                      <dd className="mt-0.5 text-slate-600">{user?.email}</dd>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <UserIcon className="mt-0.5 h-4 w-4 text-slate-400" aria-hidden="true" />
                    <div>
                      <dt className="font-medium text-slate-900">Full name</dt>
                      <dd className="mt-0.5 text-slate-600">{user?.full_name ?? "Not set"}</dd>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <CalendarDays className="mt-0.5 h-4 w-4 text-slate-400" aria-hidden="true" />
                    <div>
                      <dt className="font-medium text-slate-900">Joined</dt>
                      <dd className="mt-0.5 text-slate-600">{formatDate(user?.created_at)}</dd>
                    </div>
                  </div>
                  <div className="flex items-start gap-3">
                    <span className="mt-0.5 flex h-4 w-4 items-center justify-center text-slate-400">
                      <span className="h-2 w-2 rounded-full bg-emerald-500" />
                    </span>
                    <div>
                      <dt className="font-medium text-slate-900">Status</dt>
                      <dd className="mt-0.5 text-slate-600">
                        {user?.is_active ? "Active" : "Inactive"}
                        {user?.is_verified ? " · Email verified" : " · Email not verified"}
                      </dd>
                    </div>
                  </div>
                </dl>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Manage your account</CardTitle>
              </CardHeader>
              <CardBody>
                <p className="text-sm text-slate-600">
                  Update your name and password, and review the devices signed in to your
                  account.
                </p>
                <div className="mt-4 flex flex-col gap-3">
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
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}