"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Archive, FolderLock, Lock, Plus } from "lucide-react";
import Link from "next/link";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Skeleton } from "@/components/ui/Skeleton";
import { useToast } from "@/lib/toast";
import { createVault, deleteVault, listVaults, type Vault } from "@/lib/vault";

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
        <div className="flex items-center gap-3">
          <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-card">
            <Plus className="h-4 w-4" aria-hidden="true" />
          </span>
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-white">Create a vault</h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">Keep records organized</p>
          </div>
        </div>
        <form
          className="mt-5 flex flex-col gap-4"
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
          <Button type="submit" loading={mutation.isPending} disabled={!name.trim()} className="w-full">
            <Plus className="h-4 w-4" aria-hidden="true" />
            Create vault
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

function VaultCard({ vault, onDelete }: { vault: Vault; onDelete: (v: Vault) => void }) {
  return (
    <Card className="group transition-all duration-300 hover:-translate-y-1 hover:shadow-lifted">
      <CardBody>
        <div className="flex items-start justify-between gap-3">
          <span className="flex h-12 w-12 items-center justify-center rounded-2xl bg-gradient-to-br from-blue-500 to-blue-700 text-white shadow-card transition-transform duration-300 group-hover:scale-105">
            <FolderLock className="h-5 w-5" aria-hidden="true" />
          </span>
          <Button
            variant="ghost"
            size="xs"
            className="text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 dark:hover:text-red-400"
            onClick={() => onDelete(vault)}
          >
            Delete
          </Button>
        </div>
        <Link
          href={`/vault/${vault.id}`}
          className="mt-4 block truncate font-semibold text-slate-900 transition-colors hover:text-brand-700 dark:text-white dark:hover:text-brand-400"
        >
          {vault.name}
        </Link>
        <p className="mt-1 line-clamp-2 min-h-[2.5rem] text-sm leading-relaxed text-slate-500 dark:text-slate-400">
          {vault.description || "No description"}
        </p>
        <div className="mt-4 flex items-center justify-between border-t border-slate-100 pt-3.5 dark:border-slate-800">
          <span className="inline-flex items-center gap-1.5 text-xs text-slate-500 dark:text-slate-400">
            <Lock className="h-3.5 w-3.5" aria-hidden="true" />
            Encrypted
          </span>
          <Link
            href={`/vault/${vault.id}`}
            className="inline-flex items-center gap-1 text-sm font-medium text-brand-600 transition hover:text-brand-700 dark:text-brand-400 dark:hover:text-brand-300"
          >
            Open
            <Archive className="h-3.5 w-3.5" aria-hidden="true" />
          </Link>
        </div>
      </CardBody>
    </Card>
  );
}

export default function VaultPage() {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [pendingDelete, setPendingDelete] = useState<Vault | null>(null);

  const { data: vaults, isLoading, isError, refetch } = useQuery({
    queryKey: ["vaults"],
    queryFn: listVaults,
  });

  const remove = useMutation({
    mutationFn: (id: string) => deleteVault(id),
    onSuccess: () => {
      toast.push("success", "Vault deleted");
      setPendingDelete(null);
      queryClient.invalidateQueries({ queryKey: ["vaults"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => {
      toast.push("error", err.message);
      setPendingDelete(null);
    },
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex flex-wrap items-end justify-between gap-4">
            <div>
              <h1 className="page-heading">Vault</h1>
              <p className="page-subheading">
                Your encrypted digital emergency vaults, organized by category.
              </p>
            </div>
          </div>

          {isError && (
            <div className="alert alert-error mt-6">
              <div className="flex-1">
                <p className="font-medium">Could not load your vaults.</p>
              </div>
              <button className="shrink-0 text-sm font-semibold underline" onClick={() => refetch()}>
                Try again
              </button>
            </div>
          )}

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            <div className="space-y-6 lg:col-span-2">
              {isLoading ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {[1, 2, 3, 4].map((i) => (
                    <Skeleton key={i} className="h-48" />
                  ))}
                </div>
              ) : vaults && vaults.length > 0 ? (
                <div className="grid gap-4 sm:grid-cols-2">
                  {vaults.map((vault) => (
                    <VaultCard key={vault.id} vault={vault} onDelete={setPendingDelete} />
                  ))}
                </div>
              ) : (
                <EmptyState
                  icon={<FolderLock className="h-6 w-6" aria-hidden="true" />}
                  title="No vaults yet"
                  description="Create your first vault to start protecting your family's most important records."
                  action={
                    <a href="#create-vault">
                      <Button>
                        <Plus className="h-4 w-4" aria-hidden="true" />
                        Create your first vault
                      </Button>
                    </a>
                  }
                />
              )}
            </div>

            <div id="create-vault">
              <CreateVaultCard
                onCreated={() => queryClient.invalidateQueries({ queryKey: ["vaults"] })}
              />
            </div>
          </div>
        </div>

        <ConfirmDialog
          open={pendingDelete !== null}
          onClose={() => setPendingDelete(null)}
          title={pendingDelete ? `Delete "${pendingDelete.name}"?` : ""}
          description="All items inside this vault will be permanently removed."
          loading={remove.isPending}
          onConfirm={() => pendingDelete && remove.mutate(pendingDelete.id)}
        />
      </AppShell>
    </RequireAuth>
  );
}