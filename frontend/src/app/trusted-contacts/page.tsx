"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, ShieldCheck, UserPlus, X, Users, Lock } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import {
  acceptContact,
  declineContact,
  inviteContact,
  listContacts,
  listIncoming,
  removeContact,
  type Contact,
} from "@/lib/contacts";
import { useToast } from "@/lib/toast";

function StatusBadge({ status }: { status: Contact["status"] }) {
  return status === "active" ? (
    <Badge tone="success">
      <ShieldCheck className="h-3 w-3" aria-hidden="true" />
      Active
    </Badge>
  ) : (
    <Badge tone="warning">Pending</Badge>
  );
}

function ContactPermissions({ contact }: { contact: Contact }) {
  const permissions: string[] = [];
  if (contact.can_activate_emergency) permissions.push("Can activate emergency");
  if (contact.can_view_vaults) permissions.push("Can view vaults");
  permissions.push(`${contact.access_grace_days}d grace`);
  return (
    <div className="mt-1.5 flex flex-wrap items-center gap-1.5">
      {contact.can_activate_emergency && (
        <span className="inline-flex items-center gap-1 rounded-md bg-amber-50 px-1.5 py-0.5 text-[0.68rem] font-medium text-amber-700 dark:bg-amber-950/40 dark:text-amber-300">
          Emergency
        </span>
      )}
      {contact.can_view_vaults && (
        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-50 px-1.5 py-0.5 text-[0.68rem] font-medium text-emerald-700 dark:bg-emerald-950/40 dark:text-emerald-300">
          <Lock className="h-3 w-3" aria-hidden="true" />
          Vault access
        </span>
      )}
      <span className="text-xs text-slate-400 dark:text-slate-500">
        {contact.access_grace_days}d grace
      </span>
    </div>
  );
}

function ContactRow({
  contact,
  onRemove,
}: {
  contact: Contact;
  onRemove: (contact: Contact) => void;
}) {
  return (
    <li className="px-5">
      <div className="flex items-center justify-between gap-4 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-xs font-semibold text-white">
            {(contact.contact_name ?? contact.contact_email ?? "?")[0]?.toUpperCase()}
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
              {contact.contact_name ?? contact.contact_email ?? "Unknown"}
            </p>
            {contact.contact_email && (
              <p className="truncate text-xs text-slate-500 dark:text-slate-400">{contact.contact_email}</p>
            )}
            <ContactPermissions contact={contact} />
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusBadge status={contact.status} />
          <Button
            variant="ghost"
            size="xs"
            className="text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 dark:hover:text-red-400"
            onClick={() => onRemove(contact)}
          >
            Remove
          </Button>
        </div>
      </div>
    </li>
  );
}

function InviteForm({ onInvited }: { onInvited: () => void }) {
  const [email, setEmail] = useState("");
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: () => inviteContact({ email, access_grace_days: 30 }),
    onSuccess: () => {
      toast.push("success", "Invitation sent");
      setEmail("");
      onInvited();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Invite a trusted contact</CardTitle>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Both sides must consent
        </p>
      </CardHeader>
      <CardBody>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (email.trim()) mutation.mutate();
          }}
        >
          <Input
            label="Email"
            type="email"
            placeholder="trusted.friend@example.com"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <p className="rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs leading-relaxed text-slate-500 dark:border-slate-700 dark:bg-night-900 dark:text-slate-400">
            They must have a LifeLink account. Your contact can then accept to become an active
            emergency contact.
          </p>
          <Button type="submit" loading={mutation.isPending} disabled={!email.trim()}>
            <UserPlus className="h-4 w-4" aria-hidden="true" />
            Send invitation
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

export default function TrustedContactsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [pendingRemove, setPendingRemove] = useState<Contact | null>(null);

  const { data: contacts, isLoading, isError, refetch } = useQuery({
    queryKey: ["contacts"],
    queryFn: listContacts,
  });

  const { data: incoming } = useQuery({
    queryKey: ["contacts", "incoming"],
    queryFn: listIncoming,
  });

  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["contacts"] });
    queryClient.invalidateQueries({ queryKey: ["contacts", "incoming"] });
    queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
  };

  const accept = useMutation({
    mutationFn: (id: string) => acceptContact(id),
    onSuccess: () => {
      toast.push("success", "Contact accepted");
      invalidate();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const decline = useMutation({
    mutationFn: (id: string) => declineContact(id),
    onSuccess: () => {
      toast.push("success", "Request declined");
      invalidate();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const remove = useMutation({
    mutationFn: (id: string) => removeContact(id),
    onSuccess: () => {
      toast.push("success", "Contact removed");
      setPendingRemove(null);
      invalidate();
    },
    onError: (err: Error) => {
      toast.push("error", err.message);
      setPendingRemove(null);
    },
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="page-heading">Trusted contacts</h1>
              <p className="page-subheading">
                People you trust to act in an emergency. Invitations require mutual consent.
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              {incoming && incoming.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Incoming requests</CardTitle>
                  </CardHeader>
                  <CardBody className="p-0">
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {incoming.map((contact) => (
                        <li key={contact.id} className="px-5 py-4">
                          <div className="flex items-center justify-between gap-4">
                            <div className="flex min-w-0 items-center gap-3">
                              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-slate-100 text-xs font-semibold text-slate-600 dark:bg-night-800 dark:text-slate-300">
                                {(contact.contact_name ?? contact.contact_email ?? "?")[0]?.toUpperCase()}
                              </span>
                              <div className="min-w-0">
                                <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
                                  {contact.contact_name ?? contact.contact_email}
                                </p>
                                <p className="truncate text-xs text-slate-500 dark:text-slate-400">
                                  wants you as a contact
                                </p>
                              </div>
                            </div>
                            <div className="flex shrink-0 items-center gap-2">
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => decline.mutate(contact.id)}
                                loading={decline.isPending}
                              >
                                <X className="h-4 w-4" aria-hidden="true" />
                                Decline
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => accept.mutate(contact.id)}
                                loading={accept.isPending}
                              >
                                <Check className="h-4 w-4" aria-hidden="true" />
                                Accept
                              </Button>
                            </div>
                          </div>
                        </li>
                      ))}
                    </ul>
                  </CardBody>
                </Card>
              )}

              <Card>
                <CardHeader>
                  <CardTitle>Your contacts</CardTitle>
                </CardHeader>
                <CardBody className="p-0">
                  {isError && (
                    <div className="alert alert-error m-5">
                      <div className="flex-1">
                        <p className="font-medium">Could not load your contacts.</p>
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
                  ) : contacts && contacts.length > 0 ? (
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {contacts.map((contact) => (
                        <ContactRow
                          key={contact.id}
                          contact={contact}
                          onRemove={setPendingRemove}
                        />
                      ))}
                    </ul>
                  ) : (
                    <div className="p-6">
                      <EmptyState
                        icon={<Users className="h-6 w-6" aria-hidden="true" />}
                        title="No trusted contacts yet"
                        description="Invite someone you trust. Access is granted by mutual consent."
                      />
                    </div>
                  )}
                </CardBody>
              </Card>
            </div>

            <div>
              <InviteForm onInvited={invalidate} />
            </div>
          </div>
        </div>

        <ConfirmDialog
          open={pendingRemove !== null}
          onClose={() => setPendingRemove(null)}
          title="Remove this trusted contact?"
          description="They will immediately lose access to your vault and emergency tools."
          loading={remove.isPending}
          onConfirm={() => pendingRemove && remove.mutate(pendingRemove.id)}
        />
      </AppShell>
    </RequireAuth>
  );
}