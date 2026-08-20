"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { AlertTriangle, Check, Eye, ShieldAlert, X } from "lucide-react";
import { useMemo, useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { EmptyState } from "@/components/ui/EmptyState";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { Textarea } from "@/components/ui/Textarea";
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
  return new Date(value).toLocaleString(undefined, {
    month: "short",
    day: "numeric",
    hour: "numeric",
    minute: "2-digit",
  });
}

function StatusBadge({ status }: { status: Emergency["status"] }) {
  const map: Record<Emergency["status"], { label: string; tone: "warning" | "danger" | "success" | "neutral" }> = {
    pending: { label: "Pending", tone: "warning" },
    escalated: { label: "Escalated", tone: "danger" },
    resolved: { label: "Resolved", tone: "success" },
    cancelled: { label: "Cancelled", tone: "neutral" },
  };
  const { label, tone } = map[status];
  return <Badge tone={tone}>{label}</Badge>;
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
    <Card className={cn("overflow-hidden", isActive && "border-amber-300 dark:border-amber-800")}>
      {isActive && (
        <div className="flex items-center gap-2 bg-amber-50 px-5 py-2 text-xs font-medium text-amber-800 dark:bg-amber-950/40 dark:text-amber-300">
          <AlertTriangle className="h-3.5 w-3.5" aria-hidden="true" />
          Action needed — grace period ends {formatDateTime(emergency.grace_end_at)}
        </div>
      )}
      <CardBody>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div className="min-w-0">
            <p className="text-sm font-semibold text-slate-900 dark:text-white">
              {emergency.contact_name ?? emergency.contact_email ?? "Unknown contact"}
              <span className="font-normal text-slate-400 dark:text-slate-500"> raised an emergency</span>
            </p>
            <p className="mt-1 text-xs text-slate-500 dark:text-slate-400">
              Activated {formatDateTime(emergency.activated_at)}
            </p>
            {emergency.reason && (
              <p className="mt-2 rounded-lg border-l-2 border-amber-300 bg-slate-50 px-3 py-2 text-sm italic text-slate-700 dark:border-amber-700 dark:bg-night-950 dark:text-slate-200">
                “{emergency.reason}”
              </p>
            )}
          </div>
          <StatusBadge status={emergency.status} />
        </div>

        {isActive && (
          <div className="mt-4 flex flex-wrap items-center gap-2">
            {onConfirm && (
              <Button size="sm" onClick={() => onConfirm(emergency.id)}>
                <Check className="h-4 w-4" aria-hidden="true" />
                I&apos;m okay
              </Button>
            )}
            {onCancel && (
              <Button variant="secondary" size="sm" onClick={() => onCancel(emergency.id)}>
                <X className="h-4 w-4" aria-hidden="true" />
                Cancel emergency
              </Button>
            )}
            {showVaultAccess && emergency.status === "escalated" && (
              <Button variant="secondary" size="sm" onClick={() => release.mutate()} loading={release.isPending}>
                <Eye className="h-4 w-4" aria-hidden="true" />
                View vault
              </Button>
            )}
          </div>
        )}

        {released && (
          <div className="mt-4 animate-fade-in rounded-xl border border-slate-200 bg-slate-50 p-4 dark:border-slate-700 dark:bg-night-950">
            <p className="flex items-center gap-2 text-sm font-medium text-slate-900 dark:text-white">
              <ShieldAlert className="h-4 w-4 text-brand-600 dark:text-brand-400" aria-hidden="true" />
              Released vault contents ({released.length} items)
            </p>
            {released.length === 0 ? (
              <p className="mt-2 text-sm text-slate-500 dark:text-slate-400">No items in the vault.</p>
            ) : (
              <ul className="mt-3 space-y-3">
                {released.map((item) => (
                  <li key={item.item_id} className="border-t border-slate-200 pt-3 dark:border-slate-800">
                    <p className="text-sm font-medium text-slate-900 dark:text-white">
                      {item.title} <span className="font-normal text-slate-400">· {item.vault_name}</span>
                    </p>
                    <pre className="mt-1 overflow-x-auto rounded-lg bg-white p-3 font-mono text-xs leading-relaxed text-slate-700 dark:bg-night-900 dark:text-slate-200">
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
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          For trusted contacts who granted you access
        </p>
      </CardHeader>
      <CardBody>
        {activatable.length === 0 ? (
          <EmptyState
            icon={<AlertTriangle className="h-6 w-6" aria-hidden="true" />}
            title="No owners yet"
            description="No owners have granted you emergency access yet. They must add you as an active trusted contact with emergency permission first."
          />
        ) : (
          <form
            className="flex flex-col gap-4"
            onSubmit={(e) => {
              e.preventDefault();
              if (ownerId) mutation.mutate();
            }}
          >
            <Select label="For owner" value={ownerId} onChange={(e) => setOwnerId(e.target.value)}>
              <option value="">Select an owner…</option>
              {activatable.map((c) => (
                <option key={c.id} value={c.contact_id}>
                  {c.contact_name ?? c.contact_email}
                </option>
              ))}
            </Select>
            <Textarea
              label="Reason (optional)"
              placeholder="e.g. No response since Monday"
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
            />
            <Button type="submit" variant="danger" loading={mutation.isPending} disabled={!ownerId}>
              <AlertTriangle className="h-4 w-4" aria-hidden="true" />
              Raise emergency
            </Button>
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
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="page-heading">Emergency</h1>
              <p className="page-subheading">
                A trusted contact can raise an emergency. If you don&apos;t confirm within the
                grace period, they get read access to your vault.
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  <AlertTriangle className="h-4 w-4 text-amber-500" aria-hidden="true" />
                  About you
                </h2>
                {isLoading ? (
                  <div className="mt-3 space-y-3">
                    {[1, 2].map((i) => (
                      <Skeleton key={i} className="h-28" />
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
                  <div className="mt-3">
                    <EmptyState
                      icon={<ShieldAlert className="h-6 w-6" aria-hidden="true" />}
                      title="No emergencies for you"
                      description="When a trusted contact raises an emergency, it will appear here for you to confirm or cancel."
                    />
                  </div>
                )}
              </div>

              <div>
                <h2 className="flex items-center gap-2 text-sm font-semibold uppercase tracking-wide text-slate-500 dark:text-slate-400">
                  <Eye className="h-4 w-4 text-brand-500" aria-hidden="true" />
                  You raised
                </h2>
                {activated && activated.length > 0 ? (
                  <div className="mt-3 space-y-3">
                    {activated.map((e) => (
                      <EmergencyCard key={e.id} emergency={e} showVaultAccess />
                    ))}
                  </div>
                ) : (
                  <div className="mt-3">
                    <EmptyState
                      icon={<Eye className="h-6 w-6" aria-hidden="true" />}
                      title="Nothing raised by you"
                      description="Use the form to raise an emergency for an owner who has granted you access."
                    />
                  </div>
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