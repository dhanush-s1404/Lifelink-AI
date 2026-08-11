"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, ShieldAlert, X } from "lucide-react";
import { useMemo, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { listIncoming } from "@/lib/contacts";
import {
  activateEmergency,
  cancelEmergency,
  confirmEmergency,
  listActivated,
  listEmergencies,
  releaseVault,
  type Emergency,
  type EmergencyReleaseItem,
} from "@/lib/emergency";
import { useToast } from "@/lib/toast";
import { cn } from "@/lib/utils";

function formatDateTime(value: string): string {
  return new Date(value).toLocaleString();
}

function StatusBadge({ status }: { status: Emergency["status"] }) {
  const map: Record<Emergency["status"], { label: string; cls: string }> = {
    pending: { label: "Pending", cls: "bg-amber-50 text-amber-700" },
    escalated: { label: "Escalated", cls: "bg-red-50 text-red-700" },
    resolved: { label: "Resolved", cls: "bg-emerald-50 text-emerald-700" },
    cancelled: { label: "Cancelled", cls: "bg-slate-100 text-slate-600" },
  };
  const { label, cls } = map[status];
  return (
    <span className={cn("inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium", cls)}>
      {label}
    </span>
  );
}

function EmergencyCard({
  emergency,
  onConfirm,
  onCancel,
  showVaultAccess,
}: {
  emergency: Emergency;
  onConfirm?: (id: string) => void;
  onCancel?: (id: string) => void;
  showVaultAccess?: boolean;
}) {
  const toast = useToast();
  const [released, setReleased] = useState<EmergencyReleaseItem[] | null>(null);

  const release = useMutation({
    mutationFn: () => releaseVault(emergency.id),
    onSuccess: (data) => {
      setReleased(data);
      toast.push("success", "Vault access unlocked");
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const isActive = emergency.status === "pending" || emergency.status === "escalated";

  return (
    <Card>
      <CardBody>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-900">
              {emergency.contact_name ?? emergency.contact_email ?? "Unknown contact"}
              <span className="font-normal text-slate-400"> raised an emergency</span>
            </p>
            <p className="mt-0.5 text-xs text-slate-500">
              {formatDateTime(emergency.activated_at)} · grace ends {formatDateTime(emergency.grace_end_at)}
            </p>
            {emergency.reason && <p className="mt-1 text-sm text-slate-700">“{emergency.reason}”</p>}
          </div>
          <StatusBadge status={emergency.status} />
        </div>

        {isActive && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {onConfirm && (
              <Button size="sm" onClick={() => onConfirm(emergency.id)}>
                <Check className="h-4 w-4" />
                I&apos;m okay
              </Button>
            )}
            {onCancel && (
              <Button variant="secondary" size="sm" onClick={() => onCancel(emergency.id)}>
                <X className="h-4 w-4" />
                Cancel emergency
              </Button>
            )}
            {showVaultAccess && emergency.status === "escalated" && (
              <Button variant="secondary" size="sm" onClick={() => release.mutate()} loading={release.isPending}>
                <ShieldAlert className="h-4 w-4" />
                View vault
              </Button>
            )}
          </div>
        )}

        {released && (
          <div className="mt-4 rounded-lg bg-slate-50 p-4">
            <p className="text-sm font-medium text-slate-900">
              Released vault contents ({released.length} items)
            </p>
            {released.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500">No items in the vault.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {released.map((item) => (
                  <li key={item.item_id} className="border-t border-slate-200 pt-3">
                    <p className="text-sm font-medium text-slate-900">
                      {item.title} · {item.vault_name}
                    </p>
                    <pre className="mt-1 overflow-x-auto rounded bg-white p-2 font-mono text-xs text-slate-700">
                      {JSON.stringify(item.content, null, 2)}
                    </pre>
                  </li>
                ))}
              </ul>
            )}
          </div>
        )}
      </CardBody>
    </Card>
  );
}

