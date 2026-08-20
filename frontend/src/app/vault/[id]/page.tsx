"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Eye, EyeOff, Plus, ShieldCheck, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { ConfirmDialog } from "@/components/ui/Dialog";
import { EmptyState } from "@/components/ui/EmptyState";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Skeleton } from "@/components/ui/Skeleton";
import { Textarea } from "@/components/ui/Textarea";
import { Badge } from "@/components/ui/Badge";
import { DocumentSection } from "@/components/vault/DocumentSection";
import { ItemTypeIcon } from "@/components/vault/ItemTypeIcon";
import { useToast } from "@/lib/toast";
import {
  createItem,
  deleteItem,
  getItem,
  ITEM_TYPES,
  itemTypeLabel,
  listItems,
  type ItemType,
  type VaultItem,
  type VaultItemDetail,
} from "@/lib/vault";

function AddItemForm({ vaultId }: { vaultId: string }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [title, setTitle] = useState("");
  const [itemType, setItemType] = useState<ItemType>("note");
  const [contentJson, setContentJson] = useState('{\n  "note": ""\n}');

  const mutation = useMutation({
    mutationFn: () => {
      const content = JSON.parse(contentJson || "{}") as Record<string, unknown>;
      return createItem(vaultId, { item_type: itemType, title, content });
    },
    onSuccess: () => {
      toast.push("success", "Item added");
      setTitle("");
      setContentJson('{\n  "note": ""\n}');
      queryClient.invalidateQueries({ queryKey: ["vault", vaultId, "items"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add an item</CardTitle>
        <p className="mt-0.5 text-xs text-slate-500 dark:text-slate-400">
          Content is encrypted at rest
        </p>
      </CardHeader>
      <CardBody>
        <form
          className="flex flex-col gap-4"
          onSubmit={(e) => {
            e.preventDefault();
            if (!title.trim()) return;
            try {
              JSON.parse(contentJson || "{}");
            } catch {
              toast.push("error", "Content must be valid JSON");
              return;
            }
            mutation.mutate();
          }}
        >
          <Input
            label="Title"
            placeholder="e.g. Health insurance card"
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            required
          />
          <Select
            label="Type"
            value={itemType}
            onChange={(e) => setItemType(e.target.value as ItemType)}
          >
            {ITEM_TYPES.map((t) => (
              <option key={t.value} value={t.value}>
                {t.label}
              </option>
            ))}
          </Select>
          <Textarea
            label="Content (JSON)"
            hint={'Structured data stored encrypted, e.g. { "value": "ABC-123" }'}
            value={contentJson}
            onChange={(e) => setContentJson(e.target.value)}
            rows={6}
            spellCheck={false}
            className="font-mono text-xs"
          />
          <Button type="submit" loading={mutation.isPending} disabled={!title.trim()}>
            <Plus className="h-4 w-4" aria-hidden="true" />
            Add item
          </Button>
        </form>
      </CardBody>
    </Card>
  );
}

function ItemRow({ vaultId, item }: { vaultId: string; item: VaultItem }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [revealed, setRevealed] = useState(false);
  const [detail, setDetail] = useState<VaultItemDetail | null>(null);
  const [confirmOpen, setConfirmOpen] = useState(false);

  const load = useMutation({
    mutationFn: () => getItem(vaultId, item.id),
    onSuccess: (data) => {
      setDetail(data);
      setRevealed(true);
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const remove = useMutation({
    mutationFn: () => deleteItem(vaultId, item.id),
    onSuccess: () => {
      toast.push("success", "Item deleted");
      setConfirmOpen(false);
      queryClient.invalidateQueries({ queryKey: ["vault", vaultId, "items"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => {
      toast.push("error", err.message);
      setConfirmOpen(false);
    },
  });

  return (
    <li className="px-5">
      <div className="flex items-center justify-between gap-4 py-4">
        <div className="flex min-w-0 items-center gap-3">
          <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-slate-50 ring-1 ring-slate-100 dark:bg-night-800 dark:ring-slate-700">
            <ItemTypeIcon itemType={item.item_type} className="h-5 w-5" />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{item.title}</p>
            <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500 dark:text-slate-400">
              <span>{itemTypeLabel(item.item_type)}</span>
              <span className="text-slate-300 dark:text-slate-600">·</span>
              <span>version {item.version}</span>
            </div>
          </div>
        </div>
        <div className="flex shrink-0 items-center gap-1.5">
          <Button
            variant={revealed ? "ghost" : "outline"}
            size="sm"
            onClick={() => (revealed ? setRevealed(false) : load.mutate())}
            loading={load.isPending}
          >
            {revealed ? <EyeOff className="h-4 w-4" aria-hidden="true" /> : <Eye className="h-4 w-4" aria-hidden="true" />}
            {revealed ? "Hide" : "Reveal"}
          </Button>
          <Button
            variant="ghost"
            size="sm"
            className="text-slate-400 hover:bg-red-50 hover:text-red-600 dark:hover:bg-red-950/40 dark:hover:text-red-400"
            onClick={() => setConfirmOpen(true)}
            aria-label={`Delete ${item.title}`}
          >
            <Trash2 className="h-4 w-4" aria-hidden="true" />
          </Button>
        </div>
      </div>

      {revealed && detail && (
        <div className="mb-4 animate-fade-in space-y-3">
          <div className="overflow-hidden rounded-xl border border-slate-200 dark:border-slate-700">
            <div className="flex items-center justify-between border-b border-slate-200 bg-slate-50 px-4 py-2 dark:border-slate-700 dark:bg-night-800">
              <span className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 dark:text-slate-400">
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-500" aria-hidden="true" />
                Decrypted content
              </span>
              <span className="text-xs text-slate-400 dark:text-slate-500">v{detail.version}</span>
            </div>
            <pre className="overflow-x-auto bg-white px-4 py-3 font-mono text-xs leading-relaxed text-slate-800 dark:bg-night-950 dark:text-slate-100">
              {JSON.stringify(detail.content, null, 2)}
            </pre>
          </div>
          <DocumentSection vaultId={vaultId} itemId={item.id} />
        </div>
      )}

      <ConfirmDialog
        open={confirmOpen}
        onClose={() => setConfirmOpen(false)}
        title={`Delete "${item.title}"?`}
        loading={remove.isPending}
        onConfirm={() => remove.mutate()}
      />
    </li>
  );
}

export default function VaultDetailPage() {
  const params = useParams<{ id: string }>();
  const vaultId = params.id;

  const { data: items, isLoading, isError, refetch } = useQuery({
    queryKey: ["vault", vaultId, "items"],
    queryFn: () => listItems(vaultId),
    enabled: Boolean(vaultId),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-3">
            <Link
              href="/vault"
              className="rounded-xl p-2 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-night-800 dark:hover:text-white"
              aria-label="Back to vaults"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="page-heading">Vault items</h1>
              <p className="page-subheading">
                Contents are encrypted at rest. Reveal an item to view its decrypted content.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="space-y-4 lg:col-span-2">
              {isError && (
                <div className="alert alert-error">
                  <div className="flex-1">
                    <p className="font-medium">Could not load items.</p>
                  </div>
                  <button className="shrink-0 text-sm font-semibold underline" onClick={() => refetch()}>
                    Try again
                  </button>
                </div>
              )}

              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} className="h-16" />
                  ))}
                </div>
              ) : items && items.length > 0 ? (
                <Card>
                  <CardBody className="p-0">
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800">
                      {items.map((item) => (
                        <ItemRow key={item.id} vaultId={vaultId} item={item} />
                      ))}
                    </ul>
                  </CardBody>
                </Card>
              ) : (
                <EmptyState
                  icon={<Plus className="h-6 w-6" aria-hidden="true" />}
                  title="No items yet"
                  description="Add your first sensitive record — a policy number, medical detail, or account reference."
                  action={
                    <a href="#add-item">
                      <Button>
                        <Plus className="h-4 w-4" aria-hidden="true" />
                        Add your first item
                      </Button>
                    </a>
                  }
                />
              )}

              <div className="flex items-center gap-2 rounded-xl border border-slate-200 bg-slate-50 px-4 py-3 text-xs text-slate-500 dark:border-slate-700 dark:bg-night-900 dark:text-slate-400">
                <ShieldCheck className="h-4 w-4 text-emerald-500" aria-hidden="true" />
                All items in this vault are encrypted at rest and only decryptable by users with
                access.
              </div>
            </div>

            <div id="add-item">
              <AddItemForm vaultId={vaultId} />
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}