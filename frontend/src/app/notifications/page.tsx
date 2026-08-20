"use client";

import { BellOff, Mail } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { EmptyState } from "@/components/ui/EmptyState";
import { Button } from "@/components/ui/Button";

export default function NotificationsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-3">
            <span className="page-heading-icon">
              <Mail className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h1 className="page-heading">Notifications</h1>
              <p className="page-subheading">
                LifeLink AI sends notifications by email when something needs your attention.
              </p>
            </div>
          </div>

          <div className="mt-8">
            <EmptyState
              icon={<BellOff className="h-6 w-6" aria-hidden="true" />}
              title="You're all caught up"
              description="There are no notifications waiting for you. Emergency activity, password changes, and security events are delivered to your inbox."
              action={
                <span className="inline-flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1.5 text-xs font-medium text-slate-500 dark:border-slate-700 dark:bg-night-900 dark:text-slate-400">
                  <Mail className="h-3.5 w-3.5" aria-hidden="true" />
                  Delivered via email
                </span>
              }
            />
          </div>

          <div className="mt-6">
            <Link href="/dashboard">
              <Button variant="secondary">Back to dashboard</Button>
            </Link>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}