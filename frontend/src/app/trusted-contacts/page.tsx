"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Check, Plus, Trash2, UserPlus, X } from "lucide-react";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
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
    <span className="inline-flex items-center rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-medium text-emerald-700">
      Active
    </span>
  ) : (
    <span className="inline-flex items-center rounded-full bg-amber-50 px-2.5 py-0.5 text-xs font-medium text-amber-700">
      Pending
    </span>
  );
}

function ContactPermissions({ contact }: { contact: Contact }) {
  const permissions = [];
  if (contact.can_activate_emergency) permissions.push("Can activate emergency");
  if (contact.can_view_vaults) permissions.push("Can view vaults");
  permissions.push(`${contact.access_grace_days}d grace`);
  return <p className="mt-0.5 text-xs text-slate-500">{permissions.join(" · ")}</p>;
}

function ContactRow({
  contact,
  onRemove,
}: {
  contact: Contact;
  onRemove: (id: string) => void;
}) {
  return (
    <li>
      <div className="flex items-center justify-between gap-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-900">
            {contact.contact_name ?? contact.contact_email ?? "Unknown"}
          </p>
          <p className="truncate text-xs text-slate-500">{contact.contact_email}</p>
          <ContactPermissions contact={contact} />
        </div>
        <div className="flex shrink-0 items-center gap-2">
          <StatusBadge status={contact.status} />
          <button
            aria-label="Remove contact"
            className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600"
            onClick={() => onRemove(contact.id)}
          >
            <Trash2 className="h-4 w-4" />
          </button>
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
      </CardHeader>
      <CardBody>
        <form
          className="flex flex-col gap-3"
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
          <p className="text-xs text-slate-500">
            They must have a LifeLink account. Your contact can then accept to become an active
            emergency contact.
          </p>
          <div>
            <Button type="submit" loading={mutation.isPending} disabled={!email.trim()}>
              <UserPlus className="h-4 w-4" />
              Send invitation
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

export default function TrustedContactsPage() {
  const queryClient = useQueryClient();
  const toast = useToast();

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
      invalidate();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
          <h1 className="text-2xl font-bold text-slate-900">Trusted contacts</h1>
          <p className="mt-1 text-sm text-slate-600">
            People you trust to act in an emergency. Invitations require mutual consent.
          </p>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              {incoming && incoming.length > 0 && (
                <Card>
                  <CardHeader>
                    <CardTitle>Incoming requests</CardTitle>
                  </CardHeader>
                  <CardBody className="p-0">
                    <ul className="divide-y divide-slate-100 px-5">
                      {incoming.map((contact) => (
                        <li key={contact.id} className="py-3">
                          <div className="flex items-center justify-between gap-4">
                            <div className="min-w-0">
                              <p className="truncate text-sm font-medium text-slate-900">
                                {contact.contact_name ?? contact.contact_email}
                              </p>
                              <p className="truncate text-xs text-slate-500">
                                {contact.contact_email} wants you as a contact
                              </p>
                            </div>
                            <div className="flex shrink-0 items-center gap-2">
                              <Button
                                variant="secondary"
                                size="sm"
                                onClick={() => decline.mutate(contact.id)}
                                loading={decline.isPending}
                              >
                                <X className="h-4 w-4" />
                                Decline
                              </Button>
                              <Button
                                size="sm"
                                onClick={() => accept.mutate(contact.id)}
                                loading={accept.isPending}
                              >
                                <Check className="h-4 w-4" />
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
                    <div className="p-5 text-sm text-red-800">
                      <p className="font-medium">Could not load your contacts.</p>
                      <button className="mt-2 text-red-700 underline" onClick={() => refetch()}>
                        Try again
                      </button>
                    </div>
                  )}
                  {isLoading ? (
                    <div className="space-y-2 p-5">
                      {[1, 2].map((i) => (
                        <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-100" />
                      ))}
                    </div>
                  ) : contacts && contacts.length > 0 ? (
                    <ul className="divide-y divide-slate-100 px-5">
                      {contacts.map((contact) => (
                        <ContactRow
                          key={contact.id}
                          contact={contact}
                          onRemove={(id) => {
                            if (confirm("Remove this trusted contact?")) remove.mutate(id);
                          }}
                        />
                      ))}
                    </ul>
                  ) : (
                    <div className="p-10 text-center">
                      <Plus className="mx-auto h-8 w-8 text-slate-300" />
                      <p className="mt-3 text-sm text-slate-500">
                        No trusted contacts yet. Invite someone you trust.
                      </p>
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
      </AppShell>
    </RequireAuth>
  );
}
