"use client";

import { useQuery } from "@tanstack/react-query";
import { Monitor, RefreshCw, ShieldCheck } from "lucide-react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { apiGet } from "@/lib/api";
import { Button } from "@/components/ui/Button";

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
  return new Date(value).toLocaleString();
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
          <div className="flex items-center justify-between gap-4">
            <div>
              <h1 className="page-heading">Security</h1>
              <p className="page-subheading">
                Active sessions on your account. Signed-in devices are listed below.
              </p>
            </div>
            <Button variant="secondary" size="sm" onClick={() => refetch()} loading={isRefetching}>
              <RefreshCw className="h-4 w-4" />
              Refresh
            </Button>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Active sessions</CardTitle>
              </CardHeader>
              <CardBody className="p-0">
                {isError && (
                  <div className="p-5 text-sm text-red-800">
                    <p className="font-medium">Could not load your sessions.</p>
                    <button className="mt-2 text-red-700 underline" onClick={() => refetch()}>
                      Try again
                    </button>
                  </div>
                )}
                {isLoading ? (
                  <div className="space-y-2 p-5">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-16 animate-pulse rounded-lg bg-slate-100" />
                    ))}
                  </div>
                ) : sessions && sessions.length > 0 ? (
                  <ul className="divide-y divide-slate-100 px-5">
                    {sessions.map((session) => (
                      <li key={session.id} className="flex items-start justify-between gap-4 py-4">
                        <div className="flex items-start gap-3">
                          <span className="mt-0.5 flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-slate-100">
                            <Monitor className="h-4 w-4 text-slate-600" aria-hidden="true" />
                          </span>
                          <div className="min-w-0">
                            <p className="text-sm font-medium text-slate-900">
                              {session.device_name ?? "Web session"}
                              {session.is_current && (
                                <span className="ml-2 badge badge-brand">This device</span>
                              )}
                            </p>
                            <p className="mt-0.5 truncate text-xs text-slate-500">
                              {session.user_agent ?? "Unknown browser"}
                            </p>
                            <p className="mt-0.5 text-xs text-slate-500">
                              {session.ip_address ?? "Unknown IP"} · created{" "}
                              {formatWhen(session.created_at)}
                            </p>
                          </div>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="p-10 text-center">
                    <Monitor className="mx-auto h-8 w-8 text-slate-300" />
                    <p className="mt-3 text-sm text-slate-500">No active sessions found.</p>
                  </div>
                )}
              </CardBody>
            </Card>

            <div className="space-y-4">
              <Card>
                <CardHeader>
                  <CardTitle>Account protection</CardTitle>
                </CardHeader>
                <CardBody>
                  <ul className="space-y-3 text-sm text-slate-600">
                    <li className="flex gap-2">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
                      Passwords are stored as Argon2id hashes.
                    </li>
                    <li className="flex gap-2">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
                      Sessions rotate tokens on every refresh.
                    </li>
                    <li className="flex gap-2">
                      <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
                      Login and OTP attempts are rate limited.
                    </li>
                  </ul>
                </CardBody>
              </Card>
              <Card>
                <CardHeader>
                  <CardTitle>Two-factor authentication</CardTitle>
                </CardHeader>
                <CardBody>
                  <p className="text-sm text-slate-600">
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