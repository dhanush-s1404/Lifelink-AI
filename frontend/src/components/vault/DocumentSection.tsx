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
    <div className="rounded-lg border border-slate-200 dark:border-slate-800 bg-white dark:bg-night-900 p-3">
      <div className="flex items-center justify-between">
        <p className="flex items-center gap-1.5 text-sm font-medium text-slate-700 dark:text-slate-200">
          <Paperclip className="h-4 w-4 text-slate-400 dark:text-slate-500" />
          Documents
          {documents && documents.length > 0 && (
            <span className="rounded-full bg-slate-100 dark:bg-night-800 px-2 py-0.5 text-xs text-slate-500 dark:text-slate-400">
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
          <Upload className="h-4 w-4" />
          Upload
        </Button>
      </div>

      {isLoading ? (
        <div className="mt-2 h-8 animate-pulse rounded bg-slate-100 dark:bg-night-800" />
      ) : documents && documents.length > 0 ? (
        <ul className="mt-2 divide-y divide-slate-100 dark:divide-slate-800">
          {documents.map((doc) => (
            <li key={doc.id} className="flex items-center justify-between gap-3 py-2">
              <div className="flex min-w-0 items-center gap-2.5">
                <FileText className="h-4 w-4 shrink-0 text-brand-600 dark:text-brand-400" />
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
                  className="rounded-lg p-2 text-slate-400 dark:text-slate-500 transition hover:bg-slate-100 dark:hover:bg-night-800 hover:text-slate-700"
                  onClick={() => downloadDocument(vaultId, itemId, doc.id)}
                >
                  <Download className="h-4 w-4" />
                </button>
                <button
                  aria-label={`Delete ${doc.original_filename}`}
                  className="rounded-lg p-2 text-slate-400 dark:text-slate-500 transition hover:bg-red-50 dark:hover:bg-red-950/40 hover:text-red-600 dark:hover:text-red-400"
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
        <p className="mt-2 text-xs text-slate-400 dark:text-slate-500">
          No documents yet. Upload files such as scans or PDFs.
        </p>
      )}
    </div>
  );
}
