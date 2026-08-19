"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { ArrowLeft, Eye, EyeOff, Plus, Trash2 } from "lucide-react";
import Link from "next/link";
import { useParams } from "next/navigation";
import { useState } from "react";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { DocumentSection } from "@/components/vault/DocumentSection";
import { useToast } from "@/lib/toast";
import {
  createItem,
  deleteItem,
  getItem,
  ITEM_TYPES,
  itemTypeLabel,
  listItems,
  type ItemType,
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
      setContentJson("");
      queryClient.invalidateQueries({ queryKey: ["vault", vaultId, "items"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Add an item</CardTitle>
      </CardHeader>
      <CardBody>
        <form
          className="flex flex-col gap-3"
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
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">Type</span>
            <select
              value={itemType}
              onChange={(e) => setItemType(e.target.value as ItemType)}
              className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-night-900 px-3 py-2 text-sm text-slate-900 dark:text-white shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
            >
              {ITEM_TYPES.map((t) => (
                <option key={t.value} value={t.value}>
                  {t.label}
                </option>
              ))}
            </select>
          </label>
          <label className="flex flex-col gap-1.5">
            <span className="text-sm font-medium text-slate-700 dark:text-slate-200">
              Content (JSON, encrypted at rest)
            </span>
            <textarea
              value={contentJson}
              onChange={(e) => setContentJson(e.target.value)}
              rows={5}
              spellCheck={false}
              className="rounded-lg border border-slate-300 dark:border-slate-600 bg-white dark:bg-night-900 px-3 py-2 font-mono text-sm text-slate-900 dark:text-white shadow-sm focus:border-brand-600 focus:outline-none focus:ring-2 focus:ring-brand-600/20"
            />
          </label>
          <div>
            <Button type="submit" loading={mutation.isPending} disabled={!title.trim()}>
              <Plus className="h-4 w-4" />
              Add item
            </Button>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}

function ItemRow({ vaultId, item }: { vaultId: string; item: { id: string; title: string; item_type: ItemType; version: number } }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const [revealed, setRevealed] = useState(false);
  const [detail, setDetail] = useState<VaultItemDetail | null>(null);

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
      queryClient.invalidateQueries({ queryKey: ["vault", vaultId, "items"] });
      queryClient.invalidateQueries({ queryKey: ["dashboard", "summary"] });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <li>
      <div className="flex items-center justify-between gap-4 py-3">
        <div className="min-w-0">
          <p className="truncate text-sm font-medium text-slate-900 dark:text-white">{item.title}</p>
          <p className="text-xs text-slate-500 dark:text-slate-400">
            {itemTypeLabel(item.item_type)} · version {item.version}
          </p>
        </div>
        <div className="flex shrink-0 items-center gap-1">
          <Button
            variant="ghost"
            size="sm"
            onClick={() => (revealed ? setRevealed(false) : load.mutate())}
            loading={load.isPending}
          >
            {revealed ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
            {revealed ? "Hide" : "Reveal"}
          </Button>
          <button
            aria-label={`Delete ${item.title}`}
            className="rounded-lg p-2 text-slate-400 dark:text-slate-500 transition hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600 dark:hover:text-red-400"
            onClick={() => {
              if (confirm(`Delete "${item.title}"?`)) remove.mutate();
            }}
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      </div>
      {revealed && detail && (
        <div className="mb-3 space-y-3">
          <pre className="overflow-x-auto rounded-lg bg-slate-50 dark:bg-night-950 p-3 font-mono text-xs text-slate-800 dark:text-slate-100">
            {JSON.stringify(detail.content, null, 2)}
          </pre>
          <DocumentSection vaultId={vaultId} itemId={item.id} />
        </div>
      )}
    </li>
  );
}

export default function VaultDetailPage() {
  const params = useParams<{ id: string }>();
  const vaultId = params.id;
  const toast = useToast();

  const { data: items, isLoading, isError, refetch } = useQuery({
    queryKey: ["vault", vaultId, "items"],
    queryFn: () => listItems(vaultId),
    enabled: Boolean(vaultId),
  });

  return (
    <RequireAuth>
      <AppShell>
        <div className="mx-auto max-w-5xl p-8">
          <div className="flex items-center gap-3">
            <Link
              href="/vault"
              className="rounded-lg p-2 text-slate-500 dark:text-slate-400 transition hover:bg-slate-100 dark:hover:bg-night-800"
              aria-label="Back to vaults"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>
            <div>
              <h1 className="text-2xl font-bold text-slate-900 dark:text-white">Vault items</h1>
              <p className="mt-1 text-sm text-slate-600 dark:text-slate-400">
                Contents are encrypted at rest. Reveal an item to view its decrypted content.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 lg:grid-cols-3">
            <div className="lg:col-span-2">
              {isError && (
                <div className="rounded-lg border border-red-200 dark:border-red-900 bg-red-50 dark:bg-red-950/40 p-4 text-sm text-red-800 dark:text-red-300">
                  <p className="font-medium">Could not load items.</p>
                  <button className="mt-2 text-red-700 underline" onClick={() => refetch()}>
                    Try again
                  </button>
                </div>
              )}

              {isLoading ? (
                <div className="space-y-2">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="h-14 animate-pulse rounded-lg bg-slate-100 dark:bg-night-800" />
                  ))}
                </div>
              ) : items && items.length > 0 ? (
                <Card>
                  <CardBody className="p-0">
                    <ul className="divide-y divide-slate-100 dark:divide-slate-800 px-5">
                      {items.map((item) => (
                        <ItemRow key={item.id} vaultId={vaultId} item={item} />
                      ))}
                    </ul>
                  </CardBody>
                </Card>
              ) : (
                <div className="rounded-xl border border-dashed border-slate-300 dark:border-slate-600 p-10 text-center">
                  <p className="text-sm text-slate-500 dark:text-slate-400">
                    No items yet. Add your first sensitive record.
                  </p>
                </div>
              )}
            </div>

            <div>
              <AddItemForm vaultId={vaultId} />
            </div>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}
