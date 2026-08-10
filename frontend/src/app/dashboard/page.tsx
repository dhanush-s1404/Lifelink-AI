"use client";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { useAuth } from "@/lib/auth";

export default function DashboardPage() {
  const { user, logout } = useAuth();

  return (
    <RequireAuth>
      <main className="mx-auto max-w-5xl p-8">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
            <p className="text-sm text-slate-600">
              Welcome back{user?.full_name ? `, ${user.full_name}` : ""}.
            </p>
          </div>
          <Button variant="secondary" onClick={logout}>
            Sign out
          </Button>
        </div>

        <div className="mt-8 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
          <Card>
            <CardHeader>
              <CardTitle>Your vault</CardTitle>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-slate-600">
                Store documents, accounts, and instructions for your family.
              </p>
            </CardBody>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Trusted contacts</CardTitle>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-slate-600">
                Choose who can request access in an emergency.
              </p>
            </CardBody>
          </Card>
          <Card>
            <CardHeader>
              <CardTitle>Emergency readiness</CardTitle>
            </CardHeader>
            <CardBody>
              <p className="text-sm text-slate-600">
                Make sure the people you trust know how to reach your vault.
              </p>
            </CardBody>
          </Card>
        </div>
      </main>
    </RequireAuth>
  );
}
