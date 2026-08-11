"use client";

import { usePathname, useRouter } from "next/navigation";
import { Archive, Bell, HelpCircle, LayoutDashboard, LogOut, Settings, Shield, Sparkles, Users } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";

const navItems = [
  { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
  { href: "/vault", label: "Vault", icon: Archive },
  { href: "/trusted-contacts", label: "Trusted contacts", icon: Users },
  { href: "/emergency", label: "Emergency", icon: Shield },
  { href: "/ai", label: "AI assistant", icon: Sparkles },
  { href: "/notifications", label: "Notifications", icon: Bell },
  { href: "/settings", label: "Settings", icon: Settings },
  { href: "/security", label: "Security", icon: Shield },
];

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();

  return (
    <div className="flex min-h-screen">
      <aside className="hidden w-60 shrink-0 flex-col border-r border-slate-200 bg-white md:flex">
        <div className="flex h-14 items-center border-b border-slate-100 px-5">
          <Link href="/dashboard" className="text-lg font-bold tracking-tight text-slate-900">
            LifeLink <span className="text-brand-600">AI</span>
          </Link>
        </div>
        <nav className="flex-1 space-y-1 p-3">
          {navItems.map((item) => {
            const active = pathname === item.href || pathname.startsWith(`${item.href}/`);
            return (
              <Link
                key={item.href}
                href={item.href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  active
                    ? "bg-brand-50 text-brand-700"
                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-900"
                )}
              >
                <item.icon className="h-4 w-4" />
                {item.label}
              </Link>
            );
          })}
        </nav>
        <div className="border-t border-slate-100 p-3">
          <button
            onClick={async () => {
              await logout();
              router.replace("/auth/login");
            }}
            className="flex w-full items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-slate-900"
          >
            <LogOut className="h-4 w-4" />
            Sign out
          </button>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-10 flex h-14 items-center justify-between border-b border-slate-200 bg-white/80 px-5 backdrop-blur">
          <div className="flex items-center gap-2 text-sm text-slate-500">
            <HelpCircle className="h-4 w-4" />
            <span className="hidden sm:inline">Digital Emergency Vault</span>
          </div>
          <div className="flex items-center gap-3">
            <button
              className="relative rounded-lg p-2 text-slate-500 transition hover:bg-slate-100"
              aria-label="Notifications"
            >
              <Bell className="h-4 w-4" />
            </button>
            <div className="flex items-center gap-2">
              <div className="flex h-8 w-8 items-center justify-center rounded-full bg-brand-600 text-xs font-semibold text-white">
                {(user?.full_name?.[0] ?? user?.email?.[0] ?? "?").toUpperCase()}
              </div>
              <span className="hidden text-sm font-medium text-slate-700 lg:block">
                {user?.full_name ?? user?.email}
              </span>
            </div>
          </div>
        </header>
        <main className="flex-1">{children}</main>
      </div>
    </div>
  );
}
