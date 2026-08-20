"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileText, Paperclip, Trash2, Upload } from "lucide-react";
import { useRef } from "react";

import { Button } from "@/components/ui/Button";
import { useToast } from "@/lib/toast";
import {
  deleteDocument,
  downloadDocument,
  formatBytes,
  listDocuments,
  uploadDocument,
} from "@/lib/documents";

export function DocumentSection({ vaultId, itemId }: { vaultId: string; itemId: string }) {
  const queryClient = useQueryClient();
  const toast = useToast();
  const fileRef = useRef<HTMLInputElement>(null);

  const { data: documents, isLoading } = useQuery({
    queryKey: ["vault", vaultId, "items", itemId, "documents"],
    queryFn: () => listDocuments(vaultId, itemId),
  });

  const upload = useMutation({
    mutationFn: (file: File) => uploadDocument(vaultId, itemId, file),
    onSuccess: () => {
      toast.push("success", "Document uploaded");
      queryClient.invalidateQueries({
        queryKey: ["vault", vaultId, "items", itemId, "documents"],
      });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  const remove = useMutation({
    mutationFn: (documentId: string) => deleteDocument(vaultId, itemId, documentId),
    onSuccess: () => {
      toast.push("success", "Document deleted");
      queryClient.invalidateQueries({
        queryKey: ["vault", vaultId, "items", itemId, "documents"],
      });
    },
    onError: (err: Error) => toast.push("error", err.message),
  });

  return (
    <div className="rounded-xl border border-slate-200 bg-slate-50/60 p-4 dark:border-slate-700 dark:bg-night-900">
      <div className="flex items-center justify-between">
        <p className="flex items-center gap-2 text-sm font-medium text-slate-700 dark:text-slate-200">
          <span className="flex h-7 w-7 items-center justify-center rounded-lg bg-white text-slate-400 shadow-sm dark:bg-night-800 dark:text-slate-500">
            <Paperclip className="h-3.5 w-3.5" aria-hidden="true" />
          </span>
          Documents
          {documents && documents.length > 0 && (
            <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs font-medium text-brand-700 dark:bg-brand-900/50 dark:text-brand-300">
              {documents.length}
            </span>
          )}
        </p>
        <input
          ref={fileRef}
          type="file"
          className="hidden"
          onChange={(e) => {
            const file = e.target.files?.[0];
            if (file) upload.mutate(file);
            e.target.value = "";
          }}
        />
        <Button
          variant="secondary"
          size="sm"
          onClick={() => fileRef.current?.click()}
          loading={upload.isPending}
        >
          <Upload className="h-4 w-4" aria-hidden="true" />
          Upload
        </Button>
      </div>

      {isLoading ? (
        <div className="mt-3 h-9 animate-pulse rounded-lg bg-slate-200/60 dark:bg-slate-700/40" />
      ) : documents && documents.length > 0 ? (
        <ul className="mt-3 divide-y divide-slate-200/70 dark:divide-slate-700/60">
          {documents.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between gap-3 py-2.5">
              <div className="flex min-w-0 items-center gap-2.5">
                <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-lg bg-brand-50 text-brand-600 dark:bg-brand-900/40 dark:text-brand-400">
                  <FileText className="h-4 w-4" aria-hidden="true" />
                </span>
                <div className="min-w-0">
                  <p className="truncate text-sm text-slate-800 dark:text-slate-100">{doc.original_filename}</p>
                  <p className="text-xs text-slate-400 dark:text-slate-500">
                    {formatBytes(doc.size_bytes)} · {doc.content_type}
                  </p>
                </div>
              </div>
              <div className="flex shrink-0 items-center gap-1">
                <button
                  aria-label={`Download ${doc.original_filename}`}
                  className="rounded-lg p-2 text-slate-400 transition hover:bg-white hover:text-brand-600 hover:shadow-sm dark:text-slate-500 dark:hover:bg-night-800 dark:hover:text-brand-400"
                  onClick={() => downloadDocument(vaultId, itemId, doc.id)}
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  aria-label={`Delete ${doc.original_filename}`}
                  className="rounded-lg p-2 text-slate-400 transition hover:bg-red-50 hover:text-red-600 dark:text-slate-500 dark:hover:bg-red-950/40 dark:hover:text-red-400"
                  onClick={() => {
                    if (confirm(`Delete "${doc.original_filename}"?`)) remove.mutate(doc.id);
                  }}
                >
                  <Trash2 className="h-4 w-4" />
                </button>
              </div>
            </li>
          ))}
        </ul>
      ) : (
        <p className="mt-3 text-xs text-slate-400 dark:text-slate-500">
          No documents yet. Upload files such as scans or PDFs.
        </p>
      )}
    </div>
  );
}