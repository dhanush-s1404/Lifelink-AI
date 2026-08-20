import { ShieldCheck } from "lucide-react";
import Link from "next/link";

import { cn } from "@/lib/utils";

type LogoProps = {
  href?: string;
  className?: string;
  compact?: boolean;
};

export function Logo({ href = "/", className, compact = false }: LogoProps) {
  const mark = (
    <span
      className={cn(
        "flex shrink-0 items-center justify-center rounded-xl bg-brand-gradient text-white shadow-glow",
        compact ? "h-8 w-8" : "h-9 w-9"
      )}
    >
      <ShieldCheck className={cn(compact ? "h-4 w-4" : "h-5 w-5")} aria-hidden="true" />
    </span>
  );

  const wordmark = (
    <span className={cn("text-lg font-bold tracking-tight text-slate-900 dark:text-white", compact && "text-base")}>
      LifeLink{" "}
      <span className="bg-brand-gradient bg-clip-text text-transparent">AI</span>
    </span>
  );

  return (
    <Link href={href} className={cn("flex items-center gap-2.5", className)} aria-label="LifeLink AI home">
      {mark}
      {!compact && wordmark}
    </Link>
  );
}