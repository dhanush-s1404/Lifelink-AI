"use client";

import { AuthProvider } from "@/lib/auth";
import { QueryProvider } from "@/lib/query-provider";
import { ThemeProvider } from "@/lib/theme";
import { ToastProvider } from "@/lib/toast";

export function Providers({ children }: { children: React.ReactNode }) {
  return (
    <QueryProvider>
      <ThemeProvider>
        <AuthProvider>
          <ToastProvider>{children}</ToastProvider>
        </AuthProvider>
      </ThemeProvider>
    </QueryProvider>
  );
}