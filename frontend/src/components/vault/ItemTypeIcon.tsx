import {
  BookText,
  CreditCard,
  FileText,
  HeartPulse,
  KeyRound,
  ScrollText,
  ShieldCheck,
  Siren,
  StickyNote,
  User,
  type LucideIcon,
} from "lucide-react";

import { cn } from "@/lib/utils";
import { type ItemType } from "@/lib/vault";

const TYPE_META: Record<ItemType, { icon: LucideIcon; tint: string }> = {
  document: { icon: FileText, tint: "text-brand-600 dark:text-brand-400" },
  note: { icon: StickyNote, tint: "text-slate-500 dark:text-slate-400" },
  financial: { icon: CreditCard, tint: "text-emerald-600 dark:text-emerald-400" },
  insurance: { icon: ShieldCheck, tint: "text-cyan-600 dark:text-cyan-400" },
  medical: { icon: HeartPulse, tint: "text-red-500 dark:text-red-400" },
  legal: { icon: ScrollText, tint: "text-amber-600 dark:text-amber-400" },
  emergency: { icon: Siren, tint: "text-orange-600 dark:text-orange-400" },
  contact: { icon: User, tint: "text-violet-600 dark:text-violet-400" },
  digital_asset: { icon: KeyRound, tint: "text-blue-600 dark:text-blue-400" },
};

export function ItemTypeIcon({
  itemType,
  className,
}: {
  itemType: ItemType;
  className?: string;
}) {
  const meta = TYPE_META[itemType];
  const Icon = meta.icon;
  return <Icon className={cn(meta.tint, className)} aria-hidden="true" />;
}