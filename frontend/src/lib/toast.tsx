"use client";

import { createContext, useCallback, useContext, useMemo, useRef, useState } from "react";
import { AlertCircle, CheckCircle2, Info, X } from "lucide-react";

import { cn } from "@/lib/utils";

type ToastKind = "success" | "error" | "info";

type Toast = {
  id: number;
  kind: ToastKind;
  message: string;
};

type ToastContextValue = {
  push: (kind: ToastKind, message: string) => void;
};

const ToastContext = createContext<ToastContextValue | null>(null);

const kindStyles: Record<ToastKind, { icon: React.ReactNode; wrapper: string }> = {
  success: {
    icon: <CheckCircle2 className="h-5 w-5 text-emerald-500" aria-hidden="true" />,
    wrapper:
      "border-emerald-200 bg-white/95 text-slate-800 dark:border-emerald-800/60 dark:bg-night-800/95 dark:text-slate-100",
  },
  error: {
    icon: <AlertCircle className="h-5 w-5 text-red-500" aria-hidden="true" />,
    wrapper:
      "border-red-200 bg-white/95 text-slate-800 dark:border-red-900/60 dark:bg-night-800/95 dark:text-slate-100",
  },
  info: {
    icon: <Info className="h-5 w-5 text-brand-500" aria-hidden="true" />,
    wrapper:
      "border-slate-200 bg-white/95 text-slate-800 dark:border-slate-700/60 dark:bg-night-800/95 dark:text-slate-100",
  },
};

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idRef = useRef(0);

  const push = useCallback((kind: ToastKind, message: string) => {
    const id = ++idRef.current;
    setToasts((prev) => [...prev, { id, kind, message }]);
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4500);
  }, []);

  const dismiss = useCallback((id: number) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const value = useMemo(() => ({ push }), [push]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <div
        aria-live="polite"
        className="pointer-events-none fixed bottom-5 right-5 z-[70] flex w-[calc(100vw-2.5rem)] max-w-sm flex-col gap-2.5"
      >
        {toasts.map((toast) => {
          const style = kindStyles[toast.kind];
          return (
            <div
              key={toast.id}
              role="status"
              className={cn(
                "pointer-events-auto flex items-start gap-3 rounded-xl border px-4 py-3 text-sm shadow-soft backdrop-blur animate-slide-in-right",
                style.wrapper
              )}
            >
              <span className="mt-0.5 shrink-0">{style.icon}</span>
              <p className="flex-1 leading-snug">{toast.message}</p>
              <button
                onClick={() => dismiss(toast.id)}
                className="shrink-0 rounded-md p-0.5 text-slate-400 transition hover:text-slate-600 dark:text-slate-500 dark:hover:text-slate-300"
                aria-label="Dismiss notification"
              >
                <X className="h-4 w-4" />
              </button>
            </div>
          );
        })}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast(): ToastContextValue {
  const ctx = useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}