"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, Lock, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useToast } from "@/lib/toast";
import { createVault, deleteVault, listVaults } from "@/lib/vault";

function CreateVaultCard({ onCreated }: { onCreated: () => void }) {
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const toast = useToast();

  const mutation = useMutation({
    mutationFn: () =>
      createVault({ name, description: description || undefined }),
    onSuccess: () => {
      toast.push("success", "Vault created");
      setName("");
      setDescription("");
      onCreated();
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <Card>
      <CardBody>
        <div className="flex items-center gap-2 text-slate-900">
          <Plus className="h-4 w-4" />
          <h2 className="font-semibold">Create a vault</h2>
        </div>
        <p className="mt-1 text-sm text-slate-500">
          Vaults keep your sensitive records organized and encrypted at rest.
        </p>
        <form
          className="mt-4 flex flex-col gap-3"
          onSubmit={(e) => {
            e.preventDefault();
            if (name.trim()) mutation.mutate();
          }}
        >
          <Input
            label="Name"
            placeholder="e.g. Family Insurance"
            value={name}
            onChange={(e) => setName(e.target.value)}
            required
          />
          <Input
            label="Description (optional)"
            placeholder="What is stored here?"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
          />
          <div>
            <Button type="submit" loading={mutation.isPending} disabled={!name.trim()}>
              Create vault
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

export default function VaultPage() {
  const queryClient = useQueryClient();
  const toast = useToast();

  const { data: vaults, isLoading, isError, refetch } = useQuery({
    queryKey: ["vaults"],
    queryFn: listVaults,
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteVault(id),
    onSuccess: () => {
      toast.push("success", "Vault deleted");
      queryClient.invalidateQueries({ queryKey: ["vaults"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
          <h1 className="text-2xl font-bold text-slate-900">Vault</h1>
          <p className="mt-1 text-sm text-slate-600">
            Your encrypted digital emergency vaults.
          </p>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              {isError && (
                <div className="rounded-lg border border-red-200 bg-red-50 p-4 text-sm text-red-800">
                  <p className="font-medium">Could not load your vaults.</p>
                  <button className="mt-2 text-red-700 underline" onClick={() => refetch()}>
                    Try again
                  </button>
                </div>
              )}

              {isLoading ? (
                <div className="space-y-4">
                  {[1, 2].map((i) => (
                    <div key={i} className="h-24 animate-pulse rounded-xl bg-slate-100" />
                  ))}
                </div>
              ) : vaults && vaults.length > 0 ? (
                <ul className="space-y-3">
                  {vaults.map((vault) => (
                    <Card key={vault.id}>
                      <CardBody className="flex items-center justify-between gap-4">
                        <div className="flex min-w-0 items-center gap-3">
                          <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600">
                            <Lock className="h-5 w-5" />
                          </div>
                          <div className="min-w-0">
                            <Link
                              href={`/vault/${vault.id}`}
                              className="block truncate font-semibold text-slate-900 hover:text-brand-700"
                            >
                              {vault.name}
                            </Link>
                            <p className="truncate text-sm text-slate-500">
                              {vault.description || "No description"}
                            </p>
                          </div>
                        </div>
                        <div className="flex shrink-0 items-center gap-2">
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => (window.location.href = `/vault/${vault.id}`)}
                          >
                            <Archive className="h-4 w-4" />
                            Open
                          </Button>
                          <button
                            aria-label={`Delete ${vault.name}`}
                            className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600"
                            onClick={() => {
                              if (confirm(`Delete vault "${vault.name}"? This cannot be undone.`)) {
                                remove.mutate(vault.id);
                              }
                            }}
                          >
                            <Trash2 className="h-4 w-4" />
                          </button>
                        </div>
                      </CardBody>
                    </Card>
                  ))}
                </ul>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 p-10 text-center">
                  <Archive className="mx-auto h-8 w-8 text-slate-300" />
                  <p className="mt-3 text-sm text-slate-500">
                    No vaults yet. Create your first vault to get started.
                  </p>
                </div>
              )}
            </div>

            <div>
              <CreateVaultCard onCreated={() => queryClient.invalidateQueries({ queryKey: ["vaults"] })} />
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
