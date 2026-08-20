"use client";

import { usePathname, useRouter } from "next/navigation";
import {
  Archive,
  Bell,
  FileText,
  HelpCircle,
  LayoutDashboard,
  LogOut,
  Moon,
  Shield,
  ShieldAlert,
  Sparkles,
  Sun,
  User,
  Users,
  X,
  Menu,
  Settings,
} from "lucide-react";
import Link from "next/link";
import { useEffect, useState } from "react";

import { ChatPanel } from "@/components/ai/ChatPanel";
import { Logo } from "@/components/ui/Logo";
import { cn } from "@/lib/utils";
import { useAuth } from "@/lib/auth";
import { useTheme } from "@/lib/theme";

const navSections: {
  label: string;
  items: { href: string; label: string; icon: React.ComponentType<{ className?: string }> }[];
}[] = [
  {
    label: "Overview",
    items: [
      { href: "/dashboard", label: "Dashboard", icon: LayoutDashboard },
      { href: "/vault", label: "Vault", icon: Archive },
      { href: "/documents", label: "Documents", icon: FileText },
    ],
  },
  {
    label: "Access",
    items: [
      { href: "/trusted-contacts", label: "Trusted contacts", icon: Users },
      { href: "/emergency", label: "Emergency", icon: ShieldAlert },
    ],
  },
  {
    label: "Account",
    items: [
      { href: "/ai", label: "AI assistant", icon: Sparkles },
      { href: "/notifications", label: "Notifications", icon: Bell },
      { href: "/profile", label: "Profile", icon: User },
      { href: "/settings", label: "Settings", icon: Settings },
      { href: "/security", label: "Security", icon: Shield },
    ],
  },
];

function isActive(pathname: string, href: string): boolean {
  return pathname === href || pathname.startsWith(`${href}/`);
}

function NavList({
  pathname,
  onNavigate,
}: {
  pathname: string;
  onNavigate?: () => void;
}) {
  return (
    <nav className="flex-1 space-y-5 overflow-y-auto px-3 py-4" aria-label="Main navigation">
      {navSections.map((section) => (
        <div key={section.label}>
          <p className="mb-1.5 px-3 text-[0.68rem] font-semibold uppercase tracking-widest text-slate-400 dark:text-slate-500">
            {section.label}
          </p>
          <div className="space-y-0.5">
            {section.items.map((item) => {
              const active = isActive(pathname, item.href);
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  onClick={onNavigate}
                  aria-current={active ? "page" : undefined}
                  className={cn(
                    "group flex items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium transition-all duration-200",
                    active
                      ? "bg-brand-50 text-brand-700 dark:bg-brand-900/40 dark:text-brand-300"
                      : "text-slate-600 hover:bg-slate-100 hover:text-slate-900 dark:text-slate-400 dark:hover:bg-night-800 dark:hover:text-white"
                  )}
                >
                  <item.icon
                    className={cn(
                      "h-[1.15rem] w-[1.15rem] transition-colors",
                      active
                        ? "text-brand-600 dark:text-brand-400"
                        : "text-slate-400 group-hover:text-slate-600 dark:text-slate-500 dark:group-hover:text-slate-300"
                    )}
                    aria-hidden="true"
                  />
                  {item.label}
                  {active && (
                    <span className="ml-auto h-1.5 w-1.5 rounded-full bg-brand-500 dark:bg-brand-400" aria-hidden="true" />
                  )}
                </Link>
              );
            })}
          </div>
        </div>
      ))}
    </nav>
  );
}

