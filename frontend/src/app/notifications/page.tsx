"use client";

import { BellOff, Mail } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";

export default function NotificationsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <h1 className="page-heading">Notifications</h1>
          <p className="page-subheading">
            LifeLink AI sends notifications by email when something needs your attention.
          </p>

          <div className="empty-state mt-6">
            <BellOff className="empty-state-icon" aria-hidden="true" />
            <p className="empty-state-title">You&apos;re all caught up</p>
            <p className="empty-state-description">
              There are no notifications waiting for you. Emergency activity, password changes,
              and security events are delivered to your inbox.
            </p>
            <div className="mt-4 flex items-center gap-2 text-sm text-slate-500">
              <Mail className="h-4 w-4" aria-hidden="true" />
              Delivered via email
            </div>
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