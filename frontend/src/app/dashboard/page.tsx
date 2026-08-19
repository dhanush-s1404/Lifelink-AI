"use client";

import { useQuery } from "@tanstack/react-query";
import { Archive, ArrowRight, Shield, Users, Zap } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Card, CardBody } from "@/components/ui/Card";
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
    { label: "Vaults", value: data?.vaults_count ?? 0, icon: Archive, to: "/vault" },
    { label: "Vault items", value: data?.items_count ?? 0, icon: Zap, to: "/vault" },
    { label: "Trusted contacts", value: data?.trusted_contacts_count ?? 0, icon: Users, to: "/trusted-contacts" },
    {
      label: "Pending emergencies",
      value: data?.pending_emergencies_count ?? 0,
      icon: Shield,
      to: "/emergency",
      danger: (data?.pending_emergencies_count ?? 0) > 0,
    },
  ];

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
          <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Dashboard</h1>
          <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
            Your secure digital emergency vault at a glance.
          </p>

          {isError && (
            <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800 dark:border-red-900 dark:bg-red-950/40 dark:text-red-300">
              <p className="font-medium">Could not load your dashboard.</p>
              <button className="mt-2 text-red-700 underline dark:text-red-300" onClick={() => refetch()}>
                Try again
              </button>
            </div>
          )}

          {isLoading ? (
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="skeleton h-28" />
              ))}
            </div>
          ) : (
            <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {stats.map((stat) => (
                <Link key={stat.label} href={stat.to} className="group block">
                  <Card
                    className={cn(
                      "transition group-hover:-translate-y-0.5 group-hover:shadow-pop",
                      stat.danger && "border-red-200 dark:border-red-900"
                    )}
                  >
                    <CardBody>
                      <div className="flex items-center justify-between">
                        <div>
                          <p className="text-sm text-slate-500 dark:text-slate-400">{stat.label}</p>
                          <p
                            className={cn(
                              "mt-1 text-3xl font-bold text-slate-900 dark:text-white",
                              stat.danger && "text-red-600 dark:text-red-400"
                            )}
                          >
                            {stat.value}
                          </p>
                        </div>
                        <div
                          className={cn(
                            "flex h-11 w-11 items-center justify-center rounded-xl",
                            stat.danger
                              ? "bg-red-100 text-red-600 dark:bg-red-900/50 dark:text-red-400"
                              : "bg-brand-gradient text-white shadow-card"
                          )}
                        >
                          <stat.icon className="h-5 w-5" />
                        </div>
                      </div>
                    </CardBody>
                  </Card>
                </Link>
              ))}
            </div>
          )}

          <Card className="mt-8">
            <CardBody>
              <div className="flex items-center justify-between">
                <h2 className="text-base font-semibold text-slate-900 dark:text-white">
                  Recent activity
                </h2>
                <Link
                  href="/vault"
                  className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
                >
                  Open vault
                  <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
                </Link>
              </div>
              {data?.recent_activity.length ? (
                <ul className="mt-4 divide-y divide-slate-100 dark:divide-slate-800">
                  {data.recent_activity.map((item) => (
                    <li
                      key={item.id}
                      className="flex items-center gap-3 py-3 text-sm text-slate-700 dark:text-slate-300"
                    >
                      <span className="h-1.5 w-1.5 shrink-0 rounded-full bg-brand-500" />
                      {item.message}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="mt-4 text-sm text-slate-500 dark:text-slate-400">
                  No activity yet. Start by creating your vault.
                </p>
              )}
            </CardBody>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}