export function AppShell({ children }: { children: React.ReactNode }) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [chatOpen, setChatOpen] = useState(false);
  const [mobileNavOpen, setMobileNavOpen] = useState(false);

  useEffect(() => {
    setMobileNavOpen(false);
  }, [pathname]);

  const handleLogout = async () => {
    await logout();
    router.replace("/auth/login");
  };

  const initials = (user?.full_name ?? user?.email ?? "?")[0]?.toUpperCase() ?? "?";

  const userFooter = (
    <div className="border-t border-slate-200 p-3 dark:border-slate-800">
      <div className="flex items-center gap-3 rounded-xl px-2 py-2">
        <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-full bg-brand-gradient text-xs font-semibold text-white">
          {initials}
        </div>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-slate-900 dark:text-white">
            {user?.full_name ?? user?.email}
          </p>
          <p className="truncate text-xs text-slate-500 dark:text-slate-400">
            {user?.email}
          </p>
        </div>
      </div>
      <button
        onClick={handleLogout}
        className="mt-1 flex w-full items-center gap-3 rounded-xl px-3 py-2 text-sm font-medium text-slate-600 transition hover:bg-slate-100 hover:text-red-600 dark:text-slate-400 dark:hover:bg-night-800 dark:hover:text-red-400"
      >
        <LogOut className="h-4 w-4" aria-hidden="true" />
        Sign out
      </button>
    </div>
  );

  return (
    <div className="flex min-h-screen bg-slate-50 dark:bg-night-950">
      {/* Desktop sidebar */}
      <aside className="hidden w-64 shrink-0 flex-col border-r border-slate-200 bg-white dark:border-slate-800 dark:bg-night-900 md:flex">
        <div className="flex h-16 items-center border-b border-slate-100 px-5 dark:border-slate-800">
          <Logo href="/dashboard" />
        </div>
        <NavList pathname={pathname} />
        {userFooter}
      </aside>

      {/* Mobile drawer */}
      {mobileNavOpen && (
        <div className="fixed inset-0 z-[60] md:hidden" role="dialog" aria-modal="true" aria-label="Navigation">
          <div
            className="absolute inset-0 bg-slate-950/50 backdrop-blur-sm animate-fade-in"
            onClick={() => setMobileNavOpen(false)}
          />
          <div className="absolute inset-y-0 left-0 flex w-72 max-w-[85vw] flex-col border-r border-slate-200 bg-white animate-slide-in-left dark:border-slate-800 dark:bg-night-900">
            <div className="flex h-16 items-center justify-between border-b border-slate-100 px-5 dark:border-slate-800">
              <Logo href="/dashboard" />
              <button
                onClick={() => setMobileNavOpen(false)}
                className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-800"
                aria-label="Close navigation"
              >
                <X className="h-5 w-5" />
              </button>
            </div>
            <NavList pathname={pathname} onNavigate={() => setMobileNavOpen(false)} />
            {userFooter}
          </div>
        </div>
      )}

      <div className="flex min-w-0 flex-1 flex-col">
        <header className="sticky top-0 z-30 flex h-16 items-center justify-between border-b border-slate-200 bg-white/80 px-4 backdrop-blur dark:border-slate-800 dark:bg-night-900/80 sm:px-6">
          <div className="flex items-center gap-2.5">
            <button
              onClick={() => setMobileNavOpen(true)}
              className="rounded-lg p-2 text-slate-500 transition hover:bg-slate-100 dark:text-slate-300 dark:hover:bg-night-800 md:hidden"
              aria-label="Open navigation"
            >
              <Menu className="h-5 w-5" />
            </button>
            <span className="hidden items-center gap-1.5 text-sm text-slate-500 dark:text-slate-400 sm:flex">
              <HelpCircle className="h-4 w-4" aria-hidden="true" />
              Digital Emergency Vault
            </span>
          </div>

          <div className="flex items-center gap-1.5">
            <button
              onClick={toggleTheme}
              className="rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-night-800 dark:hover:text-white"
              aria-label={theme === "dark" ? "Switch to light mode" : "Switch to dark mode"}
            >
              {theme === "dark" ? <Sun className="h-[1.15rem] w-[1.15rem]" /> : <Moon className="h-[1.15rem] w-[1.15rem]" />}
            </button>
            <Link
              href="/notifications"
              className="rounded-xl p-2.5 text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 dark:text-slate-300 dark:hover:bg-night-800 dark:hover:text-white"
              aria-label="Notifications"
            >
              <Bell className="h-[1.15rem] w-[1.15rem]" />
            </Link>
            <div className="ml-1.5 flex items-center gap-2 border-l border-slate-200 pl-3 dark:border-slate-800">
              <div className="flex h-9 w-9 items-center justify-center rounded-full bg-brand-gradient text-xs font-semibold text-white">
                {initials}
              </div>
              <span className="hidden text-sm font-medium text-slate-700 dark:text-slate-200 lg:block">
                {user?.full_name ?? user?.email}
              </span>
            </div>
          </div>
        </header>

        <main className="flex-1">{children}</main>

        {chatOpen && <ChatPanel onClose={() => setChatOpen(false)} />}
        <button
          onClick={() => setChatOpen((open) => !open)}
          className="group fixed bottom-6 right-6 z-40 flex h-12 w-12 items-center justify-center rounded-full bg-brand-gradient text-white shadow-glow-lg transition-all duration-300 hover:scale-105 active:scale-95"
          aria-label={chatOpen ? "Collapse AI assistant" : "Open AI assistant"}
        >
          <Sparkles className="h-5 w-5 transition-transform duration-300 group-hover:rotate-12" aria-hidden="true" />
        </button>
      </div>
    </div>
  );
}