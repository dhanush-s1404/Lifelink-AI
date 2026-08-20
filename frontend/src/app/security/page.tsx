"use client";

import { useQuery } from "@tanstack/react-query";
import { KeyRound, Monitor, RefreshCw, ShieldCheck, Smartphone } from "lucide-react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Skeleton } from "@/components/ui/Skeleton";
import { apiGet } from "@/lib/api";

type Session = {
  id: string;
  device_name: string | null;
  ip_address: string | null;
  user_agent: string | null;
  last_seen_at: string | null;
  created_at: string;
  is_current: boolean;
};

function formatWhen(value: string | null): string {
  if (!value) return "Never";
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

export default function SecurityPage() {
  const { data: sessions, isLoading, isError, refetch, isRefetching } = useQuery({
    queryKey: ["auth", "sessions"],
    queryFn: () => apiGet<Session[]>("/auth/sessions"),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="page-heading">Security</h1>
              <p className="page-subheading">
                Active sessions on your account. Signed-in devices are listed below.
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={() => refetch()} loading={isRefetching}>
              <RefreshCw className="h-4 w-4" aria-hidden="true" />
              Refresh
            </Button>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Active sessions</CardTitle>
              </CardHeader>
              <CardBody className="p-0">
                {isError && (
                  <div className="alert alert-error m-5">
                    <div className="flex-1">
                      <p className="font-medium">Could not load your sessions.</p>
                    </div>
                    <button className="shrink-0 text-sm font-semibold underline" onClick={() => refetch()}>
                      Try again
                    </button>
                  </div>
                )}
                {isLoading ? (
                  <div className="space-y-2 p-5">
                    {[1, 2].map((i) => (
                      <Skeleton key={i} className="h-16" />
                    ))}
                  </div>
                ) : sessions && sessions.length > 0 ? (
                  <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                    {sessions.map((session) => (
                      <li key={session.id} className="px-5 py-4">
                        <div className="flex items-start justify-between gap-4">
                          <div className="flex min-w-0 items-start gap-3">
                            <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 ring-1 ring-slate-100 dark:bg-night-800 dark:ring-slate-700">
                              <Smartphone className="h-4 w-4 text-slate-600 dark:text-slate-400" aria-hidden="true" />
                            </span>
                            <div className="min-w-0">
                              <p className="text-sm font-medium text-slate-900 dark:text-white">
                                {session.device_name ?? "Web session"}
                              </p>
                              <p className="mt-0.5 truncate text-xs text-slate-500 dark:text-slate-400">
                                {session.user_agent ?? "Unknown browser"}
                              </p>
                              <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
                                {session.ip_address ?? "Unknown IP"} · created {formatWhen(session.created_at)}
                              </p>
                            </div>
                          </div>
                          {session.is_current && <Badge tone="brand">This device</Badge>}
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="p-6">
                    <EmptyState
                      icon={<Monitor className="h-6 w-6" aria-hidden="true" />}
                      title="No active sessions found"
                    />
                  </div>
                )}
              </CardBody>
            </Card>

            <div className="space-y-6">
              <Card>
                <CardHeader>
                  <CardTitle>Account protection</CardTitle>
                </CardHeader>
                <CardBody>
                  <ul className="space-y-3 text-sm text-slate-600 dark:text-slate-400">
                    <li className="flex gap-2.5">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden="true" />
                      Passwords are stored as Argon2id hashes.
                    </li>
                    <li className="flex gap-2.5">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden="true" />
                      Sessions rotate tokens on every refresh.
                    </li>
                    <li className="flex gap-2.5">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" aria-hidden="true" />
                      Login and OTP attempts are rate limited.
                    </li>
                  </ul>
                </CardBody>
              </Card>
              <Card>
                <CardHeader>
                  <div className="flex items-center gap-2.5">
                    <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-50 text-brand-600 ring-1 ring-brand-100 dark:bg-brand-900/40 dark:text-brand-300 dark:ring-brand-800/60">
                      <KeyRound className="h-4 w-4" aria-hidden="true" />
                    </span>
                    <div>
                      <CardTitle>Two-factor authentication</CardTitle>
                      <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">Coming soon</p>
                    </div>
                  </div>
                </CardHeader>
                <CardBody>
                  <p className="text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                    Two-factor authentication is not yet enabled on your account. It will become
                    available in an upcoming release.
                  </p>
                </CardBody>
              </Card>
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}