function ActivateForm() {
  const toast = useToast();
  const queryClient = useQueryClient();

  const { data: incoming } = useQuery({ queryKey: ["contacts", "incoming"], queryFn: listIncoming });
  const activatable = useMemo(
    () => (incoming ?? []).filter((c) => c.status === "active" && c.can_activate_emergency),
    [incoming]
  );

  const [ownerId, setOwnerId] = useState("");
  const [reason, setReason] = useState("");

  const mutation = useMutation({
    mutationFn: () => activateEmergency(ownerId, reason || undefined),
    onSuccess: () => {
      toast.push("success", "Emergency raised. The owner has been notified.");
      setReason("");
      queryClient.invalidateQueries({ queryKey: ["emergencies"] });
      queryClient.invalidateQueries({ queryKey: ["emergencies", "activated"] });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Raise an emergency</CardTitle>
      </CardHeader>
      <CardBody>
        {activatable.length === 0 ? (
          <p className="text-sm text-slate-500">
            No owners have granted you emergency access yet. They must add you as an active
            trusted contact with emergency permission first.
          </p>
        ) : (
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              if (ownerId) mutation.mutate();
            }}
          >
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-slate-700">For owner</span>
              <select
                value={ownerId}
                onChange={(e) => setOwnerId(e.target.value)}
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
              >
                <option value="">Select an owner…</option>
                {activatable.map((c) => (
                  <option key={c.id} value={c.contact_id}>
                    {c.contact_name ?? c.contact_email}
                  </option>
                ))}
              </select>
            </label>
            <label className="flex flex-col gap-1.5">
              <span className="text-sm font-medium text-slate-700">Reason (optional)</span>
              <input
                value={reason}
                onChange={(e) => setReason(e.target.value)}
                placeholder="e.g. No response since Monday"
                className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm text-slate-900 shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
              />
            </label>
            <div>
              <Button type="submit" variant="danger" loading={mutation.isPending} disabled={!ownerId}>
                <AlertTriangle className="h-4 w-4" />
                Raise emergency
              </Button>
            </div>
          </form>
        )}
      </CardBody>
    </Card>
  );
}

export default function EmergencyPage() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: emergencies, isLoading } = useQuery({
    queryKey: ["emergencies"],
    queryFn: listEmergencies,
  });
  const { data: activated } = useQuery({
    queryKey: ["emergencies", "activated"],
    queryFn: listActivated,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["emergencies"] });
    queryClient.invalidateQueries({ queryKey: ["emergencies", "activated"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
  };

  const confirm = useMutation({
    mutationFn: (id: string) => confirmEmergency(id),
    onSuccess: () => {
      toast.push("success", "Emergency confirmed");
      invalidate();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const cancel = useMutation({
    mutationFn: (id: string) => cancelEmergency(id),
    onSuccess: () => {
      toast.push("success", "Emergency cancelled");
      invalidate();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
          <h1 className="text-2xl font-bold text-slate-900">Emergency</h1>
          <p className="mt-1 text-sm text-slate-600">
            A trusted contact can raise an emergency. If you don&apos;t confirm within the grace
            period, they get read access to your vault.
          </p>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <div>
                <h2 className="text-base font-semibold text-slate-900">About you</h2>
                {isLoading ? (
                  <div className="mt-3 space-y-3">
                    {[1, 2].map((i) => (
                      <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-100" />
                    ))}
                  </div>
                ) : emergencies && emergencies.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {emergencies.map((e) => (
                      <EmergencyCard
                        key={e.id}
                        emergency={e}
                        onConfirm={(id) => confirm.mutate(id)}
                        onCancel={(id) => cancel.mutate(id)}
                      />
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">
                    No emergencies have been raised for you.
                  </p>
                )}
              </div>

              <div>
                <h2 className="text-base font-semibold text-slate-900">You raised</h2>
                {activated && activated.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {activated.map((e) => (
                      <EmergencyCard key={e.id} emergency={e} showVaultAccess />
                    ))}
                  </div>
                ) : (
                  <p className="mt-3 text-sm text-slate-500">
                    You haven&apos;t raised any emergencies.
                  </p>
                )}
              </div>
            </div>

            <div>
              <ActivateForm />
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
