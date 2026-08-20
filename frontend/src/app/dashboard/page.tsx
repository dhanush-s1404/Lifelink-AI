"use client";

import { useQuery } from "@tanstack/react-query";
import { Archive, ArrowRight, Plus, Shield, Users, Zap } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardBody } from "@/components/ui/Card";
import { Skeleton } from "@/components/ui/Skeleton";
import { Badge } from "@/components/ui/Badge";
import { apiGet } from "@/lib/api";
import { cn } from "@/lib/utils";

type DashboardSummary = {
  vaults_count: number;
  items_count: number;
  trusted_contacts_count: number;
  pending_emergencies_count: number;
  unread_notifications_count: number;
  recent_activity: { id: string; kind: string; message: string; created_at: string }[];
};

export default function DashboardPage() {
  const { data, isLoading, isError, refetch } = useQuery({
    queryKey: ["dashboard", "summary"],
    queryFn: () => apiGet<DashboardSummary>("/dashboard/summary"),
  });

  const stats = [
    { label: "Vaults", value: data?.vaults_count ?? 0, icon: Archive, to: "/vault", tint: "from-blue-500 to-blue-600" },
    { label: "Vault items", value: data?.items_count ?? 0, icon: Zap, to: "/vault", tint: "from-cyan-500 to-cyan-600" },
    { label: "Trusted contacts", value: data?.trusted_contacts_count ?? 0, icon: Users, to: "/trusted-contacts", tint: "from-emerald-500 to-emerald-600" },
    {
      label: "Pending emergencies",
      value: data?.pending_emergencies_count ?? 0,
      icon: Shield,
      to: "/emergency",
      danger: (data?.pending_emergencies_count ?? 0) > 0,
      tint: "from-red-500 to-red-600",
    },
  ];

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="page-heading">Dashboard</h1>
              <p className="page-subheading">
                Your secure digital emergency vault at a glance.
              </p>
            </div>
            <Link
              href="/vault"
              className="inline-flex items-center gap-2 rounded-xl bg-brand-gradient px-4 py-2.5 text-sm font-semibold text-white shadow-card transition-all hover:shadow-glow hover:brightness-110 active:scale-[0.98]"
            >
              <Plus className="h-4 w-4" aria-hidden="true" />
              Manage vault
            </Link>
          </div>

          {isError && (
            <div className="alert alert-error mt-6">
              <div className="flex-1">
                <p className="font-medium">Could not load your dashboard.</p>
                <p className="mt-0.5 text-sm opacity-80">Your data is safe — this is likely a temporary connection issue.</p>
              </div>
              <button className="shrink-0 text-sm font-semibold underline" onClick={() => refetch()}>
                Try again
              </button>
            </div>
          )}

          {isLoading ? (
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <Skeleton key={i} className="h-32" />
              ))}
            </div>
          ) : (
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((stat) => (
                <Link key={stat.label} href={stat.to} className="group block">
                  <Card
                    className={cn(
                      "h-full transition-all duration-300 group-hover:-translate-y-1 group-hover:shadow-lifted",
                      stat.danger && "border-red-200 dark:border-red-900"
                    )}
                  >
                    <CardBody className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <p className="truncate text-sm text-slate-500 dark:text-slate-400">{stat.label}</p>
                        <p
                          className={cn(
                            "mt-1 text-3xl font-bold text-slate-900 dark:text-white",
                            stat.danger && "text-red-600 dark:text-red-400"
                          )}
                        >
                          {stat.value}
                        </p>
                      </div>
                      <span
                        className={cn(
                          "flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br text-white shadow-card transition-transform duration-300 group-hover:scale-110",
                          stat.tint
                        )}
                      >
                        <stat.icon className="h-5 w-5" aria-hidden="true" />
                      </span>
                    </CardBody>
                  </Card>
                </Link>
              ))}
            </div>
          )}

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <Card className="lg:col-span-2">
              <CardBody>
                <div className="flex items-center justify-between">
                  <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                    Recent activity
                  </h2>
                  <Link
                    href="/vault"
                    className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 transition hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
                  >
                    Open vault
                    <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                  </Link>
                </div>
                {isLoading ? (
                  <div className="mt-4 space-y-3">
                    {[1, 2, 3].map((i) => (
                      <Skeleton key={i} className="h-9" />
                    ))}
                  </div>
                ) : data?.recent_activity.length ? (
                  <ul className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
                    {data.recent_activity.map((item) => (
                      <li
                        key={item.id}
                        className="flex items-center gap-3 py-3 text-sm text-slate-700 dark:text-slate-300"
                      >
                        <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-400">
                          <Zap className="h-3.5 w-3.5" aria-hidden="true" />
                        </span>
                        <span className="flex-1 leading-snug">{item.message}</span>
                        {item.created_at && (
                          <time className="shrink-0 text-xs text-slate-400 dark:text-slate-500">
                            {new Date(item.created_at).toLocaleDateString(undefined, {
                              month: "short",
                              day: "numeric",
                            })}
                          </time>
                        )}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <div className="mt-4 rounded-xl border border-dashed border-slate-300 px-6 py-10 text-center dark:border-slate-700">
                    <p className="text-sm text-slate-500 dark:text-slate-400">
                      No activity yet. Start by creating your vault.
                    </p>
                  </div>
                )}
              </CardBody>
            </Card>

            <Card>
              <CardBody>
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                  Security status
                </h2>
                <div className="mt-4 space-y-3">
                  <div className="flex items-center justify-between rounded-xl border border-emerald-200 bg-emerald-50 px-4 py-3 dark:border-emerald-900 dark:bg-emerald-950/40">
                    <span className="text-sm font-medium text-emerald-800 dark:text-emerald-300">
                      Account protected
                    </span>
                    <Badge tone="success">Secure</Badge>
                  </div>
                  <div className="flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 dark:border-slate-700">
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Sessions rotating
                    </span>
                    <Badge tone="brand">Active</Badge>
                  </div>
                  <Link
                    href="/security"
                    className="group flex items-center justify-between rounded-xl border border-slate-200 px-4 py-3 transition hover:border-brand-200 hover:bg-brand-50/50 dark:border-slate-700 dark:hover:border-brand-800 dark:hover:bg-brand-900/20"
                  >
                    <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
                      Review sessions
                    </span>
                    <ArrowRight className="h-4 w-4 text-slate-400 transition-transform group-hover:translate-x-0.5 dark:text-slate-500" aria-hidden="true" />
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