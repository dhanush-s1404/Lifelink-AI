"use client";

import { useQuery } from "@tanstack/react-query";
import { Archive, Shield, Users, Zap } from "lucide-react";

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
    { label: "Vaults", value: data?.vaults_count ?? 0, icon: Archive },
    { label: "Vault items", value: data?.items_count ?? 0, icon: Zap },
    { label: "Trusted contacts", value: data?.trusted_contacts_count ?? 0, icon: Users },
    { label: "Pending emergencies", value: data?.pending_emergencies_count ?? 0, icon: Shield },
  ];

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
        <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
        <p className="mt-1 text-sm text-slate-600">
          Your secure digital emergency vault at a glance.
        </p>

        {isError && (
          <div className="mt-6 rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
            <p className="font-medium">Could not load your dashboard.</p>
            <button className="mt-2 text-red-700 underline" onClick={() => refetch()}>
              Try again
            </button>
          </div>
        )}

        {isLoading ? (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-100" />
            ))}
          </div>
        ) : (
          <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            {stats.map((stat) => (
              <Card key={stat.label}>
                <CardBody>
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-500">{stat.label}</p>
                      <p className="mt-1 text-3xl font-bold text-slate-900">{stat.value}</p>
                    </div>
                    <div
                      className={cn(
                        "flex h-10 w-10 items-center justify-center rounded-lg",
                        "bg-brand-50 text-brand-600"
                      )}
                    >
                      <stat.icon className="h-5 w-5" />
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>
        )}

        <Card className="mt-8">
          <CardBody>
            <h2 className="text-base font-semibold text-slate-900">Recent activity</h2>
            {data?.recent_activity.length ? (
              <ul className="mt-4 divide-y divide-slate-100">
                {data.recent_activity.map((item) => (
                  <li key={item.id} className="py-3 text-sm text-slate-700">
                    {item.message}
                  </li>
                ))}
              </ul>
            ) : (
              <p className="mt-4 text-sm text-slate-500">
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
