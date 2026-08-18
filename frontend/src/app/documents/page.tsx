"use client";

import { FileText, FolderLock, ShieldCheck } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";

export default function DocumentsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-3">
            <span className="flex h-10 w-10 items-center justify-center rounded-xl bg-brand-50">
              <FileText className="h-5 w-5 text-brand-700" aria-hidden="true" />
            </span>
            <div>
              <h1 className="page-heading">Documents</h1>
              <p className="page-subheading">
                Files are stored inside vault items, where they inherit the item&apos;s access
                controls and encryption.
              </p>
            </div>
          </div>

          <div className="mt-6 grid gap-6 sm:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>How documents work</CardTitle>
              </CardHeader>
              <CardBody>
                <ul className="space-y-3 text-sm text-slate-600">
                  <li className="flex gap-2">
                    <FolderLock className="mt-0.5 h-4 w-4 shrink-0 text-brand-600" aria-hidden="true" />
                    Documents are attached to vault items (notes, records, legal files).
                  </li>
                  <li className="flex gap-2">
                    <ShieldCheck className="mt-0.5 h-4 w-4 shrink-0 text-emerald-600" aria-hidden="true" />
                    Uploaded files are encrypted before storage.
                  </li>
                  <li className="flex gap-2">
                    <FileText className="mt-0.5 h-4 w-4 shrink-0 text-slate-400" aria-hidden="true" />
                    Only you — and trusted contacts during an emergency — can download them.
                  </li>
                </ul>
              </CardBody>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Upload a document</CardTitle>
              </CardHeader>
              <CardBody>
                <p className="text-sm text-slate-600">
                  Open a vault, choose an item, and reveal it to upload files alongside its
                  content.
                </p>
                <div className="mt-4">
                  <Link href="/vault">
                    <Button>Go to your vault</Button>
                  </Link>
                </div>
              </CardBody>
            </Card>
          </div>
        </div>
      </AppShell>
    </RequireAuth>
  );
}