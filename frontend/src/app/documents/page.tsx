"use client";

import { FileText, FolderLock, ShieldCheck, Upload } from "lucide-react";
import Link from "next/link";

import { RequireAuth } from "@/components/auth/RequireAuth";
import { AppShell } from "@/components/layout/AppShell";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, CardTitle } from "@/components/ui/Card";

const steps = [
  {
    icon: FolderLock,
    title: "Open a vault item",
    description: "Documents are attached to vault items (notes, records, legal files).",
    tint: "text-brand-600 dark:text-brand-400 bg-brand-50 dark:bg-brand-900/40",
  },
  {
    icon: ShieldCheck,
    title: "Encrypted before storage",
    description: "Uploaded files are encrypted before they are stored.",
    tint: "text-emerald-600 dark:text-emerald-400 bg-emerald-50 dark:bg-emerald-900/40",
  },
  {
    icon: FileText,
    title: "Access-controlled downloads",
    description: "Only you — and trusted contacts during an emergency — can download them.",
    tint: "text-slate-600 dark:text-slate-400 bg-slate-100 dark:bg-night-800",
  },
];

export default function DocumentsPage() {
  return (
    <RequireAuth>
      <AppShell>
        <div className="page-shell">
          <div className="flex items-center gap-3">
            <span className="page-heading-icon">
              <FileText className="h-5 w-5" aria-hidden="true" />
            </span>
            <div>
              <h1 className="page-heading">Documents</h1>
              <p className="page-subheading">
                Files are stored inside vault items, where they inherit the item&apos;s access
                controls and encryption.
              </p>
            </div>
          </div>

          <div className="mt-8 grid gap-6 lg:grid-cols-3">
            {steps.map((step, index) => (
              <Card key={step.title} className="transition-all duration-300 hover:-translate-y-0.5 hover:shadow-lifted">
                <CardBody>
                  <div className="flex items-start gap-4">
                    <span className={`flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl ${step.tint}`}>
                      <step.icon className="h-5 w-5" aria-hidden="true" />
                    </span>
                    <div>
                      <span className="text-xs font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">
                        Step {index + 1}
                      </span>
                      <h2 className="mt-0.5 text-sm font-semibold text-slate-900 dark:text-white">
                        {step.title}
                      </h2>
                      <p className="mt-1 text-sm leading-relaxed text-slate-600 dark:text-slate-400">
                        {step.description}
                      </p>
                    </div>
                  </div>
                </CardBody>
              </Card>
            ))}
          </div>

          <Card className="mt-6">
            <CardHeader>
              <CardTitle>Upload a document</CardTitle>
            </CardHeader>
            <CardBody>
              <div className="flex flex-col items-start justify-between gap-4 sm:flex-row sm:items-center">
                <p className="max-w-xl text-sm text-slate-600 dark:text-slate-400">
                  Open a vault, choose an item, and reveal it to upload files alongside its
                  content. Supported types include PDFs, images, and office documents (max 20 MB).
                </p>
                <Link href="/vault">
                  <Button>
                    <Upload className="h-4 w-4" aria-hidden="true" />
                    Go to your vault
                  </Button>
                </Link>
              </div>
            </CardBody>
          </Card>
        </div>
      </AppShell>
    </RequireAuth>
  );
}